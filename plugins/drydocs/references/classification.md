# Classification rubric — KEEP vs EXTRACT

Applied in Step 1, section by section, seeded by `slim_claude_md.py outline`. The goal: the root MOC
(`CLAUDE.md`) should be the smallest thing that still steers every session correctly. Everything else
loads on demand.

## KEEP in the root MOC (leave it in CLAUDE.md)

- **Repo identity** — the one-line "what is this project" header.
- **Genuinely always-apply rules** — short directives you want in *every* prompt, e.g. "never commit
  secrets", "one commit per PR", a critical safety invariant. If it must be true on every task
  regardless of topic, it stays.
- **The link index itself** — the grouped pointers to the notes (this is the MOC's whole job).

Rule of thumb: **keep it terse.** If a "keep" section runs long, keep a one-line always-apply core in
CLAUDE.md and extract the *elaboration* to an Area note.

## EXTRACT to an atomic note (move it to docs/, leave a pointer)

Signals a block should move:
- It's a **spec / detailed procedure** (e.g. a multi-step validation standard).
- It's a **catalog or enumeration** (a list of patterns, commands, checklists) → split into atomic
  notes + a hub MOC.
- It's **tool / setup / environment detail** (Docker, CI, lint mechanics) — needed sometimes, not
  every turn.
- It's **verbose prose / background / rationale** — good to have, not always-apply.
- It **duplicates an existing doc** → don't move; replace with a **link** (see `dedup_merge.md`).

### Which PARA bucket
| The block is… | Bucket |
|---|---|
| a standard / convention / rule to uphold (validation, security, style, lint) | **Areas** |
| reference material, a pattern catalog, tool/setup detail, vendor notes | **Resources** |
| an active, in-flight plan or spec | **Projects** |
| superseded / historical / deprecated | **Archives** |

If the repo already has a `docs/` layout, map to the **closest existing folder** instead (see
`organization-model.md` → Adaptivity).

## Borderline calls
- **"Always-apply but long"** → keep a one-line rule in CLAUDE.md; extract the detail to an Area note
  and link it. (Example: a form-validation *policy line* stays; the full three-layer spec moves.)
- **A section other files are told to append to every session** (a growth log like "recurring
  patterns") → this is a *write-target* (see `extraction_pattern.md`). Extracting it means agents now
  append to the note instead; if you'd rather keep the append-point in CLAUDE.md, that's a legitimate
  KEEP — surface the choice, don't decide silently.
- **Small sections** (a few lines) → extracting can cost more (a stub + a file) than it saves; keep
  trivially small always-relevant sections inline.

## Output of this step
A decision table: for each section → KEEP or EXTRACT, the target bucket + note title if EXTRACT, and a
one-line rationale. Plus the projected byte savings (`outline` gives sizes). Nothing is written yet.
