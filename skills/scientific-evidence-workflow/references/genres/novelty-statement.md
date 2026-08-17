# Genre: scientific novelty and significance statement

`mode: manuscript` · `genre: novelty-statement` · bounded literature corpus and approved results required

## Authority boundary

GOST R 7.0.11-2011 requires scientific novelty and theoretical and practical
significance in the introduction. It does not prescribe separate headings, a
fixed number of novelty points, or the internal template below. The controlled
invariants are a bounded comparison corpus, approved own-result anchors, and
resolvable dissertation sections.

## Purpose

State what the work adds relative to an explicitly bounded body of prior work,
then distinguish the theoretical meaning of that addition from supported
practical applicability. Never infer global priority from absence in a local or
incomplete corpus.

## Input

Require a frozen literature corpus with provenance and search boundary,
verified prior-work claims, approved result records, and stable dissertation
section identifiers. Organizational implementation records are outside this
genre and cannot support scientific significance. Stop on “впервые” or
equivalent priority language when corpus coverage cannot authorize it.

## Canonical control sections

| Function | `output_section` |
|---|---|
| comparison corpus and prior capability | `novelty_boundary` |
| bounded difference established by own result | `novelty_claim` |
| theoretical significance | `theoretical_significance` |
| practical significance and applicability | `practical_significance` |
| result and section anchors | `novelty_traceability` |

These are control fields, not prescribed visible headings.

## Operations

### Generate

Build a prior-capability versus own-result matrix. For each novelty point, state
the bounded prior state, the approved result that differs, the comparison axis,
and the limit of the claim. Derive theoretical and practical significance as
separate claims and only from supplied records.

### Critic

Audit priority, comparison boundary, result support, and applicability. Flag
absolute absence claims, novelty based only on changed terminology, unanchored
significance, and practical implementation inferred from potential usefulness.
Use comments for missing corpus or evidence; use tracked changes only for exact
local corrections that do not alter priority or scope.

## Procedure

1. Freeze the corpus identifier, search date, provenance, inclusion boundary,
   comparison axes, approved results, and structure identifiers.
2. Record what the corpus establishes about the prior capability; preserve
   conflict, incompleteness, and non-comparability.
3. Match one own result to one stated difference and retain its object, method,
   regime, metric, and uncertainty boundary.
4. Use bounded formulations such as “в исследованном корпусе не выявлено” when
   the record does not justify global priority.
5. State theoretical significance as a supported change in explanation, model,
   relation, or knowledge boundary; do not restate novelty unchanged.
6. State practical significance as demonstrated or potential applicability,
   clearly distinguishing the two and citing the authorizing result. Keep the
   organizational fact of implementation in `approbation-record`.
7. Link every point to literature evidence, `result_id`, and `structure_id`.

## Scientific-formulation controls

- Treat “впервые”, “не имеет аналогов”, “ранее не исследовано”, and “уникальный”
  as blocked unless a supplied bounded corpus authorizes the exact scope.
- Do not equate a new object, parameter value, or implementation detail with a
  new scientific result without an approved comparison claim.
- Keep theoretical and practical significance distinct from novelty and from
  each other.
- Preserve modality: potential applicability is not implementation.
- Record every semantic correction in the revision ledger.

## Gates and stop conditions

- Every novelty claim names a bounded corpus and comparison axis.
- Every novelty and significance claim cites an approved own result and an
  existing dissertation section; prior-state claims cite literature evidence.
- Conflicting or incomplete prior evidence remains visible.
- Practical significance is anchored to an approved result; implementation is
  not claimed from within this genre.
- All five control sections occur in the claim ledger.
- Stop on an unfrozen corpus, unsupported priority, missing own-result anchor,
  or an attempted upgrade from possible use to demonstrated effect.

Apply `references/russian/genre-dissertation.md` after the evidence gate and run
the language auditor with `--profile genre-dissertation`. Use
`assets/novelty-statement.template.md` for a file artifact.
