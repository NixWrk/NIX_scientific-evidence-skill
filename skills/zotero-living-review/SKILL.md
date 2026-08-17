---
name: zotero-living-review
description: Maintain an incrementally updated literature review from a Zotero subcollection while preserving an immutable corpus snapshot for every published version. Use when new Zotero items or article annotations enter a project collection, when source or annotation hashes change, when a project context changes, or when a review must be resynthesized with traceable add/change/remove/blocking decisions.
---

# Zotero living review

Use this skill as the stateful adapter between a Zotero subcollection and the
offline `scientific-evidence-workflow`. Zotero supplies an inventory and
validated article annotations; the evidence workflow still owns study cards,
evidence records, claim ledgers, and review prose. Do not cite a Zotero note in
place of its publication.

## Workflow

1. Load the project context and the review state. Confirm `review_id`,
   `project_id`, `corpus_id`, and the exact collection binding. The project
   context hash covers the goal, objectives, questions, scope, and exclusions.
2. Read the Zotero collection inventory through the Zotero MCP adapter. Keep
   this skill's deterministic script offline: pass it a JSON inventory rather
   than making network calls from the script.
3. Ensure each item has a Zotero key, `source_content_hash`, `annotation_hash`,
   `project_context_hash`, and `annotation_status`. Require the item-level
   `project_context_hash` to equal the inventory context hash. Set
   `annotation_status` to `validated` only after the upstream
   `zotero-project-annotation`/`scientific-evidence-workflow` annotation gate
   passes. Require content and context hashes to use `sha256:` followed by 64
   lowercase hexadecimal digits.
4. Run `scripts/update_review.py` against the previous state and the current
   inventory. Inspect the plan before writing a review artifact.
5. If the plan reports `synthesis_blocked`, annotate or re-annotate the listed
   items and run the update again. Do not use an old annotation to clear a
   source or project-context change.
6. For every relevant change, synthesize from the new immutable snapshot as a
   whole. Rebuild study cards, the cross-study matrix, and the claim–evidence
   ledger with `scientific-evidence-workflow`; never append a paragraph to the
   previous review. Record the resulting artifact against the snapshot only
   after its evidence gate passes. Then call `record_published_artifact` with
   the matching `snapshot_id`, resulting `artifact_path`, and its `content_hash`
   (`sha256:` plus 64 lowercase hexadecimal digits).
7. Preserve the returned state, including removed item records and all prior
   snapshots. A no-op update must be byte-for-byte stable apart from the
   caller's JSON formatting.

Read [state-machine.md](references/state-machine.md) for the transition and
invalidation rules. Use [review-state.template.json](assets/review-state.template.json)
and [zotero-inventory.template.json](assets/zotero-inventory.template.json) as
the machine-readable contract. The dependency-free update script can be used
in a CI check or by an agent:

```text
python skills/zotero-living-review/scripts/update_review.py \
  previous-state.json current-inventory.json \
  --output next-state.json --plan-output update-plan.json
```

## Invariants

- Each published review artifact names exactly one immutable snapshot.
- A relevant inventory or context change creates a new snapshot and requires
  resynthesis; the previous artifact remains historical.
- New or source/annotation-changed items without a validated annotation block
  synthesis. A changed project context invalidates annotations that do not
  carry the new context hash.
- Removed items remain in `items` and in snapshot history; they are not erased.
- A published artifact carries its existing snapshot ID, artifact path,
  SHA-256 content hash, and `resynthesis_required: false`.
- The update script is deterministic, does not contact Zotero, and does not
  mutate its input state.
