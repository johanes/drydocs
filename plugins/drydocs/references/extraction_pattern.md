# Extraction pattern — reference-scan → move → repoint (atomically)

This is the hard part and the net-new capability. Moving a block out of `CLAUDE.md` is easy; **not
breaking the things that point at it** is the discipline. Do this per block.

All rewriting happens on the **working copy** `dry-CLAUDE.md` (run `begin --apply` once first). The
original `CLAUDE.md` is never edited in place.

## 1. Scan for references BEFORE moving

```bash
python3 "$H" refs --heading "<Heading>"
```
It derives tokens from the heading (the text, its slug anchor `#…`, and distinctive sub-headings inside
the block), greps the repo (excluding the CLAUDE.md variants), and tags each hit:

- **read/source** — a file that *reads from* or cites the block (e.g. a manifest row, a doc that says
  "see CLAUDE.md → X"). It expects the content to be findable.
- **write-target** — a file that instructs an agent to *append to* the block (e.g. "record new patterns
  in CLAUDE.md → Recurring patterns"). Moving the block changes where they should write.
- **incidental** — the token appears but not in a CLAUDE.md context. Usually no action.

The tags are **heuristic** — always eyeball the surrounding text and re-classify if wrong.

## 2. Decide handling per referrer

- **read/source** → repoint it to the new note path.
- **write-target** → a decision, not an automatic move. A block that agents append to *every session*
  (a living log) may be **better kept inline** in CLAUDE.md as its growth point. Either:
  (a) keep the block (classify it KEEP after all), or
  (b) repoint **every** write-target referrer to the new note so they append there instead.
  Never move the block and leave a write-target pointing at a location that no longer holds it.
- **incidental** → usually skip; repoint only if it genuinely refers to the moved content.

## 3. Move the block

```bash
python3 "$H" extract dry-CLAUDE.md --heading "<Heading>" --into docs/<bucket>/<note>.md --mode new
```
- Writes the block as an **atomic note** (frontmatter + `# Title` + a backlink to `CLAUDE.md` + the
  body). `--mode append` adds it under a sub-heading in an existing note instead.
- Replaces the block in `dry-CLAUDE.md` with a **pointer stub that keeps the original heading**:
  ```
  ## <Heading>

  > Moved to [`docs/<bucket>/<note>.md`](docs/<bucket>/<note>.md) — load on demand.
  ```
- **Split catalogs:** for a multi-item block, run `extract` once per meaningful sub-heading into
  separate atomic notes, then build a hub (`moc`) — this is the Zettelkasten atomicity rule.

### Why keep the heading in the stub
It is a **graceful-degradation safety net**: any prose referrer that names the heading still lands on a
stub that redirects, so a *missed* referrer degrades to a redirect instead of a dangling reference. It's
also the **idempotency marker** — `extract` skips a block that is already a stub.

## 4. Repoint, then verify

Apply the referrer edits decided in step 2 (Edit — wording is judgment). Then **re-run `refs`** for the
same heading and confirm no referrer still claims the content lives "in CLAUDE.md". This closes the loop.

## 5. Atomic commit

Extraction + its referrer repoints + the MOC update for that pass go into **one commit**. A partial
state (block moved, referrers stale) is never committed, and `git revert <commit>` is a clean, total
undo. Recommend doing the whole drydocs run on a dedicated branch.

## Idempotency & safety recap
- Re-running `extract` on an already-moved block → **skip** (stub detected).
- The helper refuses to run outside a git tree and never writes a file named `CLAUDE.md`.
- Only Markdown / agent-instruction files are touched — never application source or config.
