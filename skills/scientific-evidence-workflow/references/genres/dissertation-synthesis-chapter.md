# Genre: dissertation synthesis chapter

`mode: manuscript` · `genre: dissertation-synthesis-chapter` · literature and approved results required

## Authority boundary

GOST R 7.0.11-2011 requires chapters and subdivisions in the main part, but does
not require a separately named discussion or synthesis chapter and does not
prescribe the structure below. Treat it as a conventional layer for relating the
author's results to verified literature. The mandated controls are resolvable
cross-references, result-backed numbers, and consistent dissertation terms.

## Purpose

Interpret approved results, compare them with a frozen literature corpus, state
where they agree or disagree, and delimit applicability. Never blur three claim
types: `result` reports what was obtained, `interpretation` explains its bounded
meaning, and `comparison` relates it to an identified literature claim.

## Input

Require approved result records, verified literature evidence, the result
chapter map, and stable structure identifiers. Also use uncertainty, method,
limitation, and comparison-boundary records when supplied. Stop on any proposed
interpretation lacking result anchors or comparison lacking literature evidence.

## Canonical control sections

| Function | `output_section` |
|---|---|
| frozen results, corpus, and comparison axes | `synthesis_scope` |
| bounded interpretation of own results | `result_interpretation` |
| comparison with verified literature | `literature_comparison` |
| disagreement and alternative explanations | `conflicts_and_explanations` |
| applicability and study limitations | `limitations` |
| synthesis conclusions | `chapter_conclusions` |

These are ledger functions, not prescribed reader-facing headings.

## Operations

### Generate

Build a matrix whose rows are approved results and whose columns are comparable
literature claims, objects, methods, regimes, and boundaries. Draft result,
interpretation, and comparison claims as separate ledger entries. Preserve
incommensurability and conflict instead of forcing agreement.

### Critic

Classify each substantive sentence as result, interpretation, comparison, or
limitation, then verify the required anchors for that class. Flag category
blurring, unsupported mechanisms, false consensus, and overbroad applicability.
Use comments for scientific alternatives or missing evidence; use tracked
changes only for safe, exact wording corrections.

## Procedure

1. Freeze the approved results, literature corpus, and comparison axes.
2. Restate only the minimum result needed for interpretation and link it to the
   results chapter; do not create a second uncontrolled result narrative.
3. For each interpretation, name the result, boundary, reasoning step, and any
   alternative explanation retained by the evidence.
4. For each comparison, identify the literature claim and verify commensurability
   of object, method, metric, and regime before stating agreement or difference.
5. Separate disagreement caused by boundaries from genuine contradictory claims.
6. State methodological, sample, measurement, and applicability limitations
   without converting absence of evidence into evidence of absence.
7. End with bounded synthesis conclusions linked to results and literature; do
   not add a new result or a new source there.

## Scientific-formulation controls

- Mark causal, mechanistic, and explanatory language as interpretation unless an
  approved result directly tests it.
- Use “согласуется” only for comparable claims; it does not mean “подтверждает”.
- Do not write “впервые” or “не исследовано” without an explicit bounded corpus.
- Preserve modality and applicability boundaries from both result and source.
- Keep author attribution when reporting an explanation from literature.
- Record every semantic correction in the revision ledger.

## Gates and stop conditions

- At least one approved result and the compared literature evidence are frozen
  in `task.input_scope`.
- Every result claim resolves to `result_id`; every comparison resolves to both
  `result_id` and literature `evidence_id`.
- Every interpretation is explicitly typed and bounded; it is not presented as
  a direct observation unless the result record authorizes that status.
- Conflicts and non-comparable studies remain visible.
- All six control sections occur in the claim ledger.
- Stop on missing comparison axes, unresolved result/source anchors, or an
  interpretation that requires evidence outside the frozen bundle.

Apply `references/russian/genre-dissertation.md` and, for literature synthesis,
`references/literature-review-workflow.md` after the evidence gate. Run the
language auditor with `--profile genre-dissertation`. Use
`assets/dissertation-synthesis-chapter.template.md` for a file artifact.
