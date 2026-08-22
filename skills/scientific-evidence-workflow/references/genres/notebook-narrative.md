# Genre: notebook narrative

`mode: record` · `genre: notebook-narrative` · data, protocol, or note source required

## Purpose

Create or criticise an `.ipynb` artifact as a self-contained executable
scientific and technical report. The `.ipynb` format does not determine the applied role. A
notebook may validate a method, analyse data, justify a choice, document an
experiment, prepare a later experiment, or transfer a result into an
engineering artifact. In every case it must expose the calculations, data,
rationale, observable outputs, and limits that support that role.

One notebook answers one main research question, or several dependent subtasks
that form one computational chain and support one bounded summary. State the
applied role explicitly; do not route or criticise a notebook only by its file
extension.

`Notebook narrative` is an internal genre identifier. Do not use “research
notebook”, “research diary”, or “passport” as a reader-facing document type or
opening rubric. The artifact is a report whose executable calculations are
part of the evidence.

The genre controls the scientific narrative in Markdown cells and the relation
between code, observable output, and conclusion. Use complete scientific
sentences throughout the notebook, including transitions, captions, and rendered
Markdown; telegraphic result slogans, conversational fragments, and implication
arrows do not constitute a narrative. It does not prescribe a fixed set of
headings and does not rewrite executable code for style.

Also load `references/notebook-genre-profiles.md` and
`references/reproducibility-contract.md` and `references/reader-html.md`.
When external publications are cited,
load `references/bibliography-gost.md` for Russian output. For Russian text,
load both `references/russian-scientific-style.md` and
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
prose. This state is an internal provenance requirement, not a reader-facing
heading. If the notebook is already executed, preserve the original cells and
outputs during criticism.

Select one primary `genre_profile` from `references/notebook-genre-profiles.md`.
Use its semantic functions and stop rules in addition to this common contract;
do not infer the profile from a filename, library, or saved output.

## Executable technical-report contract

Organise the notebook into meaningful report blocks with subject-specific
headings. The opening states the task and practical purpose, then describes the
source material in scientific terms. For empirical data, name the experiment
or observation, its purpose, object or sample, place and date when supplied,
conditions, equipment or recording scheme when material, measured signals and
units, and the subset analysed. For simulated or derived data, name the model
or preceding calculation, parameters, conditions, scientific status, and the
quantity transferred to the current task. A filename, directory, item key, or
table identifier may be given only as a secondary locator; it is not an input
description.

Do not expose a generic passport, execution environment, inherited-state
register, run manifest, or file inventory as part of the readable report.
Retain paths, hashes, library versions, kernel information, and upstream
identifiers in notebook metadata, loader code, or a separate machine-readable
run record. Surface one of them in prose only when it changes the meaning,
validity, or reproducibility of the scientific result, and explain that effect.

Before a material calculation, introduce the investigated object and the
measurement, physical, mathematical, statistical, or computational model used
to represent it. Explain necessary terms and distinctions, geometry or causal
relations, variables and units, equations, boundary and initial conditions,
assumptions, expected limiting behaviour, applicability domain, and claims the
model cannot support. When a term or model is unfamiliar or spatial, add a
labelled explanatory scheme derived from supplied information.

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

Before every material figure, state why the relation, comparison, or assessment
must be examined and which scientific question it resolves. Name the related
quantities, relevant conditions, selection, and encodings, but do not open the
paragraph with a deictic announcement such as `Ниже представлен рисунок` or
`На рисунке показан`. The prose must lead the argument to the visualisation,
rather than merely announce a display operation.

Place a standalone caption immediately after the displayed figure in the form
`Рисунок N. <предметное название>`. The caption identifies the relation or
object, data and selection, conditions, axes and units, and material encodings.
It also distinguishes observed data from computed geometry, an explanatory
illustration, simulation, or external validation. Do not combine this caption
with the analysis or a result-status block.

After the caption, write unlabelled connected prose that explicitly refers to
the numbered figure and separates direct observation from interpretation. Do
not create a heading or bold label such as `Анализ рисунка`, `Наблюдение`, or
`Интерпретация`. State the bounded conclusion and applicable limitation; add a
hypothesis and its verification step only when the displayed result justifies
them. Neither a caption nor a semantic tag replaces this analysis.

Close the material stage with a separate concluding paragraph. This paragraph
names the established dependence, numerical result, limitation, and reason for
the next operation without repeating a citation to the figure number. The
following material block must perform the declared task and use the stated
decision criterion. Do not leave a proposed check as decorative closing prose
and then begin an unrelated calculation.

