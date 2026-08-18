# Research Domain Model

## Normative status

This document is normative for the shared entity vocabulary, identity
boundaries, and relationships used by future architectural changes. It is a
semantic model, not a JSON schema, storage design, or migration specification.
Field names and example values are illustrative unless an existing versioned
contract already defines them.

Read the normative package in this order:

1. [`product-boundary.md`](product-boundary.md) defines product scope and
   non-goals;
2. this document defines domain meaning and relationships;
3. [`invariants.md`](invariants.md) defines mandatory behaviour.

Scoped precedence is unchanged across the package: `product-boundary.md`
governs scope, `invariants.md` governs mandatory semantic behaviour, and this
document governs entity meaning subject to both. Existing contracts and
validators remain authoritative for their current serialized formats until an
explicit versioned migration. A difference between this model and a current
format is a compatibility mapping, not an implicit format change.

## 1. Minimal version 1 model

The accepted minimum model is:

```text
WORKSPACE

PROJECT
└── PROJECT_STATE_ITEM

SOURCE
└── SOURCE_VERSION

SOURCE_PROJECT_RELATION

IDEA

ARTIFACT
└── ARTIFACT_REVISION
```

Version 1 has no persisted generic `RELATION` entity. Typed relationships stay
with the object that gives them meaning. Shared reference shapes such as an
`EntityRef` are value objects, not a graph store.

The model does not require a database, global event log, universal project
snapshot, or new operational schema.

## 2. Entities

### `WORKSPACE`

`WORKSPACE` is the thin authority and routing boundary for multiple projects,
shared sources, ideas, and derived artifacts. It provides stable identity,
selection, ownership, and access scope. It is not a mandatory central database,
an autonomous memory system, a scheduler, or a dump of every project record.

Workspace-scoped source identity allows one logical source to be reused without
copying its intrinsic analysis into each project. All project-relative meaning
remains explicitly project-scoped.

### `PROJECT`

`PROJECT` is a long-lived context root for work such as a dissertation, an
article, an experiment, a report, or a smaller research task. It owns stable
identity and the relatively stable problem statement: title, kind, purpose,
scope, questions, objectives, constraints, terminology, and applicable method
context.

A project context hash may identify a defined context projection. It does not
by itself identify all accepted project knowledge or all dependencies of a
project-relative assessment.

### `PROJECT_STATE_ITEM`

`PROJECT_STATE_ITEM` is the atomic unit of project knowledge and decision state.
Typical types include, without freezing a closed enumeration:

- definition;
- proposition;
- hypothesis;
- assumption;
- decision;
- result;
- limitation;
- open question.

One entity is used with a type discriminator; version 1 does not create a
separate top-level schema for every type. The record preserves stable identity,
project identity, type, content, scope, basis, provenance, and optional typed
assessments or successor links.

The model keeps these questions separate:

| Question | Representation |
|---|---|
| What is this item? | `entity_type` or equivalent typed discriminator |
| Has the project adopted it? | Projection of authorized `AcceptanceDecision` records |
| What do its current grounds indicate? | A typed evidence assessment, when applicable |
| What checking was performed? | One or more typed `VerificationRecord` records |
| Has another accepted item replaced it? | An accepted successor's `supersedes` link |

A bare generic `status` is not part of the future domain model. Not every item
requires every axis. `not_assessed` is distinct from `unsupported`.

`contested` is not a universal state. Conflicting evidence is represented by an
evidence assessment; changed inputs require reassessment; disagreement about
adoption requires a competing proposal or a review decision.

`superseded` is not an acceptance value. A new item points to the item it
supersedes. Until the successor is accepted, the predecessor remains current.
The current canonical project-state projection contains accepted items for
which no accepted successor applies. Historical content and decisions remain
available.

An accepted item's exact content must be identifiable by the acceptance
decision. Changing accepted meaning creates a successor rather than rewriting
history. A result item should normally refer to the data, analysis run, or
`ARTIFACT_REVISION` that carries its reproducible detail instead of duplicating
all result data in project state.

### `SOURCE`

`SOURCE` is the internal logical identity of a source. Its identity is
independent of Zotero, a DOI registry, a local path, PubMed, GitHub, or any other
provider. Provider identifiers are external references with provenance.

Two external records may resolve to one `SOURCE` only after identity resolution.
Equal Zotero item keys in different libraries do not establish either identity
or collision because the library scope is part of the external reference.

### `SOURCE_VERSION`

In version 1, `SOURCE_VERSION` is a technical identity for the exact immutable
content or representation that was analysed. It does not assert that PDF, HTML,
a preprint, and a version of record are bibliographic versions of one work.

