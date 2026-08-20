# Architectural handoff for Codex

## Purpose of this document

This is not a request to immediately rewrite the repository. It is the current architectural direction reached after critically reviewing the repository and discussing the intended product boundary.

Use the repository itself as the source of truth for current implementation details. Treat this document as the design intent that should guide the next refactoring proposal.

Repository:
`NixWrk/NIX_scientific-evidence-skill`

---

## 1. Original intent

The project originally started as a skill that should make LLM/agent output:

- Russian;
- scientific/technical rather than conversational;
- precise in terminology;
- explicit about evidence, assumptions, limitations, uncertainty, and causal strength;
- resistant to semantic drift during rewriting;
- suitable for serious scientific and engineering work.

The original intent was **not** to build a complete autonomous scientific assistant.

During development, the repository expanded toward:

- fixed-corpus scientific Q&A;
- literature reviews;
- evidence records and claim ledgers;
- manuscript drafting;
- frozen research results;
- figure/formatting modes;
- journal-example memory;
- bundle validation;
- benchmark infrastructure.

Much of this is useful, but the skill itself started to absorb responsibilities that belong to more specialized workflows or infrastructure.

---

## 2. Current architectural diagnosis

The repository currently mixes at least four concerns:

1. **Language layer**
   - Russian scientific/technical language;
   - terminology;
   - sentence structure;
   - removal of unsupported rhetorical strengthening;
   - preservation of numbers, units, variables, citations, and technical tokens.

2. **Epistemic layer**
   - distinction between fact, inference, assumption, hypothesis, limitation, uncertainty, and conflict;
   - calibration of claim strength to its basis;
   - preservation of scientific meaning during editing;
   - source honesty.

3. **Task-specific scientific workflows**
   - Q&A over a fixed corpus;
   - literature synthesis;
   - manuscript drafting/revision;
   - evidence tables, study cards, claim ledgers, frozen results, journal patterns.

4. **Repository/benchmark infrastructure**
   - experiments;
   - schemas;
   - validators;
   - metrics;
   - benchmark comparisons.

The important conclusion is:

> The current `scientific-evidence-workflow` is not necessarily overbuilt for its present fixed-corpus evidence-processing purpose. It is over-scoped relative to the original universal language/epistemic skill.

The goal is therefore **not simply to delete complexity**. The goal is to put each responsibility at the correct architectural layer.

---

## 3. Revised target

The desired system should support both very small and very large scientific tasks without becoming a full research agent.

Examples:

- improve one technical paragraph;
- choose consistent Russian terminology;
- annotate one scientific paper;
- analyze a paper in the context of one or several projects;
- prepare a literature review based on the actual papers, not only summaries;
- work on a dissertation chapter while preserving definitions, hypotheses, assumptions, results, terminology, limitations, and decisions from previous chapters;
- detect that new evidence affects an existing review or chapter;
- discover potentially useful non-obvious relationships between a new paper and other projects.

The central target can be described as:

> A portable layer for project-contextual, evidence-aware, terminologically consistent work of an LLM with scientific and technical material.

Three core responsibilities:

- **Context** — maintain and select relevant long-lived project/workspace state.
- **Grounding** — preserve the basis, epistemic status, scope, and traceability of material scientific claims.
- **Expression** — produce strict Russian scientific/technical language without changing scientific meaning.

---

## 4. Explicit non-goals

The core skill must not become an autonomous research manager.

It should not, on its own:

- choose the research topic;
- design the study;
- select experimental methods;
- invent or approve research hypotheses on behalf of the user;
- perform or replace statistical analysis;
- decide what the user must investigate next;
- choose journals or publication strategy;
- predict publishability;
- autonomously search for new literature unless another tool/workflow explicitly provides that capability;
- automatically promote model-generated ideas into accepted project knowledge;
- require MCP, function calling, a vector database, Zotero, or online services.

It may assist with any of these activities when explicitly initiated by the user or another workflow, but they are not responsibilities of the core skill.

---

## 5. Important boundary: skill vs system

Do not put all desired behavior into one `SKILL.md`.

Separate four layers.

### A. Skill kernel

Defines cognitive and semantic policy:

- how to distinguish evidence, interpretation, assumption, hypothesis, limitation, and uncertainty;
- how to preserve meaning;
- how to use project context;
- how to select sufficient context;
- how to evaluate relevance;
- how to identify candidate cross-project connections;
- how to assess whether new information affects existing artifacts;
- how to formulate the final Russian scientific/technical output.

It answers:

> How should the model reason and what counts as a valid state/change?

### B. Knowledge state / workspace

Stores durable information.

It answers:

> What is currently known, accepted, proposed, connected, and current?

### C. Workflows

Specialized procedures such as:

- article ingestion;
- literature synthesis;
- chapter work;
- project audit;
- cross-project discovery;
- Q&A.

They answer:

> What sequence of operations should be performed for this class of task?

### D. Orchestrator

Detects or receives events and invokes workflows.

Examples:

- new Zotero item;
- changed source file;
- user asks for project audit;
- collection was updated.

It answers:

> When should a workflow run?

The core skill should define the **protocol for reacting to a corpus change**, but not claim to be the watcher/webhook/cron system itself.

---

## 6. Workspace, not one project

A user may have many concurrent projects.

Therefore the long-lived state should be organized above individual projects.

Conceptually:

```text
WORKSPACE
├── PROJECTS
├── SOURCES
├── IDEAS
├── CONCEPTS / TERMINOLOGY
├── RELATIONS
└── ARTIFACTS
```

A scientific paper should normally be a workspace-level source, not a copy owned by one project.

Example:

```text
SRC-017
  ├── relevant_to → PROJECT-A
  ├── relevant_to → PROJECT-C
  └── inspired → IDEA-008
```

Project-specific interpretation must be stored separately from the intrinsic analysis of the source.

---

## 7. Source model: intrinsic content vs project-relative relevance

For every source, preserve two different layers.

### Source-intrinsic layer

What the publication itself contains, independently of any current project:

- purpose;
- research question;
- design/method;
- population/material;
- variables/outcomes;
- principal findings;
- negative findings;
- limitations;
- author interpretation;
- important locators;
- version/provenance.

### Project-relative layer

How the source relates to a particular project:

- relevance;
- which project claims/hypotheses it supports or challenges;
- applicability limits;
- methodological analogies;
- useful techniques;
- chapter/section relevance;
- open questions raised for that project.

Do not allow project expectations to overwrite the source-intrinsic record.

This separation is important to reduce confirmation bias and to make the same source reusable across projects.

---

## 8. Source cards are indices, not substitutes for the paper

Do not build literature reviews from summaries of summaries.

The intended pattern is:

```text
full papers
    ↓
source cards
    ↓
identify relevant sources/fragments
    ↓
return to original papers for material claims
    ↓
synthesis
```

A source card helps answer:

> Where should I look and why is this source relevant?

It is not itself the final evidence for every important claim.

Material synthesis claims should remain traceable to original source locations when practicable.

---

## 9. Project state

For large projects such as a dissertation, do not rely on the model merely remembering all previous text.

Maintain an explicit, versioned project state.

Candidate content:

```text
PROJECT
├── purpose / question / scope
├── terminology / definitions
├── propositions
├── hypotheses
├── assumptions
├── constraints / limitations
├── decisions
├── results
├── open questions
├── structure
└── artifacts
```

The project state contains what is currently considered active, not the entire historical transcript.

History and current state are different concepts.

---

## 10. Semantic entity types and statuses

Avoid encoding several different dimensions in one overloaded claim status.

At minimum distinguish **entity type** from **project status**.

Possible entity types:

- proposition;
- hypothesis;
- assumption;
- interpretation;
- limitation;
- decision;
- open question;
- definition;
- result;
- idea.

Possible lifecycle status:

```text
proposed
accepted
contested
superseded
rejected
```

A model-generated proposal must not automatically become accepted project state.

Key invariant:

> generated ≠ accepted

Promotion into canonical project state requires an explicit user/project decision or another clearly defined acceptance mechanism.

---

## 11. Chapter interfaces for large documents

A dissertation chapter should not be represented only by its full text.

After substantial work on a chapter, extract a compact interface for later chapters:

```text
Introduced
  definitions / terms

Established
  propositions / results

Assumed
  assumptions

Hypothesized
  hypotheses

Rejected
  rejected hypotheses/interpretations

Constraints for later work
  applicability boundaries / methodological constraints

Open
  unresolved questions
```

