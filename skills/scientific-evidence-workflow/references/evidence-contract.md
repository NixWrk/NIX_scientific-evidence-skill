# Evidence contract

Use this contract in every mode. Keep identifiers stable across revisions.

## Source record

| Field | Requirement |
|---|---|
| `source_id` | Unique stable identifier. |
| `title` | Human-readable source label. |
| `content_hash` | Hash when available; otherwise `null` with version note. |
| `representation` | `html`, `pdf`, `markdown`, `text`, `table`, `figure`, `data`, `protocol`, or `note`. |
| `local_ref` | Local file, Zotero key, or other authorized record reference. |

Do not treat a derived note as stronger than the publication or research record
from which it was derived.

## Evidence record

One record supports one atomic proposition.

| Field | Requirement |
|---|---|
| `evidence_id` | Unique identifier. |
| `source_id` | Existing source record. |
| `locator` | Stable block, page, table cell, figure panel, row, or protocol step. |
| `claim` | Atomic proposition supported or challenged by the source. |
| `support_type` | `direct`, `inferential`, `method`, `context`, `limitation`, or `contrary`. |
| `fragment` | Optional short source fragment; do not copy more than needed. |
| `value`, `unit` | Exact supplied value and unit when applicable. |
| `study_context` | Design, sample, group, time point, and comparison needed for interpretation. |
| `limitations` | Boundaries that must travel with the claim. |
| `verification_status` | `extracted`, `verified`, or `rejected`. |

An `extracted` record may be used for drafting but must not silently become
`verified`. A `rejected` record cannot support an output claim.

## Research result record

Use a result record for author-provided research data used in a manuscript.

| Field | Requirement |
|---|---|
| `result_id` | Unique stable identifier. |
| `source_id` | Approved data, table, figure, or analysis-output source. |
| `locator` | File plus row/column, table cell, figure panel, or named output. |
| `value` | Exact frozen result. |
| `unit` | Exact unit or `null` when not applicable. |
| `version` | File version, run identifier, or content hash. |
| `analysis` | Test or computation that produced the value, if supplied. |

Do not calculate or transform a result unless the user explicitly authorizes
that operation and the transformation is recorded as a new versioned result.

## Claim record

| Field | Requirement |
|---|---|
| `claim_id` | Unique identifier. |
| `text` | Exact proposed output claim. |
| `output_section` | Answer, review section, Abstract, Methods, Results, Discussion, or other named location. |
| `claim_type` | `factual`, `numeric`, `causal`, `interpretive`, `synthesis`, `method`, or `limitation`. |
| `certainty` | `direct`, `inferred`, `uncertain`, or `conflicted`. |
| `evidence_ids` | Supporting or contrary evidence records. |
| `result_ids` | Approved research results, normally required for manuscript Results numbers. |
| `status` | `supported`, `bounded`, `unsupported`, or `conflicted`. |
| `disposition` | `keep`, `hedge`, `keep_with_boundary`, `drop`, `request_input`, or `disclose_conflict`. |
| `boundary` | Required when the claim needs sample, design, time, or applicability limits. |
| `causal_basis` | Required for a direct causal claim; name the design feature that permits it. |

## Consistency rules

- `supported` requires evidence or result references and normally uses `keep`.
- `bounded` requires evidence plus `hedge` or `keep_with_boundary`.
- `unsupported` uses `drop` or `request_input`; absence is not evidence.
- `conflicted` cites at least two conflicting records and uses
  `disclose_conflict`.
- A numeric manuscript Results claim must cite at least one `result_id`.
- A direct causal claim must name a supplied causal basis.
- A locator must be meaningful within the authorized local record system.
- A passing JSON validator does not establish that the referenced fragment
  truly supports the wording; perform semantic review separately.