The record must make the analysed representation reproducible by retaining:

- a content identity or hash;
- its `SOURCE` identity;
- acquisition provenance and external reference;
- representation information;
- material extraction, OCR, or normalization provenance;
- the time or observation context needed by the acquisition contract.

Analysis schema and analyser versions are processing dependencies, not part of
source content identity. A later model may separate scholarly work,
publication version, and representation after real workflows demonstrate the
need.

### `SOURCE_PROJECT_RELATION`

`SOURCE_PROJECT_RELATION` is a specialized, reproducible project-relative
assessment, not a generic graph edge and not source-intrinsic metadata. It
records why an exact source representation may matter to a project, for which
questions or state items, within what scope, and on what basis.

Each recorded assessment must pin sufficient inputs:

- internal `SOURCE` identity and exact `SOURCE_VERSION`;
- `PROJECT` identity and the applicable project-context reference or hash;
- `project_state_dependencies` for the questions, definitions, hypotheses,
  assumptions, decisions, results, limitations, or other state actually used;
- or an immutable project-state snapshot reference that captures the same
  dependency closure;
- evidence locators, assessment provenance, and the relevant analysis method or
  version when applicable.

The dependency set must be sufficient to reproduce why the judgement was made.
A context hash alone is insufficient when the assessment used state that the
hash does not cover. A workflow must not require a complete project snapshot
when explicit dependencies are sufficient.

An assessment is historical once recorded. If a source version, context, or
state dependency changes, the old assessment is retained and a reassessment is
created or explicitly supersedes it. Candidate relevance may be reviewed or
dismissed, but even confirmed relevance is not evidence and does not create an
accepted `PROJECT_STATE_ITEM` automatically.

### `IDEA`

`IDEA` is a non-canonical proposal inbox for a possible research question,
method transfer, connection, interpretation, or other direction. It preserves
content, origin, related projects or sources, basis, and review provenance.

Reviewing or retaining an idea does not make it accepted project knowledge.
Promotion creates a separate proposed `PROJECT_STATE_ITEM`; acceptance requires
its own authorized decision. Cross-project discovery therefore cannot silently
modify the target project.

### `ARTIFACT`

`ARTIFACT` is the logical, long-lived identity and purpose of an output such as
an annotation, source card, literature review, report, article, chapter,
research script, notebook, or dissertation artifact. The artifact identity is
not the identity of one generated file or text snapshot.

A source card may initially be an artifact kind. This avoids a premature
`SOURCE_CARD` entity while retaining the option to separate it if a real pilot
demonstrates incompatible semantics.

### `ARTIFACT_REVISION`

`ARTIFACT_REVISION` is an immutable concrete output. It records exact content
identity or reference, production provenance, and pinned dependencies such as:

- `SOURCE_VERSION` references;
- `PROJECT_STATE_ITEM` content or revision references;
- project-context references or hashes;
- upstream `ARTIFACT_REVISION` references;
- an immutable corpus or input snapshot where set membership matters;
- producer, contract, and analysis versions when applicable.

Changing content or original dependencies creates a new revision. Verification,
freshness, publication, and historical correctness are separate questions.
Current freshness is not stored as intrinsic content of the revision.

## 3. Supporting records and projections

These records support the entities but do not require separate top-level stores
or a particular serialization design.

### External and internal references

`ExternalRef` identifies a provider-scoped external object. A Zotero reference
must include at least the system, library identity or equivalent scope, and item
key. `EntityRef`, `BasisRef`, and `DependencyRef` may share a technical reference
shape while preserving their domain-specific roles.

### `AcceptanceDecision`

Acceptance is sourced from a traceable, append-only, explicitly authorized
decision tied to the exact item content or revision considered. A decision
preserves actor, action, time, authorization or decision reference, and
provenance. A model-generated proposal cannot issue an authoritative decision.

`acceptance.state` may be materialized for efficient reading, but it is only the
deterministic current projection of applicable decisions. Decision ordering,
revocation, and concurrency semantics remain an implementation decision that
must preserve this invariant.

### Evidence assessment and verification

An evidence assessment records what declared grounds currently indicate about
an item and which basis was assessed. Verification records what check was
performed, with what method, outcome, report, and provenance. Neither is the
same as project acceptance.

The fact that an item belongs to project state gives it no evidential force.
A traceable and verified project result may support a claim; a goal, hypothesis,
convention, or methodological decision has only the evidential role justified
by its type and basis.

### `FreshnessAssessment`

