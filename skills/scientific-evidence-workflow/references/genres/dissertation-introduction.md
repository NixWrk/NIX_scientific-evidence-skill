# Genre: dissertation introduction

`mode: manuscript` · `genre: dissertation-introduction` · literature evidence required

## Purpose

Draft or revise the introduction of a Russian candidate dissertation from a
closed evidence bundle. The introduction states why the bounded problem is
scientifically relevant, what is already known, what this work aims to obtain,
and which supplied results and organizational records authorize its claims.

## Required normative elements

Cover all eight elements established by GOST R 7.0.11-2011:

1. relevance of the topic;
2. degree of development of the problem;
3. aim and tasks;
4. scientific novelty;
5. theoretical and practical significance;
6. methodology and methods;
7. propositions submitted for defence;
8. reliability and approbation.

Use these stable `output_section` keys in the claim ledger:

| Element | Key |
|---|---|
| relevance | `relevance` |
| degree of development | `state_of_art` |
| aim | `aim` |
| tasks | `tasks` |
| novelty | `novelty` |
| theoretical and practical significance | `significance` |
| methodology and methods | `methods` |
| propositions | `propositions` |
| reliability and approbation | `validity_and_approbation` |

Headings are working controls, not an asserted formatting requirement. Merge or
rename them only when a higher-priority supplied requirement calls for it, and
retain all eight elements. Personal contribution, implementation, publications,
specialty-passport compliance, and volume/structure are optional here unless a
supplied requirement or approved institutional practice requires them.

## Input

Require:

- the approved topic and one aim;
- a task ledger with stable identifiers;
- verified literature evidence for relevance and degree of development;
- approved result records for novelty, significance, and propositions;
- protocol or method records for the methodology and methods element;
- organizational records for approbation, implementation, and publications;
- the dissertation outline and stable structure identifiers.

If novelty, a proposition, or an organizational statement lacks its required
record, stop on that element instead of completing it from general knowledge.

## Procedure

1. Lock the topic terms and create a terminology map used by aim, tasks,
   novelty, propositions, and conclusions.
2. Build relevance as a bounded problem statement: object, unresolved relation,
   consequence, and the evidence that establishes each link.
3. Synthesize degree of development by approaches and unresolved questions,
   not as a sequence of author summaries.
4. State exactly one aim as the intended scientific result, not as a list of
   activities. Express tasks in parallel grammatical form and assign each a
   stable task identifier.
5. State novelty only against an explicit comparison corpus or prior capability.
   Preserve the boundary in the claim record.
6. Separate theoretical significance from practical significance. Do not infer
   implementation from potential usefulness.
7. Describe only supplied methodology and methods; do not reconstruct a
   protocol from the final result.
8. Write every proposition as a falsifiable assertion. Link it to an approved
   result and to the section that establishes it.
9. Report reliability through supplied design, controls, comparison, and
   reproducibility records; report approbation through organizational records.
10. Check the introduction against the outline and the task-result-conclusion
    traceability ledger.

## Scientific-formulation revisions

When revising supplied wording, create a revision record before applying a
change. Preserve the original, corrected wording, category, reason, decision,
and authorizing evidence/result/structure identifiers. Accepted semantic
changes require evidence or an approved result. Grammar and layout changes may
be evidence-neutral but may not alter scientific meaning.

Do not silently strengthen `may`, `is associated with`, or a bounded sample
result into causation or general validity. Do not silently repair quotations
from analysed dissertations; record their errors as observations.

## Gates

- Exactly one supported or bounded aim.
- Every task has a stable structure unit and an intended conclusion mapping.
- Every novelty claim is bounded and names the comparison boundary.
- Every proposition cites both an approved result and a proposition/section
  structure unit.
- Every number cites evidence or a frozen result.
- All eight normative elements are present in the claim ledger.
- Every accepted semantic correction is traceable in the revision ledger.
- The table of contents and the introduction use the same labels and terms.

For Russian output, apply `references/russian/genre-dissertation.md` after the
evidence gate and run the audit with `--profile genre-dissertation`.

Use `assets/dissertation-introduction.template.md` for a file artifact.
