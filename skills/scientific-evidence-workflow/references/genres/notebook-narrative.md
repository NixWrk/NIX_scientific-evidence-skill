# Genre: notebook narrative

`mode: record` · `genre: notebook-narrative` · data, protocol, or note source required

## Purpose

Create or criticise a research notebook as a self-contained executable
technical report. The `.ipynb` format does not determine the applied role. A
notebook may validate a method, analyse data, justify a choice, document an
experiment, prepare a later experiment, or transfer a result into an
engineering artifact. In every case it must expose the calculations, data,
rationale, observable outputs, and limits that support that role.

One notebook answers one main research question, or several dependent subtasks
that form one computational chain and support one bounded summary. State the
applied role explicitly; do not route or criticise a notebook only by its file
extension.

The genre controls the scientific narrative in Markdown cells and the relation
between code, observable output, and conclusion. It does not prescribe a fixed
set of headings and does not rewrite executable code for style.

Also load `references/reproducibility-contract.md` and, for Russian text,
both `references/russian-scientific-style.md` and
`references/russian/genre-notebook.md`. The Russian language gate is mandatory
for static Markdown, captions, research comments, and narrative rendered by
code.

## Input

Require at least one supplied `data`, `protocol`, or `note` source. A generated
dataset is described by its generating protocol and parameters. Keep external
literature optional and distinguish it from the notebook's own outputs.

Fix the notebook file/version, applied role, main question, scope, completion
criterion, inputs, expected outputs, and intended audience. Identify upstream
facts, numerical results, and hypotheses that the notebook inherits. Resolve
them from current versioned artifacts rather than copying their values into
prose. If the notebook is already executed, preserve the original cells and
outputs during criticism.

## Executable technical-report contract

Organise the notebook into meaningful report blocks. The first block states
the task, practical purpose, inputs and their provenance, scope, assumptions,
limitations known in advance, completion criterion, and retained outputs.

Before a material calculation or choice, explain the terms, quantities,
formulae, comparison basis, and decision rule needed to read it. Define every
formula by naming its variables, units, numerator and denominator where
applicable, aggregation level, independent unit, missing-data rule, and the
direction or threshold used for interpretation. Explain why a method or
parameter was chosen when the choice affects the conclusion. Use a diagram or
illustration when prose alone does not make a spatial, geometric, procedural,
or unfamiliar concept clear.

After every material calculation, table, or visualisation, record the
applicable parts of this sequence:

1. what the output represents and which input/version produced it;
2. the direct observation, including a negative or inconclusive result;
3. the bounded result or interpretation;
4. assumptions, uncertainty, exceptions, ambiguity, and applicability limits;
5. a new hypothesis, with its status and a way to check it, when one arose;
6. the unresolved problem or next subtask when it follows from the result.

Do not create empty labels for parts that do not apply. Keep the transition to
the next block explicit when the previous result supplies its input, premise,
or question.

Give every figure a caption that identifies what is shown, the data and
selection represented, axes and units, encodings such as colour or line type,
and the evidential role of the visualisation. Distinguish a data figure from a
computed geometry, explanatory illustration, simulation, or external
validation. A caption does not replace the post-output observation and limit.

## Traceable narrative and calculation chain

Make the logic reproducible and evidential, not merely chronological. Within a
notebook, every material block identifies the input or preceding result it uses,
the operation or check performed, the observable output, the bounded statement
supported by that output, and the reason for the next operation. A link or a
matching heading does not establish this relation by itself.

Across a sequence of notebooks, preserve the same chain through versioned
artifacts and inherited-state records. The downstream notebook must identify
which accepted fact, number, hypothesis, or artifact it consumes, its resolved
version and scientific status, and the operation for which it is needed. A
reader must be able to reconstruct the path from source data through checks and
intermediate results to the final conclusion without relying on chat history or
interactive-kernel memory.

Use the semantic function `calculation-chain` to mark where this dependency
logic is stated. The marker is not proof of coherence; inspect whether the
declared links match actual variables, artifacts, outputs, and execution order.

