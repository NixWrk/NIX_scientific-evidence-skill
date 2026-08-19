# Research Architecture Invariants

## Normative status

This document is normative for architectural changes to this repository. It
defines the semantic and behavioural constraints that future skills, contracts,
schemas, workflows, adapters, and migrations must preserve. It does not define
a serialization format and does not change any current operational contract.

Read the normative package in this order:

1. [`product-boundary.md`](product-boundary.md) for product scope and non-goals;
2. [`domain-model.md`](domain-model.md) for the shared vocabulary and entity
   boundaries;
3. this document for mandatory cross-cutting behaviour.

When documents overlap, `product-boundary.md` governs scope and non-goals, this
document governs mandatory semantic behaviour, and `domain-model.md` governs
entity meaning and relationships subject to the first two. Existing versioned
contracts and validators remain authoritative for their current file formats
until an explicit migration changes them. A mismatch between an operational
contract and this package is a migration requirement, not permission to change
current data or behaviour implicitly.

## 1. Proportionate and sufficient context

1. A workflow MUST select context, sources, and project state proportionately
   to the task and MUST NOT load unrelated state without a defined retrieval or
   discovery purpose. It SHOULD use the minimum context sufficient to perform
   the task reliably. A declared discovery purpose MAY widen the context beyond
   already known project dependencies, including to identify candidate
   cross-project relevance.
2. A local language edit or other low-rigour task MUST NOT require a workspace
   scan, corpus inventory, project manifest, or evidence bundle unless the user
   asks for project alignment or evidential checking.
3. Higher-rigour workflows MAY require progressively richer project state,
   evidence, dependency, and verification records.
4. Lack of optional infrastructure such as Zotero, search, a scheduler, or a
   database MUST NOT prevent a supplied-source task that does not need it.

## 2. Identity, versions, and provenance

1. An internal entity identity MUST be independent of an external system
   identifier. In particular, a Zotero item key MUST NOT be a `SOURCE` identity.
2. A Zotero reference MUST include sufficient library scope together with the
   item key so that identical keys in different libraries do not collide.
3. `SOURCE` MUST identify the logical source used by the workspace.
   `SOURCE_VERSION` MUST identify the exact immutable content or representation
   actually analysed in version 1. The term does not assert a bibliographic
   version relationship between a preprint, version of record, PDF, or HTML.
4. A `SOURCE_VERSION` MUST preserve a content identity and provenance for the
   acquisition and every material transformation used for analysis, including
   extraction, OCR, and normalization when applicable. Analysis schema and
   analyser versions MUST remain separate from source content identity.
5. IDs, hashes, locators, dependency references, and provenance MUST survive
   drafting, language revision, export, and migration without silent weakening.

## 3. Source-intrinsic and project-relative knowledge

1. Source-intrinsic description MUST be separated from project-relative
   relevance, interpretation, and proposed use.
2. A source card, annotation, derived note, or summary MUST be treated as an
   index and reading aid, not as the primary source or a substitute for evidence.
3. A `SOURCE_PROJECT_RELATION` MUST be a reproducible project-relative
   assessment. It MUST reference the exact `SOURCE_VERSION` assessed and enough
   project inputs to reproduce the judgement.
4. Sufficient project inputs MUST include the project identity and context plus
   the actually used questions, definitions, hypotheses, decisions, results, or
   other `PROJECT_STATE_ITEM` dependencies. A complete immutable project-state
   snapshot MAY replace the explicit dependency list when it captures the same
   information. A legacy `context_hash` alone is insufficient when the judgement
   depends on project state outside that hash.
5. A changed source version or project dependency MUST make the prior assessment
   eligible for reassessment. It MUST NOT rewrite the prior assessment or alter
   unchanged source-intrinsic analysis.
6. Candidate cross-project relevance MUST remain proposed until reviewed. It
   MUST NOT create accepted knowledge, a hypothesis, or a decision in the target
   project automatically.

