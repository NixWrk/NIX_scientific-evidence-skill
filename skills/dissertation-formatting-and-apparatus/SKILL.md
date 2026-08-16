---
name: dissertation-formatting-and-apparatus
description: Format and audit the document apparatus of Russian candidate dissertations, including abbreviations, terminology glossaries, bibliographic citations and reference lists, title matter, rendered tables of contents, illustration lists, appendices, and Word review copies with comments or tracked changes. Use for deterministic dissertation-format checks, apparatus generation from an approved manuscript, bibliography reconciliation, or criticism delivered as a report or reviewed .docx.
---

# Dissertation formatting and apparatus

Work only on the apparatus and its document representation. Preserve the
scientific claims, numbers, units, causal strength, and approved terminology of
the supplied manuscript. Return scientific-content problems to the evidence
workflow instead of silently repairing them here.

## Resolve authority before formatting

Load `references/normative-profile.md`. For title-page or final-TOC work also
load `references/title-page-and-word-toc.md`. Resolve applicable versioned normative
cards and local council requirements before selecting a citation form,
bibliographic description, numbering, grouping, sorting, title page, or list.
Treat an uncovered rule as `not_assessed`, never as a pass. Never infer an
obligation from defended-work frequency.

For bibliography work, keep these layers distinct:

- GOST R 7.0.5-2008: bibliographic citations;
- GOST R 7.0.100-2018: bibliographic descriptions;
- council/organization profile: applicability and local choices.

## Choose an operation

### Generate apparatus

Require an approved, versioned manuscript and the relevant ledgers. Generate
only fields supported by those inputs. Materialize a title page with
`scripts/apply_dissertation_title_page.py`. A logical outline comes from the
scientific workflow; finalize it with `scripts/finalize_word_toc.py` only from
Word heading styles and refresh the real field after layout.

### Audit apparatus

Run deterministic scripts first. Emit findings using
`assets/critic-findings.schema.json`. Separate normative violations, internal
inconsistencies, evidence gaps, observed-practice differences, and
recommendations. Keep the original artifact unchanged.

### Produce a Word review copy

Read `references/word-review.md`. Use `scripts/apply_word_review.py` to
materialize the same findings as comments, tracked changes, or a hybrid copy.
Use comments for ambiguity, evidence gaps, structural problems, and alternative
solutions. Use tracked changes only for exact local replacements. Do not accept
changes automatically.

## Audit modules

- Abbreviations: run `scripts/audit_abbreviations.py`; check first expansion,
  one abbreviation–one meaning, list/text closure, and mixed-script collisions.
- Terminology: run `scripts/audit_terminology.py` against an approved term
  ledger; check canonical forms, definitions, aliases, and forbidden variants.
  Do not invent definitions.
- Bibliography: run `scripts/audit_bibliography.py` against a citation ledger
  and resolved normative profile; check resolution, duplicates, numbering,
  selected order, and supported record rules. Do not enforce an unspecified
  sort strategy.
- Title page: require all GOST fields and structured supervisor/consultant
  credentials; enforce a local signature only when its authority is selected.
- Final TOC: derive entries from Word heading styles, reject hierarchy jumps,
  insert a real field, refresh externally, and inspect its cached result.

## Critic and benchmark contract

Validate findings with `scripts/validate_critic_findings.py`. Evaluate the
skill with `scripts/run_dissertation_benchmark.py` and the four stages defined
in `references/evaluation.md`: regression corpus, controlled mutations, clean
controls, and a holdout corpus. Never expose gold issues or mutation logs to
the critic.

## Gates

- Preserve the original file and source hashes.
- Resolve every normative finding to a card and requirement identifier.
- Resolve every Word annotation to one `issue_id`.
- Fail on missing or ambiguous exact-text locators; never guess an anchor.
- Mark unsupported bibliography source types `not_assessed`.
- Gate source quality before language or structure criticism; if the text
  layer is corrupt, emit one source-quality finding and mark dependent checks
  `not_assessed` instead of inventing errors.
- Structurally inspect comments and revisions in OOXML.
- Render and inspect every page after any DOCX write. Rendering does not prove
  that comments exist; verify their OOXML anchors, relationships, and content
  types separately.
