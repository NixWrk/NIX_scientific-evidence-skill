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

Set the working language before generating any text. For Russian work, load
`../scientific-evidence-workflow/references/russian-scientific-style.md` and
`../scientific-evidence-workflow/references/russian/genre-micro-report.md`.
Apply them to every natural-language fragment produced by this skill: chat and
progress messages, diagnostics, plans, machine-record string values, candidate
notes, and final notes. Do not limit the language gate to the visible note.

Keep schema keys, stable IDs, hashes, paths, code, exact source titles, and
exact quotations unchanged, but keep machine metadata out of the readable note
unless the user explicitly requests provenance details. A machine identifier
does not replace a human-readable Russian label. Require an accepted Russian
project title before rendering a Russian project-relative note.

The research-project-workflow manifest stores the project context hash as
top-level `context_hash`. Copy that value into the annotation record's
`project_context_hash`; the validator tolerates older manifests that used
`project_context_hash` directly.

## Workflow

1. Load the project manifest and exactly one Zotero item. Reject an empty or
   multi-item selection. Require `project_id`, the manifest's `context_hash`, a
   goal, objectives, research questions, and at least one requested relevance
   target. Before interpreting the source, freeze the exact text of every
   targeted project question and objective from the accepted manifest. If the
   user supplied a separate question to this publication, preserve that
   wording as task input. If no separate question was supplied, say so rather
   than inventing one from the publication.
2. Read the item metadata and the available attachment/content through the
   Zotero MCP. Compute a SHA-256 content hash over the exact source content
   used for the annotation. Do not use the annotation or Zotero note to form
   this hash.
3. Resolve every `relevance_target_ids` value against the project's `OBJ-*`
   and `RQ-*` identifiers, and require the copied target text to match the
   accepted manifest exactly. Never rewrite a project question so that it
   resembles a question the publication happens to answer. Never invent a
   generic "relevant to the project" statement when no target is supplied.
4. If only metadata is available, record `status: blocked_metadata_only`, a
   non-empty block reason, and `remake_required: true`. Do not infer methods,
   findings, conclusions, or limitations from a title or abstract field alone.
5. For a readable source, produce the three required voices:
   `annotation.source_voice` (what the paper did and reports),
   `annotation.author_conclusion` (what its authors conclude), and
   `annotation.project_judgement` (the reader's project-specific usefulness and
   open questions). Keep three question layers explicit: the pre-existing
   project question posed to the source, the research question or task of the
   publication itself, and the publication's actual contribution to the
   project question. A contribution may be partial, null, or contrary; do not
   silently narrow the project question to manufacture a complete answer. Add
   a concise summary and exact outcomes with locators.
6. Validate the machine record with
   `scripts/validate_project_annotation.py`. It enforces hashes, target IDs,
   exact target text, metadata-only blocking, and voice separation. Its
   operational command requires the accepted project manifest and at least one
   targeted `RQ-*` question. If either the source content hash or the
   annotation's `project_context_hash` (copied from the manifest's
   `context_hash`) changes, mark the prior record `stale` and remake it; do
   not silently reuse it.
7. Write the human-readable note and machine-readable record only after
   validation. Follow `references/zotero-note-layout.md` for the Russian
   reader-facing layout, separation of machine metadata, stable note-key mapping, update/insert
   rules, and write safety. Run the Russian language gate before the write and
   reject a candidate Russian note that contains an unexplained foreign word,
   abbreviation, letter-number method name, or non-localized unit outside an
   exact publication title or necessary proper name. This gate also covers
   terms copied from project or source fields. Prefer established Russian terms,
   Cyrillic abbreviations, Russian bibliographic connective text, and Russian
   unit symbols. Never modify the publication or an unrelated Zotero note.

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