## 4. Project state and acceptance

1. Generated content MUST NOT be accepted implicitly. A model or workflow MAY
   create a proposal but MUST NOT create an authoritative acceptance decision.
2. Acceptance MUST originate in a traceable, append-only, explicitly authorized
   `AcceptanceDecision` tied to the exact `PROJECT_STATE_ITEM` content or
   revision under consideration.
3. A convenient `acceptance.state` field MAY be materialized, but it MUST be a
   deterministic projection of applicable acceptance decisions, not an
   independent source of truth.
4. Replacing accepted knowledge MUST preserve history. A successor item MUST
   identify the item it supersedes. The predecessor remains historically
   accepted and becomes non-current only after the successor is accepted.
   `superseded` MUST NOT be encoded as an acceptance value.
5. The directed `supersedes` graph MUST be acyclic.
6. If multiple accepted successors compete for the same effective role and
   scope, the canonical project-state projection MUST expose the ambiguity and
   MUST NOT silently select one.
7. `contested` MUST NOT be a universal state. Conflicting evidence belongs in an
   evidence assessment; changed dependencies belong in a reassessment or
   freshness decision; disagreement about project adoption requires a competing
   proposal or explicit review decision.
8. Membership in project state alone MUST NOT confer evidential force.
   Evidential use depends on entity type, basis, provenance, scope, and
   verification. A traceable and verified project result MAY support a claim;
   a goal, hypothesis, convention, or methodological decision does not become
   empirical evidence merely because the project accepted it.

## 5. Orthogonal semantic axes

1. Entity type, project acceptance, evidence assessment, verification outcome,
   processing state, release state, and dependency freshness MUST remain
   semantically distinct.
2. New domain records MUST NOT introduce a bare generic `status` field. Each
   state-bearing field or record MUST name the question it answers.
3. Not every entity needs every axis. An axis MUST appear only where its
   semantics apply.
4. `not_assessed` MUST remain distinct from `unsupported`: the absence of an
   assessment is not negative evidence.
5. Existing fields such as `status`, `annotation_status`, or
   `current_artifact.status` remain compatibility projections for their current
   operational contracts; they MUST NOT be interpreted as a universal state
   model.

## 6. Artifacts, revisions, and freshness

1. A logical `ARTIFACT` and a concrete `ARTIFACT_REVISION` MUST be distinct.
2. Once recorded, an `ARTIFACT_REVISION`'s content, content identity,
   dependencies, and production provenance MUST be immutable. A changed output
   requires a new revision.
3. Freshness MUST be expressed by a separate, traceable, append-only
   `FreshnessAssessment` that references the immutable revision, the trigger,
   the dependency state considered, the conclusion, time, and provenance.
4. A convenient current freshness field MAY be materialized, but it MUST be a
   projection of applicable freshness assessments. Marking a revision
   `needs_review` MUST NOT mutate its content or original dependencies.
5. Freshness, correctness, evidential validity, verification, and publication
   state MUST remain independent. A previously verified revision may require
   review after an input changes without becoming retroactively invalid.
6. A source card MAY initially use the `ARTIFACT` and `ARTIFACT_REVISION` model.
   A separate source-card entity MUST NOT be introduced until a real workflow
   demonstrates incompatible semantics.

## 7. Change, impact, and regeneration

1. New or changed source content within a workflow's declared monitored corpus
   or workspace source scope MUST pass the applicable ingestion and
   relevance/impact assessment before a dependent corpus-derived artifact is
   considered current. The declared scope MAY be a project corpus or a workspace
   collection evaluated against selected active projects; an existing
   `SOURCE_PROJECT_RELATION` MUST NOT be required for a source to enter this
   process.
2. Impact assessment MUST precede rewriting. It MAY identify candidate affected
   regions, but it MUST NOT publish changes or accept project state.
3. A conclusion of no impact MUST be supported by the declared dependency scope
   and required validation. An unverified generated conclusion MUST NOT silently
   restore a revision to current.
