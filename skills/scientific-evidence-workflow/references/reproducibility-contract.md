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

## Required account

### Inputs

For every material input state its path or identifier, origin, version or hash
when available, units, and confidentiality boundary. Distinguish generated,
measured, manually entered, and externally obtained data. A local path is not
provenance by itself.

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
    "execution_status": "not_run"
  }
}
```

For `artifact_status: frozen`, also provide non-empty `run_id`, `executed_at`,
`code_version`, `environment`, and `significant_outputs`; set
`execution_status` to `clean_kernel_pass`. This metadata is an attestation and
index, not a substitute for the described inputs, method, outputs, and limits.

## Gates

- A fresh-kernel run or an explicit declaration of the unexecuted/manual part.
- No unrecorded state required from earlier interactive work.
- Material inputs, parameters, environment, and outputs are identifiable.
- Every released numerical conclusion preserves its unit or dimensionless
  status and its context.
- Errors, negative outcomes, deviations, and uncertainty remain visible.
- Scientific validity is reported separately from execution success.