When working on a later chapter, load:

- global project state;
- local chapter state;
- relevant interfaces from earlier chapters;
- only the source/result material needed for the current task;
- the current text being edited.

Retrieve full earlier chapter text only when a dependency needs inspection.

---

## 12. Progressive formalization

Do not require the same heavy evidence pipeline for every request.

Use the minimum sufficient rigor for the task.

Conceptual levels:

```text
L0 local
  language + terminology + epistemic discipline

L1 project-aware
  + relevant project state

L2 source-grounded
  + sources, source cards, locators

L3 synthesis
  + cross-source comparison, conflict/applicability analysis

L4 project audit
  + cross-artifact/chapter consistency and dependency checking
```

These are primarily internal levels. Do not force the user to choose one manually unless necessary.

The model/workflow should select the minimum sufficient level.

---

## 13. Cross-project discovery

When a new source is analyzed, do not evaluate it only against the currently active project.

After creating a neutral source-intrinsic record, perform a workspace relevance scan against active projects and existing ideas.

Look for:

- shared variables or concepts;
- analogous methods;
- transferable analysis techniques;
- shared mechanisms;
- conflicting findings;
- common limitations;
- possible methodological precedent;
- useful differences in population/system/conditions;
- potential relationships to hypotheses in other projects.

However, non-obvious connections are **candidate connections**, not established facts.

Example conceptual record:

```yaml
id: LINK-042
type: candidate_connection

source:
  SRC-017

target:
  PROJECT-C/H-004

observation:
  "The source reports a related dependence in a different system."

possible_relevance:
  "This may be an analogue relevant to H-004."

basis:
  - source locator
  - project hypothesis

limitations:
  - different population
  - different measurement method

status: proposed
```

The system may say:

> This may be useful for project C.

It must not silently convert that into:

> Source X confirms hypothesis H-004.

---

## 14. Ideas as first-class but non-canonical entities

Potential research or methodological ideas should be preserved so they are not lost.

But ideas must remain separate from accepted project knowledge.

Conceptually:

```yaml
id: IDEA-014
text: "Check whether method X can be applied to project C."
origin:
  - SRC-042
related_projects:
  - PROJECT-C
basis:
  - SRC-042:Methods
type: methodological_transfer
status: proposed
```

Ideas may later become reviewed/accepted/rejected, but creation alone does not modify the project research program.

This enables a cross-project idea inbox without making the skill an autonomous scientific director.

---

## 15. New-source invariant

A newly added or changed scientific source should not be silently ignored.

However, distinguish **policy** from **event detection**.

The core rule should be approximately:

> Before source-grounded, synthesis, or project-level work, determine whether the relevant source set contains unprocessed or changed sources. A newly observed or changed source must pass source ingestion and impact analysis before dependent synthesis artifacts can be treated as current.

A complete source-ingestion pass should guarantee at least:

```text
1. register the source and version/hash;
2. read the primary material;
3. create/update the source-intrinsic card;
4. record material findings/limitations with useful locators;
5. evaluate relevance to active projects;
6. search for candidate cross-project connections;
7. assess impact on dependent reviews/claims/artifacts;
8. mark affected artifacts for review;
9. register new ideas only as proposed;
10. record completion/version of analysis.
```

The skill defines this invariant.

A Zotero watcher, webhook, cron task, CLI command, or other orchestration mechanism may trigger it, but that trigger mechanism is outside the kernel.

---

## 16. Do not automatically regenerate a literature review

The desired dependency flow is:

```text
new source
    ↓
source ingestion
    ↓
impact analysis
    ↓
dependency invalidation / freshness update
    ↓
selective review
    ↓
revision only if required
```

Not:

```text
new source
    ↓
regenerate everything
```

A new paper may:

- add nothing material;
- strengthen an existing conclusion;
- add an applicability boundary;
- contradict a material claim;
- introduce a new method;
- affect several projects.

Therefore perform impact analysis first.

---

## 17. Artifact dependencies and freshness

Derived artifacts such as literature reviews and dissertation chapters should know what they depend on.

Conceptually:

```yaml
artifact: REVIEW-003

depends_on:
  sources:
    - SRC-001
    - SRC-002
    - SRC-014
  project_state:
    - H-003
    - DEF-007

evidence_status: valid
corpus_status: current
```

After a corpus change:

```yaml
corpus_status: needs_review
trigger:
  - SRC-042
```

After impact analysis, either return it to `current` or mark a material revision as needed.

Important distinction:

> New evidence does not automatically mean an old artifact is wrong. It means its currency relative to the new corpus must be checked.

Keep correctness/evidence validity distinct from corpus freshness if the schema supports it.

---

## 18. Idempotent ingestion

Repeated processing of the same unchanged source must not create duplicate cards, duplicate ideas, duplicate links, or duplicate evidence records.

Retain/use concepts such as:

```text
source_id
content_hash
analysis_schema_version
analysis_version
```

If the source content and relevant analysis schema have not changed, ingestion should be recognized as already complete.

If the source changes, or the analysis schema meaningfully changes, explicit re-analysis can occur.

---

## 19. What to retain from the current repository

Do not discard useful work merely because it belongs to another layer.

Important existing ideas to preserve include:

- semantic lock during revision;
- evidence-first discipline where the task requires it;
- source IDs/content hashes/locators;
- distinction between fact and interpretation;
- causal-strength calibration;
- explicit uncertainty and missing-data handling;
- numeric/unit preservation;
- terminology discipline;
- version awareness;
- local-model compatibility;
- separation of evidence checking from language checking.

Current `russian-scientific-style.md` is close to the original language/semantic core.

Current `evidence-contract.md` contains useful primitives, but its ontology should be reviewed for unnecessary overlap and excessive domain specificity.

Current Q&A/literature-review/manuscript files should be treated as candidate specialized workflows, not automatically as the universal kernel.

The Russian style audit script is a heuristic linter, not a validator of scientific correctness. Its limitations should remain explicit.

---

## 20. Evidence model should become more general

The original skill may be useful not only for empirical biomedical/scientific papers but also for engineering, software, mathematics, and technical analysis.

Therefore the universal core should not assume that every justified claim is based on a scientific publication or an empirical `result_id`.

Possible grounds include:

- source publication;
- supplied data;
- measurement;
- derivation;
- calculation;
- code;
- test result;
- specification;
- standard;
- protocol;
- explicit assumption;
- accepted project decision.

Use a general concept such as **basis of claim** in the kernel.

Specialized scientific evidence schemas may remain available inside scientific workflows.

---

## 21. Current evidence ontology needs review

The current model includes dimensions such as:

- `support_type`;
- `certainty`;
- `status`;
- `disposition`;
- `boundary`;
- `causal_basis`.

These are useful concepts, but some appear semantically overlapping.

Examples:

- `conflicted` appears conceptually as both epistemic condition and status;
- `bounded` is not necessarily an evidence-support level—a claim can be strongly supported but valid only within a narrow scope;
- disposition is an editing/action decision, not evidence state.

When redesigning, prefer orthogonal dimensions rather than one large status vocabulary.

Do not redesign this blindly; first map current semantics and real experiment usage.

---

## 22. Benchmarks should follow the new product boundary

The benchmark suite should not optimize only for source extraction/evidence tables/manuscript workflows.

For the kernel, add or prioritize evaluation dimensions such as:

```text
semantic preservation
numeric preservation
causal calibration
epistemic calibration
terminology consistency
Russian scientific/technical language quality
concision
source honesty
technical-token preservation
task preservation
cross-project relevance precision
false-positive rate for speculative connections
state-update correctness
artifact freshness detection
```

Existing experiments already suggest two useful lessons:

- evidence-first processing has demonstrated improved traceability/auditability, but not yet a demonstrated accuracy improvement in the existing comparison;
- the separate Russian-language layer can preserve claims/evidence/numbers while changing language, but verbosity should be monitored.

Treat those as architectural evidence for separating the kernel from heavier evidence workflows.

---

## 23. Proposed conceptual architecture

