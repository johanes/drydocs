# Changelog

All notable changes to the `drydocs` plugin are documented here. Versions follow [semver](https://semver.org/).

## [0.1.1] - 2026-07-04

- Marketplace renamed to `cardio`, so installing reads `drydocs@cardio` (no repeated name).
- Single-skill-at-root layout: the command is now `/drydocs` (was `/drydocs:drydocs`).
- Runs end-to-end without pausing to ask for confirmation (the output is non-destructive), instead of
  stopping mid-run for approval.
- Produces only `dry-CLAUDE.md`; the original `CLAUDE.md` is left untouched (git is the backup). No more
  `fat-CLAUDE.md` rename.
- Marketplace description aligned with the README.

## [0.1.0] - 2026-07-04

Initial release.

- `drydocs` skill: slims your `CLAUDE.md` into a lean index and extracts the detail into a
  well-organized `docs/` folder.
- Classification grounded in **MOC** (Maps of Content), **PARA** (Projects / Areas / Resources /
  Archives), and **Zettelkasten** (atomic, linked notes).
- Non-destructive: leaves your original `CLAUDE.md` untouched (git is the backup), writes the lean
  version as `dry-CLAUDE.md`, and leaves promotion to you.
- `slim_claude_md.py` helper (stdlib-only): `outline`, `refs`, `extract`, `moc`, `begin`, `finalize`,
  `stamp`. Dry-run by default; refuses to run outside a git work tree; idempotent.
