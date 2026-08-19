# Zotero note layout and write safety

The note is a readable projection of one validated machine record. It is a
derived record, never an evidence source.

## Language and audience boundary

Set the note language from the user's request and project context. For Russian
output, apply the Russian scientific-language core and the `genre-micro-report`
profile to every natural-language fragment generated during the run, including
chat, diagnostics, machine-record string values, and the note itself.

The readable note serves the researcher. Keep internal identifiers, source and
project hashes, local paths, schema statuses, validator output, and
`evidence_role` in the machine record. Do not render them in the note unless the
user explicitly requests a provenance audit. If a technical value must be
shown, explain its purpose in ordinary language.

For a Russian note, use a human-readable accepted Russian project title. Do not
use `project_id`, `OBJ-*`, `RQ-*`, or an English placeholder as its visible
name. If the project record has no accepted Russian title, stop before writing
the note and request one.

## Question boundary

Keep the accepted project question, the publication's own research question,
and the reader's answer about project relevance separate.

Freeze the project question before interpreting the publication. Copy its
machine-record text exactly from the accepted manifest. In the readable note,
reproduce the user's explicit question to this publication verbatim. If none
was supplied, reproduce the targeted accepted project question verbatim. Put
any language clarification or abbreviation expansion outside the quoted
question; never reshape its scope, modality, or predicate. Never generate that question
retrospectively from the publication's methods, findings, or conclusion. If no
separate source-specific question was supplied, state that the annotation is
assessed against the accepted project question; do not invent a more convenient
question.

Describe the publication's own research question or task only in source voice.
Then state separately whether the publication answers, partly informs, does
not answer, or contradicts the pre-existing project question. A relevance
statement must not imply that the publication answered the full project
question merely because it answered its own narrower question.

## Stable note identity

Zotero normalizes note HTML and removes HTML comments as well as unrecognized
custom attributes during an update. Do not place an idempotency marker, note
key, source key, project key, hash, or path in the readable note.

Store the note key returned by Zotero in the machine record as
`provenance.zotero_note_key`. The pair `(zotero_item_key, project_id)`
identifies the logical annotation; `zotero_note_key` identifies its physical
Zotero note. Keep this mapping outside the readable note and verify it against
the note's actual parent item before every update.


## Russian readable layout

Render a Russian note in this order:

1. `Аннотация к статье: <краткое название по-русски>`;
2. normal bibliographic description with the exact publication title where
   needed, plus a plain-language description of what was read;
3. `Исходный вопрос проекта к статье`;
4. `Краткое содержание`;
5. `Исследовательский вопрос публикации`;
6. `Что исследовали и как проводили работу`;
7. `Основные результаты`, with exact values, units, and human-readable source
   locations;
8. `Вывод авторов`;
9. `Значение для проекта «<понятное русское название>»`;
10. `Ограничения и нерешённые вопросы`.

Prefer an established Russian term and Cyrillic abbreviation. Do not copy a
foreign abbreviation from a project question, source field, or machine record
without adaptation: use `ТМС` rather than unexplained `TMS` and `МРТ` rather
than `MRI`. Include the original foreign term only when it is necessary for
identification or search. Explain every specialized abbreviation and
letter-number method name at first use in plain Russian; if a nonessential term
cannot be explained reliably, omit it. Preserve necessary proper product names
such as SimNIBS or Nexstim, but state their function. Localize bibliographic
connective text (`и соавт.`, not `et al.`) and unit symbols in Russian prose
(`мм`, `см²`, `дБ`, not `mm`, `cm²`, `dB`). Preserve an exact original
publication title only in the bibliographic description.

Before any write, scan every heading, table cell, project-relative paragraph,
and inherited natural-language string. Refuse the write while an unexplained
foreign term, abbreviation, or service code remains visible.

Keep exact numbers and locators in the source-voice section. Do not turn a
reader judgement into a reported finding by putting it in that section.

## Safe writes

- Read the item and all child notes before writing. Select exactly one
  publication; do not update the parent item metadata or attachment content.
- If the machine record contains `provenance.zotero_note_key`, retrieve that
  exact child note and verify that its parent is the expected source item. Stop
  if the key is missing, points elsewhere, or is not unique in the read result.
  Do not fall back to title matching.
- If the machine record has no note key, create a derived child note only when
  no prior machine record exists for the logical annotation. Never overwrite
  an existing user note to infer a missing mapping.
- After a successful create, store the returned note key in the machine record
  before considering the operation complete. Reuse that key for every future
  refresh of the same logical annotation.
- If a create result is unknown after a timeout, re-read the child-note keys and
  compare them with the exact pre-write set. Bind only when exactly one new note
  has content equal to the canonical candidate; otherwise stop for
  reconciliation instead of retrying create blindly.
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
`annotation_id` or explicit `supersedes_annotation_id`, preserves the verified
`zotero_note_key`, writes the new machine record, and then updates only that
note. The machine-side mapping, not readable-note content, provides
idempotency. On a first create, persist the returned note key before advancing
project state.

The machine record belongs in the project artifact store, not in the evidence
ledger. Downstream claims cite the Zotero item/publication and its source
locator, never the note or JSON record.