4. Full resynthesis MUST remain the safe fallback for literature reviews until
   a benchmark demonstrates that selective impact analysis has an acceptable
   false-negative rate.
5. Unchanged ingestion MUST be idempotent with respect to source content,
   project inputs, analysis schema, and analyser version. It MUST NOT create
   duplicate sources, assessments, notes, snapshots, or revisions.
6. No change signal MAY cause automatic publication or automatic acceptance of
   generated project knowledge.

## 8. Kernel, workflow, and integration boundaries

1. The grounding kernel MUST define semantic policy, not storage, scheduling,
   transport, or application-specific orchestration.
2. The kernel MUST NOT require Zotero, literature search, MCP, a vector database,
   Word, a scheduler, or another online service.
3. Task workflows MUST own composition. Every workflow run whose working
   language is Russian MUST compose grounding with the separate Russian
   scientific expression layer and MUST apply it to every natural-language
   text created during the run. This includes chat, progress and diagnostic
   messages, plans, intermediate drafts, final artifacts, headings, captions,
   labels, comments, and natural-language string values in machine-readable
   records; the obligation is not limited to final or explicitly user-facing
   prose. Exact source titles, quotations, schema keys, stable identifiers,
   hashes, paths, commands, and code MAY remain exact, but they do not exempt
   surrounding prose from the expression layer and MUST NOT be exposed in a
   reader-facing artifact unless required by the task or requested by the user.
   The expression step MUST preserve claims, modality, numbers, units,
   terminology, locators, uncertainty, causal force, and scope.
4. Literature acquisition and search MUST remain an external workflow and be
   selected by benchmark rather than embedded in the kernel.
5. Accepted state changes and publication transitions MUST be traceable and
   atomic at the authority boundary. Partial failure MUST NOT silently advance
   authoritative state or erase the last valid version.

## 9. Typed relations and compatibility

1. Version 1 MUST NOT persist a generic `RELATION` entity. Relations MUST remain
   with the domain object that defines their semantics, such as
   `SOURCE_PROJECT_RELATION`, `PROJECT_STATE_ITEM.basis`,
   `PROJECT_STATE_ITEM.supersedes`, `IDEA.origin`, and
   `ARTIFACT_REVISION.dependencies`.
2. A shared `EntityRef` or similar reference value MAY be used, but it MUST NOT
   become a duplicate relation store.
3. Current project, evidence, Zotero annotation, and living-review schemas remain
   operational compatibility implementations. This package clarifies their
   meaning but neither invalidates their stored records nor changes their
   validators.
4. Current project-context hashes and relevance target identifiers MUST NOT be
   treated as complete `project_state_dependencies` until a versioned migration
   supplies sufficient dependency pinning.
5. Future migration MUST be explicit, versioned, reversible where practical,
   and regression-tested against the existing fixed corpus and experiments.

## Relationship to earlier documents

- [`../possible-project-workspace-architecture.md`](../possible-project-workspace-architecture.md)
  is superseded as decision authority. It remains a historical design memo.
- Root-level `CODEX_ARCHITECTURE_HANDOFF.md`, when present as local design input,
  is superseded as decision authority and is not required by a repository checkout.
- [`../handoff.md`](../handoff.md) is clarified: it remains a descriptive project
  handoff, while this package governs architectural changes.
- [`../project-literature-architecture.md`](../project-literature-architecture.md)
  is clarified for shared entity semantics, acceptance, dependencies, and
  freshness. Its current offline workflow and full-resynthesis behaviour remain
  operational until explicitly migrated.
- [`../research-notebook-architecture.md`](../research-notebook-architecture.md)
  remains the specialized notebook design, constrained by these invariants.
- Current skill reference contracts, including the project manifest, evidence,
  Zotero annotation, and living-review contracts, are clarified but not changed.
  Their existing fields are compatibility projections until a versioned
  migration is implemented.
