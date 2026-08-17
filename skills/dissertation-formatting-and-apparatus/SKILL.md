---
name: dissertation-formatting-and-apparatus
description: Format and audit the document apparatus of Russian candidate dissertations, including abbreviations, terminology glossaries, bibliographic citations and reference lists, title matter, rendered tables of contents, illustration lists, appendices, and optional review artifacts such as Word copies with comments or tracked changes. Use for deterministic dissertation-format checks, apparatus generation from an approved manuscript, bibliography reconciliation, or delivery of criticism in a requested representation.
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

Scientific-content criticism belongs to `scientific-evidence-workflow`.
This skill checks technical apparatus rules and may deliver findings from other
skills, but it must not rewrite their rationale or severity.

### Deliver a review

Choose a delivery representation after the criticism is complete. Plain JSON,
Markdown or a report needs no Word dependency.

For a Word review copy, read `references/word-review.md`. Use
`scripts/apply_word_review.py` to materialize the same findings as comments,
tracked changes, or a hybrid copy. Use comments for ambiguity, evidence gaps,
structural problems, and alternative solutions. Use tracked changes only for
exact local replacements. Do not accept changes automatically.

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
- Title page: generate with `scripts/apply_dissertation_title_page.py`; audit an
  existing DOCX with `scripts/audit_dissertation_title_page.py` against the same
  approved facts. Require all GOST fields and structured supervisor/consultant
  credentials; enforce a local signature only when its authority is selected.
  If the first-page boundary is not explicit, return a source-quality
  recommendation instead of inferring missing normative fields.
- Final TOC: derive entries from Word heading styles, reject hierarchy jumps,
  insert a real field, and refresh externally. Audit an existing refreshed copy
  with `scripts/audit_existing_word_toc.py`. Do not treat a missing Word field as
  a GOST violation and do not claim that cached page numbers were verified.
- Illustrations and tables: run `scripts/audit_illustration_register.py`
  against an approved registry; check unique numbers, matching captions, and a
  separate main-text reference. Treat declared pages as a final-render concern.
- Appendices: run `scripts/audit_appendix_register.py` against an approved
  registry; check unique designations, matching titles, and references from the
  main text before the first appendix. If the appendix boundary or final page
  cannot be established, return `not_assessed` rather than infer it.

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
- Require an evidence-verification record only when a delivered finding makes
  a factual, numeric, absence, citation-coverage, or normative assertion.
- Fail on missing or ambiguous exact-text locators; never guess an anchor.
- Mark unsupported bibliography source types `not_assessed`.
- Gate source quality before language or structure criticism; if the text
  layer is corrupt, emit one source-quality finding and mark dependent checks
  `not_assessed` instead of inventing errors.
- Structurally inspect comments and revisions in OOXML.
- Render and inspect every page after any DOCX write. Rendering does not prove
  that comments exist; verify their OOXML anchors, relationships, and content
  types separately.
