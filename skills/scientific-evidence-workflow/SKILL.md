---
name: scientific-evidence-workflow
description: Process only user-supplied scientific publications, research records, and notebooks into source-traceable Q&A, literature reviews, manuscript text, critic reports, and the scientific genres of a Russian candidate dissertation, including outline, introduction, review, methods, results, synthesis, conclusion, defense propositions, novelty, approbation, and synopsis. Use when an instruction-following agent or local model must answer questions, synthesize a fixed corpus, audit or revise scientific prose with a traceable correction ledger, analyse defended dissertations for writing patterns, or generate or criticise a paper or qualification-work section without retrieving new sources, calling model APIs, inventing data, or losing claim-level locators.
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

An evidence bundle may carry an optional top-level `project_context` with
`project_id`, `manifest_ref`, `context_hash`, `objective_ids`, and
`question_ids`. This block scopes and routes work against the authoritative
project manifest; it is never a source, evidence, or support for a claim. When
`context_hash` changes, invalidate and regenerate every project-relative
output derived under the old context while leaving source evidence unchanged.

## Select one output mode

Always read `references/evidence-contract.md` first. Then load exactly one mode:

- Q&A from a fixed corpus: `references/qa-workflow.md`.
- Literature review from a fixed corpus:
  `references/literature-review-workflow.md` and
  `references/literature-review-patterns.md`. Also load
  `references/bibliography-gost.md` for a Russian-language review. The first
  controls evidence; the second selects a synthesis architecture from the
  review question and source types; the third controls references and the
  reference list without changing the source corpus. For a changing Zotero collection,
  route snapshot management through `zotero-living-review`; each published
  version still uses one immutable corpus snapshot.
- Manuscript drafting, audit, or revision from supplied literature and research
  records: `references/manuscript-workflow.md`.
- Scientific criticism of a supplied work: manuscript mode plus
  `references/critic-workflow.md`. Load `references/critic-verification-protocol.md`
  only for an evidence-dependent finding.
- A record of the author's own work in a bounded stage: mode `record`, with the
  genre reference below.

## Select a genre when one fits

A genre narrows a mode to a named kind of text with its own required parts and
gates. When the request matches one, set `task.genre` and also load its
reference:

- `article-annotation`: one publication annotated for the reference library —
  `references/genres/article-annotation.md`, mode `qa`; when the item is in
  Zotero and relevance is project-relative, route the adapter work through
  `zotero-project-annotation`.
- `stage-report`: what was done, produced, opened, and blocked in one stage —
  `references/genres/stage-report.md`, mode `record`.
- `micro-review`: one review question across two to five sources —
  `references/genres/micro-review.md`, mode `literature_review`.
- `experiment-description`: the lifecycle dossier of one bounded experiment from supplied
  protocol, data, or note sources — from rationale and planned/approved procedure
  through performed work, observed and interpreted results, and explicit
  `not_assessed` fields — `references/genres/experiment-description.md`, mode
  `record`; keep expected outcomes separate from result records and use
  `assets/experiment-description.template.md`.
- `procedure-record`: one performed procedure, its deviations and outputs —
  `references/genres/procedure-record.md`, mode `record`.
- `decision-log`: why a choice was made, against what was known then —
  `references/genres/decision-log.md`, mode `record`.
- `notebook-narrative`: one bounded computational chain expressed as a
  self-contained executable technical report, with an explicit applied role,
  current upstream state, traceable calculation logic, calculated prose, and
  bounded conclusions —
  `references/genres/notebook-narrative.md`, mode `record`; also load
  `references/notebook-genre-profiles.md` and
  `references/reproducibility-contract.md`. When the notebook cites external
  publications, also load `references/bibliography-gost.md` for Russian output.
  For Russian notebooks, also load
  `references/russian-scientific-style.md` and
  `references/russian/genre-notebook.md`; this language route is mandatory for
  static Markdown and programmatically rendered narrative alike.
- `stage-presentation`: what a stage produced, shown and spoken over —
  `references/genres/stage-presentation.md`, mode `record`, figure control
  applies as it does to a manuscript.
- `dissertation-outline`: the addressable hierarchy and table of contents of a
  candidate dissertation — `references/genres/dissertation-outline.md`, mode
  `record`.
- `dissertation-introduction`: the evidence-bound introduction with all eight
  normative elements — `references/genres/dissertation-introduction.md`, mode
  `manuscript`.
- `dissertation-literature-review-chapter`: a bounded synthesis of a frozen
  literature corpus, including conflict and a non-absolute research gap —
  `references/genres/dissertation-literature-review-chapter.md`, mode
  `manuscript`.
