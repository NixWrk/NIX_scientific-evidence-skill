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

Read `references/local-model-compatibility.md` when preparing context or a run
for a local model.

## Required workflow

### 1. Fix the task boundary

Record the requested mode, question or artifact, allowed source identifiers,
input versions, language, audience, and requested output format. State any
missing requirement that affects the result.

For a manuscript, separate literature sources from research records. Literature
may support context and interpretation. Only approved protocol and result
records may support Methods and Results.

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
3. every number exactly matches its source or approved result record;
4. causal language is permitted by the design;
5. conflicting evidence is visible;
6. unsupported claims are removed or explicitly blocked;
7. no scientific source was introduced from model memory.

When a bundle is available, run:

```text
python scripts/validate_bundle.py evidence-bundle.json
```

The validator checks structural integrity, not scientific truth. Inspect the
source behind every high-impact claim even when validation passes.

### 7. Return a transparent result

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
- `assets/qa-output.template.md`: Q&A output scaffold.
- `assets/literature-review-output.template.md`: review scaffold.
- `assets/manuscript-output.template.md`: manuscript scaffold.
- `scripts/validate_bundle.py`: dependency-free structural validator.