## Scientific status, checks, and stop rules

Assign every material inherited or produced result an explicit scientific
status appropriate to its role: `measurement`, `estimate`, `bound`, `reference`,
`approximation`, `model_prediction`, `placeholder`, `hypothesis`, or `decision`.
Use `result-status` on the narrative cell that reports it. Do not promote a
bound to an estimate, an approximation to a measurement, or a hypothesis to a
finding without new evidence and an explicit status change.

When the method admits internal checks, make them part of the report rather
than leaving them implicit in code. Appropriate checks include dimensional
consistency, limiting cases, invariants, analytic-versus-numeric derivatives,
reciprocity, rank and conditioning, independent estimates, or agreement with a
declared reference. Mark the applicable account `verification-checks`. A failed
material check limits or blocks the conclusion; it is not removed from the
released narrative.

Apply an identifiability and confounding stop rule. If the available design
cannot separate parameters, sources, or experimental factors, state which
conclusion is prohibited and why no downstream processing can recover it from
the same information. Then specify the changed measurement, intervention, or
model comparison needed to remove the ambiguity. Do not replace this stop with
a point estimate from an optimiser boundary.

For an analytical proxy or other approximation, state its purpose, the class of
claims it may support, the claims it cannot support, and the higher-fidelity
calculation or observation that will replace it.

## Current inherited state and calculated prose

Inherit facts, numerical results, and hypotheses, not a previous notebook's
wording or decision. Keep the source identifier, locator, resolved version or
hash, and hypothesis status with every inherited item. A working notebook
resolves the current approved upstream state through a stable manifest,
registry, or loader. A frozen notebook records the exact resolved versions; an
upstream change produces a new run rather than silently changing the frozen
report.

Generate every material numerical statement in observations, captions,
results, and summaries from the same variables or loaded result object that
produced the table or figure. Render such prose from a code cell, for example
with a formatted Markdown display, and tag it `computed-narrative`. Do not
retype a calculated value into a static Markdown cell. Static Markdown may
contain fixed definitions, declared parameters, formulae, source facts, and
decision thresholds, with provenance where required.

If input files may have aliases or physical copies, establish identity by a
stable content identifier such as a checksum, record duplicates, and select a
canonical copy. A path or filename alone does not establish data identity.

When an output is consumed by another notebook or engineering calculation,
record an `artifact-handoff`: artifact identifier, source notebook and run,
version or hash, schema, units, scientific status, applicability limits,
intended consumer, and acceptance criterion. Formulate the next task
operationally: required quantity, inputs, method, required accuracy or decision
threshold, validation check, and the conclusion that will become possible.

## Minimal narrative arc

Cover these functions, using headings, labels, semantic cell metadata, or
another clear arrangement appropriate to the notebook:

1. `notebook_scope`: applied role, question, included and excluded scope,
   completion criterion, inputs, inherited state, and expected outputs;
2. `method_and_assumptions`: method, material parameters, assumptions, units,
   interpretation criterion, calculation chain, and applicable verification
   checks before the result;
3. `observed_outputs`: observable numbers, tables, figures, errors, and negative
   or inconclusive outcomes produced by the executed steps, with result status;
4. `interpretation_and_limits`: interpretation separated from observation,
   uncertainty, applicability boundary, unresolved problem, or attributed
   hypothesis;
5. `notebook_summary`: what was established, what was not established, retained
   artifacts, and a next action only when a decision was actually made.

Use the local arc `purpose/input → concepts/method/assumptions → calculation or
visualisation → observable output → interpretation/limit → next justified
question` for a logical calculation stage. Do not create headings around
imports, display settings, or trivial helper cells.

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
2. Resolve inherited facts, numbers, and hypotheses from the current approved
   upstream artifacts and retain their versions.
3. Put reusable algorithms in modules when they are no longer part of the
   report's explanatory path.
