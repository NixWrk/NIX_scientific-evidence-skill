# Evidence contract

Use this contract in every mode. Keep identifiers stable across revisions.

## Optional project context

An evidence bundle may include one optional top-level `project_context`. When
present, it contains exactly these fields:

| Field | Requirement |
|---|---|
| `project_id` | Stable identifier of the owning research project. |
| `manifest_ref` | Reference to the authoritative `RP-001/v1` project manifest. |
| `context_hash` | `sha256:<64 lowercase hex digits>` for the manifest's current project context. |
| `objective_ids` | Project objective identifiers used to route this task. |
| `question_ids` | Research-question identifiers used to route this task. |

This block is context and routing metadata only. It is not a source record, an
evidence record, a result, or support for a claim. Claims still cite the
publication or approved research record through stable locators.

If `context_hash` changes, invalidate project-relative outputs produced under
the previous context, including applicability judgements, usefulness notes,
thematic routing, and synthesis. Rebuild them against the new manifest. The
context change does not invalidate facts extracted from an unchanged source;
those facts retain their source and locator provenance.

## Source record

| Field | Requirement |
|---|---|
| `source_id` | Unique stable identifier. |
| `title` | Human-readable source label. |
| `content_hash` | Hash when available; otherwise `null` with version note. |
| `representation` | `html`, `pdf`, `markdown`, `text`, `table`, `figure`, `data`, `protocol`, `note`, or `organizational`. |
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

## Structure record

Use a structure record for an addressable unit of the work being produced, not
of a source. Create these records whenever the output carries internal
references: a chapter, a numbered section, an equation, a table, a figure, a
declared task, a conclusion, or a proposition defended.

| Field | Requirement |
|---|---|
| `unit_id` | Unique stable identifier. |
| `unit_type` | `part`, `chapter`, `section`, `paragraph`, `equation`, `table`, `figure`, `appendix`, `task`, `conclusion`, or `proposition`. |
| `label` | Label as it appears in the work, such as `3.4`, `Рис. 2`, or `Задача 1`. |
| `title` | Optional heading or caption text. |
| `parent_id` | Optional containing unit; the chain must not close on itself. |
| `document` | Optional document the unit belongs to, for a reference that crosses documents. |
| `status` | `planned`, `drafted`, or `final`. |

An identifier is stable; a label is not. Renumbering a section changes `label`
and leaves `unit_id` untouched, so existing references survive. Keep the
identifier out of user-facing prose and render it as the label the reader
expects.

## Formulation revision record

Use a revision record whenever supplied scientific wording is changed. A
revision is an audit trail, not evidence and not a new claim.

| Field | Requirement |
|---|---|
| `revision_id` | Unique stable identifier. |
| `locator` | Exact place in the draft or supplied manuscript. |
| `structure_ids` | Addressable output units affected by the change. |
| `claim_ids` | Claim records whose wording is being revised. |
| `original`, `corrected` | Exact before and after wording; they must differ. |
| `reason` | Specific reason for the proposed change. |
| `category` | `scientific_precision`, `evidence_boundary`, `terminology`, `logic`, `grammar`, or `structure`. |
| `evidence_ids`, `result_ids` | Authority for a semantic correction. |
| `status` | `proposed`, `accepted`, or `rejected`. |

An accepted semantic correction requires a linked claim and evidence or an
approved result. Grammar may be corrected without a scientific source only if
the claim, number, unit, uncertainty, population, comparison, and causal force
remain unchanged. A revision record never raises the status of its claim.

## Claim record

| Field | Requirement |
|---|---|
| `claim_id` | Unique identifier. |
| `text` | Exact proposed output claim. |
| `output_section` | Answer, review section, Abstract, Methods, Results, Discussion, or other named location. |
| `claim_type` | `factual`, `numeric`, `causal`, `interpretive`, `synthesis`, `method`, `limitation`, `structural`, or `hypothesis`. |
| `certainty` | `direct`, `inferred`, `uncertain`, or `conflicted`. |
| `evidence_ids` | Supporting or contrary evidence records. |
| `result_ids` | Approved research results, normally required for manuscript Results numbers. |
| `structure_ids` | Units of the work referenced by the claim. |
| `status` | `supported`, `bounded`, `unsupported`, or `conflicted`. |
| `disposition` | `keep`, `hedge`, `keep_with_boundary`, `drop`, `request_input`, or `disclose_conflict`. |
| `boundary` | Required when the claim needs sample, design, time, or applicability limits. |
| `causal_basis` | Required for a direct causal claim; name the design feature that permits it. |
| `attribution` | Who formulated the claim when it is not the current analysis; required for a hypothesis. |

## Recorded hypotheses

A `hypothesis` is a conjecture the researcher already holds, written down so
that a later stage can test it. It is never an assertion of the current
analysis. Recording one is permitted; proposing new research directions is not.

A hypothesis keeps status `unsupported` and disposition `request_input`, and
names its author in `attribution`. This is what stops a working guess from
reappearing in a later report as an established result.

## Internal references

An internal reference points; it does not support. Naming a section does not
make a claim true, and a chain of internal references can otherwise launder an
unsupported statement into an apparently supported one.

Two rules keep the distinction:

- For every claim type except `structural`, `structure_ids` locate the claim
  inside the work and never count toward `supported` or `bounded`. Those
  statuses still require evidence or result records.
- A `structural` claim is a statement about the organization of the work
  itself, such as "task 3 is solved in chapter 4" or "proposition 2 is
  established in section 3.4". It requires `structure_ids`, and those
  references are its support.

A `structural` claim may not rest on a `planned` unit. A unit that has not been
drafted cannot yet establish anything.

## Consistency rules

- `supported` requires evidence or result references and normally uses `keep`.
- `bounded` requires evidence plus `hedge` or `keep_with_boundary`.
- `unsupported` uses `drop` or `request_input`; absence is not evidence.
- `conflicted` cites at least two conflicting records and uses
  `disclose_conflict`.
- A numeric manuscript Results claim must cite at least one `result_id`.
- A direct causal claim must name a supplied causal basis.
- Every `structure_id` must resolve to an existing unit.
- A `structural` claim requires `structure_ids`; no other claim type is
  supported by them.
- A locator must be meaningful within the authorized local record system.
- A passing JSON validator does not establish that the referenced fragment
  truly supports the wording; perform semantic review separately.
