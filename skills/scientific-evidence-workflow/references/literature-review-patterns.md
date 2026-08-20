# Literature-review synthesis patterns

Use this reference with `literature-review-workflow.md`. It turns a verified
evidence set into reader-facing review prose. It is not a catalogue of exemplar
texts and must not be used to imitate the wording or content of a publication.

## Select the synthesis profile before drafting

Choose the closest profile from the review question, source types, and real
provenance. Record the profile in working data; do not print its key as a
reader-facing heading.

| Profile key | Use when | Default analytical movement |
|---|---|---|
| `protocol_quantitative` | A documented systematic search supports comparison or quantitative aggregation | question -> methods -> comparable results -> heterogeneity and bias -> bounded inference |
| `protocol_thematic` | A documented systematic search supports categorical or qualitative synthesis | question -> methods -> analytical categories -> convergence and disagreement -> gaps |
| `conceptual_thematic` | The review compares definitions, theories, interpretations, or schools without claiming systematic coverage | scope and terms -> approaches -> relations and tensions -> unresolved questions |
| `mechanism_application` | The review explains a technology, material, process, condition, or intervention through mechanisms and uses | definition and classification -> properties or mechanisms -> applications or management -> constraints and risks |

Do not select either `protocol_*` profile merely because a source or requested
title uses the word *systematic*. Search, screening, eligibility, extraction,
and corpus provenance must exist. If no profile fits exactly, name the nearest
profile in working data and state the deviations; do not invent a fifth label
to hide a mixed design.

## Build a profile-aware source card

Every source card has a common core:

- source and locator IDs;
- source question or purpose;
- object and context;
- source or study design;
- findings or contribution relevant to the review question;
- limitations stated by the source and limitations found during extraction;
- scope of applicability;
- positive, null, contrary, and missing results kept separately.

Add only the fields needed by the selected profile:

- `protocol_quantitative`: population or material, exposure or intervention,
  comparator, outcome, unit, denominator, time point, effect estimate,
  uncertainty, and risk-of-bias facts;
- `protocol_thematic`: analytical category, setting, operational definition,
  method, observed pattern, rival account, and transfer conditions;
- `conceptual_thematic`: term, definition, theoretical frame, adjacent or
  opposed concepts, domain of validity, and unresolved tension;
- `mechanism_application`: class or subtype, composition or inputs, property or
  process, proposed mechanism, application, performance condition, failure
  mode, constraint, and risk.

Use `not_applicable` rather than forcing a biomedical field such as sample or
population onto conceptual and technical sources. Missing data remain
`not_reported`; they are never reconstructed.

## Compare before writing

1. Convert the review question into two to seven analytical dimensions. These
   dimensions, not the order of sources, become the body structure.
2. Assign each relevant source-card field to a dimension.
3. For every comparison, record one status: `direct`, `qualified`,
   `contextual`, or `not_comparable`.
4. For `qualified`, `contextual`, and `not_comparable`, record the reason:
   design, definition, population or material, condition, metric, unit, time
   point, or missing information.
5. Deduplicate reports of the same underlying study before counting support.
6. Within every dimension, retain convergence, divergence, null results,
   internal contradictions, and unstudied cells. Silence is not convergence.
7. Create a synthesis claim only after its supporting and constraining rows are
   visible together.

A relation table is optional. Use one only when relations are the substance of
the question: quantitative comparability for an aggregation, or concept
alignment for a conceptual review. Do not manufacture a universal relation
record or persist a relation merely because two sources mention the same term.

## Draft analytical paragraphs

An ordinary synthesis paragraph follows this movement:

1. **Analytical claim.** State the pattern, distinction, or unresolved issue
   that the paragraph will establish.
2. **Comparative evidence.** Bring together the relevant independent sources,
   designs, conditions, and locators.
3. **Boundary or contrast.** Explain a null result, disagreement,
   non-comparability, limitation, or condition that changes the pattern.
4. **Bounded transition.** State what follows for the next analytical
   dimension without adding a new factual claim.

The sequence is a reasoning pattern, not a four-sentence quota. A paragraph may
focus on one source only when that source supplies a unique definition,
method, or counterexample; mark that role explicitly. Avoid serial paragraphs
whose only organizing principle is "Source A says..., Source B says...".

## Realize each profile as a coherent review

### `protocol_quantitative`

Use an explicit methods section. Preserve the chain from eligibility and
selection through extraction to effect estimates, heterogeneity, risk of bias,
and applicability. Results report what the corpus contains; discussion
interprets why patterns differ. Do not convert association into causation or a
non-significant estimate into evidence of no effect.

### `protocol_thematic`

Use an explicit methods and corpus section, followed by analytical categories.
Within each category compare operational definitions, contexts, and methods.
End the body with cross-category tensions and genuine gaps rather than a list
of sources that were not found.

### `conceptual_thematic`

Open by fixing scope and working definitions. Organize the body by approaches,
conceptual relations, or disagreements. Distinguish an author's proposal from
an empirical result and a reviewer's synthesis from both. Do not claim
completeness without protocol provenance.

### `mechanism_application`

Move from classification to properties or mechanisms and then to applications,
management, or intervention. Keep mechanism, measured performance, practical
use, and recommendation as separate claim types. Report failure modes,
constraints, and risks beside benefits rather than in a decorative final list.

## Shape the conclusion from the synthesis

The conclusion contains no new source, datum, mechanism, or recommendation.
It answers the review question at the same certainty as the body and then names
the main boundary.

- `protocol_quantitative`: strongest supported estimate or direction, degree
  of consistency, principal bias or heterogeneity, and the population or
  conditions to which the result applies;
- `protocol_thematic`: stable categories, important disagreement, missing
  evidence, and implications limited to the searched corpus;
- `conceptual_thematic`: clarified definitions or relations, remaining
  tension, and the boundary of the proposed synthesis;
- `mechanism_application`: established properties or mechanisms, supported
  applications, failure modes or risks, and conditions for practical use.

A practical recommendation is permitted only when the ledger contains direct
support for the recommendation, the target and conditions are explicit, and
contrary evidence is carried into the sentence. Otherwise state an implication
or an evidence gap, not an instruction.

## Reader-facing structure gate

Headings must follow the selected profile and subject matter. Do not expose
working labels such as "claim ledger", "convergence", or "profile" as mandatory
chapters. The ledger and comparison matrix are verification artifacts; append
them only when the user or delivery contract requests them.

Before delivery, verify:

- the introduction defines the question and boundary;
- a methods section appears when, and only when, corpus provenance supports it;
- body sections are analytical dimensions rather than source names;
- each central paragraph contains comparison or an explicit unique-source role;
- null, contrary, and non-comparable evidence has not disappeared;
- causal and practical language does not outrun the designs;
- the conclusion answers the question without introducing new evidence.
