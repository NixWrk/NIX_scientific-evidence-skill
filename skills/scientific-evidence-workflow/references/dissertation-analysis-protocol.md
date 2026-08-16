---
protocol_id: PSAD-2.2.12
version: 0.1.0
status: preliminary
effective_date: 2026-08-16
scope: Russian candidate dissertations and synopses used as evidence of writing practice
---

# Preliminary standard for dissertation analysis

This protocol fixes the method used to analyse defended dissertations before
their recurring textual patterns enter skill memory. It is a preliminary
standard: later corpus evidence may change the observation vocabulary,
thresholds, or comparison axes. A defended work is evidence of accepted
practice in one case, never a normative requirement.

## Authority boundary

Keep three layers separate:

1. normative requirements, supported by a versioned normative card;
2. recurring practice, supported by work cards and exact locators;
3. an individual author's wording or error, retained as a local observation.

Never turn frequency into obligation. Never repair a source silently while
recording it. The protocol governs analysis; it does not prescribe what a
dissertation must say.

## Required inputs

- the immutable source file, its content hash, size, format, and local address;
- bibliographic identity of the work and document type;
- author, year, specialty, supervisor, council when established;
- the applicable normative cards;
- an empty work card and reading log using the current schemas.

If the source version, document identity, or page/paragraph address system is
uncertain, stop before comparative conclusions.

## Pass 0: freeze and map the source

1. Verify the source hash against the work card.
2. Record the actual page count or, for a Word source without stable pages, the
   paragraph count and extraction method.
3. Extract the table of contents exactly as printed: order, numbering, titles,
   and page numbers. Record apparent numbering errors without correcting them.
4. Mark title matter, introduction, every chapter and subsection, conclusions,
   bibliography, lists, and appendices.
5. Record unavailable layers such as images, embedded equations, or absent OCR.

The table of contents is both an object of analysis and the address map for the
continuous read. A final generated Word table of contents must later come from
heading styles and updated fields; page numbers are not guessed from this map.

## Pass A: deterministic measurements

Measure only surfaces that code can identify reproducibly, for example:

- heading sequence and depth;
- page or paragraph distribution by section;
- formula, table, figure, citation, and list markers;
- recurring exact strings and section-opening formulas;
- declared quantities such as pages, figures, tables, formulas, and sources.

Save the measurement record separately from interpretive observations. A
counter result is a lead for reading, not a textual pattern by itself.

## Pass B: continuous reading

Read every page or paragraph in order. Work in bounded chunks and append the
log after each chunk. Give every observation one stable locator and classify
its role: section opening or closure, transition, argument move, own/other
boundary, support, qualification, number, term, formula glossary, illustration,
or an unnamed phenomenon proposed for review.

For a partially read work:

- report the exact completed range;
- retain positive observations from that range;
- make no whole-work absence claim;
- never count the work as complete in a cross-work denominator.

## Observation contract

The journal file name contains the work identifier. Each JSONL record contains
the locator, section, observation kind, concise finding, and, when wording is
the evidence, a short exact quote. An unnamed observation also contains
`proposed_name`.

Keep subject matter separate from textual form. Repetition of one anatomical
object, device, or experimental condition is not a writing pattern. Several
adjacent slices of one table, bibliography, or argument are one event unless
they perform independently repeated textual functions.

## Promotion review

Three independent locators are the threshold for semantic review, not automatic
promotion. Add a proposed name to settled memory only when all conditions hold:

1. the locators are independent textual events;
2. the name describes a transferable writing or argument function;
3. the definition can be stated without the source's subject-specific nouns;
4. the observations remain in the log as evidence of the promotion;
5. a human-readable definition and exact locators enter pattern memory.

One locator is an event. Two are a coincidence. Three make a review candidate.

## Cross-work comparison

Aggregate by author first, then compare supervisor, council, year, and document
type as possible explanatory axes. Record common patterns only at the current
declared author threshold. Below it, retain named variants and the works that
show them. Do not use multiple documents by one author as multiple independent
authors.

Every matrix cell must resolve to work-level evidence. An empty cell means
`not assessed` unless the work was read completely and the searched unit was
explicitly covered.

## Scientific-formulation corrections

When analysis or later drafting reveals an inaccurate scientific formulation,
keep both forms in a revision record:

- exact original wording;
- proposed corrected wording;
- correction category;
- reason for the change;
- claim, evidence, result, or structure identifiers that authorize it;
- decision: proposed, accepted, or rejected.

Semantic corrections include scientific precision, evidence boundary,
terminology, and logic. They require evidence or an approved result. Grammar
and layout corrections may be evidence-neutral but must not change the claim,
number, unit, population, comparison, uncertainty, or causal strength. Source
quotes in reading logs are never rewritten.

## Required outputs

A completed analysis produces:

1. a source and coverage record;
2. a Pass A measurement file when the format permits deterministic measures;
3. a complete or explicitly partial Pass B JSONL log;
4. a validated work card;
5. reviewed promotions in work-pattern memory;
6. cross-work aggregate and author/supervisor matrix updates;
7. a revision ledger when scientific wording was corrected;
8. validator and test results.

## Known limits of version 0.1

The validator counts proposed-name locators but cannot determine whether they
are semantically independent or transferable; that decision remains a recorded
human review. Completeness and partial status currently live in coverage
records rather than a separate run manifest. Aggregate thresholds below five
authors produce a warning, not a hard failure. Normative-reference resolution
and `expected_arc` completeness still require manual review. These limits are
revision candidates, not permission to omit the checks.

## Versioning and revision

Use semantic versions for this protocol. Increment:

- patch for clarification that changes no decision;
- minor for a new observation field, comparison axis, or promotion rule;
- major when existing records would be interpreted differently.

Every revision must name the corpus evidence or failure that motivated it,
state whether older logs require migration, update validators and tests when
the machine contract changes, and preserve prior versions in Git history. The
working queue in `docs/pass-b.md` may change without changing this protocol;
the protocol changes only when the method changes.
