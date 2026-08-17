# Genre: dissertation conclusion

`mode: manuscript` · `genre: dissertation-conclusion` · approved results and task map required

## Authority boundary

GOST R 7.0.11-2011 requires a conclusion as part of the dissertation. It does
not by itself prescribe the reader-facing headings or the exact internal order
below. The registry requires coverage of numbered task-linked conclusions,
practical recommendations, and directions for further work; treat that layout as
the controlled dissertation profile unless a supplied higher-priority card says
otherwise. The no-new-result and task-closure invariants are mandatory controls.

## Purpose

Close the dissertation's aim and tasks using results already established in the
main part. State recommendations and future directions only when the supplied
records authorize them. The conclusion is a compression and closure layer, not
a place to introduce evidence, methods, results, or comparisons.

## Input

Require the approved aim, task ledger, chapter conclusions, approved result
records, and stable structure identifiers. Use approved recommendation and
future-work records when available. Literature and organizational records are
forbidden as scientific support in this genre.

## Canonical control sections

| Function | `output_section` |
|---|---|
| aim and task closure scope | `conclusion_scope` |
| numbered conclusions mapped to tasks | `task_conclusions` |
| evidence-backed practical recommendations | `practical_recommendations` |
| bounded directions for further work | `future_work` |
| final aim-closure statement | `aim_closure` |

The keys are mandatory in the control ledger; they need not become five visible
headings. If no supported recommendation or future direction exists, stop that
item and record the gap rather than inventing content.

## Operations

### Generate

Build a task-result-chapter-conclusion matrix before prose. Form each numbered
conclusion from already approved claims and retain their boundaries. Add a
recommendation only when a supplied result supports both the action and its
scope. Mark future work as prospective, never as an obtained result.

### Critic

Trace every sentence back to the main part and task map. Flag new results,
stronger generalization, unmapped tasks, duplicated activity descriptions, and
recommendations lacking anchors. Use comments for scientific gaps; apply tracked
changes only when the exact correction preserves the approved claim.

## Procedure

1. Freeze aim, tasks, results, chapter conclusions, and structure identifiers.
2. Assign each task at least one supported conclusion and verify that every
   conclusion answers an approved task.
3. Write numbered conclusions as scientific outcomes, not as descriptions of
   work performed or chapter summaries.
4. Preserve value, unit, uncertainty, object, regime, and applicability boundary
   from the supporting result.
5. Add practical recommendations only from approved result/recommendation links;
   distinguish demonstrated applicability from possible usefulness.
6. State future work as an unresolved or prospective direction with its boundary
   and rationale; do not imply that it has been completed.
7. Close the single approved aim without claiming more than the mapped tasks and
   results jointly establish.

## Scientific-formulation controls

- Prefer “установлено”, “разработано”, “получено”, and “показано” only when the
  corresponding approved result authorizes that predicate.
- Do not replace a bounded result with an unconditional universal conclusion.
- Do not call a method effective, implementable, or recommended without the
  recorded criterion and applicability boundary.
- Keep future tense and proposed status explicit in `future_work`.
- Record every semantic correction in the revision ledger.

## Gates and stop conditions

- The aim is singular and every task has at least one mapped conclusion.
- Every conclusion resolves to an approved result and an existing chapter unit.
- No result, number, method, source, or interpretation appears for the first time
  in the conclusion.
- Every recommendation and future direction has an authorizing record or is
  reported as missing, not synthesized from general knowledge.
- All five control sections occur in the claim ledger.
- Stop on an unclosed task, an unsupported recommendation, a new claim, or a
  mismatch between dissertation terms and the aim/task ledger.

Apply `references/russian/genre-dissertation.md` after the evidence gate and run
the language auditor with `--profile genre-dissertation`. Use
`assets/dissertation-conclusion.template.md` for a file artifact.