- `dissertation-methods-chapter`: a reproducible account of objects, procedures,
  processing, and quality control from protocol/data records —
  `references/genres/dissertation-methods-chapter.md`, mode `manuscript`.
- `dissertation-results-chapter`: task-ordered reporting from approved result
  records without literature or invented interpretation —
  `references/genres/dissertation-results-chapter.md`, mode `manuscript`.
- `dissertation-synthesis-chapter`: bounded interpretation and comparison of
  approved results with a frozen literature corpus —
  `references/genres/dissertation-synthesis-chapter.md`, mode `manuscript`.
- `dissertation-conclusion`: task-linked closure without a new result, source,
  method, or stronger claim — `references/genres/dissertation-conclusion.md`,
  mode `manuscript`.
- `defense-propositions`: numbered falsifiable assertions anchored to approved
  results and dissertation sections — `references/genres/defense-propositions.md`,
  mode `manuscript`.
- `novelty-statement`: corpus-bounded novelty plus distinct theoretical and
  practical significance anchored to own results —
  `references/genres/novelty-statement.md`, mode `manuscript`.
- `thesis-synopsis`: a claim-preserving compression of a frozen dissertation
  with verified author works — `references/genres/thesis-synopsis.md`, mode
  `manuscript`.
- `approbation-record`: verified conferences, publications, registrations, and
  implementation acts that remain organizational rather than scientific
  evidence — `references/genres/approbation-record.md`, mode `record`.
- `normative-pattern-analysis`: one normative document turned into a card —
  `references/genres/normative-pattern-analysis.md`. This genre produces a card
  rather than an evidence bundle and is validated by
  `scripts/validate_normative_card.py`.

Leave `task.genre` unset for a request that no listed genre describes. Do not
force a request into a genre it does not fit.

When analysing a defended dissertation or synopsis as evidence of writing
practice, first read `references/dissertation-analysis-protocol.md`. Treat its
current version as the preliminary corpus-analysis standard. Version it when
the method changes; never treat it or the observed works as a normative source
for what a dissertation must contain.

Read `references/local-model-compatibility.md` when preparing context or a run
for a local model.

When the working language is Russian or the user requests Russian scientific
or technical expression, read `references/russian-scientific-style.md` before
producing any natural-language text. Apply it to every natural-language text
created during the run: chat replies and progress updates, plans, diagnostics,
intermediate drafts, final artifacts, headings, captions, table text, comments,
notes, reports, and natural-language string values in JSON, YAML, or other
machine-readable records. It is not limited to final or explicitly
user-facing prose.

Preserve exact machine syntax: schema keys, stable identifiers, hashes, file
paths, commands, code, exact bibliographic titles, and exact source fragments.
Keep such syntax in the machine layer and do not surface it in a readable
artifact unless the task requires it or the user asks for it. Explain every
surfaced identifier or necessary foreign term in the reader's language.
Machine syntax never exempts the surrounding natural-language text from the
language gate. Treat bundled templates as structural scaffolds: localize their
headings and explanatory text before using them in a Russian artifact.

## Required workflow

### 1. Fix the task boundary

Record the requested mode, question or artifact, allowed source identifiers,
input versions, language, audience, and requested output format. State any
missing requirement that affects the result.

If `project_context` is supplied, verify its manifest reference and context
hash before project-relative synthesis. Use its objective and question IDs for
routing only. Never cite the project context, an annotation, or routing state
as evidence.

For a notebook, identify its applied role, one principal research question or
bounded computational chain, scope, completion criterion, inputs, inherited
facts/numbers/hypotheses, method, observable outputs, limitations, and final
artifacts. Select one primary notebook genre profile by scientific role, not by
filename or library. Treat every notebook as an executable technical report
even when its applied role is model validation, data analysis, choice justification,
experiment analysis, planning, or engineering transfer. Do not infer the role
from the `.ipynb` extension, impose fixed headings, or use a cell-count
threshold. Split by independent questions, data or execution boundaries,
reusable intermediate artifacts, or independently changing preparation,
computation, and interpretation stages.

The reader-facing notebook must be a scientific and technical report, not a
metadata form. Do not call it a "research notebook" or open it with a
"passport", environment, inherited-state, file-list, or run-manifest section.
Describe inputs by scientific meaning: which experiment or calculation
produced them, for what object, under which conditions, where and when it was
performed when those facts are supplied, what quantities were recorded, and
which subset is analysed. Keep filenames, paths, hashes, software versions,
and upstream identifiers in technical metadata or loader code unless one of
them materially affects scientific interpretation.

Before each calculation stage, explain the investigated object, measurement or
computational model, necessary terms, geometry or causal relations, variables
and units, boundary or initial conditions, assumptions, expected limiting
behaviour, and applicability limits needed for that stage. Do not satisfy the
genre by prepending generic narrative cells to an otherwise unexplained
notebook.

