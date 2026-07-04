---
name: drydocs
description: >-
  Slim your CLAUDE.md into a lean index and move the detail into a well-organized docs/ folder,
  so the always-loaded context stays small (token savings) and detail loads on demand. Classifies with
  MOC (Maps of Content) + PARA (Projects/Areas/Resources/Archives) + Zettelkasten (atomic, linked
  notes). Non-destructive (leaves your CLAUDE.md untouched; writes dry-CLAUDE.md), idempotent, git-reversible.
  Use when a CLAUDE.md is too long, or the user says "slim my CLAUDE.md", "my CLAUDE.md is huge",
  "organize CLAUDE.md into docs", "make CLAUDE.md a lean index". This is the subtractive counterpart
  to onboarding skills that *add* structure — drydocs *removes* inline bulk and leaves pointers.
allowed-tools: Read Grep Glob Edit Write Bash(git:*) Bash(ls:*) Bash(find:*) Bash(python3:*)
---

# drydocs — slim CLAUDE.md into a lean index

`CLAUDE.md` loads into context **every session**. When it's a monolith, every turn pays for detail it
doesn't need. drydocs turns it into a **lean index** (identity + always-apply rules + pointers) and
moves the bulk into a `docs/` folder of atomic, linked notes.

It is **non-destructive**: it never touches your live `CLAUDE.md`. It writes the proposed lean version
as `dry-CLAUDE.md` (one new file; your original stays put, and git keeps its history), and leaves the
final `mv dry-CLAUDE.md CLAUDE.md` to you.

## Quick start

```bash
H="${CLAUDE_SKILL_DIR}/scripts/slim_claude_md.py"   # the deterministic helper (stdlib-only)

python3 "$H" outline CLAUDE.md                       # 1. see sections + sizes (JSON)
# 2. classify each section (agent judgment) → KEEP vs EXTRACT + PARA bucket
python3 "$H" begin --apply                            # 3. make the dry-CLAUDE.md working copy
python3 "$H" refs --heading "<H>"                    #    find who references a block BEFORE moving it
python3 "$H" extract dry-CLAUDE.md --heading "<H>" --into docs/<bucket>/<note>.md --apply
# … repoint referrers (Edit), repeat per block …
python3 "$H" moc --root dry-CLAUDE.md --apply         # 4. (re)build the grouped link index
python3 "$H" finalize                                 # 5. report size drop + review/promote help (CLAUDE.md untouched)
```
**Just run it end-to-end, don't stop to ask.** The output is non-destructive: it never overwrites
`CLAUDE.md`, it only produces `fat-`/`dry-` copies + notes as one `git revert`-able commit. So drive the
whole flow with `--apply` and report the result when done. (The helper's `--dry-run` default is only for
previewing a single command by hand.) The **one** thing you never do automatically is the final
`mv dry-CLAUDE.md CLAUDE.md` promotion. That stays the user's call.

## When it activates

Triggers: "slim/shrink my CLAUDE.md", "my CLAUDE.md is too long/huge", "organize CLAUDE.md into docs",
"make CLAUDE.md a lean index / an MOC", "reduce CLAUDE.md tokens".

**Guard — refuse unless inside a git work tree.** git is the undo mechanism; the helper enforces this
and refuses to run otherwise. Recommend working on a branch.

## Organization model (summary)

Classification is grounded in three established methods — full detail + citations in
`references/organization-model.md`:

- **MOC (Maps of Content):** `CLAUDE.md` becomes the **root MOC** — a lean hub of links + the few
  always-apply rules. Large areas get their own sub-MOC hub page.
- **Zettelkasten:** each extracted block becomes an **atomic note** (one topic), connected by links;
  "link, don't duplicate" resolves the case where a block already lives in an existing doc.
- **PARA:** the `docs/` folders organize by **actionability** — `projects/`, `areas/` (standards &
  rules), `resources/` (reference & catalogs), `archive/` (superseded).

