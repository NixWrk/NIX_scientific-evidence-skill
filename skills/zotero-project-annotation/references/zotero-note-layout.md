# Zotero note layout and write safety

The note is a readable projection of one validated machine record. It is a
derived record, never an evidence source.

## Stable layout

Begin the note with an idempotency marker whose values are stable for the
source item and project:

```html
<!-- zpa:annotation_id=ANN-001; zotero_item_key=ABCD1234; project_id=PRJ-001 -->
```

Then render these sections in this order:

1. `Annotation — <title>` and the marker;
2. `Status`, `Source`, `Source content hash`, `Project`, `Project context
   hash`, `Read scope`, and `Relevance targets`;
3. `Summary`;
4. `Source voice — what the work did and reports`;
5. `Author conclusion`;
6. `Project judgement — why it is useful here`;
7. `What it does not settle`;
8. `Derived-record pointer` containing the local machine-record path and
   `evidence_role: derived_annotation_not_evidence`.

Keep exact numbers and locators in the source-voice section. Do not turn a
reader judgement into a reported finding by putting it in that section.

## Safe writes

- Read the item and candidate child notes before writing. Select exactly one
  publication; do not update the parent item metadata or attachment content.
- Search for the exact marker, not a title substring. If one matching note
  exists, replace only that note after validating the new record. If multiple
  matching markers exist, stop and report the collision. If none exists,
  create one derived child note rather than overwriting an unrelated note.
- Refuse a write when the machine record is invalid, `status` is `stale`, or
  `status` is `blocked_metadata_only`. A blocked status may be saved as a
  diagnostic record only when the caller explicitly requests that audit trail;
  it must not be presented as an annotation ready for synthesis.
- Do not delete existing notes, merge notes, change tags, or silently resolve
  a stale hash. Preserve the old record and create a new version on remake.

## Idempotency and versioning

The pair `(zotero_item_key, project_id)` identifies the logical annotation.
The source content hash and `project_context_hash` identify its version. A
changed hash means the old record is `stale` and `remake_required: true`; it is
not safe to update only the prose. A successful remake gets a new
`annotation_id` or explicit `supersedes_annotation_id`, writes a new machine
record, and then replaces the note matched by the stable marker.

The machine record belongs in the project artifact store, not in the evidence
ledger. Downstream claims cite the Zotero item/publication and its source
locator, never the note or JSON record.
