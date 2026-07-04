# Dedup & merge — link, don't duplicate

When `docs/` already has content, a CLAUDE.md block may already be covered by an existing note. The
Zettelkasten rule is **"link, don't duplicate."** Creating a second copy is the worst outcome — now two
places can drift apart. This step runs in Step 2, before extraction, for each EXTRACT block.

## Detect coverage

1. Pull the block's topic signals: its heading, distinctive sub-headings, and key nouns/paths it
   mentions.
2. Search existing docs:
   ```bash
   grep -ri "<key phrase>" docs/
   ```
   and skim any strong hit. Judge coverage as one of:

| Coverage | Meaning | Action |
|---|---|---|
| **Full** | an existing note already says what the block says (often the block even ends with "see docs/…") | **No new note.** Replace the CLAUDE.md block with a pointer to the existing note. Diff first — if the block has content the note lacks, append that delta to the note before removing it. |
| **Partial** | an existing note covers part of it | **Append** the block's unique content to that note (`extract … --mode append`), then link. |
| **None** | nothing covers it | **New atomic note** in the chosen PARA bucket (`extract … --mode new`). |

## The "full coverage" case (most important)

A very common pattern: a CLAUDE.md section is a summary that already points at the canonical doc
(e.g. it literally ends "See `docs/…` for the full spec"). That block should **not** be re-extracted
into a new note — it should collapse to a pointer at the existing canonical doc:

```
## <Heading>

> See [`docs/areas/<existing-note>.md`](docs/areas/<existing-note>.md) — load on demand.
```

Before deleting the inline copy, **diff it against the target**. If the inline block contains anything
the target doesn't, append that delta to the target first — never drop content. Only when the target
truly covers the block do you replace it with the pure pointer.

## Guardrails
- **Never delete content without a home.** If in doubt whether the target covers the block, treat it as
  partial and append the delta rather than dropping it.
- **Prefer one canonical note per topic.** If two existing notes both partially cover a topic, that's a
  pre-existing mess — flag it to the user rather than adding a third.
- All of this is judgment; the helper's `extract` only mechanically moves bytes and writes stubs. The
  decision to *link vs create* is yours.