Introduce each material equation only when the narrative first needs it for a
calculation, transformation, check, or interpretation. Do not collect equations
in an opening formula catalogue or term glossary. State the need in prose,
display and number the equation, define its symbols and units, apply it, and
refer to its number in the later sentence that transforms or interprets it.
Preserve stable internal equation identifiers beneath human-readable numbering
so that renumbering does not break the calculation chain.

Require a traceable narrative at both scales. Within one notebook, every
material operation must follow from an identified input, premise, or preceding
result and must expose the observable output that supports the next bounded
statement. Across a notebook sequence, pass accepted facts, numbers, hypotheses,
and artifacts through versioned handoff records so that the complete path from
source data to downstream conclusion can be reproduced and audited.

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
may not rest on a unit that is still `planned` when it is supported or bounded.
An unsupported outline proposal may point to a planned unit while it remains a
proposal.

When revising supplied scientific prose, create a formulation revision record
before applying a change. Preserve exact original and corrected wording,
locator, category, reason, affected claims and structure, evidence/result
references, and decision. An accepted semantic correction requires an existing
claim and evidence or an approved result. A revision record is never evidence.

### 5. Draft the requested artifact

Draft only after the evidence and claim ledgers exist. Preserve the direction,
population, design, comparison, unit, denominator, time point, uncertainty, and
causal strength of each source claim.

Keep observation, author interpretation, and synthesis by the current model
distinct. Make limitations travel with the claim they constrain.

For `dissertation-outline`, render the table of contents from stable structure
records and generate final page numbers only after document layout. For
`dissertation-introduction`, use the canonical claim-ledger section keys from
its genre reference and keep all eight normative elements present.
For `dissertation-literature-review-chapter`, freeze the corpus before synthesis,
retain conflicts, and require every research-gap claim to name its boundary.
For `dissertation-methods-chapter`, require protocol/data records, keep all five
control sections addressable, and never reconstruct a procedure from results.
For `dissertation-results-chapter`, use only approved result records and keep
observation distinct from interpretation. For `dissertation-synthesis-chapter`,
require both approved results and frozen literature, test comparability, and
retain conflicts and limits. For `dissertation-conclusion`, close every task
without adding a result or source. For `defense-propositions`, require an
atomic falsifiable assertion with result and structure anchors. For
`novelty-statement`, bound every priority claim to the actual corpus and own
result. For `thesis-synopsis`, map every claim back to the frozen dissertation.
For `approbation-record`, verify organizational facts without promoting them to
scientific support.

For a critic task, check the artifact first against the owning skill and genre:
required parts, logic, scientific formulation, narrative progression,
consistency, and formatting. Use the lightweight finding record from
`references/critic-workflow.md`. Escalate only factual, numeric, source,
absence, citation-coverage, or normative assertions to the evidence-verification
protocol. Do not require source machinery for a technical or reasoned editorial
finding.

### 6. Run the evidence gate

Before release, verify:

1. every material claim has valid evidence or result references;
2. every cited locator belongs to the allowed input set;
3. every internal reference resolves to an existing unit of the work;
4. every number exactly matches its source or approved result record;
5. causal language is permitted by the design;
6. conflicting evidence is visible;
7. unsupported claims are removed or explicitly blocked;
8. every accepted semantic wording correction is traceable;
9. no scientific source was introduced from model memory;
10. every evidence-dependent critic finding was checked against the relevant
    source, calculation, coverage record, or applicable authority;
11. technical, computational, and scientific validation statuses are reported
    separately and no status is inferred from another;
12. every local link, internal equation reference, in-text citation, and
    bibliography entry resolves under the selected reference contract;
13. every cross-notebook artifact has a versioned handoff record;
14. automation is blocked while data-selection rules or canonical-input
    decisions remain conflicted.

When a bundle is available, run:

```text
python scripts/validate_bundle.py evidence-bundle.json
```

The validator checks structural integrity, not scientific truth. Inspect the
source behind every high-impact claim even when validation passes.

### 7. Run the language gate

For every run whose working language is Russian, apply
`references/russian-scientific-style.md` to each natural-language fragment
before it is emitted, displayed, or persisted. This includes intermediate
chat and diagnostic text and natural-language values inside machine records,
not only the final artifact. Lock claims, numbers, units, citations, locators,
uncertainty, and causal strength before revising. Improve only terminology,
syntax, cohesion, and concision.

A complete Russian-language gate has three independent passes:

1. Rebuild headings, sentences, and paragraph transitions as original Russian
   prose. Reject translation-shaped rhetoric such as non-literal `From X to Y`
   headings, repeated negative contrasts, stock English summary frames, and
   Cyrillic English calques.
