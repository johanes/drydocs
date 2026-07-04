#!/usr/bin/env python3
"""slim_claude_md.py — deterministic helper for the drydocs skill.

Turns a CLAUDE.md into a lean index by extracting sections into atomic notes
under docs/. Produces one new file, dry-CLAUDE.md (the proposed lean version);
the original CLAUDE.md is left untouched (git is the backup).

Safety invariants:
  * Dry-run is the DEFAULT. Nothing is written without --apply.
  * Refuses to run outside a git work tree (git is the undo mechanism) unless --force.
  * NEVER creates or overwrites a file literally named CLAUDE.md. Promotion
    (`mv dry-CLAUDE.md CLAUDE.md`) is the user's deliberate manual step.
  * Mechanical only: block boundaries, byte-moving, pointer stubs, link indexes.
    All judgment (what to extract, where, how to reword referrers) stays with the
    agent driving the skill.

Subcommands
  outline   FILE                                  Parse markdown into sized sections (JSON).
  refs      --heading H [--file F]                Find references to a section across the repo (JSON).
  extract   FILE --heading H --into P [--mode]    Move a section to a note; leave a pointer stub.
  moc       --root FILE [--docs DIR]              (Re)generate the grouped link index in the root MOC.
  begin     [--src CLAUDE.md] [--dst dry-CLAUDE.md]   Copy the original to a working copy.
  finalize  [--src CLAUDE.md]                         Report dry vs original + review/promote help.
  stamp     FILE --tipo T --area A [--status S]   Prepend minimal frontmatter if absent.

Global flags: --apply (write; default dry-run), --force (skip git guard), --root-dir DIR.
"""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

STUB_MARKER = "> Moved to "
INDEX_START = "<!-- drydocs:index:start -->"
INDEX_END = "<!-- drydocs:index:end -->"
PARA_LABELS = {
    "projects": "Projects",
    "areas": "Areas",
    "resources": "Resources",
    "archive": "Archives",
    "archives": "Archives",
}
TIPO_BY_BUCKET = {
    "projects": "project",
    "areas": "area",
    "resources": "resource",
    "archive": "archive",
    "archives": "archive",
}
TEXT_SUFFIXES = {".md", ".markdown", ".txt", ".rst", ".mdx"}
IGNORE_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist",
               "build", ".next", "target", "vendor", ".idea", ".claude/plugins"}


