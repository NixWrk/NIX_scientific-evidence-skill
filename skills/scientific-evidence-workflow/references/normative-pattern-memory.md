# Normative-pattern memory

## Purpose

A normative document becomes usable only as a card. Until a card exists, the
workflow has a pointer to a document, not a requirement, and must not act as
though a rule were established. This mirrors `journal-pattern-memory.md` but
carries an authority the journal example never has: a normative requirement
overrides a stylistic preference and outranks any defended example.

## What may be carded

Card the text that states the requirements. A registry entry, a catalogue card,
or a listing page is not that text: it establishes the designation, the current
status, and the dates, and nothing about content. Record its `source_kind`
honestly. The validator refuses to accept requirements on a card whose source
is a catalogue entry, because a designation standing in for content is the
failure this whole mechanism exists to prevent.

## Required provenance

Create one JSON record from `assets/normative-pattern.template.json`. Preserve:

- a stable `pattern_id` and the registry `document_id` it cards;
- the priority `tier`, so a conflict can be resolved without argument;
- `source_kind`, the local file, its `sha256:` hash, the retrieval URL, and the
  analysis date;
- `coverage`: which portions of the document were actually read.

Store records under `references/normative-patterns/<pattern-id>.json`.

## Extraction procedure

Read the document in order and record only what it states:

1. structure: required parts, their order, what is optional;
2. length limits, where the document states them;
3. page layout, typography, numbering, headings;
4. citation and reference conventions, and which external standard is invoked
   for them;
5. tables, figures, equations, appendices;
6. declarations, approvals, signatures, and physical submission;
7. deadlines and counts;
8. what the document explicitly leaves to another authority.

Each requirement carries a locator into the document. A requirement without a
locator cannot be checked back and is not recorded.

## Binding strength

Use `mandatory`, `recommended`, `conditional`, or `unclear`. A conditional
requirement names what it applies to. `unclear` is a legitimate outcome and is
better than promoting an ambiguous sentence to a rule; it tells a later reader
where to ask.

Do not convert a recommendation into a requirement because it seems sensible,
and do not soften a requirement because it seems inconvenient.

## What was not observed

List every feature the document does not settle. This list carries as much
weight as the requirements: silence about an absent rule reads as completeness
later, and the next reader will assume the question was answered. Where the
document defers to another authority, name that authority.

## Versioning and conflict

Keep an old record when a newer document changes a requirement. Raise
`record_version` and describe the difference in `conflicts` rather than
overwriting. Two publications of the same requirements are not established as
identical until their hashes or their content are compared; where only one was
retrievable, say so.

## Application gate

Apply a card only when the task names its `pattern_id` and the stored hash
still identifies the analyzed file. Where cards conflict, the lower priority
tier wins. A defended example never overrides a card, and a card never
overrides a document of a higher tier.

Run:

```text
python scripts/validate_normative_card.py card.json
```

The validator checks structure, provenance, and the catalogue-entry rule. It
cannot check whether a requirement was read correctly; that needs a second
reading against the locator.
