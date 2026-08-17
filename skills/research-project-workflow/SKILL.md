---
name: research-project-workflow
description: Define, link, and validate a project manifest that supplies stable research context for literature search, annotation, review, scripts, reports, articles, and dissertation work. Use when creating or updating a candidate-dissertation, article, study, report, exploratory, or other research project, or when checking its Zotero bindings, corpus snapshots, artifacts, and linked manifests.
---

# Research Project Workflow

Use a project manifest as the routing record above document genres. Keep the project identity and research context in one small JSON file; let genre-specific skills own annotations, evidence, methods, and prose.

## Workflow

1. Copy `assets/project-manifest.template.json` and assign a durable `project_id`; do not replace it with a run ID or a random UUID.
2. Fill `context` before connecting artifacts. Keep `problem`, `goal`, objectives, research questions, scope, and exclusions explicit.
3. Recompute the top-level `context_hash` with `scripts/validate_project_manifest.py --print-context-hash` after every context edit, then validate the manifest.
4. Bind Zotero collections by stable collection key. Record corpus policy (`dynamic` or `frozen`) and snapshots; a new dynamic corpus may have no snapshot before its first sync, while a frozen corpus has exactly one snapshot.
5. Link artifacts to `linked_manifests` by ID. Keep the manifest a routing/context record: do not put claims, citations, evidence, article annotations, or literature-review conclusions here.

Read [project-manifest-contract.md](references/project-manifest-contract.md) for field rules and hashing semantics. Run the dependency-free validator directly on a JSON manifest:

```text
python skills/research-project-workflow/scripts/validate_project_manifest.py path/to/project.json
```

The validator fails closed: malformed JSON, missing required fields, unknown fields, duplicate IDs, broken local references, stale context hashes, and corpus-policy violations are invalid.