## Traceable narrative and calculation chain

Make the logic reproducible and evidential, not merely chronological. Within a
notebook, every material block identifies the input or preceding result it uses,
the operation or check performed, the observable output, the bounded statement
supported by that output, and the reason for the next operation. A link or a
matching heading does not establish this relation by itself.

Do not satisfy these requirements by adding a generic introductory wrapper
while leaving the original code and outputs unexplained. Each material
calculation must be integrated into the report's reasoning, and every retained
section must contribute to the same bounded question.

Across a sequence of notebooks, preserve the same chain through versioned
artifacts and machine-readable handoff records. The downstream notebook must identify
which accepted fact, number, hypothesis, or artifact it consumes, its resolved
version and scientific status, and the operation for which it is needed. A
reader must be able to reconstruct the path from source data through checks and
intermediate results to the final conclusion without relying on chat history or
interactive-kernel memory.

Use the semantic function `calculation-chain` to mark where this dependency
logic is stated. The marker is not proof of coherence; inspect whether the
declared links match actual variables, artifacts, outputs, and execution order.

## Forward reasoning bridges

Use a reasoning bridge between every pair of material stages. A bridge is a
standalone concluding paragraph, not a checklist or continuation of the figure
analysis. Separate it from the observation and interpretation block. Let the
first sentence itself synthesise the completed section by naming the established
dependence, comparison, calculation, or result rather than the figure that
displayed it. An introductory connector such as `Таким образом` is optional and
must not become a template.
Audit repeated first two or three lexical words across the document and rewrite
frequent openings through subject-specific sentence structure; cycling through
synonyms for the same stock phrase does not create narrative variety. The paragraph contains all
applicable moves:

1. identify the preceding result or results by their scientific content, equation,
   table, section, result identifier, or versioned artifact; do not use a figure
2. state what those results establish and which limitation, ambiguity, or open
   question prevents the argument from stopping there;
3. explain why the next calculation, comparison, or check is the appropriate
   response to that specific gap;
4. state an explicit decision criterion or attribute the forecast to the model,
   hypothesis, equation, protocol, or comparison that licenses it; when useful,
   give the alternative observations and the conclusion permitted by each;
   never use an unattributed `Ожидается ...` / `Ожидаются ...` or report an unperformed result as
   fact;
5. open the next stage by resolving the declared task and naming the inherited
   results it actually uses.

When several earlier results jointly motivate a step, name each result and its
distinct role. For example, one figure may establish a sensitivity trend while
another establishes an admissible range; the next optimisation is justified by
their intersection, not by the vague phrase “based on the preceding analysis”.

Mark only this standalone closing paragraph `reasoning-bridge`; do not combine
that tag with the figure, observable-output, interpretation, method, or next-stage
paragraph. Mark the opening paragraph of the
declared next material stage `forward-task`. The tags expose the seam for static
review but do not prove that the scientific relation is valid. A bridge may end
with a blocked task when required data or an authoritative selection rule is
absent; state the blocker instead of inventing the next result.

Across notebook boundaries, store the same moves in the `reasoning_context` of
a schema-version `1.1` artifact handoff. The downstream introduction renders
the established result, unresolved question, decision rationale, next task,
attributed prediction or observable alternatives, and evaluation criterion as
ordinary scientific prose. Do not reproduce the machine field names as
reader-facing headings.

## Equation narrative and reference integrity

When equations carry the argument, introduce each physical or mathematical
relationship at the first calculation stage where it becomes necessary. Never
front-load material equations in an opening formula catalogue, background
section, or term glossary. Definitions may be introduced early, but an equation
belongs immediately before the calculation, transformation, check, or
interpretation that uses it.

State the local need in prose before displaying the equation. Number each
material equation and treat it as part of the surrounding sentence: put a comma
immediately after the display, begin the following clause with lowercase `где`,
and define every symbol in that clause, including units and conditions when
applicable. A reference to a remote glossary does not replace the local
definitions. Apply the equation and then cite its
number in the prose that transforms, compares, or interprets the result. Keep
prose between successive equations: explain what the previous relation
establishes and why the next relation is now needed. Later stages refer to the
first numbered occurrence instead of repeating the equation.