4. Describe terms, formulae, method, comparison basis, assumptions, and
   decision rule before interpreting outputs.
5. State the traceable calculation chain and run every applicable model,
   identifiability, data-identity, and consistency check.
6. Keep observations, interpretations, hypotheses, decisions, and limitations
   linguistically distinct.
7. Assign material results a scientific status and preserve it through every
   inheritance or handoff.
8. Render material result numbers in Markdown from variables or result objects;
   never maintain a second manually typed copy.
9. Caption every material figure and interpret it in the following report block.
10. Preserve negative and uncertain results. Attribute a new hypothesis and state
   how it could be checked; never convert it into the current conclusion.
11. Record every downstream artifact handoff and its acceptance criterion.
12. Complete the reproducibility account, run the notebook lint, extract all
    Russian narrative including rendered Markdown, and pass the mandatory core
    and `genre-notebook` Russian language gate.

## Critic

Check the notebook against its declared question and this genre before applying
generic preferences. Report:

- a missing or drifting question, scope, or completion criterion;
- a conclusion without an observable output;
- an unstated applied role or a role inferred only from the file extension;
- inherited facts, numbers, or hypotheses copied without a current source
  version and status;
- a material result number retyped in static Markdown instead of rendered from
  the variable or result object that produced it;
- a number without unit/dimensionless status or context;
- a calculation whose premise, input, observable output, or downstream use is
  not traceable inside the notebook or across its upstream handoff;
- a result whose scientific status is absent or silently promoted;
- interpretation presented as direct observation;
- an unexplained formula, metric, decision rule, or comparison made under
  unequal conditions;
- an uncaptioned figure or a caption that omits axes, units, encodings, source,
  or evidential role;
- hidden state, stale/error output, missing randomness control, or an undeclared
  manual step;
- a negative result, problem, or limitation hidden by a positive summary;
- an applicable verification check omitted, failed, or hidden;
- a point estimate reported where confounding or rank deficiency makes the
  target non-identifiable;
- duplicate or renamed input files treated as independent observations without
  an identity check;
- a downstream artifact without version, schema, units, status, limits, or an
  acceptance criterion;
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
- The declared calculation chain connects material inputs, operations,
  observable outputs, bounded statements, and downstream handoffs.
- Every material result preserves its scientific status; a status change is
  supported by new evidence.
- Every material numerical statement in a result, caption, or summary is
  rendered from the corresponding variable or loaded result object.
- Inherited facts, numbers, and hypotheses retain source/version provenance;
  hypotheses retain their current status.
- A hypothesis stays unsupported, attributed, and marked for later checking.
- Applicable model checks and identifiability limits are reported; a failed
  stop rule blocks the prohibited conclusion.
- Every downstream artifact has an addressable handoff contract.
- An `empirical` or `mixed` notebook covers all four experiment tags and links
  its observed result to the supplied experiment or data source.
- Every Russian static or rendered narrative fragment passes the common Russian
  scientific-language rules and the `genre-notebook` profile without unresolved
  errors; warnings are reviewed manually.

## Technical lint

Run:

```text
python scripts/lint_notebook.py path/to/notebook.ipynb --json
```

The lint checks notebook structure and selected static signals only. It can
verify the `computed-narrative` tag and a dynamic Markdown expression, but it
cannot prove that the variable came from the current approved upstream artifact
or that it also produced the displayed table or figure. A clean report does not
prove scientific correctness, fresh-kernel execution, or absence of every
hidden dependency. Record resolved input versions and hashes in the run
manifest under the reproducibility contract.

For Russian output, the language check is a release gate, not an optional
editorial pass. Execute the notebook as declared, extract both static Markdown
and rendered narrative text, and run:

```text
python scripts/audit_russian_style.py extracted-notebook-text.md --json --profile genre-notebook
```

Resolve every error and review every warning. Apply the same rules manually to
headings, captions, programmatically formatted observations, summaries, and
research comments that the heuristic auditor cannot reliably reconstruct.
