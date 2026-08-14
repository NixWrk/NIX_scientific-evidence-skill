---
name: scientific-evidence-workflow
description: Process only user-supplied scientific publications and research results into source-traceable Q&A, literature reviews, or manuscript text. Use when an instruction-following agent or local model must answer questions, synthesize a fixed corpus, audit or revise scientific prose, or draft a paper without retrieving new sources, calling model APIs, inventing data, or losing claim-level locators.
---

# Scientific Evidence Workflow

## Operating contract

Treat supplied publications, protocol records, result files, tables, figures,
and approved notes as the only scientific sources. Treat model knowledge as
orientation, never as evidence.

Remain offline while processing scientific content. Do not expand the corpus,
invent a citation, reconstruct a missing value, propose a new study, select a
venue, or predict publication outcomes.

Use the same workflow with an agent or a local instruction-following model. Do
not require function calling, a particular MCP server, or product-specific
tools. Accept local UTF-8 text, JSON, JSONL, HTML, Markdown, CSV, or extracted
PDF content. An adapter may obtain these records from Zotero, but Zotero is not
required by the skill.

## Select one output mode

Always read `references/evidence-contract.md` first. Then load exactly one mode:

- Q&A from a fixed corpus: `references/qa-workflow.md`.
- Literature review from a fixed corpus:
  `references/literature-review-workflow.md`.
- Manuscript drafting, audit, or revision from supplied literature and research
  records: `references/manuscript-workflow.md`.
- A record of the author's own work in a bounded stage: mode `record`, with the
  genre reference below.

## Select a genre when one fits

A genre narrows a mode to a named kind of text with its own required parts and
gates. When the request matches one, set `task.genre` and also load its
reference:

- `article-annotation`: one publication annotated for the reference library —
  `references/genres/article-annotation.md`, mode `qa`.
- `stage-report`: what was done, produced, opened, and blocked in one stage —
  `references/genres/stage-report.md`, mode `record`.
- `micro-review`: one review question across two to five sources —
  `references/genres/micro-review.md`, mode `literature_review`.

Leave `task.genre` unset for a request that no listed genre describes. Do not
force a request into a genre it does not fit.

Read `references/local-model-compatibility.md` when preparing context or a run
for a local model.

When the requested output is Russian scientific or technical prose, also read
`references/russian-scientific-style.md`. Apply it to user-facing prose, not to
machine-readable field names, identifiers, code, or exact source fragments.

## Required workflow

### 1. Fix the task boundary

Record the requested mode, question or artifact, allowed source identifiers,
input versions, language, audience, and requested output format. State any
missing requirement that affects the result.

For a manuscript, separate literature sources from research records. Literature
may support context and interpretation. Only approved protocol and result
records may support Methods and Results.

For every manuscript, require two explicit choices before drafting:

- `figure_mode`: `with_figures` or `without_figures`;
- `formatting_mode`: `journal_example` or `section_only`.

If `journal_example` is selected, require a user-supplied example from the
named journal. Analyze only that example and save the observed formatting
patterns as a versioned skill-memory record according to
`references/journal-pattern-memory.md`. Do not infer unobserved journal rules.
If `section_only` is selected, use scientific sections without inventing a
journal style. If figures are requested, record their supplied or reproducibly
derivable inputs in `figure_source_ids`; never fabricate scientific images or
missing data.

### 2. Inventory and freeze inputs

Assign every source a stable `source_id`. Preserve an existing content hash or
version when available. Do not silently replace an input with a newer file.

If the source is too large for one context, process it in stable chunks. Keep
the chunk locator attached to every extracted fact.

### 3. Build evidence before prose

Create atomic evidence records using stable local locators. Separate:

- direct observations;
- statistical or qualitative inference;
- method and protocol facts;
- literature context;
- limitations and contrary evidence.

For every number, retain its exact source string, value, unit, denominator,
group, time point, and uncertainty where supplied.

### 4. Build the claim ledger

Map every material output claim to evidence or approved research results. Mark
each claim as `supported`, `bounded`, `unsupported`, or `conflicted`.

Use only these dispositions:

- `keep` for supported claims;
- `hedge` or `keep_with_boundary` for bounded claims;
- `drop` or `request_input` for unsupported claims;
- `disclose_conflict` for unresolved conflicts.

