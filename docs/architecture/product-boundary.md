# Product Boundary

## Normative status and package precedence

This document is normative for product scope, composition, non-goals, and
architectural boundaries. It defines policy, not a serialization format. No
JSON schemas are defined here.

Read the shared normative package in this order:

1. `product-boundary.md` — product scope, composition, and non-goals;
2. `domain-model.md` — shared entity vocabulary and relationships, subject to
   this document and the invariants;
3. `invariants.md` — mandatory semantic and behavioural constraints.

When documents overlap, scoped precedence is:

| Question | Governing document |
|---|---|
| What the product includes or excludes | `product-boundary.md` |
| What semantic behaviour is mandatory | `invariants.md` |
| What entities mean and how they relate | `domain-model.md`, subject to the first two |
| How a current file or runtime contract behaves | The existing operational contract until an explicit migration |

Existing skills, schemas, validators, experiments, and stored records are not
changed by this document. Current operational contracts remain compatibility
implementations until a versioned, explicit, and tested migration changes
them.

## Product definition

The product is a composable skill suite, its explicit contracts, and a
benchmark/development lab for supplied scientific and technical materials. It
covers the path from source annotation and evidence-aware review through
research scripts and notebooks, reports, articles, and dissertation work. The
suite may support a small local edit or a large project audit, but it is not a
single universal procedure.

The product must keep semantic grounding, project context, expression, task
procedures, integrations, and evaluation separable. A workflow composes the
parts required for its task and records the applicable contract and checks.

## Required architectural separation

| Layer | Responsibility | Boundary |
|---|---|---|
| `research-grounding-kernel` | Basis and provenance of claims, epistemic distinctions, semantic preservation, source honesty, context use, and change/impact policy | Portable semantic policy; no storage, scheduler, transport, or application-specific workflow |
| `russian-scientific-expression` | Russian scientific/technical terminology, syntax, and controlled expression | Composable expression layer; it must preserve claims, modality, numbers, units, locators, uncertainty, causal force, and scope |
| Workspace and state | External mutable state for multiple projects, shared sources, ideas, typed assessments, and derived artifacts | State is stored outside skills and may be supplied, absent, or implemented by a compatible host; it is not one mega-skill |
| Task workflows | Annotation, review and synthesis, scripts/notebooks, reports, articles, dissertation, critique, and formatting procedures | Workflow-specific contracts and gates; workflows compose the kernel and expression layers as needed |
| Integrations and orchestration | Zotero or other source transports, event detection, scheduling, and host adapters | Optional external mechanisms; never kernel dependencies |
| Benchmarks and development lab | Contract tests, validators, comparisons, reports, and experiments for quality and regression control | Evaluation/development support, not hidden runtime state or semantic authority |

The grounding kernel and Russian expression layer are independent but
composable. Russian scientific output normally uses both through a task
workflow; neither layer absorbs the other layer's responsibilities.

## Workspace and project boundary

Multiple concurrent projects are a required product use case. Sources should
be reusable at workspace scope, while project-relative interpretation and
relevance remain separate from source-intrinsic analysis. Generated ideas and
candidate cross-project connections remain proposals until an explicit review
or acceptance process acts on them.

Workspace version 1 remains thin. It provides only the minimum routing,
selection, reference, dependency, and freshness context needed by workflows.
It must not become a mandatory central database, event bus, scheduler, global
memory dump, or autonomous project manager. Detailed entity definitions and
relationships belong in `domain-model.md`, not in this boundary document.

Project state is context and routing information, not scientific evidence by
itself. A source card, annotation, summary, or derived note is an index and
reading aid, not a substitute for the supplied source or its locators.

## Source acquisition and integrations

The baseline product processes supplied materials. Literature search and other
acquisition are not kernel responsibilities. Search acquisition may be added
later as an external workflow/integration selected by a comparative benchmark
with a shared result contract; it is not an assumed current capability.

Zotero is an optional integration and transport, not a dependency of the
grounding kernel, the expression layer, or supplied-source workflows. A Zotero
adapter may provide inventory, annotation, or synchronization operations when
explicitly installed and tested, but the product must remain useful without
Zotero, MCP, function calling, a vector database, an online service, Word, or a
scheduler.

## Explicit non-goals

The product is not an autonomous research manager. The core suite must not, on
its own:

- choose a research topic, design a study, or select experimental methods;
- invent or approve hypotheses, decisions, or project knowledge;
- perform or replace statistical analysis;
- decide what the user investigates next;
- choose journals, publication strategy, or publishability;
- search for or acquire literature without an explicitly selected external
  workflow;
- silently turn a generated idea, candidate connection, or project relevance
  judgement into accepted knowledge or evidence;
- require heavyweight infrastructure for a task that does not need it.

These activities may be supported when the user explicitly initiates them or a
separate workflow owns them, but they are outside the kernel and product
boundary defined here. New evidence triggers ingestion and impact review; it
does not automatically publish, accept state, or regenerate every artifact.
Full resynthesis remains the safe operational fallback until selective update
is validated by benchmark.

## Progressive formalization

Workflows must use the minimum sufficient rigor and may increase it as task
scope increases:

| Level | Minimum composition |
|---|---|
| L0 | Local language, terminology, and epistemic discipline |
| L1 | L0 plus relevant project state |
| L2 | L1 plus supplied sources, source records, and locators |
| L3 | L2 plus cross-source synthesis, conflict, and applicability analysis |
| L4 | L3 plus cross-artifact or chapter consistency and dependency audit |

The level is an internal workflow decision; users should not be forced to
choose a level unless the task genuinely requires clarification. A local edit
must not require a workspace scan or evidence bundle. A source-grounded or
project-level result must load the corresponding supplied sources and state.

## Supersedes and clarifies

This table records document authority. It does not rewrite any referenced file.

| Existing document or memo | Effect of this boundary |
|---|---|
| `docs/possible-project-workspace-architecture.md` | Superseded as decision authority. It remains a non-normative historical design memo. Its options for a thick workspace, event model, planner, SQLite, live Zotero, and search are not requirements; only explicitly adopted, benchmarked work may promote one of them. |
| Root-level `CODEX_ARCHITECTURE_HANDOFF.md`, when present as local design input | Superseded as decision authority by this package. It remains intermediate discovery material and is not required by a repository checkout. |
| `docs/handoff.md` | Clarified as a descriptive handoff covering current work, priorities, and implementation status. It does not define the product boundary or authorize a mega-skill, mandatory integrations, or infrastructure expansion. |
| `docs/project-literature-architecture.md` | Clarified as the current offline project/annotation/living-review contract and workflow description. Its existing schemas, validators, snapshots, and compatibility behaviour remain operational; live Zotero, a unified multi-project state, and a scheduler are not implied or required. |
| `docs/architecture/invariants.md` | Companion normative document for mandatory semantic behaviour. It governs invariants, while this document governs scope and non-goals. |
| Current skills and operational schemas | Compatibility implementations until explicit migration. This document does not claim that any existing skill or schema has been changed. |