```text
                         WORKSPACE / KNOWLEDGE STATE
                       /            |              \
                PROJECTS          SOURCES           IDEAS
                   |                 |                |
                   └────────── RELATIONS ─────────────┘
                                  |
                                  v
                         CONTEXT SELECTION
                                  |
                                  v
                           +--------------+
                           | SKILL KERNEL |
                           |--------------|
                           | context      |
                           | grounding    |
                           | discovery    |
                           | change logic |
                           | expression   |
                           +------+-------+
                                  |
             +--------------------+--------------------+
             |                    |                    |
             v                    v                    v
       article workflow     synthesis workflow    chapter workflow
             |                    |                    |
             +--------------------+--------------------+
                                  ^
                                  |
                           ORCHESTRATOR
                     (optional environment layer)
```

Dependency direction:

> specialized workflow → kernel

not:

> kernel → every specialized workflow as mandatory behavior

---

## 24. Desired next step in this repository

Do **not** start by rewriting everything.

First inspect the current repository and produce an architectural migration proposal.

The proposal should contain:

### A. File-by-file classification

Classify current relevant files/rules into:

```text
CORE
PROJECT_STATE
SOURCE_CONTEXT
TASK_SPECIFIC_WORKFLOW
ORCHESTRATION / INTEGRATION
BENCHMARK_DEVELOPMENT
DELETE_OR_RELAX
```

For mixed files, classify individual sections rather than forcing the whole file into one class.

### B. Minimal domain model

Propose the smallest coherent schema for:

```text
WORKSPACE
PROJECT
SOURCE
SOURCE_PROJECT_RELATION
IDEA
ARTIFACT
RELATION
```

Do not over-normalize prematurely.

For each entity identify:

- identity;
- minimum fields;
- lifecycle/status;
- provenance;
- versioning;
- dependencies;
- which fields are mandatory vs optional.

### C. Invariants

Explicitly specify invariants including:

```text
generated != accepted
source intrinsic content != project interpretation
source card != substitute for source
new/changed source => ingestion + impact check
impact check before regeneration
unchanged ingestion is idempotent
candidate connection != established evidence
artifact correctness != corpus freshness
kernel does not require an orchestrator
```

### D. Revised kernel proposal

Draft the conceptual structure of a smaller universal `SKILL.md`.

It should focus on:

- task boundary;
- context selection;
- epistemic discipline;
- semantic preservation;
- source honesty;
- progressive formalization;
- cross-project discovery;
- change/freshness handling;
- Russian scientific/technical expression;
- explicit non-goals.

Do not include detailed manuscript/journal procedures in the kernel.

### E. Migration path

Propose how to migrate from the current repository incrementally without destroying existing experiments.

Prefer:

1. preserve current behavior and benchmark artifacts;
2. extract the kernel;
3. define workspace/project/source schemas;
4. move specialized procedures behind workflows;
5. adapt tests/experiments;
6. only then deprecate obsolete or duplicated structures.

### F. Critical review

Do not merely implement these ideas literally.

Look for:

- unnecessary complexity;
- duplicated concepts;
- hidden coupling;
- requirements that cannot work reliably for an LLM;
- state that does not need to be persistent;
- operations that belong to retrieval/orchestration rather than the skill;
- likely false-positive sources in cross-project discovery;
- scalability issues for dozens of projects and hundreds/thousands of papers.

Explicitly challenge the architecture where appropriate.

---

## 25. Output requested from Codex now

For this first pass, return:

1. your reconstruction of the intended product boundary;
2. a map of the current repository against the target layers;
3. the minimal proposed entity model;
4. the key invariants;
5. the proposed new `SKILL.md` outline;
6. a migration plan;
7. major unresolved architectural questions and risks.

Do not perform a broad repository rewrite before presenting this analysis.

Small exploratory sketches/diffs are acceptable if they make the proposal concrete, but preserve the repository until the architecture is agreed.

---

## 26. Decision criterion

The redesign is successful if the same kernel can sensibly support all of these without mandatory heavyweight processing:

```text
"Improve this paragraph."

"Annotate this one paper in the context of project A."

"Check whether this paper is useful to any of my other projects."

"Update the literature synthesis after the corpus changed."

"Work on dissertation chapter 4 while preserving the accepted state from chapters 1–3."

"Audit the dissertation for contradictions, terminology drift, unsupported claims,
and outdated literature-dependent synthesis."
```

The kernel should scale in rigor with the task rather than forcing a full evidence workflow every time.

The surrounding system may be sophisticated. The **kernel itself should remain conceptually narrow and portable**.