Never resolve a conflict by choosing the more convenient value.

When the output carries internal references, record every addressable unit of
the work — chapter, numbered section, equation, table, figure, declared task,
conclusion, proposition — as a structure record with a stable identifier. Point
claims at those units through `structure_ids`.

An internal reference points; it does not support. Naming a section never makes
a claim supported: evidence or result records are still required. The single
exception is a `structural` claim, which states how the work is organized, such
as "task 3 is solved in chapter 4"; it is established by the units it names and
may not rest on a unit that is still `planned`.

### 5. Draft the requested artifact

Draft only after the evidence and claim ledgers exist. Preserve the direction,
population, design, comparison, unit, denominator, time point, uncertainty, and
causal strength of each source claim.

Keep observation, author interpretation, and synthesis by the current model
distinct. Make limitations travel with the claim they constrain.

### 6. Run the evidence gate

Before release, verify:

1. every material claim has valid evidence or result references;
2. every cited locator belongs to the allowed input set;
3. every internal reference resolves to an existing unit of the work;
4. every number exactly matches its source or approved result record;
5. causal language is permitted by the design;
6. conflicting evidence is visible;
7. unsupported claims are removed or explicitly blocked;
8. no scientific source was introduced from model memory.

When a bundle is available, run:

```text
python scripts/validate_bundle.py evidence-bundle.json
```

The validator checks structural integrity, not scientific truth. Inspect the
source behind every high-impact claim even when validation passes.

### 7. Run the language gate

When writing in Russian, revise the evidence-checked draft using
`references/russian-scientific-style.md`. Lock claims, numbers, units,
citations, locators, uncertainty, and causal strength before revising. Improve
only terminology, syntax, cohesion, and concision.

The language rules layer: the core file always applies, a genre profile under
`references/russian/` describes how this kind of text typically fails, and a
domain profile carries subject vocabulary. Genre and subject area are
independent; neither implies the other.

When Python is available, run the audit with the same profiles:

```text
python scripts/audit_russian_style.py output.md --json --profile genre-review
```

Use `--list-profiles` to see what exists. The script detects selected surface
patterns only. Resolve its findings, then
perform the manual checks in the reference. Do not report a clean automated
audit as proof of linguistic or scientific quality.

### 8. Return a transparent result

Lead with the requested answer, review, or manuscript text. Follow it with a
compact claim–evidence ledger when the output format permits. Always report:

- unresolved conflicts;
- unavailable evidence;
- assumptions introduced only for formatting;
- sections not assessed;
- whether any deterministic validator was run.

## Stop conditions

Stop and request input instead of guessing when:

- the requested claim lacks supplied evidence;
- a manuscript Results value lacks an approved result record;
- Methods lacks a protocol or record of what was actually done;
- source versions conflict and no authoritative version is identified;
- a full systematic-review claim lacks real search and screening provenance;
- the requested action would create research plans or publication strategy
  rather than process the supplied material.

## Bundled resources

- `assets/evidence-bundle.template.json`: neutral machine-readable bundle.
- `assets/evidence-bundle.schema.json`: structural declaration of the bundle for
  a host that cannot run Python. `scripts/validate_bundle.py` enforces the same
  structure plus the semantic rules and stays authoritative for release.
- `assets/qa-output.template.md`: Q&A output scaffold.
- `references/genres/`: genre references with their required parts and gates.
- `assets/article-annotation.template.md`, `assets/stage-report.template.md`,
  `assets/micro-review.template.md`: genre output scaffolds.
- `assets/literature-review-output.template.md`: review scaffold.
- `assets/manuscript-output.template.md`: manuscript scaffold.
- `assets/journal-pattern.template.json`: journal-pattern memory scaffold.
- `scripts/validate_bundle.py`: dependency-free structural validator.
- `references/journal-pattern-memory.md`: rules for extracting and retaining
  formatting patterns from a user-supplied journal example.
- `references/russian-scientific-style.md`: Russian language core.
- `references/russian/`: genre language profiles.
- `scripts/audit_russian_style.py`: dependency-free heuristic style audit.
- `scripts/russian/`: machine-readable core, genre, and domain rule profiles.
