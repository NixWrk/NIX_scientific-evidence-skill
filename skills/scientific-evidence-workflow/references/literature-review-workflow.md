# Literature-review workflow

## Input

Require a fixed corpus, topic or review question, intended review type, and
desired structure. Do not call a review systematic unless real search,
screening, extraction, and eligibility provenance is supplied.

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

1. Create one study card per source with question, design, sample, method,
   results, limitations, and applicability.
2. Normalize comparable outcomes without changing units or denominators.
3. Build a cross-study matrix using the same fields for every study.
4. Group evidence by themes or review subquestions, not by source order.
5. Deduplicate by study and source before counting support.
6. Separate convergence, disagreement, missing evidence, and inapplicable
   comparisons.
7. Preserve internal conflicts inside an individual publication.
8. Draft synthesis claims only after the matrix and claim ledger exist.
9. Attach limitations to every synthesis claim they constrain.

An annotation may route or reuse study-card extraction, but it never becomes
evidence. Downstream claims cite the publication and its locators. A new or
changed item without a current validated annotation blocks synthesis in the
living-review route.

## Evidence-strength language

Describe the actual pattern instead of assigning an opaque quality score. Name:

- the number of independent studies;
- their designs and relevant limitations;
- whether results are consistent, mixed, or conflicting;
- whether the comparison is direct or indirect.

Do not use venue prestige, citation counts, or recency as substitutes for
methodological relevance to a claim.

## Output order

1. Scope and corpus boundary.
2. Thematic synthesis.
3. Areas of convergence.
4. Conflicts and heterogeneity.
5. Evidence limitations.
6. Claim–evidence ledger.

Use `assets/literature-review-output.template.md` for a file artifact.
