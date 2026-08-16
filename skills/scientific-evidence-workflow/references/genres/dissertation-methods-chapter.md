# Genre: dissertation methods chapter

`mode: manuscript` · `genre: dissertation-methods-chapter` · protocol/data record required

## Authority boundary

GOST R 7.0.11-2011 requires the main text to be divided into chapters and
paragraphs or sections and subsections. It does not require a separately named
methods chapter and does not prescribe the chapter structure below. Treat this
genre as a reproducible writing convention. Applicable organization, ethics,
safety, device, and specialty requirements remain higher-priority inputs when
the user supplies their normative cards.

Observed defended dissertations show several valid arrangements: methods may
occupy one chapter, recur inside result chapters, or form a chain from model
construction through verification and error analysis. These are practice
variants, never requirements.

## Purpose

Describe what was actually studied or constructed, under which conditions,
with which equipment, procedure, transformations, and quality controls, so
that a competent reader can understand and, where the supplied records permit,
reproduce the work. Do not reconstruct a procedure from its final result.

## Input

Require at least one frozen `protocol` or `data` source and the corresponding
verified evidence records. Also use, when applicable:

- `experiment-description` and `procedure-record` artifacts;
- equipment, software, calibration, sampling, inclusion/exclusion, and version
  records;
- approved research results used only to select or verify a method;
- organizational or normative cards for ethics, safety, registration, or
  reporting obligations;
- the dissertation outline and stable chapter/section identifiers.

If a sequence, parameter, sample, device version, exclusion rule, statistical
method, or quality control is absent from the supplied records, stop on that
item. Never infer it from a graph, result table, or customary practice.

## Canonical control sections

Use these `output_section` keys in the claim ledger. Reader-facing headings may
be merged or renamed while the control sections remain addressable.

| Function | Key |
|---|---|
| object, inputs, and conditions | `method_scope` |
| ordered experiment, measurement, model, or algorithm | `procedure` |
| transformations and analysis | `data_processing` |
| calibration, uncertainty, controls, and reproducibility | `quality_control` |
| methodological conclusions and handoff to results | `chapter_conclusions` |

Equipment/materials, ethics/safety, and method-selection rationale are
conditional subsections. Include them when the supplied records establish
their content; do not fill them with generic prose.

## Procedure

1. Freeze names, versions, units, sample definitions, and stable structure IDs.
2. Separate the object and boundary conditions from actions performed on it.
3. Describe the procedure in executable order. For each step name its input,
   operation, parameter or decision rule, output, and exception when recorded.
4. Identify equipment and software precisely enough to distinguish the used
   configuration. Do not invent manufacturer, model, version, calibration, or
   access date.
5. Define every symbol at first use and preserve the recorded unit system.
6. Describe data exclusion, preprocessing, transformation, and statistical or
   computational analysis before reporting their outcomes.
7. State calibration, reference methods, controls, uncertainty sources, and
   repeatability or reproducibility checks only when they have records.
8. Keep method-verification results beside the decision they authorize and link
   them to `result_id`; move substantive research findings to the results
   chapter.
9. End with conclusions about the constructed or selected method and an
   explicit handoff to the result sections, not with new empirical findings.

## Scientific-formulation controls

- Replace “standard method”, “known procedure”, and “conventional processing”
  with an identified record or mark the item unsupported.
- Distinguish what was selected, designed, implemented, measured, calculated,
  and verified; these verbs are not interchangeable.
- Do not use a result verb such as “established” or “proved” for an unexecuted
  procedural step.
- Keep accuracy, error, uncertainty, repeatability, and reproducibility as
  different concepts unless the supplied method defines them otherwise.
- Record every semantic wording correction in the revision ledger before
  applying it.

## Gates

- At least one `protocol` or `data` source is in `task.input_scope`.
- The structure ledger contains a chapter and a nested section.
- Every claim resolves to an addressable output unit.
- All five control sections occur in the claim ledger.
- Every material method claim cites verified evidence or an approved result.
- Every number, unit, threshold, sample size, model version, and analysis choice
  has a source locator or result record.
- A result used in this chapter only selects, calibrates, or verifies a method;
  it does not replace the results chapter.
- Conditional ethics, safety, and organizational claims have their own cards.
- The chapter conclusion introduces no procedure or empirical result absent
  from the body of the chapter.

Apply `references/russian/genre-dissertation.md` and
`references/russian/genre-experiment.md` after the evidence gate. Run the
language auditor with both `--profile genre-dissertation` and
`--profile genre-experiment`: the first controls qualification-work claims, the
second catches planned procedures, unrecorded controls, versionless inputs, and
generalization from one run.

Use `assets/dissertation-methods-chapter.template.md` for a file artifact.
