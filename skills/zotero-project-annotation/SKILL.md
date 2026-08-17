---
name: zotero-project-annotation
description: Read exactly one Zotero publication through the Zotero MCP, annotate it against a project manifest, and safely write a human-readable derived note plus a machine-readable record. Use when a paper needs a summary, source/author/reader voice separation, project-specific relevance, or an idempotent annotation refresh.
---

# Zotero Project Annotation

## Overview

Use this as a thin Zotero adapter over the `article-annotation` genre in
`scientific-evidence-workflow`. Keep the publication as the only evidence
source; the annotation is a derived reading aid and never replaces the paper
in a claim, review, or manuscript.

The research-project-workflow manifest stores the project context hash as
top-level `context_hash`. Copy that value into the annotation record's
`project_context_hash`; the validator tolerates older manifests that used
`project_context_hash` directly.

## Workflow

1. Load the project manifest and exactly one Zotero item. Reject an empty or
   multi-item selection. Require `project_id`, the manifest's `context_hash`, a
   goal, objectives, research questions, and at least one requested relevance
   target.
2. Read the item metadata and the available attachment/content through the
   Zotero MCP. Compute a SHA-256 content hash over the exact source content
   used for the annotation. Do not use the annotation or Zotero note to form
   this hash.
3. Resolve every `relevance_target_ids` value against the project's `OBJ-*`
   and `RQ-*` identifiers. Never invent a generic "relevant to the project"
   statement when no target is supplied.
4. If only metadata is available, record `status: blocked_metadata_only`, a
   non-empty block reason, and `remake_required: true`. Do not infer methods,
   findings, conclusions, or limitations from a title or abstract field alone.
5. For a readable source, produce the three required voices:
   `annotation.source_voice` (what the paper did and reports),
   `annotation.author_conclusion` (what its authors conclude), and
   `annotation.project_judgement` (the reader's project-specific usefulness and
   open questions). Add a concise summary and exact outcomes with locators.
6. Validate the machine record with
   `scripts/validate_project_annotation.py`. It enforces hashes, target IDs,
   metadata-only blocking, and voice separation. If either the source content
   hash or the annotation's `project_context_hash` (copied from the manifest's
   `context_hash`) changes, mark the prior record `stale` and remake it; do not
   silently reuse it.
7. Write the human-readable note and machine-readable record only after
   validation. Follow `references/zotero-note-layout.md` for the marker,
   update/insert rules, and write safety. Never modify the publication or an
   unrelated Zotero note.

## Record contract

Start from `assets/project-annotation.template.json`. The record must retain:

- one Zotero item key and one source content hash;
- one `project_id` and matching `project_context_hash` copied from the
  manifest's `context_hash`;
- `relevance_target_ids` containing only IDs present in the project and named
  with the `RQ-` or `OBJ-` prefix;
- separate source voice, author conclusion, and project judgement fields;
- explicit `status`, `read_scope`, and `evidence_role` values.

The validator accepts an optional project manifest and current hash arguments,
so a refresh can fail closed before any Zotero write:

```text
python skills/zotero-project-annotation/scripts/validate_project_annotation.py \
  annotation.json --project-manifest project.json \
  --source-content-hash sha256:<64 hex digits> \
  --project-context-hash sha256:<64 hex digits>
```

See `references/zotero-note-layout.md` before a Zotero write and keep the
machine record under the project's derived-artifacts area.
