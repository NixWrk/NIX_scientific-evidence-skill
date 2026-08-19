# Genre: article annotation

`mode: qa` · `genre: article-annotation` · exactly one source

## Purpose

Record what a single supplied publication did and how it bears on the current
research. The annotation is written for the researcher's own reference library,
typically as a note attached to the item.

## Input

Require one source, its version or content hash, and the current research
question the annotation is written against. Without that question the
usefulness statement has nothing to be relative to; ask for it instead of
inventing a generic summary.

Treat the question posed to the source as pre-existing input, not as a
retrospective summary of what the source can answer. Preserve a user-supplied
question verbatim. When the question comes from accepted project state,
preserve its exact text in the machine record. If no separate question to this
publication was supplied, use the targeted accepted project question and say
that no narrower source-specific question was provided. Never infer a
convenient project question from the publication after reading it.

When the publication is a Zotero item and project relevance comes from a
project manifest, use `zotero-project-annotation` as the adapter. Read the
generic manifest's top-level `context_hash` and store it as
`project_context_hash` in the derived annotation record. Project context and
routing identifiers guide the usefulness judgement; they are not evidence.
Require a human-readable project title in the working language for the readable
annotation. For Russian output, do not substitute an English placeholder or a
project/objective/question identifier for that title. If no accepted Russian
title is available, stop before rendering the readable note and request one;
do not invent a translation of an authoritative project name.

## Procedure

1. Freeze the question posed to the source and its accepted project basis
   before extracting the publication's contents.
2. Record the source identity: identifier, version or hash, and what portion was
   actually read. A metadata-only reading is annotated as metadata-only.
3. Extract the publication's own research question or task, object, method,
   design, and sample in source voice. Do not relabel this as the project
   question.
4. Extract the reported outcome with exact numbers, units, groups, and
   uncertainty. A number that cannot be quoted exactly is not carried over.
5. Extract the boundaries the authors themselves state.
6. Write the usefulness statement separately, as the current reader's judgement
   relative to the frozen project question. Classify the contribution as full,
   partial, null, or contrary where the distinction matters. Never attribute it
   to the authors and never narrow the project question to fit the source.
7. Mark the annotation as derived.

## Separation of voices

Three voices must stay distinguishable in the finished note:

- what the source reports;
- what the source's authors conclude from it;
- what the current reader judges to be useful.

Collapsing the third into the first is the characteristic failure of this
genre: an opinion about relevance quietly becomes a finding of the paper.

## Readable projection

The readable annotation is for a researcher, not for the storage adapter. Keep
machine provenance in the machine record. By default, do not render source or
project hashes, internal source/project/objective/question/claim identifiers,
local paths, validator statuses, schema field values, or `evidence_role` in the
human-readable note. Zotero note keys and other idempotency state remain in the
machine record or adapter state; they are not embedded in the readable note
unless the user explicitly requests a provenance audit.

For Russian output, render every natural-language element in Russian scientific
language: the title scaffold, section headings, table headings and cells,
explanations, limitations, and project judgement. This gate also applies to
natural-language strings inherited from project or source records; do not copy
a foreign abbreviation from an input merely because the input is machine
readable. Prefer the established Russian term and Cyrillic abbreviation, such
as `ТМС` instead of unexplained `TMS` and `МРТ` instead of `MRI`. Give an
original foreign term only when it is necessary for identification or search,
and explain every specialized abbreviation or letter-number method name at
first use. Preserve product names such as SimNIBS or Nexstim, but identify
their function in plain Russian. If a nonessential foreign designation cannot
be explained reliably, omit it rather than exposing it unexplained. Localize
bibliographic connective text (`и соавт.`, not `et al.`) and unit symbols in
running Russian text (`мм`, `см²`, `дБ`, not `mm`, `cm²`, `dB`). An exact
original publication title may remain in the bibliographic citation.

## Derived-note marking

The machine record carries the source identifier, version or hash, date, local
path, Zotero note key when applicable, and derived-record role. The readable
note carries a normal bibliographic description and no machine ledger. An
annotation never becomes a source for a later review or manuscript, and a claim
may not cite it in place of the publication. When the source version changes,
the annotation is re-made rather than silently reused.

When the project `context_hash` changes, the project-relative annotation is
also stale and must be re-made. The publication remains the evidence source;
the changed project context only invalidates derived relevance and usefulness
judgements.

## Gates

- Exactly one source in `input_scope`.
- No research result records: this genre reports someone else's work.
- No internal references: an annotation is not part of the author's own work.
- Every number matches the source string exactly.
- The usefulness statement is `interpretive`, not `factual`.

## Stop conditions

Stop and ask instead of guessing when the full text was unavailable and only
metadata was read, when the current research question was not supplied, or when
the source version cannot be identified.

For Russian output, apply `references/russian/genre-micro-report.md` after the
evidence gate and run the audit with `--profile genre-micro-report`. Apply the
Russian language core to every natural-language fragment produced during the
run, including chat and machine-record values, not only the readable note.

Use `assets/article-annotation.template.md` for a file artifact.
