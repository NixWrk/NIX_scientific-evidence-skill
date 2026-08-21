# Genre: dissertation literature-review chapter

`mode: manuscript` · `genre: dissertation-literature-review-chapter` · literature evidence required

## Authority boundary

GOST R 7.0.11-2011 requires a structured main text and a reference list, but it
does not prescribe a separately named literature-review chapter or a universal
sequence of its themes. The controls below are evidence and synthesis rules,
not mandatory chapter names. Patterns observed in defended dissertations may
suggest candidate structures; they become neither norms nor evidence merely
because they recur.

## Purpose

Build a bounded synthesis of the supplied literature that establishes the
conceptual frame, separates convergence from disagreement, and states exactly
what remains unresolved within the reviewed corpus. The chapter must lead to
the research problem without pretending that absence from the corpus proves
absence from science.

## Operations

### Generate

Freeze the corpus and its provenance, build source and evidence ledgers, group
studies by the scientific question they answer, and draft only after the
comparison matrix is complete. Preserve contradictions, scope differences,
and limits of applicability. Every substantive sentence resolves to evidence
inside `task.input_scope`.

### Critic

Audit an existing chapter against the same frozen corpus. Return a findings
journal conforming to the dissertation critic schema. Classify unsupported
synthesis and overbroad gaps as evidence gaps; do not rewrite scientific
meaning automatically. Word comments are appropriate for missing evidence,
ambiguous boundaries, and alternative synthesis structures. Exact tracked
changes are allowed only for safe local corrections.

## Canonical control sections

| Function | `output_section` |
|---|---|
| corpus boundary and selection provenance | `review_scope` |
| definitions and comparison axes | `conceptual_framework` |
| thematic comparison across sources | `thematic_synthesis` |
| disagreement, bias, and applicability limits | `conflicts_and_limits` |
| bounded unresolved problem | `research_gap` |
| conclusions and handoff to dissertation tasks | `chapter_conclusions` |

Reader-facing headings may differ, but all six functions must remain
addressable in the claim and structure ledgers.

## Procedure

1. Freeze the corpus identifier, inclusion boundary, search provenance, and
   source versions. Do not call the review systematic without a reproducible
   search and selection record.
2. Create study cards and a comparison matrix before synthesis. Record object,
   method, sample or data boundary, principal result, uncertainty, and stated
   limitation only when the source supplies them.
3. Define terms and comparison axes before grouping studies. Do not group only
   by author or chronology when the scientific relationship is the point.
4. For each theme, state convergence, disagreement, incommensurability, and
   missing evidence separately. Explain whether differences can follow from
   method, population, material, regime, or measurement boundary.
5. Distinguish a source's claim from the dissertation author's synthesis.
   Synthesis needs evidence from every source named in the comparison.
6. Formulate a gap as bounded by the corpus, search date, objects, methods, and
   regimes actually reviewed. “Not found in this corpus” is not “does not
   exist”.
7. End with conclusions that answer the review questions and lead to approved
   dissertation tasks. Introduce no new source or empirical result there.

## Gates

- At least three literature sources are frozen in `task.input_scope`.
- The structure ledger contains a chapter and a nested section.
- Every supported or bounded non-structural claim cites verified evidence from
  the frozen input scope.
- Every `research_gap` claim is `bounded` and has an explicit `boundary`.
- Contradictory sources are retained and represented as conflict, not averaged
  into false consensus.
- Own empirical results and organizational records are not used as literature
  evidence in this chapter.
- Conclusions introduce neither new literature nor a stronger claim than the
  reviewed body supports.
- Every in-text reference resolves to one bibliographic record formatted under
  the selected GOST-permitted form.
- Publication titles match the source and are not translated or replaced by a
  Russian paraphrase.

Apply `references/literature-review-workflow.md`,
`references/bibliography-gost.md`, and
`references/russian/genre-dissertation.md` after the evidence gate. Preserve
publication titles in their source language and form; do not translate them in
the bibliography. Use
`assets/dissertation-literature-review-chapter.template.md` for the artifact.
