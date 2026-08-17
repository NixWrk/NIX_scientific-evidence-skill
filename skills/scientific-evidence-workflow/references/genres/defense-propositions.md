# Genre: propositions submitted for defence

`mode: manuscript` · `genre: defense-propositions` · approved result anchors required

## Authority boundary

GOST R 7.0.11-2011 includes propositions submitted for defence among the
normative elements of the introduction. It does not prescribe the wording,
number, separate heading, or standalone document structure used below. The
controlled invariants are that every proposition is a numbered falsifiable
assertion, not a topic, and resolves to both an approved result and the section
that establishes it.

## Purpose

Formulate the scientific assertions the dissertation author is prepared to
defend. A proposition states what is asserted under identified conditions; it
does not merely name a subject, repeat the aim, list an activity, or promise a
result.

## Input

Require approved result records, stable section identifiers, the task ledger,
and the locked terminology map. Literature and organizational records cannot
support a proposition. Stop when a proposed assertion has no result or section
anchor, no falsifiable predicate, or an unresolved applicability boundary.

## Canonical control sections

| Function | `output_section` |
|---|---|
| numbered assertion | `proposition_statement` |
| object, conditions, and applicability | `proposition_boundary` |
| approved result support | `proposition_result_anchor` |
| establishing dissertation section | `proposition_section_anchor` |

These functions may be represented in a compact numbered paragraph while
remaining separate ledger fields.

## Operations

### Generate

Select only results central to the dissertation's scientific contribution.
Transform each into one bounded, falsifiable assertion without changing its
meaning, then attach its result and structure anchors. Remove topics, methods
without outcomes, generic significance claims, and duplicate conclusions.

### Critic

Test whether each item could be contradicted by admissible evidence and whether
its predicate, object, conditions, result, and section anchors are explicit.
Flag topics, activities, compounds of unrelated claims, unsupported strength,
and broken anchors. Use comments for scientific reformulation; tracked changes
are allowed only for an exact, evidence-neutral local correction.

## Procedure

1. Freeze approved results, terminology, and dissertation structure.
2. Select a defensible result and state one testable relation, property, method
   capability, or regularity it establishes.
3. Preserve the object, regime, comparison basis, metric, and boundary.
4. Link the assertion to `result_id`, `structure_id`, and, where applicable,
   `task_id`.
5. Split propositions containing independent predicates; merge only genuine
   duplicates supported by the same result chain.
6. Number the final assertions without implying that numbering is a prescribed
   standalone layout.

## Scientific-formulation controls

- Reject “разработка метода”, “исследование зависимости”, and similar topic
  phrases unless they contain an asserted, falsifiable outcome.
- Do not use “доказано”, “обеспечивает”, “повышает”, or causal language beyond
  the approved result and its design.
- Do not copy a conclusion verbatim when that copy fails to express a distinct
  defensible assertion.
- Keep each proposition atomic enough to test and challenge.
- Record every semantic correction in the revision ledger.

## Gates and stop conditions

- Every item is numbered and grammatically an assertion.
- Every item is falsifiable within its stated object and conditions.
- Every item cites one or more approved results and an existing dissertation
  section; literature is not used as support.
- Terms match the topic, aim, tasks, and conclusion ledgers.
- All four control functions occur for every proposition.
- Stop rather than invent an anchor, predicate, boundary, or scientific result.

Apply `references/russian/genre-dissertation.md` after the evidence gate and run
the language auditor with `--profile genre-dissertation`. Use
`assets/defense-propositions.template.md` for a file artifact.
