# Journal-pattern memory

## Purpose

Use this memory only to reproduce formatting patterns observed in an example
that the user supplied from a named journal. A journal example is formatting
evidence, not scientific evidence. Never use its scientific statements,
references, data, or conclusions to support the new manuscript unless the user
also supplied that publication as part of the scientific corpus.

## Required provenance

Create one JSON record from `assets/journal-pattern.template.json`. Preserve:

- a stable pattern identifier and journal name;
- the example source identifier, local reference, content hash, and access or
  analysis date;
- which portions of the example were actually available;
- every observed pattern and every feature that remained unobserved.

Store records under `references/journal-patterns/<pattern-id>.json`. Keep old
records when a new example changes a pattern. Increase the record version and
describe the conflict instead of silently replacing earlier observations.

## Extraction procedure

Inspect the supplied example in document order and record only observable
features:

1. front matter, title, author and affiliation arrangement;
2. abstract form, length when measurable, and keyword placement;
3. section order, heading hierarchy, and numbering;
4. page layout, body typography, paragraph, list, equation, abbreviation, and
   unit conventions;
5. narrative progression, paragraph functions, and reusable transition forms;
6. in-text citation and reference-list patterns;
7. table and figure caption, numbering, callout, and note patterns;
8. declarations, data statements, acknowledgements, and supplements;
9. explicit length or formatting constraints printed in the example.

For narrative patterns, store rhetorical functions rather than long copied
sentences. Separate useful transitions from unsupported boosters, vague
evaluations, typographical errors, and source-specific conclusions. A phrase
observed in the example remains subject to the evidence and Russian-language
gates when applied to another manuscript.

Use `observed`, `not_observed`, or `uncertain` for each feature. One example
shows a pattern in that example; it does not establish a universal journal
rule. Label inferred regularities as `uncertain` and state their basis.

Record a user clarification about variable journal practice separately from
the example observations. In particular, the absence of a Discussion heading
in one article does not mean that the journal forbids it. Treat the heading as
optional when the user confirms that both variants occur, while preserving the
functions of interpretation, literature comparison, and limitations.

## Application gate

Apply a record only when the task names its `pattern_id` and the stored hash
still identifies the supplied example. Scientific accuracy, the evidence
ledger, and explicit user instructions override formatting patterns. Do not
invent missing sections, figures, word limits, reference styles, or submission
requirements.

The record is plain UTF-8 JSON so an instruction-following local model can use
it without function calling or external services.
