# Manuscript workflow

## Required inputs

For drafting or revising a final research article, distinguish:

- literature corpus for context and, when present, Discussion;
- approved protocol or record of performed Methods;
- frozen research results for Results;
- versioned tables and figures;
- existing manuscript text, if revising;
- target structure and word limits, if supplied.

Before drafting, record both manuscript controls:

- `figure_mode`: `with_figures` or `without_figures`;
- `formatting_mode`: `journal_example` or `section_only`.

These choices are required even when the answer appears obvious from context.
For `with_figures`, inventory every supplied or reproducibly derivable figure
and its data source in `figure_source_ids`. If no valid figure input exists,
stop instead of creating a scientific illustration from unsupported content.
For `without_figures`, do not set `figure_source_ids` and do not insert figure
placeholders or figure callouts.

For `journal_example`, require the journal name and a user-supplied example.
Analyze its structure according to `journal-pattern-memory.md`, store the
resulting versioned record with the skill, and identify the record in the task.
The example supports formatting only; it cannot support scientific claims. For
`section_only`, use the section scaffold and do not imitate an unstated journal.

Stop when Methods or Results inputs are missing. Do not reconstruct them from
typical practice or literature.

## Narrative examples

Use these as approved defaults when they fit the evidence, user instruction,
and stored journal pattern. They are examples of a good result, not mandatory
wording:

- Introduction: broad context → limitation of existing knowledge or methods →
  exact gap addressed by the work → explicit aim.
- Methods: research objects and inputs → instruments or models → performed
  procedure → sample, quality control, ethics, and analysis as applicable.
- Results: answer the tasks in their declared order → give the observation and
  number first → make the comparison → add only a bounded interpretation.
  Report negative results together with their verified causes.
- Conclusion: restate the achieved result → name the validated boundary → give
  the scientific or practical meaning without a new claim.

Useful transition functions include: “Для решения поставленной задачи…”, “Для
описания модели…”, “Исследования проводили…”, “Результаты показали…”, “Как видно
из рис. N…”, “Полученные результаты…” and “В работе представлен…”. Adapt the
grammar and vary the form. Use each only when the following statement is
supported; a transition never supplies evidence or certainty by itself.

## Section rules

### Abstract

Use only claims already supported in the body records. Verify every number.
Bound feasibility, association, prediction, and causal language by the design.

### Introduction

Use literature evidence for context and the stated problem. Do not manufacture
novelty or claim that no prior work exists without a supplied, adequate search
record.

### Methods

Use only the approved protocol and records of what was actually performed.
Preserve sample definitions, instruments, exclusions, versions, parameters, and
analysis procedures.

### Results

Use only frozen result records. Every number must cite a `result_id` and retain
its unit, group, denominator, time point, test, and uncertainty. Keep
descriptive, within-group, between-group, and causal statements distinct.

### Discussion (optional heading)

The Discussion functions are mandatory, but a separate heading is optional.
Use a separate section when the user or journal pattern requires it. Integrate
interpretation, literature comparison, and limitations into adjacent sections
when the supplied journal pattern omits it. If neither gives guidance, retain a
separate Discussion in `section_only` mode. In every form, keep observed
results, interpretation, literature comparison, and limitations distinct. Do
not let literature overwrite the study's own result. Hedge mechanisms that
were not directly observed.

### Conclusion

Introduce no new result. Reuse verified body claims at the same or lower
certainty. State the practical or scientific meaning without promising effects
that were not measured.

## Revision rules

Preserve the accepted source version and change only what the task requires.
Do not silently alter numbers, citations, variables, equations, sample sizes,
or causal direction. Record unresolved issues as `request_input`.

## Final gate

Check manuscript text against the claim ledger, research result records, tables,
figures, and source versions. If one authoritative value cannot be identified,
disclose the conflict instead of selecting a value.

Use `assets/manuscript-output.template.md` for a file artifact. Apply a journal
pattern only when the task identifies a valid stored record.
