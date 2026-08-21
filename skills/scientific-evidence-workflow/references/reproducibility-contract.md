# Reproducibility contract

Use this contract for a research notebook, procedure record, experiment
description, or standalone reproducibility note. It records what another
researcher needs to repeat the computation; it does not certify the scientific
validity of the method or interpretation.

## Working notebook and frozen snapshot

Keep an ordinary working notebook editable under version control. Do not demand
a sealed record, full output hashing, or a correction card for every debug run.

Create a frozen snapshot only when a result will be reviewed, cited, transferred
to another artifact, or used as an input elsewhere. A frozen snapshot records:

- `run_id` and execution time;
- notebook or code version: Git commit or content hash;
- execution status;
- environment reference;
- parameters and random seed that affect the result;
- significant inputs and outputs with versions or hashes when available.

## Current upstream state

A working notebook that depends on earlier work must resolve the current
approved facts, numerical results, and hypotheses through a stable manifest,
registry, result file, or loader. Do not copy a mutable result into prose or a
second configuration file. Preserve the upstream source identifier, locator,
resolved version or hash, and scientific status. For a hypothesis, preserve its
current acceptance state and check plan.

“Current” applies to the working report. A frozen snapshot pins the versions
resolved for that run and never updates in place. When an upstream artifact
changes, execute a new run and freeze a new snapshot if the result is released.
This preserves both automatic propagation and reviewable history.

## Required account

### Inputs

For every material input state its path or identifier, origin, version or hash
when available, units, and confidentiality boundary. Distinguish generated,
measured, manually entered, and externally obtained data. A local path is not
provenance by itself.

When input directories may contain renamed files, exports, or physical copies,
establish content identity with a checksum or another stable identifier before
counting observations. Record duplicates and the rule used to select the
canonical copy.

For measured data, link the computation to a stable experiment or study
description. Record the object or sample, acquisition conditions, recorded
signals or variables, channel roles, units, and the intended quantity. Keep the
planned protocol separate from what was actually performed and from what was
actually observed. A notebook that only names a CSV, DICOM series, or device
has not documented the experiment that produced the input.

### Environment and execution

Link to the shared lock, environment, container, or dependency file. Record only
the notebook-specific software, hardware, service, locale, or manual dependency
that can change the result. State the intended cell order and every external or
manual step. Do not hide a required preparation step in an interactive kernel.

Use these execution statuses:

- `not_run`: structure prepared, execution not attempted;
- `partial`: only a declared subset was executed;
- `clean_kernel_pass`: executed from a fresh kernel in the declared order;
- `failed`: execution stopped or produced an unhandled error.

Saved outputs do not establish `clean_kernel_pass`. Set that status only from an
actual fresh-kernel run.

### Independent validation axes

Record validation on three axes. Never derive one axis from another.

- Technical: `not_checked`, `passed`, `failed`, or `blocked`. This axis covers
  structure, declared files, schemas, hashes, local links, equation references,
  citation labels, and bibliography integrity.
- Computational: `not_checked`, `partial`, `passed`, `failed`, or `blocked`.
  This axis covers actual execution, tests, invariants, numerical checks, and
  the declared coverage of those checks.
- Scientific: `not_reviewed`, `bounded`, `approved`, `rejected`, or
  `conflicted`. This axis covers the method, interpretation, evidence boundary,
  applicability, and unresolved scientific conflicts.

`clean_kernel_pass` does not imply computational validation: code may execute
while a required invariant fails or a method branch remains unavailable.
Computational validation does not approve the scientific interpretation.
Scientific approval does not repair an unresolved input, broken reference, or
unreproducible execution.

### Parameters and randomness

Record parameters that affect a material output. Fix and report a seed for
pseudorandom operations or explain why repeated stochastic realizations, rather
than one seeded run, are required. Report the number of realizations and the
aggregation or uncertainty rule when applicable.

### Outputs

Name the outputs that matter for the research question. For a number preserve
value, unit, object, denominator or group, conditions, and uncertainty when it
was evaluated. For a table or figure preserve the input/result identity and the
code step that produced it. Do not hash disposable display output merely to
increase apparent rigor.

Generate every material numerical statement in report prose, captions, and the
final summary from the same variable or loaded result object as the table or
figure. Mark the rendering cell with `computed-narrative`. Static Markdown may
state fixed definitions, declared parameters, formulae, and source facts, but
must not contain a manually retyped calculated result. Formatting a value for
display must not create a second authoritative value.

Record the scientific status of each material output: measurement, estimate,
bound, reference, approximation, model prediction, placeholder, hypothesis, or
decision. Preserve that status through inheritance. Changing it requires a new
evidential operation and a recorded reason.

For an output consumed downstream, preserve an artifact handoff containing the
artifact identifier, producing run, version or hash, schema, units, scientific
status, applicability limits, intended consumer, and acceptance criterion. This
handoff must make the calculation sequence reproducible across notebooks, not
only within one kernel session.

