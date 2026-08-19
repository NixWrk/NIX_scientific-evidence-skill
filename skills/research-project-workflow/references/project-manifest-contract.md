# Project manifest contract (RP-001/v1)

This file defines the portable routing/context record used by the research skills. It is deliberately not an evidence store: source claims, quotations, citations, article annotations, methods, results, and review prose belong to linked genre-specific artifacts.

## Top-level record

The JSON root must be an object with exactly these keys:

| Key | Rule |
| --- | --- |
| `schema_version` | Required literal `RP-001/v1`. |
| `project_id` | Required durable identifier matching `[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+`; use a human-readable ID such as `PRJ-001`, not a run ID. |
| `context_hash` | Required lowercase `sha256:<64 hex digits>` for the project-relative context described below. |
| `project_kind` | Required one of `candidate_dissertation`, `article`, `study`, `report`, `exploratory`, `other`. |
| `parent_project_id` | Optional string identifier or JSON `null`; it must not equal `project_id`. The parent need not be present in the same file. |
| `title` | Required human-readable title in the project's working language; an ID, English placeholder, or untranslated technical label does not substitute for a Russian project title. |
| `status` | Required one of `draft`, `active`, `paused`, `completed`, `archived`. |
| `context` | Required object with the six fields below and no others. |
| `zotero_collection_bindings` | Required list of Zotero binding objects; it may be empty. |
| `corpora` | Required list of corpus objects; it may be empty. |
| `artifacts` | Required list of project artifact objects; it may be empty. |
| `linked_manifests` | Required list of manifest-link objects; it may be empty. |

Every collection binding, corpus, snapshot, artifact, and linked manifest has a stable ID. IDs are unique within their namespace; IDs referenced by another object must exist in this manifest.

## Context and hash

`context` has exactly these keys:

```json
{
  "problem": "non-empty string",
  "goal": "non-empty string",
  "objectives": [{"objective_id": "OBJ-001", "text": "non-empty string"}],
  "research_questions": [{"question_id": "RQ-001", "text": "non-empty string"}],
  "scope": "non-empty string",
  "exclusions": ["non-empty string"]
}
```

Write every natural-language value in the project's working language. For a
Russian project, apply the Russian scientific-language rules to `title`, all
six context fields, collection and corpus labels, artifact explanations, chat
messages, diagnostics, and any other natural-language text created during the
workflow. Machine keys and stable IDs remain unchanged, but they must not leak
into a readable artifact as substitutes for labels. If a Russian project has
no accepted Russian title, block the readable projection instead of inventing
or exposing a code-like name.

`objectives` and `research_questions` must each contain at least one item. Their IDs are stable so annotations and review sections can point to the same objective or question after a manifest is edited. `exclusions` may be empty.

Compute `context_hash` from exactly the six context fields above, excluding `project_id`, `project_kind`, title, status, parent, collections, corpora, artifacts, links, and the hash itself:

1. Build an object containing those fields and their values exactly as stored.
2. Serialize it as UTF-8 JSON with lexicographically sorted keys, `ensure_ascii=false`, compact separators `(',', ':')`, and no NaN/Infinity values.
3. Hash those bytes with SHA-256 and prefix the lowercase hexadecimal digest with `sha256:`.

Array order is meaningful; object key order is not. The validator recomputes this value and rejects a stale or malformed hash. `context_hash_for_context()` and `context_hash_for_manifest()` in `scripts/validate_project_manifest.py` expose the same algorithm.

## Zotero bindings

Each `zotero_collection_bindings` entry has exactly:

```json
{
  "binding_id": "ZCB-001",
  "library": "user:123456",
  "collection_key": "AB12CD34",
  "label": "Primary reading collection"
}
```

All four values are non-empty strings. `collection_key` is the stable Zotero collection key; `label` is for human orientation and is not used as an identifier. A new project may leave this list empty until a real Zotero collection is bound.

## Corpora and snapshots

Each corpus has exactly these fields:

```json
{
  "corpus_id": "CORP-001",
  "label": "Living literature corpus",
  "policy": "dynamic",
  "binding_ids": [],
  "objective_ids": ["OBJ-001"],
  "question_ids": ["RQ-001"],
  "snapshots": [],
  "active_snapshot_id": null
}
```

`policy` is `dynamic` or `frozen`. Binding, objective, and question ID lists may be empty, but every listed ID must resolve. Snapshot objects, when present, have `snapshot_id`, `captured_at`, unique non-empty `item_keys`, and a lowercase SHA-256 `content_hash`; `captured_at` is an RFC-3339 timestamp with a timezone. Snapshot IDs are globally unique in the manifest.

The policy invariants are intentionally strict:

- A `dynamic` corpus may have zero snapshots before the first Zotero sync. With zero snapshots, `active_snapshot_id` must be JSON `null`. Once one or more snapshots exist, `active_snapshot_id` must be non-null and resolve to one of them; historical snapshots may be retained.
- A `frozen` corpus has exactly one snapshot, and `active_snapshot_id` must resolve to that snapshot.

The snapshot fingerprint is a routing/integrity value. It does not make the listed items scientific evidence; annotation and evidence workflows own that distinction.

## Artifacts and linked manifests

An artifact has exactly `artifact_id`, `kind`, `path`, `status`, and `linked_manifest_ids`. `artifact_id`, `kind`, and `path` are non-empty strings; `status` is one of `planned`, `draft`, `active`, `published`, or `archived`; every `linked_manifest_ids` entry must resolve.

A linked manifest has exactly `manifest_id`, `kind`, `path`, and `relation`. All values are non-empty strings. The link is local metadata: the target file may be a genre manifest such as an annotation, notebook, report, article, or dissertation stage record. The target's own validator remains responsible for its schema.

## Validation posture

The validator rejects malformed JSON, non-object records, unknown fields, missing fields, wrong scalar types, duplicate IDs, invalid IDs or hashes, broken local references, self-parenting, stale context, duplicate Zotero/item keys, and invalid dynamic/frozen snapshot state. It does not contact Zotero or inspect linked files.
