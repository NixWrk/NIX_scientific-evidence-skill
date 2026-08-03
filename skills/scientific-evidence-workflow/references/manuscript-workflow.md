# Manuscript workflow

## Required inputs

For drafting or revising a final research article, distinguish:

- literature corpus for context and Discussion;
- approved protocol or record of performed Methods;
- frozen research results for Results;
- versioned tables and figures;
- existing manuscript text, if revising;
- target structure and word limits, if supplied.

Stop when Methods or Results inputs are missing. Do not reconstruct them from
typical practice or literature.

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

### Discussion

Separate observed results, interpretation, comparison with literature, and
limitations. Do not let literature overwrite the study's own result. Hedge
mechanisms that were not directly observed.

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

Use `assets/manuscript-output.template.md` for a file artifact.