### Narrative and calculation trace

Record the dependency chain from each material input or inherited result to the
operation, observable output, bounded interpretation, and next justified
operation. The same trace must continue across notebook boundaries through the
resolved input and artifact handoff records. A fresh run must be able to rebuild
the chain without chat history or undeclared interactive state.

For every nonterminal stage, retain a reasoning bridge that identifies its
material basis, the unresolved limitation or question, the rationale for the
next task, and the expected observable alternatives or decision criterion. The
next stage must resolve the declared task; chronology alone is not a dependency
trace. When several results motivate one task, retain all of their identifiers
and distinct roles.

Use `reasoning_context` in schema-version `1.1` artifact handoffs to carry this
bridge between notebooks: `basis_refs`, `established`, `unresolved_question`,
`decision_rationale`, `next_task`, `expected_observations`, and
`evaluation_criterion`. These are provenance and planning state, not evidence
that the expected result has already occurred.

When internal checks or identifiability tests apply, retain their outputs and
effect on the conclusion. A failed check or a completely confounded design
blocks the unsupported conclusion and requires a changed acquisition or model
comparison, not a more elaborate post-processing step on the same information.

### Selection policies and automation

Version every material inclusion, exclusion, duplicate-resolution, and
canonical-input policy. Record the rule identifiers, policy version, source of
the decision, and affected downstream consumers.

When two supplied records prescribe incompatible selections, mark the policy
`conflicted`, retain both records, and set automated downstream use to
`blocked`. Do not choose the rule implemented in code merely because it ran.
Resume automation only after a versioned resolution record identifies the
authoritative policy, explains the decision, and invalidates or reruns every
affected downstream artifact.

### Deviations and limits

Separate the intended procedure from what was performed. Record failures,
manual corrections, excluded data, unavailable dependencies, and known sources
of non-reproducibility. An unexplained discrepancy blocks a frozen snapshot; it
does not disappear because the final cell ran.

## Optional notebook metadata

The lint understands this small notebook-level object:

```json
{
  "scientific_report": {
    "schema_version": "1.0",
    "artifact_status": "working",
    "study_type": "computational",
    "genre_profile": "model-derivation",
    "execution_status": "not_run",
    "technical_validation_status": "not_checked",
    "computational_validation_status": "not_checked",
    "scientific_validation_status": "not_reviewed",
    "bibliography_status": "not_applicable",
    "selection_policy_status": "not_applicable",
    "selection_resolution_ref": null,
    "automation_status": "blocked"
  }
}
```

Use `study_type: empirical` when the notebook directly analyses experimental
observations and `study_type: mixed` when experiment and simulation are both
material to its conclusion. In those modes the notebook narrative must carry
the experiment-context, experiment-procedure, experimental-observation, and
experimental-analysis functions defined by the notebook genre.

Use `selection_policy_status: clear`, `conflicted`, or `resolved` when a
selection policy applies. `resolved` requires `selection_resolution_ref`;
`conflicted` requires `automation_status: blocked`. Use `not_applicable` only
when no material selection or canonical-input choice enters the calculation.
`automation_status: permitted` requires passed technical and computational
validation plus bounded or approved scientific validation.

For `artifact_status: frozen`, also provide non-empty `run_id`, `executed_at`,
`code_version`, `environment`, `significant_inputs`, and `significant_outputs`; set
`execution_status` to `clean_kernel_pass`. This metadata is an attestation and
index, not a substitute for the described inputs, method, outputs, and limits.

## Gates

- A fresh-kernel run or an explicit declaration of the unexecuted/manual part.
- No unrecorded state required from earlier interactive work.
- Material inputs, parameters, environment, and outputs are identifiable.
- Technical, computational, and scientific validation statuses are recorded
  independently; no pass is inferred from execution alone.
- The selected notebook genre profile is declared and its additional checks are
  present.
- Renamed or duplicated inputs are resolved to stable content identities.
- Material selection policies are versioned. A conflicted policy blocks
  automation until a versioned resolution is supplied.
- Inherited facts, results, and hypotheses resolve from versioned upstream
  artifacts; the frozen run records the resolved versions.
- Material results and handoffs preserve scientific status, schema, units,
  limits, consumer, and acceptance criterion.
- Local links, equation references, citations, and bibliography entries resolve.
- The calculation trace is reproducible within the notebook and across every
  declared upstream or downstream notebook boundary.
- Each declared next task is linked to named results and limitations, and the
  following material stage performs it or records an explicit blocker.
- Schema-version `1.1` cross-notebook handoffs carry a complete reasoning context.
- Every released numerical conclusion preserves its unit or dimensionless
  status and its context.
- Every material result number in Markdown is generated from the corresponding
  variable or result object.
- Errors, negative outcomes, deviations, and uncertainty remain visible.
- Failed verification or identifiability checks block prohibited conclusions.
- Scientific validity is reported separately from execution success.
