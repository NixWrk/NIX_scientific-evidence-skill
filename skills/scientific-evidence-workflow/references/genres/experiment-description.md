# Genre: experiment description

mode: record · genre: experiment-description · a protocol, data, or note source required

## Purpose

Record the lifecycle of one bounded experiment: why it was undertaken, what was
approved and planned, what was actually done, what was observed, how the
observation was interpreted, and what remains unassessed. This is the source for
a later Methods section, result record, or notebook narrative; it is not a
protocol-only plan or a Results section.

## Lifecycle state contract

Label every material statement, field, and link with exactly one state:

- planned: rationale/trigger, question or hypothesis, goal, expected observable
  outcomes, intended use, decision rule, and planned procedure;
- approved: protocol, roles, calibration, or ethics decision explicitly approved
  with authority, version, and date. Approval does not prove execution;
- performed: actual place, time, organization, roles, equipment, sample,
  procedure, and deviations supported by a run record;
- observed: measured or directly recorded outcome linked to data, figure, table,
  or result record. An expectation is never an observation;
- interpreted: bounded analysis of an observed result against the goal or decision
  rule. Interpretation does not replace the observation;
- not_assessed: not measured, not checkable, or absent from supplied records.
  State the reason; do not fill the field from convention.

Use distinct identifiers for expectations and results, for example EXP-OUT-01 and
RES-01. Expected outcomes cannot satisfy a result link. If a field is
inapplicable, write not applicable; if its status is unknown, write not_assessed.

## Input and boundary

Require at least one supplied source of type protocol, data, or note in
input_scope. A protocol supports planned and approved claims; a
contemporaneous note may support a declared plan or contemporaneous status. A
data source or linked RES-* result record is required for an observed numeric
result: a note alone cannot establish that result. Identify one experiment_id,
record version, source versions or hashes, and the run boundary. Split a new
question, data set, or execution boundary into a new record and link the
records.

## Required lifecycle content

Cover all of the following, with state and evidence kept separate:

1. rationale/trigger; question, hypothesis, goal, target quantity, and completion
   criterion;
2. expected observable outcomes, including direction, range, or pattern;
3. intended use and the decision rule (support, reject, defer, or redirect);
4. planned and actual place, time, organization, and roles;
5. object, sample, materials, inclusion/exclusion criteria, and discarded units;
6. equipment, software, versions, settings, calibration, and validation status;
7. planned procedure and actual procedure as two ordered blocks;
8. data, variables, operational definitions, units, sampling, resolution, time
   points, channels, files, and transformations;
9. quality control, exclusions, ethics/consent, and approving organization;
10. deviations, with extent, reason, and known or unknown effect;
11. observed results with data/result locators, followed by separate
    interpretation;
12. downstream result links, limitations, uncertainty, conflicts, and
    not_assessed fields.

## Canonical output sections

When the record is represented in an evidence bundle, use these nine stable
output_section keys. Reader-facing headings may be combined, but each key must
remain addressable and retain the lifecycle state and evidence links.

| Content | output_section |
|---|---|
| rationale, trigger, prior observation, or gap | rationale |
| question, hypothesis, goal, target quantity, and completion criterion | objective |
| approved/planned object, materials, equipment, calibration, and procedure | planned_method |
| predictions stated before execution | expected_outcomes |
| intended use and decision rule | planned_use |
| place, time, organization, roles, sample, conditions, and approvals | execution_context |
| actual procedure, data handling, QC, exclusions, ethics, and deviations | performed_method |
| direct observations and derived results with data/RES locators | observations_results |
| interpretation boundaries, uncertainty, conflicts, limitations, and not_assessed fields | limits |

Expected_outcomes is a planned claim, not an observations_results claim. An
observed numeric value in observations_results must link to data or RES-*; a
note-only numeric statement is insufficient.

## Procedure

1. Freeze the experiment identifier, source versions, and intended boundary.
2. Write rationale, question, goal, expectations, intended use, and decision rule
   as planned before treating the run as evidence.
3. Record approvals separately; approval is not a performed claim.
4. Reconstruct the run from protocol, data, logs, and contemporaneous notes;
   record only what these sources establish as performed.
5. Link direct measurements to observed result records before interpreting. Mark
   derived quantities and retain reproducible calculations.
6. Interpret only against observed results, the stated goal, and the decision
   rule; carry uncertainty and limitations with the interpretation.
7. Mark absent or unchecked fields not_assessed with the reason.

## Planned versus performed

Retain both versions whenever they differ. Use future or conditional wording only
in planned; use past tense for performed. A deviation is an explicit record, not
“in general accordance with the protocol”.

## Ethical conditions

When people take part, identify the organization where the experiment occurred,
the approving body, approval identifier/date, consent basis, and scope. Do not
infer approval from the author's affiliation. If ethics was not assessed in the
supplied records, mark it not_assessed and stop before claiming compliance.

## Gates

- At least one supplied protocol, data, or note source exists in input_scope.
- One bounded experiment_id and explicit source versions are present.
- Planned, approved, performed, observed, interpreted, and not_assessed claims
  are distinguishable; expected outcomes never count as results.
- Performed-method claims have protocol/data/note/log locators; observed results
  have data or RES-* locators; interpretations point to observed results.
- A contemporaneous note may support a declared plan or status, but an observed
  numeric result requires data or a linked RES-* result record.
- Numeric values have a stage-appropriate source, unit where applicable, and
  variable, sample, and time-point context.
- QC, exclusions, deviations, ethics, and limitations are documented or marked
  not_assessed/not applicable; internal references resolve.

## Stop conditions

Stop and request input when protocol, data, and note sources are all unavailable,
when a note is the only support for an observed numeric result and no data or
RES-* record exists, when an actual procedure would be reconstructed from
convention, an observed result has no locator, the exclusion rule is unknown, or
the approving organization for human participants cannot be identified.

For Russian output, apply references/russian/genre-experiment.md after the
evidence gate and run the audit with --profile genre-experiment.

Use assets/experiment-description.template.md for a file artifact.
