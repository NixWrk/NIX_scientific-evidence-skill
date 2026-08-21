# Notebook genre profiles

Use one primary profile for every `notebook-narrative`. Record it in
`scientific_report.genre_profile`. The common technical-report contract still
applies; a profile adds only the checks needed for the notebook's scientific
role. Do not combine profiles merely because several methods appear in one
file. Split the notebook when the roles lead to independent questions or
conclusions.

## `model-derivation`

Use for deriving, explaining, or extending a mathematical or physical model.

- Introduce the object, quantities, assumptions, and applicability domain
  before the first equation.
- Number material equations and refer to those numbers in the prose that uses
  them. Define symbols and units at first use.
- Explain what each equation adds to the chain; do not present an isolated
  formula catalogue.
- Mark the equation account `equation-narrative` and report dimensional,
  limiting-case, analytic-versus-numeric, or other applicable checks under
  `verification-checks`.

## `computational-verification`

Use when the main result is whether an implementation, approximation, or
numerical method satisfies declared checks.

- Name the reference, invariant, tolerance, and tested domain before running
  the comparison.
- Separate observed discrepancy from the judgement against the tolerance.
- Report coverage and cases not tested; a sampled sweep is not a proof over a
  continuous domain.
- Mark the check account `verification-checks`.

## `inverse-estimation`

Use when data are converted into an estimated parameter or latent state.

- Distinguish the forward model, inverse target, objective, constraints, and
  observation model.
- Check rank, conditioning, parameter correlation, profile behaviour,
  sensitivity to initialization, and boundary solutions when applicable.
- Mark the account `identifiability-check` and `verification-checks`.
- Report a bound, interval, or `not_assessed` result when the design does not
  identify a point estimate.

## `empirical-analysis`

Use when recorded observations are the main input and the notebook estimates,
compares, or summarizes them.

- Cover all four experiment functions from the notebook genre.
- State inclusion, exclusion, duplicate handling, missing-data treatment, and
  the independent unit before analysis. Mark this account `selection-policy`.
- Keep observed values separate from model-based interpretation and causal
  claims.
- Block automated downstream use while selection rules are contradicted or
  unresolved.

## `experiment-diagnostic`

Use when the notebook diagnoses acquisition quality, apparatus behaviour,
protocol deviations, drift, or failure modes.

- Cover all four experiment functions and the applicable technical checks.
- Preserve failed channels, negative outcomes, deviations, and alternative
  explanations.
- Mark the diagnostic checks `verification-checks`; do not promote a supported
  fault hypothesis to an established cause without a discriminating test.

## `synthesis-decision`

Use when the notebook combines approved upstream results to justify one
bounded decision.

- Resolve every upstream result through a versioned handoff; do not copy a
  mutable number into prose or configuration.
- State the decision criterion before comparing alternatives and mark it
  `decision-basis`.
- Preserve conflicts and applicability limits. A decision may be recorded even
  when the scientific evidence remains bounded, but the boundary must travel
  with it.
- Mark each produced downstream record `artifact-handoff`.

## `engineering-transfer`

Use when the main output is a parameter set, dataset, model, or other artifact
for a downstream calculation or implementation.

- Define schema, units, coordinate system, version, content hash, scientific
  status, applicability limits, consumer, and acceptance criterion.
- Mark the transfer `artifact-handoff` and the consumer check
  `acceptance-criterion`.
- Validate the handoff record with `scripts/validate_artifact_handoff.py`.
- Permit automation only when the validation axes and any selection policy
  satisfy the handoff contract.

## Profile selection gate

Before release, verify that the selected profile matches the notebook's main
question, its required semantic functions are present, and its stop conditions
affect the conclusion. A profile label in metadata is routing information, not
evidence that the functions were performed.
