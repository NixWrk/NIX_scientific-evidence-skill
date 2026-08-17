# Living-review state machine

The logical review is living; a released artifact is not. Every synthesis is
bound to an immutable corpus snapshot. The state file is a synchronization
record, not the review text.

## Records

- `collection` is the exact Zotero binding (`library_id`, `collection_key`,
  and optional display name). Never silently switch collections.
- `project_context_hash` identifies the project goal, objectives, questions,
  scope, and exclusions used for project-relative annotation. Use the canonical
  form `sha256:` followed by 64 lowercase hexadecimal characters.
- `items` is keyed by Zotero item key. An item keeps its
  `source_content_hash` and `annotation_hash` (each canonical SHA-256), its
  item-level `project_context_hash`, validation status, first/last snapshot,
  and event history. A removed item has `status: removed` and remains in this
  map.
- `snapshots` is append-only. Each entry contains a sorted item inventory and
  `immutable: true`; it is never edited in place.
- `current_artifact` points to the artifact candidate for the latest snapshot.
  Its status is `needs_resynthesis`, `blocked`, or `published`.

## Change classification

Compare the current inventory with the active items in the previous state:

| Signal | Meaning | Consequence |
|---|---|---|
| `added` | key was absent or was previously removed | new study card and annotation check |
| `source_changed` | `source_content_hash` changed | old study card/evidence cannot be reused as current |
| `annotation_changed` | annotation hash, status, or annotation context changed | re-check the derived record |
| `removed` | active key is absent from the current inventory | retain history; rebuild synthesis without it |
| `unchanged` | source and annotation identity are unchanged | may be reused after snapshot-wide resynthesis |
| `context_changed` | project context hash changed | invalidate project-relative usefulness judgments |

`source_changed` and `annotation_changed` are independent signals: one item
may occur in both when a new source version was annotated. `context_changed` is
a review-level boolean, not an item key.

## Transition rules

1. **Initial sync**: create a snapshot even for an empty inventory so the
   collection boundary is explicit. Added items with validated annotations can
   proceed to synthesis; all other added items block it.
2. **No-op**: if collection binding, project context, item hashes, statuses,
   and active keys are unchanged, return the prior state exactly. Do not add a
   duplicate snapshot.
3. **Relevant change**: add one deterministic snapshot containing the complete
   current inventory, mark the artifact `needs_resynthesis`, and preserve all
   earlier snapshots. Re-synthesize the whole snapshot; never patch the prior
   prose append-only.
4. **Blocking**: `added`, `source_changed`, and `annotation_changed` items
   require `annotation_status: validated` and an item-level context hash equal
   to the inventory context. A source change also requires a changed annotation
   hash, because a same-hash note cannot describe a new source. On a context
   change, every current annotation must be validated and carry the new context
   hash; otherwise the artifact is `blocked`.
5. **Removal**: mark the item removed in the new snapshot and append a removal
   event. Do not delete its hashes or history. Reappearance is classified as
   `added` and must pass the annotation gate again.
6. **Publication**: only a synthesis whose claim–evidence gate passes may set
   `current_artifact.status` to `published`; the artifact must retain the
   snapshot ID used to build it. Use `record_published_artifact`; it rejects
   blocked candidates, stale snapshot IDs, and non-SHA-256 content hashes.

## Upstream/downstream boundary

The Zotero adapter reads item metadata and writes/reads derived annotation
notes. An annotation may route or help reuse study-card extraction when its
source and annotation hashes match the current snapshot and its validation
status is `validated`; it is never evidence and must never replace the
publication. The `scientific-evidence-workflow` remains the authority for
one-source article annotation, study cards, normalized outcomes, conflicts,
claim–evidence ledgers, and synthesis. Downstream claims cite the publication
and its locators, not the derived Zotero note. After the evidence gate passes,
call `record_published_artifact(state, snapshot_id=..., artifact_path=...,
content_hash="sha256:<64 lowercase hex>")` to mark the matching artifact
published.