If the repo already has a `docs/` structure, **respect it** and map into the closest existing bucket;
only lay down the PARA skeleton when creating `docs/` fresh.

## Flow

1. **Analyze → classify.** `outline CLAUDE.md` gives sized sections. For each, decide **KEEP-in-root-MOC**
   (identity, terse always-apply rules, the link index) vs **EXTRACT** (specs, catalogs, tool/setup
   detail, verbose prose, duplicates), and for EXTRACT pick the **PARA bucket + note title**. Rubric in
   `references/classification.md`. This step is read-only: keep the decision table + projected savings
   for your final summary, then continue straight into the next steps (no need to pause for approval).
2. **Detect `docs/` + choose targets.** If absent, plan the PARA skeleton. If present, respect it and
   run **dedup** (`references/dedup_merge.md`): if an existing note already covers a block → plan a
   **link** to it (no new note); partial → append the delta; none → a new atomic note.
3. **Per block: reference-scan → move → repoint (atomically).** See `references/extraction_pattern.md`.
   - `begin --apply` once, to create the `dry-CLAUDE.md` working copy (never edit `CLAUDE.md`).
   - `refs --heading "<H>"` **before** moving: it tags referrers **read/source**, **write-target**, or
     **incidental** (heuristic — you refine). read/source → repoint to the note; **write-target →
     decide**: a block agents append to every session may be better kept inline (surface it); else
     repoint every referrer — never silently orphan one.
   - `extract dry-CLAUDE.md --heading "<H>" --into docs/<bucket>/<note>.md [--mode new|append]` moves
     the block to an atomic note and leaves a **pointer stub that keeps the heading** in the working
     copy. Split a multi-item catalog into several atomic notes (+ a hub) by extracting per sub-heading.
   - Apply the referrer repoints with Edit, then re-run `refs` to confirm nothing still says the content
     is "in CLAUDE.md".
4. **Rebuild the index.** `moc --root dry-CLAUDE.md --apply` regenerates the grouped link index (and any
   `*.moc.md` hub) from what's on disk. `dry-CLAUDE.md` is now: identity + always-apply rules + the
   grouped pointer index.
5. **Finish + hand off.** `finalize` reports the size drop and prints the review/promote instructions.
   Your original `CLAUDE.md` is left untouched; the only new file is `dry-CLAUDE.md` (plus the notes).
   **Do not promote for the user** (the final `mv dry-CLAUDE.md CLAUDE.md` is theirs). Commit the change
   as one commit so `git revert` is a clean undo.

## Safety & idempotency

- **Non-destructive:** the helper never creates or overwrites a file named `CLAUDE.md`. Promotion is the
  user's manual `mv dry-CLAUDE.md CLAUDE.md`.
- **Act, don't ask:** the output is non-destructive and git-reversible, so run the whole flow with
  `--apply` without pausing for permission. Report what you did at the end. The only never-automatic
  step is the final `mv dry-CLAUDE.md CLAUDE.md` promotion.
- **Idempotent:** re-running skips blocks already turned into pointer stubs and rows already indexed;
  a second pass on a slim repo is a no-op.
- **Reversible:** every change is a git-visible edit; the operation is one commit, so `git revert` undoes
  it (removes `dry-CLAUDE.md` and the notes). Your `CLAUDE.md` was never modified in the first place.
- **Scope:** only touches Markdown / agent-instruction files. Never edits application source or config.
  No RAG / embeddings / vector index — navigation is the manifest + grep + links.

## References
- `references/organization-model.md` — MOC + PARA + Zettelkasten, with citations. The backbone.
- `references/classification.md` — the KEEP-vs-EXTRACT rubric and which PARA bucket.
- `references/extraction_pattern.md` — the reference-scan → move → repoint discipline (the hard part).
- `references/dedup_merge.md` — detecting when to link to an existing note instead of creating one.
- `scripts/slim_claude_md.py` — the deterministic helper (`outline`, `refs`, `extract`, `moc`, `begin`,
  `finalize`, `stamp`). `--help` on any subcommand.