2. Apply the core manual checklist plus the selected genre and domain profiles.
3. Run the deterministic surface audit and resolve every finding. A clean
   report never waives the first two passes.

Apply all three passes to every natural-language fragment covered above. When
Python is available, pass each proposed standalone fragment to
`audit_text()` before emitting it; use the command-line form for files and
persisted artifacts. Do not postpone the check until after chat text has
already been shown or a note has been saved.

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
- formulation corrections made, rejected, or still proposed;
- whether any deterministic validator was run.

## Stop conditions

Stop and request input instead of guessing when:

- the requested claim lacks supplied evidence;
- a manuscript Results value lacks an approved result record;
- Methods lacks a protocol or record of what was actually done;
- a Results claim lacks an approved result record or a complete numeric
  boundary;
- synthesis lacks either approved results or a frozen comparable literature
  corpus;
- a conclusion introduces a claim, result, method, or recommendation absent
  from the approved ledgers;
- a proposition lacks a falsifiable predicate, approved result, or dissertation
  section anchor;
- novelty lacks a bounded literature corpus or own-result anchor;
- a synopsis source dissertation is not frozen or contains an unmatched claim;
- an approbation fact lacks an organizational record;
- an evidence-dependent critic finding cannot be checked against its source,
  calculation, declared coverage, or applicable authority;
- source versions conflict and no authoritative version is identified;
- data-selection rules conflict and no versioned resolution record identifies
  the authoritative policy;
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
- `references/reproducibility-contract.md`: shared working-versus-frozen
  reproducibility contract for notebooks, procedures, and experiments.
- `references/notebook-genre-profiles.md`: scientific-role profiles and their
  additional notebook gates.
- `assets/notebook-narrative.template.ipynb`: minimal editable notebook
  scaffold with report metadata and semantic cell tags.
- `scripts/lint_notebook.py`: dependency-free static notebook audit. It does
  not prove clean-kernel execution, scientific validity, or absence of all
  hidden state.
- `scripts/validate_notebook_references.py`: local-link, equation-reference,
  citation-label, and bibliography integrity audit.
- `assets/artifact-handoff.template.json` and
  `assets/artifact-handoff.schema.json`: versioned cross-notebook artifact
  contract.
- `scripts/validate_artifact_handoff.py`: handoff validator that blocks
  automated use of unresolved selection conflicts.
- `assets/<genre>.template.md`: genre output scaffolds.
- `assets/literature-review-output.template.md`: review scaffold.
- `references/literature-review-patterns.md`: review-profile selection,
  comparison units, paragraph architecture, and conclusion gates.
- `assets/manuscript-output.template.md`: manuscript scaffold.
- `assets/journal-pattern.template.json`: journal-pattern memory scaffold.
- `scripts/validate_bundle.py`: dependency-free structural validator.
- `references/journal-pattern-memory.md`: rules for extracting and retaining
  formatting patterns from a user-supplied journal example.
- `references/normative-pattern-memory.md`: rules for carding a normative
  document, and why a catalogue entry may carry no requirements.
- `assets/normative-pattern.template.json`: normative-card scaffold.
- `scripts/validate_normative_card.py`: dependency-free card validator.
- `references/dissertation-analysis-protocol.md`: preliminary, versioned
  standard for source freezing, Pass A measurements, continuous Pass B reading,
  promotion review, cross-work comparison, contents extraction, and correction
  logging.
- `references/work-pattern-memory.md`: rules for reading a defended work for
  its form — structure, how a chapter argues, how chapters connect, how the
  load-bearing statements are worded — why such a record has no field in which
  a requirement could be written, and why an expected arc lives in data with
  the name of whoever stated it.
- `assets/work-pattern.template.json`: work-card scaffold.
- `assets/work-aggregate.template.json`: scaffold for a pattern across works.
- `scripts/validate_work_card.py`: dependency-free work and aggregate
  validator; refuses obligation in keys and in prose, and refuses a claim
  resting on a work too weak to bear it.
- `references/russian-scientific-style.md`: Russian language core.
- `references/russian/`: genre language profiles.
- `scripts/audit_russian_style.py`: dependency-free heuristic style audit.
- `scripts/russian/`: machine-readable core, genre, and domain rule profiles.
- `references/critic-workflow.md`: lightweight technical, editorial, and
  evidential critic workflow.
- `references/critic-verification-protocol.md`: conditional verification for
  source-, number-, absence-, citation-, and authority-dependent findings.
- `references/scientific-judgment-calibration.md`: optional calibration for
  inference, sample roles, units of analysis, hierarchy, and severity.
