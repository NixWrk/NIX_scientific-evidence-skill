# Genre: notebook narrative

`mode: record` · `genre: notebook-narrative` · data, protocol, or note source required

## Purpose

Create or criticise a research notebook as a small executable calculation
report. One notebook answers one main research question, or several dependent
subtasks that form one computational chain and support one bounded summary.

The genre controls the scientific narrative in Markdown cells and the relation
between code, observable output, and conclusion. It does not prescribe a fixed
set of headings and does not rewrite executable code for style.

Also load `references/reproducibility-contract.md` and, for Russian text,
`references/russian/genre-notebook.md`.

## Input

Require at least one supplied `data`, `protocol`, or `note` source. A generated
dataset is described by its generating protocol and parameters. Keep external
literature optional and distinguish it from the notebook's own outputs.

Fix the notebook file/version, its main question, scope, completion criterion,
inputs, expected outputs, and intended audience. If the notebook is already
executed, preserve the original cells and outputs during criticism.

## Minimal narrative arc

Cover these functions, using headings, labels, cell metadata, or another clear
arrangement appropriate to the notebook:

1. `notebook_scope`: question, included and excluded scope, completion criterion,
   inputs, and expected outputs;
2. `method_and_assumptions`: method, material parameters, assumptions, units,
   and interpretation criterion before the result;
3. `observed_outputs`: observable numbers, tables, figures, errors, and negative
   or inconclusive outcomes produced by the executed steps;
4. `interpretation_and_limits`: interpretation separated from observation,
   uncertainty, applicability boundary, unresolved problem, or attributed
   hypothesis;
5. `notebook_summary`: what was established, what was not established, retained
   artifacts, and a next action only when a decision was actually made.

Use the local arc `purpose/input → action/assumption → observable output →
interpretation/limit` for a logical calculation stage. Do not create four
headings around imports, display settings, or trivial helper cells.

## Empirical and mixed notebooks

When measured or observed data come from an experiment, the computational arc
does not replace the experimental account. Set
`scientific_report.study_type` to `empirical` or `mixed` and cover four tagged
functions:

1. `experiment-context`: stable experiment or study identifier, link to the
   supplied description or protocol, purpose and planned quantity, object or
   sample, conditions, recorded signals or variables, units, and channel roles;
2. `experiment-procedure`: intended method, what was actually performed,
   selection or exclusion steps, manual operations, and material deviations;
3. `experimental-observation`: what was actually obtained from the recorded
   data, with a source locator and without replacing the observation by a model
   interpretation;
4. `experimental-analysis`: analysis of those observations against the planned
   quantity, including uncertainty, failed steps, alternatives, and what the
   experiment did not establish.

Do not copy a long protocol into every notebook. Link to one versioned
experiment description and retain only the notebook-specific subset. If the
description, raw data, or result is absent, state that absence; do not silently
turn a planned calculation into a performed experiment or a saved legacy
output into a reproduced result.

Keep these states linguistically distinct: `planned`, `performed`, `observed`,
`interpreted`, and `not assessed`.

## Generate

1. Start from `assets/notebook-narrative.template.ipynb` or preserve the user's
   existing notebook structure.
2. Put reusable algorithms in modules when they are no longer part of the
   report's explanatory path.
3. Describe the method and assumptions before interpreting outputs.
4. Keep observations, interpretations, hypotheses, decisions, and limitations
   linguistically distinct.
5. Preserve negative and uncertain results. Attribute a new hypothesis and state
   how it could be checked; never convert it into the current conclusion.
6. Complete the reproducibility account and run the lint.

## Critic

Check the notebook against its declared question and this genre before applying
generic preferences. Report:

- a missing or drifting question, scope, or completion criterion;
- a conclusion without an observable output;
- a number without unit/dimensionless status or context;
- interpretation presented as direct observation;
- hidden state, stale/error output, missing randomness control, or an undeclared
  manual step;
- a negative result, problem, or limitation hidden by a positive summary;
- an empirical notebook that omits the experiment source, purpose, procedure,
  recorded variables, actual observations, or analysis of those observations;
- independent questions that should be split.

Do not claim clean execution from stored outputs. Do not require a split merely
because the notebook is long, and do not require a specific heading when the
same function is unambiguous elsewhere.

## Split decision

Recommend a split when at least one content boundary is present:

- independently testable questions or hypotheses;
- different datasets, confidentiality regimes, environments, or manual methods;
- an intermediate output becomes a versioned input reused elsewhere;
- data preparation, pipeline execution, and interpretation change at different
  rates;
- expensive early steps must be skipped or cached to work on later steps;
- the notebook simultaneously acts as library, pipeline, and report;
- top-to-bottom execution requires a manual branch;
- one bounded summary cannot cover the independent conclusions.

Cell or line count is only a prompt to inspect these boundaries.

## Evidence-bundle gates

- At least one `data`, `protocol`, or `note` source in `input_scope`.
- At least one own result record, including a bounded negative or inconclusive
  result when that is the outcome.
- Addressable task and conclusion units.
- Claims cover all five canonical output sections above.
- Every supported numerical claim points to an evidence value or result record.
- A hypothesis stays unsupported, attributed, and marked for later checking.
- An `empirical` or `mixed` notebook covers all four experiment tags and links
  its observed result to the supplied experiment or data source.

## Technical lint

Run:

```text
python scripts/lint_notebook.py path/to/notebook.ipynb --json
```

The lint checks notebook structure and selected static signals only. A clean
report does not prove scientific correctness, fresh-kernel execution, or absence
of every hidden dependency. Resolve warnings manually under the reproducibility
contract.

For Russian output, run `audit_russian_style.py` on extracted Markdown with
`--profile genre-notebook` after the evidence gate.