# ---------------------------------------------------------------------------
# small utilities
# ---------------------------------------------------------------------------
def eprint(*a):
    print(*a, file=sys.stderr)


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def slugify(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-{2,}", "-", s).strip("-")


def git_toplevel(start: Path, force: bool) -> Path:
    try:
        out = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        if force:
            return start
        eprint("error: not inside a git work tree. drydocs relies on git as the undo "
               "mechanism. Run inside a git repo, or pass --force to override.")
        sys.exit(2)


def norm_heading(h: str) -> str:
    return re.sub(r"^#+\s*", "", h).strip().lower()


# ---------------------------------------------------------------------------
# markdown section parsing (code-fence aware)
# ---------------------------------------------------------------------------
def iter_headings(lines):
    fence = None
    for i, line in enumerate(lines):
        s = line.lstrip()
        if s.startswith("```") or s.startswith("~~~"):
            tok = s[:3]
            if fence is None:
                fence = tok
            elif s.startswith(fence):
                fence = None
            continue
        if fence is not None:
            continue
        m = re.match(r"^(#{1,6})\s+(.*\S)\s*$", line)
        if m:
            yield i, len(m.group(1)), m.group(2).strip()


def parse_sections(text: str):
    """Return (sections, lines). A section owns its lower-level subsections."""
    lines = text.splitlines()
    heads = list(iter_headings(lines))
    sections = []
    for idx, (ln, level, title) in enumerate(heads):
        end = len(lines)
        for (ln2, level2, _t2) in heads[idx + 1:]:
            if level2 <= level:
                end = ln2
                break
        n_lines = end - ln
        n_bytes = sum(len(lines[j]) + 1 for j in range(ln, end))
        sections.append({
            "level": level, "title": title,
            "start_line": ln + 1, "end_line": end,
            "n_lines": n_lines, "n_bytes": n_bytes,
        })
    return sections, lines


def find_sections(sections, heading):
    want = norm_heading(heading)
    return [s for s in sections if s["title"].strip().lower() == want]


def is_pointer_stub(lines, sec) -> bool:
    body = lines[sec["start_line"]:sec["end_line"]]  # after heading line
    for ln in body:
        if ln.strip():
            return ln.strip().startswith(STUB_MARKER)
    return False


# ---------------------------------------------------------------------------
# outline
# ---------------------------------------------------------------------------
def cmd_outline(args, ctx):
    p = Path(args.file)
    sections, _ = parse_sections(read_text(p))
    total = p.stat().st_size
    print(json.dumps({"file": str(p), "total_bytes": total, "sections": sections}, indent=2))
    return 0


# ---------------------------------------------------------------------------
# refs
# ---------------------------------------------------------------------------
IMPERATIVE = r"\b(add|append|record|graduate|save|write|put|log|note|register|document|capture)\b"


def walk_text_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        rel = os.path.relpath(dirpath, root)
        parts = set(Path(rel).parts) if rel != "." else set()
        if parts & IGNORE_DIRS or any(seg.startswith(".") and seg not in (".",) and seg != ".claude"
                                      for seg in Path(rel).parts if rel != "."):
            # prune obvious noise but keep .claude
            pass
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for fn in filenames:
            fp = Path(dirpath) / fn
            if fp.suffix.lower() in TEXT_SUFFIXES:
                yield fp


def cmd_refs(args, ctx):
    root = ctx["root"]
    heading = args.heading
    title = norm_heading(heading)
    tokens = {heading.strip("# ").strip(), "#" + slugify(heading)}
    # distinctive sub-headings inside the block (from --file if given)
    src = Path(args.file) if args.file else None
    if src is None:
        for cand in ("CLAUDE.md", "fat-CLAUDE.md", "dry-CLAUDE.md"):
            if (root / cand).exists():
                src = root / cand
                break
    if src and src.exists():
        secs, lines = parse_sections(read_text(src))
        match = find_sections(secs, heading)
        if match:
            sec = match[0]
            for ln, level, t in iter_headings(lines):
                if sec["start_line"] <= ln + 1 < sec["end_line"] and level > sec["level"]:
                    tokens.add(t)
    tokens = {t for t in tokens if len(t) >= 4}

    hits = []
    exclude = {str((root / n).resolve()) for n in ("CLAUDE.md", "fat-CLAUDE.md", "dry-CLAUDE.md")}
    for fp in walk_text_files(root):
        if str(fp.resolve()) in exclude:
            continue
        try:
            content = read_text(fp)
        except (UnicodeDecodeError, OSError):
            continue
        for i, line in enumerate(content.splitlines()):
            for tok in tokens:
                if tok in line:
                    has_claude = "CLAUDE.md" in line
                    low = line.lower()
                    if has_claude and re.search(IMPERATIVE + r"[^.]{0,40}claude\.md", low):
                        tag = "write-target"
                    elif has_claude and re.search(r"claude\.md[^.]{0,40}" + IMPERATIVE, low):
                        tag = "write-target"
                    elif has_claude:
                        tag = "read/source"
                    else:
                        tag = "incidental"
                    hits.append({
                        "file": str(fp.relative_to(root)), "line": i + 1,
                        "tag": tag, "token": tok, "text": line.strip()[:200],
                    })
                    break
    print(json.dumps({"heading": heading, "tokens": sorted(tokens), "hits": hits}, indent=2))
    return 0


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------
def cmd_extract(args, ctx):
    root = ctx["root"]
    src = Path(args.file)
    if src.name == "CLAUDE.md":
        eprint("error: refuse to edit CLAUDE.md in place. Operate on the working copy "
               "(dry-CLAUDE.md). Run `begin` first.")
        return 2
    text = read_text(src)
    sections, lines = parse_sections(text)
    match = find_sections(sections, args.heading)
    if not match:
        eprint(f"error: heading not found: {args.heading!r}")
        return 2
    if len(match) > 1:
        eprint(f"warning: {len(match)} sections match {args.heading!r}; using the first "
               f"(line {match[0]['start_line']}).")
    sec = match[0]
    if is_pointer_stub(lines, sec):
        print(f"skip: {args.heading!r} is already a pointer stub (idempotent).")
        return 0

    heading_line = lines[sec["start_line"] - 1]
    body_lines = lines[sec["start_line"]:sec["end_line"]]  # everything after the heading
    body = "\n".join(body_lines).strip("\n")
    title = sec["title"]

    into = Path(args.into)
    if not into.is_absolute():
        into = root / into
    bucket = into.parent.name
    tipo = args.tipo or TIPO_BY_BUCKET.get(bucket, "reference")
    area = args.area or bucket
    rel_link = os.path.relpath(into, root)                       # link from CLAUDE.md (repo root)
    backlink_target = os.path.relpath(root / "CLAUDE.md", into.parent)  # note -> root CLAUDE.md
    today = datetime.date.today().isoformat()

    note_new = (
        f"---\ntipo: {tipo}\narea: {area}\nstatus: active\nsource: CLAUDE.md\n"
        f"updated: {today}\n---\n\n"
        f"# {title}\n\n"
        f"> Part of [CLAUDE.md]({backlink_target}) — extracted here by drydocs. Load on demand.\n\n"
        f"{body}\n"
    )
    append_block = f"\n\n## {title}\n\n{body}\n"
    stub = f"{heading_line}\n\n{STUB_MARKER}[`{rel_link}`]({rel_link}) — load on demand.\n"

    mode = args.mode
    if mode == "append" and not into.exists():
        mode = "new"

    # rebuild the working file with the stub replacing the block
    new_lines = lines[: sec["start_line"] - 1] + stub.rstrip("\n").split("\n") + lines[sec["end_line"]:]
    new_text = "\n".join(new_lines).rstrip("\n") + "\n"

    if not ctx["apply"]:
        print(f"[dry-run] extract {args.heading!r} ({sec['n_lines']} lines, {sec['n_bytes']} bytes)")
        print(f"  -> {'append to' if mode == 'append' else 'new note'} {rel_link}  (tipo={tipo}, area={area})")
        print(f"  -> replace block in {src.name} with pointer stub:")
        for l in stub.strip("\n").split("\n"):
            print(f"       {l}")
        return 0

    into.parent.mkdir(parents=True, exist_ok=True)
    if mode == "append":
        with into.open("a", encoding="utf-8") as f:
            f.write(append_block)
    else:
        into.write_text(note_new, encoding="utf-8")
    src.write_text(new_text, encoding="utf-8")
    print(f"extracted {args.heading!r} -> {rel_link} ({mode}); stub left in {src.name}")
    return 0


# ---------------------------------------------------------------------------
# moc — regenerate the grouped link index in the root MOC
# ---------------------------------------------------------------------------
def note_title(fp: Path) -> str:
    try:
        text = read_text(fp)
    except OSError:
        return fp.stem
    m = re.search(r"^#\s+(.*\S)\s*$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return fp.stem.replace("-", " ").replace("_", " ")


def build_index(root: Path, docs_dir: Path) -> str:
    groups = {}
    if docs_dir.exists():
        for fp in sorted(docs_dir.rglob("*.md")):
            if fp.name.endswith(".moc.md"):
                continue
            rel_parts = fp.relative_to(docs_dir).parts
            bucket = rel_parts[0] if len(rel_parts) > 1 else "docs"
            groups.setdefault(bucket, []).append(fp)
    if not groups:
        return ""
    out = [INDEX_START, "## Documentation index", ""]
    for bucket in sorted(groups, key=lambda b: list(PARA_LABELS).index(b) if b in PARA_LABELS else 99):
        out.append(f"### {PARA_LABELS.get(bucket, bucket.capitalize())}")
        for fp in groups[bucket]:
            rel = os.path.relpath(fp, root)
            out.append(f"- [{note_title(fp)}]({rel})")
        out.append("")
    out.append(INDEX_END)
    return "\n".join(out).rstrip() + "\n"


def cmd_moc(args, ctx):
    root = ctx["root"]
    rootfile = Path(args.root)
    if not rootfile.is_absolute():
        rootfile = root / rootfile
    if rootfile.name == "CLAUDE.md":
        eprint("error: refuse to edit CLAUDE.md in place; run moc against dry-CLAUDE.md.")
        return 2
    docs_dir = Path(args.docs) if args.docs else (root / "docs")
    if not docs_dir.is_absolute():
        docs_dir = root / docs_dir
    index = build_index(root, docs_dir)
    if not index:
        print("no docs notes found — nothing to index yet.")
        return 0
    text = read_text(rootfile) if rootfile.exists() else ""
    if INDEX_START in text and INDEX_END in text:
        new_text = re.sub(re.escape(INDEX_START) + r".*?" + re.escape(INDEX_END),
                          index.rstrip("\n"), text, flags=re.DOTALL)
    else:
        new_text = text.rstrip("\n") + "\n\n" + index

    if not ctx["apply"]:
        print(f"[dry-run] would (re)generate the index in {rootfile.name}:")
        print(index)
        return 0
    rootfile.write_text(new_text if new_text.endswith("\n") else new_text + "\n", encoding="utf-8")
    print(f"index regenerated in {rootfile.name}")
    return 0


# ---------------------------------------------------------------------------
# begin / finalize
# ---------------------------------------------------------------------------
def cmd_begin(args, ctx):
    root = ctx["root"]
    src = root / args.src
    dst = root / args.dst
    if not src.exists():
        eprint(f"error: {args.src} not found at repo root.")
        return 2
    if dst.exists():
        print(f"skip: {args.dst} already exists (idempotent). Working copy ready.")
        return 0
    if not ctx["apply"]:
        print(f"[dry-run] would copy {args.src} -> {args.dst} (working copy).")
        return 0
    dst.write_text(read_text(src), encoding="utf-8")
    print(f"created working copy {args.dst} from {args.src}.")
    return 0


def cmd_finalize(args, ctx):
    root = ctx["root"]
    orig = root / args.src            # CLAUDE.md, left untouched
    dry = root / "dry-CLAUDE.md"
    if not dry.exists():
        eprint("error: dry-CLAUDE.md not found. Run `begin --apply` and the extraction steps first.")
        return 2
    if orig.exists():
        print(f"{args.src}: {orig.stat().st_size} bytes (untouched)  ->  "
              f"dry-CLAUDE.md: {dry.stat().st_size} bytes (lean)")
    _promotion_help(args)
    return 0


def _promotion_help(args):
    print()
    print("Next steps (your CLAUDE.md is untouched; git keeps its history):")
    print(f"  Review:   git diff --no-index {args.src} dry-CLAUDE.md")
    print(f"  Activate: mv dry-CLAUDE.md {args.src}   (overwrites; the old version stays in git)")
    print("  Discard:  rm dry-CLAUDE.md   (then 'git checkout -- .' and 'git clean -fd docs' to drop notes)")


# ---------------------------------------------------------------------------
# stamp — prepend minimal frontmatter if absent
# ---------------------------------------------------------------------------
def cmd_stamp(args, ctx):
    p = Path(args.file)
    if not p.is_absolute():
        p = ctx["root"] / p
    text = read_text(p)
    if text.lstrip().startswith("---"):
        print(f"skip: {p.name} already has frontmatter (idempotent).")
        return 0
    today = datetime.date.today().isoformat()
    fm = (f"---\ntipo: {args.tipo}\narea: {args.area}\nstatus: {args.status}\n"
          f"updated: {today}\n---\n\n")
    if not ctx["apply"]:
        print(f"[dry-run] would prepend to {p.name}:")
        print(fm)
        return 0
    p.write_text(fm + text, encoding="utf-8")
    print(f"stamped frontmatter on {p.name}.")
    return 0


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------
def build_parser():
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    parent.add_argument("--force", action="store_true", help="skip the git work-tree guard")
    parent.add_argument("--root-dir", default=".", help="repo root hint (default: cwd)")

    p = argparse.ArgumentParser(prog="slim_claude_md.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    o = sub.add_parser("outline", parents=[parent], help="parse markdown into sized sections (JSON)")
    o.add_argument("file")
    o.set_defaults(func=cmd_outline)

    r = sub.add_parser("refs", parents=[parent], help="find references to a section (JSON)")
    r.add_argument("--heading", required=True)
    r.add_argument("--file", help="source file to read sub-headings from (default: CLAUDE.md/fat/dry)")
    r.set_defaults(func=cmd_refs)

    e = sub.add_parser("extract", parents=[parent], help="move a section to a note; leave a stub")
    e.add_argument("file", help="the working copy (dry-CLAUDE.md), never CLAUDE.md")
    e.add_argument("--heading", required=True)
    e.add_argument("--into", required=True, help="target note path, e.g. docs/areas/foo.md")
    e.add_argument("--mode", choices=["new", "append"], default="new")
    e.add_argument("--tipo")
    e.add_argument("--area")
    e.set_defaults(func=cmd_extract)

    m = sub.add_parser("moc", parents=[parent], help="regenerate the grouped link index")
    m.add_argument("--root", default="dry-CLAUDE.md", help="root MOC file (default: dry-CLAUDE.md)")
    m.add_argument("--docs", help="docs dir (default: docs/)")
    m.set_defaults(func=cmd_moc)

    b = sub.add_parser("begin", parents=[parent], help="copy original -> working copy")
    b.add_argument("--src", default="CLAUDE.md")
    b.add_argument("--dst", default="dry-CLAUDE.md")
    b.set_defaults(func=cmd_begin)

    f = sub.add_parser("finalize", parents=[parent], help="report dry vs original + print review/promote help")
    f.add_argument("--src", default="CLAUDE.md")
    f.set_defaults(func=cmd_finalize)

    s = sub.add_parser("stamp", parents=[parent], help="prepend minimal frontmatter if absent")
    s.add_argument("file")
    s.add_argument("--tipo", required=True)
    s.add_argument("--area", required=True)
    s.add_argument("--status", default="active")
    s.set_defaults(func=cmd_stamp)

    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    root = git_toplevel(Path(args.root_dir).resolve(), args.force)
    ctx = {"root": root, "apply": args.apply, "force": args.force}
    return args.func(args, ctx)


if __name__ == "__main__":
    sys.exit(main())
