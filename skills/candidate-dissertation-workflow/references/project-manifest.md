# CDW-001/v1 project manifest

The project manifest is a routing record, not evidence. A status string never
proves that a gate or artifact passed validation.

## Frozen source

Each frozen source records `source_id`, `role`, `local_ref`, `frozen: true` and
`content_hash` in the exact form `sha256:<64 hex digits>`. A result or data
source that is allowed to support the Results stage also records
`approved: true`; approval is not inferred from its filename or role.

## Validated artifact

A `validated` or `final` artifact records:

```json
{
  "artifact_id": "ART-RESULTS-001",
  "genre": "dissertation-results-chapter",
  "path": "artifacts/results.md",
  "version": "v1",
  "status": "validated",
  "content_hash": "sha256:<64 hex digits>",
  "source_ids": ["RESULT-001"],
  "validation": {
    "status": "pass",
    "validator_id": "scientific-evidence-workflow/validate_bundle.py",
    "report_path": "reports/results.validation.json",
    "content_hash": "sha256:<64 hex digits>"
  }
}
```

A stage cannot become `complete` from a `draft`, from an artifact of another
genre, or from an unvalidated artifact. One `artifact_id` belongs to one stage;
duplicating it inside a stage or reusing it across stages is invalid. The
Results artifact itself must trace to at least one approved result/data source;
the mere presence of such a source elsewhere in the project is insufficient.

## Gate report

`gates` is the compact status view. `gate_reports` is its proof surface. Every
report records `gate_id`, the same `status`, a `validator_id` or named manual
review procedure, `report_path`, and the report `content_hash`.

```json
{
  "gate_id": "bibliography",
  "status": "pass",
  "validator_id": "dissertation-formatting-and-apparatus/audit_bibliography.py",
  "report_path": "reports/bibliography.json",
  "content_hash": "sha256:<64 hex digits>"
}
```

At release the CLI resolves every relative path from the manifest directory,
checks file existence and SHA-256, requires one passing report for every gate,
and rejects any unresolved optional stage. A report must be a JSON object with
a positive `valid: true` or `status: pass` signal, no contradictory failure
signal, and no non-empty `errors` list. Validator IDs are not interchangeable:
scientific genres, apparatus artifacts and each named gate accept only their
explicitly routed validators or manual procedure. Library callers must pass
`base_dir`; release validation without a filesystem base is invalid.

## Readiness and release

`ready`, `in_progress`, and `complete` are permitted only when every declared
dependency is `complete` or explicitly `not_applicable`. An optional stage may
be omitted during work, but before release it must be either `complete` or
`not_applicable` with a reason. No `pending` optional stage is silently treated
as a release decision.
