# Genre: stage report

`mode: record` · `genre: stage-report` · own research records required

## Purpose

Report what was actually done in a bounded stage of the work, what came out of
it, what is now open, and what blocks progress. The reader is the author or the
supervisor, and the report is a record, not an argument.

## Input

Require the stage boundary, the records of what was performed, the frozen
outputs produced, and the previous stage report when one exists.

## Procedure

1. State the stage boundary: what period or task the report covers.
2. List the work performed, each item traceable to a procedure record.
3. Give the results with exact values, units, and the result records they come
   from. A number without a record is not reported.
4. Report negative and inconclusive outcomes together with their established
   cause, or state that the cause is not yet established.
5. List open questions as questions, not as soft claims.
6. List obstacles. Each obstacle names what is blocked and the condition under
   which it would be cleared. An obstacle without a clearing condition is a
   complaint, not a record.
7. List working hypotheses. Each names who formulated it.
8. State the next step.

## Hypotheses

A hypothesis in this genre is recorded, not generated. The skill writes down a
conjecture the researcher already holds; it does not propose research
directions, and the boundary matters because proposing directions is outside
the scope of this repository.

Every hypothesis keeps status `unsupported` and disposition `request_input`,
and names its author in `attribution`. This is what prevents a working guess
from being carried into a later report as an established result.

## Gates

- At least one research result record: a stage with no output is reported as
  such in prose, not as a result.
- Every reported number cites a result record or an evidence value.
- Every hypothesis is attributed and unsupported.
- Internal references, when used, resolve to existing units.

## Tone

Report, do not persuade. Do not soften a negative outcome, do not describe an
unfinished item as nearly complete, and do not convert an obstacle into a
neutral observation.

For Russian output, apply `references/russian/genre-micro-report.md` after the
evidence gate and run the audit with `--profile genre-micro-report`.

Use `assets/stage-report.template.md` for a file artifact.
