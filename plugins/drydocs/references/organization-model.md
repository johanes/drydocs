# Organization model — MOC + PARA + Zettelkasten

drydocs does not invent a taxonomy. It applies a documented hybrid of three established
knowledge-organization methods. This file is the backbone the classification and extraction steps
apply.

## The three methods

### MOC — Maps of Content
A **MOC** is a hub page whose job is to *link out* to related notes — an index, not a container.
(Popularized by Nick Milo / *Linking Your Thinking*.)

- **`CLAUDE.md` is reframed as the root MOC.** After slimming it holds: repo identity, the handful of
  genuinely always-apply rules, and a **grouped link index** pointing at the notes. It is navigation +
  invariants, not detail.
- **Large areas get a sub-MOC.** If one area accumulates many notes, emit a hub page
  (`docs/<bucket>/<area>.moc.md`) so the root MOC links to the hub and the hub links to the atomic
  notes — a two-level index that keeps the always-loaded file minimal.

### Zettelkasten — atomic, linked notes
Notes are **atomic** (one concept per note) and connected by **links** rather than deep folder trees.
(From Niklas Luhmann's slip-box method.)

- Each extracted block becomes **one atomic note** with a clear title.
- Notes **link** to related notes and back to their MOC. Connection lives in links, not in folder depth.
- A multi-item catalog (e.g. a "Recurring patterns" list) is split into **several atomic notes + a hub
  MOC**, at a sensible granularity — one note per meaningful sub-topic, never absurdly granular.
- **"Link, don't duplicate."** If a topic already has a note, you *link* to it; you never copy it. This
  is the rule that resolves the dedup/merge case (see `dedup_merge.md`).

### PARA — organize by actionability
Top-level buckets by **how a note is used**, not by topic. (Tiago Forte, *Building a Second Brain*.)

| Bucket | Holds | Typical CLAUDE.md content |
|---|---|---|
| **Projects** (`docs/projects/`) | active, goal/deadline-bound work | in-flight plans/specs |
| **Areas** (`docs/areas/`) | ongoing standards & responsibilities to uphold | coding conventions, security posture, validation rules, lint policy |
| **Resources** (`docs/resources/`) | reference material by topic | architecture notes, pattern catalogs, tool/setup detail, vendor docs |
| **Archives** (`docs/archive/`) | inactive / superseded | old plans, deprecated specs |

## How they compose

- **PARA** gives the *top-level folders* (by actionability).
- **Zettelkasten** keeps the notes *atomic and flat-ish inside* those folders, connected by *links*.
- **MOCs** are the *navigation layer* — `CLAUDE.md` at the root, hub pages per area — that makes a
  link-based system browsable.

The three don't conflict; they cover different axes (folders / notes / navigation). This PARA-buckets +
Zettelkasten-notes + MOC-navigation hybrid is a common, well-documented setup in tools like Obsidian.

## Adaptivity (this is generic — it must fit any repo)

- **Respect an existing `docs/` structure.** If the repo already organizes docs (e.g. `docs/guides/`,
  `docs/adr/`), map extracted notes into the **closest existing bucket** rather than imposing PARA on
  top. Only lay down the PARA skeleton when creating `docs/` from scratch.
- **Bucket names are conventional, not mandatory.** A repo that prefers a flat Zettelkasten (links +
  MOCs, no PARA folders) is fully supported — extract into `docs/` and rely on the MOC + links.
- **Nothing is hardcoded.** No project-specific paths or types live in the tooling; this model is the
  only classification input, applied by judgment.

## Citations
- PARA — Tiago Forte, *The PARA Method* / *Building a Second Brain* (fortelabs.com).
- Zettelkasten — Niklas Luhmann's slip-box (zettelkasten.de).
- MOC (Maps of Content) — Nick Milo, *Linking Your Thinking* (LYT).