Reject embedded control characters that can corrupt prose or LaTeX commands.
Validate relative links in companion Markdown reports as well as notebooks, and
exclude generated checkpoint copies from the canonical corpus. Every relative
link must resolve in the frozen corpus. Every equation reference
must resolve to one equation label. Every in-text citation must resolve to one
bibliography entry, every scientific bibliography entry must contain an
explicit clickable publication link, and exact publication titles must remain
in the source language. Add or repair the link in the regenerated `.ipynb` or
companion `.md` before HTML export; an HTML-only correction is invalid. Use
stable machine identifiers beneath reader-facing numbering.

## Reader HTML release

Publish a sibling `.html` for every released notebook. Treat the `.ipynb` as
the executable source and the HTML as its reader-facing scientific report.
Exclude code inputs, input prompts, and output prompts from HTML while retaining
the narrative, formulae, tables, numerical results, figures, images, captions,
and interpretation. Preserve all internal and external links as clickable
anchors and require local targets to travel with the release or be embedded.

Build the reader artifact with `scripts/export_reader_html.py` or an equivalent
exporter configured to hide inputs. Validate it with
`scripts/validate_reader_html.py`. A frozen release fails if the reader HTML is
missing, exposes a code-input area, has an unresolved internal anchor, or
refers to an absent local link or image. Record remote URL availability and
scientific support as separate validation axes because static HTML inspection
does not establish them.

## Scientific status, checks, and stop rules

Assign every material inherited or produced result an explicit scientific
status appropriate to its role: `measurement`, `estimate`, `bound`, `reference`,
`approximation`, `model_prediction`, `placeholder`, `hypothesis`, or `decision`.
Use `result-status` on the narrative cell that reports it. Do not promote a
bound to an estimate, an approximation to a measurement, or a hypothesis to a
finding without new evidence and an explicit status change.

Report three validation axes independently in notebook metadata:

- `technical_validation_status`: structure, declared inputs, schemas, hashes,
  local links, internal references, and bibliography integrity;
- `computational_validation_status`: actual execution, tests, invariants,
  numerical checks, and declared coverage;
- `scientific_validation_status`: scientific review of the method,
  interpretation, evidence boundary, and unresolved conflicts.

A pass on one axis never implies a pass on another. A clean-kernel run does not
approve the interpretation, and scientific approval does not repair a broken
link, missing input, or failed calculation.

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
Validate the machine record with `scripts/validate_artifact_handoff.py`.

If selection, exclusion, duplicate handling, or canonical-input rules conflict,
set automation to `blocked`. Permit automated downstream use only after a
versioned resolution identifies the authoritative policy and its provenance.

## Minimal narrative arc

Cover these functions, using headings, labels, semantic cell metadata, or
another clear arrangement appropriate to the notebook:

1. `notebook_scope`: task, practical purpose, included and excluded scope,
   completion criterion, semantically described inputs, and expected outputs;
2. `technical-background`: investigated object, experimental or computational
   model, terms, quantities, equations, units, conditions, assumptions,
   applicability limits, and any required explanatory scheme;
3. `method_and_assumptions`: method, material parameters, interpretation
   criterion, calculation chain, and applicable verification checks before the
   result;
4. `observed_outputs`: observable numbers, tables, figures, errors, and negative
   or inconclusive outcomes produced by the executed steps, with result status;
5. `interpretation_and_limits`: interpretation separated from observation,
   uncertainty, applicability boundary, unresolved problem, or attributed
   hypothesis;
6. `notebook_summary`: what was established, what was not established, retained
   artifacts, and a next action only when a decision was actually made.

Use the local arc `purpose/input → concepts/method/assumptions → calculation or
visualisation → observable output → interpretation/limit → reasoning bridge →
declared next task` for a logical calculation stage. At the next stage, show
that this declared task is the operation actually performed. Do not create headings around
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
   existing notebook structure. Select and record one primary notebook genre
   profile.
2. Write a scientific title and an ordinary report introduction; do not expose
   a passport, environment form, inherited-state register, or file inventory.
3. Describe inputs by scientific origin and meaning before giving technical
   locators.
4. Resolve inherited facts, numbers, and hypotheses from the current approved
   upstream artifacts and retain their versions.
5. Put reusable algorithms in modules when they are no longer part of the
   report's explanatory path.
6. Describe the object and model, then introduce only the terms, assumptions,
   and conditions needed to begin the first calculation stage. Introduce and
   number each material equation at its first actual use, define its symbols
   and units in an immediately following `, где ...` clause, apply it, and cite
   it in the prose that interprets or transforms the result. Do not place a
   formula catalogue in the opening sections.
