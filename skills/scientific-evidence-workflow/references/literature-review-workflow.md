# Literature-review workflow

## Input

Require a fixed corpus, topic or review question, intended review type, and
delivery constraints. Select the synthesis profile in
`literature-review-patterns.md` before accepting or proposing a reader-facing
structure. Do not call a review systematic unless real search, screening,
extraction, and eligibility provenance is supplied.

An optional `project_context` may route themes to project objective and
question IDs. It is not evidence. A project-context hash change invalidates the
project-relative synthesis and requires it to be rebuilt against the new
context, even when the publications themselves are unchanged.

For a dynamic Zotero subcollection, use `zotero-living-review` to maintain the
logical living review. Every published review version must nevertheless be
based on one immutable full-corpus snapshot. Any relevant source, validated
annotation, removal, or project-context change creates a new snapshot and a
full resynthesis; never update a published review by appending prose only.

## Procedure

1. Select one profile from `literature-review-patterns.md` using the question,
   source types, and actual corpus provenance.
2. Convert the question into analytical dimensions that can organize the body.
3. Create one profile-aware source card per source. Use the common core plus
   only the fields relevant to that profile; never force every discipline into
   a population-sample-outcome card.
4. Normalize genuinely comparable quantities without changing units,
   denominators, definitions, or time points.
5. Build a cross-source matrix around the analytical dimensions and mark each
   comparison `direct`, `qualified`, `contextual`, or `not_comparable` with a
   reason.
6. Deduplicate by underlying study and source before counting support.
7. Keep positive, null, contrary, missing, and inapplicable evidence visible;
   preserve internal conflicts inside a publication.
8. Draft synthesis claims only after the matrix and claim ledger exist. Attach
   every constraining limitation to the claim it bounds.
9. Plan analytical paragraphs and the profile-specific conclusion before
   producing continuous prose.

An annotation may route or reuse study-card extraction, but it never becomes
evidence. Downstream claims cite the publication and its locators. A new or
changed item without a current validated annotation blocks synthesis in the
living-review route.

## Bibliographic apparatus

For a Russian-language review, apply `bibliography-gost.md` to every in-text
reference and every record in the reference list. Select one GOST-permitted
reference form and use it consistently. Resolve each in-text reference to one
publication record; cite the publication, not its annotation or Zotero note.

Reproduce a publication title exactly in the language and form supplied by the
publication. Do not translate the title or replace it with a Russian paraphrase.
Add a parallel title only when the source itself supplies it as a parallel
title. Verify Zotero metadata against the publication when possible and retain
an explicit incompleteness status instead of inventing a missing field.

## Evidence-strength language

Describe the actual pattern instead of assigning an opaque quality score. Name:

- the number of independent studies;
- their designs and relevant limitations;
- whether results are consistent, mixed, or conflicting;
- whether the comparison is direct or indirect.

Do not use venue prestige, citation counts, or recency as substitutes for
methodological relevance to a claim.

## Output structure

Use the selected profile and subject matter to determine reader-facing
headings. Do not impose separate chapters for convergence, conflicts,
limitations, or the ledger when those functions belong inside thematic
sections. The introduction always establishes the question and boundary. A
methods section is explicit for a protocol-based review; a non-systematic
review must not imply exhaustive selection. The analytical body compares
sources by dimension. The conclusion answers the question at the certainty
supported by the body and adds no new evidence.

Keep the comparison matrix and claim-evidence ledger as verification artifacts.
Include them in the delivered document only when the user or delivery contract
requests them.

Use `assets/literature-review-output.template.md` for a file artifact. Before
release, verify the one-to-one resolution of citations, the consistency of the
chosen GOST form, and the exact, untranslated titles in the reference list.
