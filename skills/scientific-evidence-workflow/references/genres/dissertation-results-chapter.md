# Genre: dissertation results chapter

`mode: manuscript` · `genre: dissertation-results-chapter` · approved result records required

## Authority boundary

GOST R 7.0.11-2011 requires a structured main part, but it does not require a
separately named results chapter or prescribe the internal sequence below.
Treat the chapter boundary and headings as a conventional evidence architecture.
The mandated controls are the dissertation-level invariants: numbers and
figures resolve to approved results, internal references resolve, and the chain
from tasks to chapter conclusions remains complete.

## Purpose

Present the author's obtained results in the order needed to answer the approved
research tasks. Keep observation and calculation separate from interpretation.
Literature is forbidden in this genre; move comparison and explanation involving
prior work to `dissertation-synthesis-chapter`.

## Input

Require approved result records and stable task and structure identifiers. Use
only:

- result records with status permitting manuscript use;
- frozen tables, figures, calculations, uncertainty records, and negative-result
  records linked to those results;
- the task ledger and dissertation outline;
- method-section cross-references, without reconstructing the method.

Stop on a result if its value, unit, uncertainty, sample boundary, figure source,
or approval status is absent. Do not recover a scientific result from prose,
literature, an organizational record, or an unapproved working file.

## Canonical control sections

| Function | `output_section` |
|---|---|
| task and result scope | `result_scope` |
| obtained positive and null findings | `reported_results` |
| approved negative results and established causes | `negative_results` |
| figures, tables, numbers, and internal anchors | `result_traceability` |
| task-linked conclusions | `chapter_conclusions` |

Reader-facing headings may differ or these functions may recur in several
sections. Keep every function addressable in the claim ledger.

## Operations

### Generate

Freeze approved result records, order them by task and dependency, and write only
claims that resolve to those records. Introduce each table or figure through the
result it displays. Report a negative result and its cause together only when the
cause itself is an approved result; otherwise report the observation without a
causal explanation.

### Critic

Audit every result sentence, number, table, figure, and conclusion against the
same frozen records. Flag literature, unsupported interpretation, missing units
or boundaries, and result strengthening. Use comments for scientific gaps and
ambiguous anchors. Allow tracked changes only for exact local corrections that
do not change scientific meaning.

## Procedure

1. Freeze result, task, figure, table, and structure identifiers.
2. Map each approved result to one or more tasks and one addressable output unit.
3. State the measured or calculated quantity, conditions, boundary, value, unit,
   uncertainty, and comparison internal to the experiment only when recorded.
4. Distinguish raw observation, derived value, statistical decision, and result
   conclusion. Preserve their recorded order and dependencies.
5. Link every number, table, and figure to `result_id`; never use an illustration
   as an independent source of an unrecorded value.
6. Include null and negative results when approved. Do not invent a reason for
   them or hide them because they do not support the expected outcome.
7. End each result block and the chapter with conclusions mapped to tasks. Do not
   cite literature or introduce interpretation beyond the result record.

## Scientific-formulation controls

- Use “получено”, “измерено”, “рассчитано”, and “установлено” only according to
  the operation and claim authorized by the result record.
- Do not turn association into causation, a sample result into universal law, or
  absence of statistical evidence into proof of absence.
- Preserve signs, units, uncertainty, conditions, comparison basis, and scope.
- Replace evaluative words such as “существенный”, “значительный”, and “лучший”
  with the recorded criterion or mark the claim unsupported.
- Record every semantic wording correction in the revision ledger.

## Gates and stop conditions

- Every scientific claim cites an approved `result_id` in `task.input_scope`.
- Literature evidence and organizational records do not support chapter claims.
- Every number and figure resolves to a result and an addressable structure unit.
- Each task represented in the chapter has at least one mapped conclusion; no
  conclusion exceeds the result records used to support it.
- A stated cause of a negative result has its own approved result anchor.
- All five control sections occur in the claim ledger.
- Stop rather than draft around an unapproved result, unresolved unit, missing
  boundary, or broken task/result/section link.

Apply `references/russian/genre-dissertation.md` after the evidence gate and run
the language auditor with `--profile genre-dissertation`. Use
`assets/dissertation-results-chapter.template.md` for a file artifact.