Freshness is a separate, traceable, append-only assessment of an immutable
`ARTIFACT_REVISION` relative to a declared dependency state. It records the
target revision, trigger, dependency state considered, conclusion, time, and
provenance.

A materialized current freshness value is only a projection. A new source or
changed project dependency can produce a `needs_review` assessment without
mutating the revision or making it retroactively incorrect. A new output is a
new `ARTIFACT_REVISION`.

### `InputSnapshot`

An immutable input or project-state snapshot may be used where exact set
membership is necessary for reproducibility. It is a workflow-owned supporting
record, not a mandatory universal entity. Explicit dependency references remain
preferred when they are sufficient and more precise.

## 4. Typed relationships

Version 1 persists no generic `RELATION`. Required relationships remain where
their semantics are enforceable:

```text
SOURCE_PROJECT_RELATION
IDEA.origin and IDEA.related_projects
PROJECT_STATE_ITEM.basis and PROJECT_STATE_ITEM.supersedes
ARTIFACT_REVISION dependencies
```

A common reference value must not become a second store for the same
relationship. A generic relation model may be reconsidered only after several
real workflows reveal repeated semantics that cannot be enforced cleanly by
the typed relationships.

## 5. Compatibility projections

This model introduces no schema or data migration. Existing records continue to
mean what their current contracts and validators say. The following mappings
guide future changes:

| Current operational field or record | Compatibility interpretation |
|---|---|
| Project manifest and `project_id` | Current projection of `PROJECT` identity and routing context |
| `context_hash` / `project_context_hash` | Hash of the context projection defined by the current contract; not a full project-state identity and not sufficient alone for every project-relative assessment |
| Evidence or Zotero source record | Current operational projection toward `SOURCE` plus analysed content identity; no automatic global deduplication is implied |
| `source_content_hash` | Current content-identity projection toward `SOURCE_VERSION`; acquisition and transformation provenance remain limited to the current contract |
| `zotero_item_key` | Provider-local compatibility identifier; a future canonical external reference also requires library scope |
| Project annotation record | Current combined projection of source analysis, project-relative assessment, and derived note output; the current validator remains authoritative. Existing `project_context_hash` and relevance target fields do not constitute complete `project_state_dependencies` until a versioned migration adds sufficient dependency pinning. |
| Project manifest artifact record | Current logical artifact projection; it does not yet supply the full `ARTIFACT_REVISION` history defined here |
| Living-review `current_artifact.status` | Operational workflow projection combining review state; it is not a universal freshness, verification, correctness, or publication axis |
| Other bare `status` fields | Local compatibility fields whose meanings remain contract-specific; they are not the future domain status model |

No consumer may reinterpret these fields destructively before a versioned
migration and regression tests exist.

## 6. Explicitly deferred decisions

The following remain open and must not be inferred from this model:

- physical storage, transaction, and indexing technology;
- exact serialized field names and enumerations;
- whether explicit dependencies or project-state snapshots dominate at scale;
- bibliographic identity across preprints, accepted manuscripts, versions of
  record, and representations;
- global versus project-local terminology authority;
- the authorization interface and conflict rules for acceptance decisions;
- scheduler, synchronization, locking, and distributed recovery design;
- whether a source card ultimately needs a specialized entity;
- whether selective impact analysis is safe enough to replace full
  resynthesis;
- whether repeated typed relationships later justify a generic relation model.

These questions require a real vertical pilot or benchmark, not another
speculative schema.

## 7. Relationship to earlier documents and contracts

| Existing document or contract | Normative relationship |
|---|---|
| [`../possible-project-workspace-architecture.md`](../possible-project-workspace-architecture.md) | Superseded as decision authority. It remains a historical non-normative design memo. Its alternative storage and orchestration options are not adopted requirements. |
| Root-level `CODEX_ARCHITECTURE_HANDOFF.md`, when present as local design input | Superseded as decision authority by this package. It remains intermediate discovery material and is not required by a repository checkout. |
| [`../handoff.md`](../handoff.md) | Clarified as descriptive implementation status and priorities. It does not override this domain model. |
| [`../project-literature-architecture.md`](../project-literature-architecture.md) | Clarified for shared source identity, project state, assessments, acceptance, artifact revisions, and freshness. Its existing offline workflow and full-resynthesis contract remain operational until migration. |
| [`../research-notebook-architecture.md`](../research-notebook-architecture.md) | Remains the specialized notebook design; its artifacts and results must respect this model when migrated. |
| Project manifest, evidence, Zotero annotation, and living-review reference contracts | Clarified but not changed. Their fields and validators remain current compatibility implementations. |
