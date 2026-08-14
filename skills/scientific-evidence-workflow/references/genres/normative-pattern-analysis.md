# Genre: normative-pattern analysis

`genre: normative-pattern-analysis` · produces a card, not an evidence bundle

## Purpose

Turn one supplied normative document into a card the workflow may act on.
Until the card exists, the repository holds a pointer to a document and no
established requirement, and every dissertation genre stays blocked.

## Output

This genre does not produce an evidence bundle. Setting it as `task.genre` on a
bundle is rejected. It produces a JSON record under
`references/normative-patterns/`, validated by
`scripts/validate_normative_card.py`.

## Input

Require one document, its local file, its hash, the URL it came from, and the
priority tier it occupies. Require also which portions are actually available:
a document read in part yields a card that says so.

## Procedure

Follow `references/normative-pattern-memory.md`. In outline:

1. Record provenance and `source_kind`.
2. Read the document in order and record each requirement with a locator.
3. Assign binding strength; leave `unclear` where the text is ambiguous.
4. List what the document does not settle and to whom it defers.
5. On a newer version, raise `record_version` and describe the difference
   rather than overwriting.

## A catalogue entry is not the document

The registry entry of a standard carries the designation, the current status
and the dates. It carries nothing about content. Card it with
`source_kind: catalogue_card` and record no requirements — the validator
enforces this. Such a card is still useful: it establishes that a designation
is current, which is exactly what a stale reference gets wrong.

## Do not fill gaps from knowledge

Where the document is silent, the card is silent. A requirement that "everyone
knows" but the document does not state is not observed, and writing it down as
observed is the failure this genre exists to prevent. Model recollection of a
standard is not a source.

## Gates

- Exactly one document.
- Provenance with a `sha256:` hash and an analysis date.
- Every requirement carries a locator.
- No requirements on a card built from a catalogue entry or an index page.
- A conditional requirement names what it applies to.
- An uncertain observation carries a note.

## Stop conditions

Stop and request input when the file is unavailable, when its hash does not
match the registry, when the tier is not established, or when the document
references an annex that was not supplied.

For Russian output, apply `references/russian/genre-micro-report.md` and run
the audit with `--profile genre-micro-report`.