7. State the traceable calculation chain and run every applicable model,
   identifiability, data-identity, and consistency check.
8. Keep observations, interpretations, hypotheses, decisions, and limitations
   linguistically distinct.
9. Assign material results a scientific status and preserve it through every
   inheritance or handoff.
10. Render material result numbers in Markdown from variables or result objects;
    never maintain a second manually typed copy.
11. Motivate every material figure, place a standalone `Рисунок N. ...` caption
    immediately after it, then interpret it in unlabelled prose with a numbered
    reference; keep the stage conclusion free of repeated figure references.
12. Close every nonterminal material stage with a standalone, subject-specific
    synthesising `reasoning-bridge` paragraph, audit repeated openings, and mark
    the opening that performs its declared operation `forward-task`.
13. Preserve negative and uncertain results. Attribute a new hypothesis and state
    how it could be checked; never convert it into the current conclusion.
14. Record and validate every downstream artifact handoff, its reasoning
    context, and its acceptance criterion. Block automation while selection rules are conflicted.
15. Validate local links, equation references, citations, and the bibliography.
16. Record technical, computational, and scientific validation separately.
17. Complete the reproducibility account, run the notebook lint, extract all
    Russian narrative including rendered Markdown, and pass the mandatory core
    and `genre-notebook` Russian language gate.

## Critic

Check the notebook against its declared question and this genre before applying
generic preferences. Report:

- a missing or drifting question, scope, or completion criterion;
- a generic wrapper or metadata form substituted for a scientific and
  technical report;
- “passport”, environment, inherited state, file inventory, or the internal
  genre name exposed as reader-facing content without scientific necessity;
- input described only by filename, path, item key, or table identifier;
- a missing account of the investigated object, model, terms, equations,
  variables, units, conditions, assumptions, or applicability limits needed to
  understand the calculation;
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
- a formula catalogue or equation bundle placed before the calculation stages
  that actually use the equations;
- an uncaptioned figure or a caption that omits axes, units, encodings, source,
  or evidential role;
- hidden state, stale/error output, missing randomness control, or an undeclared
  manual step;
- a negative result, problem, or limitation hidden by a positive summary;
- a nonterminal stage that ends without naming the result, unresolved question,
  reason for the next operation, and an attributed prediction, observable
  alternative, or decision criterion;
- a `reasoning-bridge` embedded in the result analysis instead of a separate
  concluding paragraph with a subject-specific synthesis;
- an unattributed `Ожидается ...` / `Ожидаются ...`, a repeated opening, or a
- a figure introduced by `Ниже представлен ...` instead of the scientific need
  for the relation or assessment;
- a figure caption combined with its numerical result or interpretation;
- a post-figure analysis that has its own heading, omits the numbered reference,
  or is not followed by a separate stage conclusion;
- a stage conclusion that cites the figure instead of naming the established result;
  rotation of stock synonyms used in place of a subject-specific argument;
- a declared next task that the following material stage does not perform;
- a multi-result decision that cites only a generic “preceding analysis” instead
  of identifying the contributing results and their distinct roles;
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
- Every nonterminal material stage has a reasoning bridge, and the next material
  stage performs the declared task or records an explicit blocker.
- Every multi-result decision identifies all material bases and their roles.
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
- Technical, computational, and scientific validation statuses are present and
  no status is inferred from another.
- Every local link, equation reference, citation, and bibliography label
  resolves; external scientific sources have complete records.
- Conflicted selection or canonical-input rules block automation until a
  versioned resolution record is supplied.
- An `empirical` or `mixed` notebook covers all four experiment tags and links
  its observed result to the supplied experiment or data source.
- Every Russian static or rendered narrative fragment passes the common Russian
  scientific-language rules and the `genre-notebook` profile; every warning is
  corrected or receives a recorded contextual adjudication. Unreviewed warnings
  require `language_audit_status: partial`.

## Technical lint

Run:

```text
python scripts/lint_notebook.py path/to/notebook.ipynb --json
python scripts/validate_notebook_references.py path/to/notebook.ipynb --json
python scripts/validate_artifact_handoff.py path/to/handoff.json --json
```

The notebook lint and reference audit check structure and selected static
signals only. They can
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
The auditor's `valid: true` and `language_gate_status: partial` mean only that
no error-level surface pattern was found. Keep the notebook language status
`partial` until every warning has been adjudicated and the complete static and
rendered narrative has been read manually; only then attest `passed`.
