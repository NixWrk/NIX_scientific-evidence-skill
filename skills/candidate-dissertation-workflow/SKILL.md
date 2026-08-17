---
name: candidate-dissertation-workflow
description: Orchestrate the complete evidence-bound workflow for a Russian candidate dissertation, from literature and similar-work acquisition handoff through corpus freezing, outline, introduction, review, methods, results, synthesis, conclusion, defense propositions, novelty, approbation, synopsis, apparatus, Word review, and final release. Use when an LLM must decide what dissertation task comes next, resume a dissertation project, coordinate multiple dissertation skills, audit whole-work readiness, or prevent scientific writing and formatting stages from being run with missing inputs.
---

# Candidate dissertation workflow

Coordinate the project; delegate scientific prose and technical formatting to
the specialized child skills. Do not duplicate their rules or treat this
orchestrator as evidence.

## Start from project state

Load an existing `CDW-001/v1` project manifest or copy
`assets/dissertation-project.template.json`. Read
`references/project-manifest.md`, then validate it with:

```text
python scripts/validate_dissertation_project.py dissertation-project.json
```

Preserve source and artifact hashes. Update a stage only after its artifact,
child-validator report and gate report exist. A status string is not validation
evidence. Record a missing input as an open blocker; do not hide it in prose.

## Route the current request

Read `references/routing.md` and select exactly one primary stage. Load the
named child skill and only its relevant genre/reference files:

- scientific content, evidence, chapters and qualification statements:
  `scientific-evidence-workflow`;
- title page, Word TOC, abbreviations, terminology, bibliography, illustration
  and appendix registers, critic journals and Word review copies:
  `dissertation-formatting-and-apparatus`;
- final DOCX rendering and visual QA: the host document capability.

Search and Zotero/web retrieval belong only to acquisition. Freeze every
selected source before evidence extraction or drafting. Once drafting starts,
do not silently expand or replace the corpus.

## Apply stage gates

Before a child stage starts, verify its input gate:

- review chapter: frozen literature corpus;
- methods: protocol or data records;
- results: approved result records;
- synthesis: approved results plus frozen literature;
- conclusion: final task, result and structure ledgers;
- propositions: falsifiable result and structure anchors;
- novelty: literature boundary plus own-result anchors;
- approbation: organizational records;
- synopsis: final dissertation claims; it may add no claim;
- apparatus: approved scientific text and resolved normative profile.

If a gate fails, set the stage to `blocked`, add the exact required input, and
continue only with another independent ready stage. Never reconstruct Methods
from Results, create Results from literature, or turn defended-work frequency
into a normative rule.

## Persist each completed stage

For every produced or audited artifact:

1. record genre, path, version, hash, source IDs and validation status;
2. run the child skill's deterministic validator and semantic/manual gates;
3. record scientific formulation revisions separately from evidence;
4. update dependent stage readiness without marking it complete;
5. commit a stable repository state when the project is version-controlled.

Parallelize only stages with satisfied inputs and no dependency edge between
them. Merge through shared structure, terminology, claim, result and normative
profiles; never merge prose by convenience.

## Release the dissertation

Read `references/release-gates.md`. Release only when all required stages are complete, every optional stage is
resolved as `complete` or reasoned `not_applicable`, every gate has a hashed
passing report, every referenced file and SHA-256 verifies, and no blocker
remains open. A conditional stage may be `not_applicable` only with a recorded
reason and may not be marked required.

Run the apparatus critic on the final manuscript, materialize the same journal
as Word comments/tracked changes when requested, open-save the copy in Word or
a compatible engine, structurally audit its OOXML, and inspect every rendered
page. Do not claim that a cached TOC proves current page numbers.

## Return status

Lead with the requested artifact or the next executable stage. Also report:

- completed, ready and blocked stages;
- exact missing inputs and unresolved authorities;
- validators and manual gates run;
- findings not assessed;
- next stage and why it is now safe.
