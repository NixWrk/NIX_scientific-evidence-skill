# Genre: stage presentation

`mode: record` · `genre: stage-presentation` · figure control required

## Purpose

Present what a bounded stage produced, to a supervisor or to co-authors, in a
form meant to be spoken over. The audience decides what happens next from what
they see on the slide, so a chart that overstates is more expensive here than a
sentence that overstates in a draft.

## Input

Require the stage boundary, the frozen results, the supplied or reproducibly
derivable inputs of every chart, and the previous presentation if one exists.

## Figure control

This genre carries `figure_mode` exactly as a manuscript does, and for the same
reason: a chart is as capable of inventing data as a sentence.

- `with_figures` requires `figure_source_ids`, each naming a source inside
  `input_scope`. Every chart traces to a result record or a supplied input.
- `without_figures` forbids figure placeholders and figure callouts.

If a chart has no valid input, stop rather than draw something plausible. A
smoothed curve through three points, an axis that starts above zero without
saying so, and a trend line over a stage with no trend are all fabrication in
the form the audience trusts most.

Journal formatting does not apply to this genre; `formatting_mode` is not used.

## Procedure

1. State the task of the stage in one sentence.
2. Report what was performed, each item traceable to a procedure record.
3. Show results. Every number on a slide cites a result record; every chart
   names its input and its units.
4. Report negative and inconclusive outcomes with their established cause, or
   state that the cause is not established. Do not drop them because the slide
   is crowded.
5. State obstacles with the condition that would clear each one.
6. State open questions as questions.
7. State one next step.

## One claim per slide

A slide carries one statement, and its caption says what is shown, not what
kind of thing it is. "Результаты" is a label, not a caption. A caption that
names the quantity, the group, and the condition lets the audience check the
chart against the claim.

## Speaking does not soften the record

Text prepared for speech tends to round numbers, drop units, and turn a bounded
result into a general one. The claim ledger applies here unchanged: the spoken
version of a claim may not be stronger than the written one.

## Gates

- `figure_mode` is required.
- At least one research result record.
- Every number cites a result record or an evidence value.
- Every figure source lies inside `input_scope`.
- Internal references resolve to existing units.

For Russian output, apply `references/russian/genre-presentation.md` after the
evidence gate and run the audit with `--profile genre-presentation`.

Use `assets/stage-presentation.template.md` for a file artifact.
