# Experiment description — <experiment_id>: <short name>

- Record version: v...
- Protocol source: SRC-PROT-... (version or hash; write not_assessed if absent)
- Data/run source: SRC-DATA-... (version or hash; write not_assessed if absent)
- Boundary: one question, sample, run, and execution boundary
- State vocabulary: planned · approved · performed · observed · interpreted · not_assessed

> Keep expected outcomes (EXP-OUT-*) separate from observed results (RES-*).
> Approval is not performance; observation is not interpretation.

## Rationale and trigger [planned]

- Triggering observation, gap, or practical problem: ...
- Source or prior result: SRC-... / RES-...

## Question, hypothesis, and goal [planned]

- Question: ...
- Hypothesis (author and version): ...
- Goal and target quantity: ...
- Completion criterion: ...

## Expected observable outcomes [planned]

| Expected ID | Observable and unit | Expected direction/range/pattern | Basis |
|---|---|---|---|
| EXP-OUT-01 | ... | ... | SRC-... / hypothesis |

## Intended use and decision rule [planned]

- Intended use of the result: ...
- DEC-01: if ..., then ...; otherwise ..., or defer because ...

## Approval and responsibility [approved]

- Approved protocol: SRC-PROT-..., version/date ..., authority ...
- Approval scope: ...
- Ethics approval, if applicable: organization ..., body ..., identifier/date ..., scope ...
- Roles: responsible operator ..., analyst ..., supervisor ...

## Place, time, organization, and actual roles [approved] / [performed]

| Item | Planned/approved | Actual/performed | Evidence |
|---|---|---|---|
| Place and organization | ... | ... | SRC-... |
| Date/time window | ... | ... | SRC-... |
| Roles | ... | ... | SRC-... |

## Object, sample, and materials [planned] / [performed]

- Object and state: ...
- Materials and preparation: ...
- Planned sample: ...
- Included sample actually measured: ...
- Excluded/discarded units and reasons: ...

## Equipment, software, and calibration [approved] / [performed]

| Item | Model/asset identity | Version/settings | Calibration/validation | State/evidence |
|---|---|---|---|---|
| ... | ... | ... | ... | approved / performed, SRC-... |

## Planned procedure [planned]

1. ...
2. ...

## Actual procedure [performed]

1. ... (past tense; link each non-trivial step to SRC-...)
2. ...

## Data, variables, and units [performed] / [observed]

| Variable | Operational definition | Unit | Sampling/resolution | Time point/channel | Source/result |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | SRC-DATA-... / RES-... |

## Quality control, exclusions, and ethics [performed] / [not_assessed]

- QC check and threshold: ...; outcome: ...; evidence: SRC-... / RES-...
- Data integrity and missingness: ...
- Exclusion rule and application: ...
- Ethics/consent scope: ... (or not_assessed: reason ...)

## Deviations from approved/planned procedure [performed]

| Step | Deviation | Extent | Reason | Known effect / not_assessed | Evidence |
|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | SRC-... |

## Observed results [observed]

| Result ID | Direct observation or derived value | Unit/context | Source locator |
|---|---|---|---|
| RES-01 | ... | ... | SRC-DATA-..., file/table/figure/cell ... |

## Interpretation [interpreted]

- RES-01 against EXP-OUT-01: ...
- DEC-01: supported / not supported / inconclusive; reason ...
- Analysis assumptions and uncertainty: ...

## Limitations and not assessed [not_assessed]

- Missing or uncontrolled factors: ...
- Claims this run cannot support: ...
- Fields not assessed and why: ...

## Downstream use and result links [interpreted]

| Result/decision | Planned use | Downstream artifact and locator | Status |
|---|---|---|---|
| RES-01 / DEC-01 | ... | SRC-... / notebook/report section ... | ... |

## Validation

- Structural validator: ...
- Manual evidence and state check: ...
