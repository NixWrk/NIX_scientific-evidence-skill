# Example: style_overrides.md

Copy this file to `<paper-repo>/.paper/style_overrides.md` and edit it for the
specific manuscript. Rules here override the skill defaults.

## Banned Terms For This Paper

```text
- "GUL" because the manuscript uses "flood damage" throughout.
- "worst-case" because it is reserved for the named scenario only.
- "Monte Carlo" because the study uses stochastic runs, not a Monte Carlo estimator.
```

## Allowed Terms Despite Defaults

```text
- "significant" is allowed when reporting p-values or confidence intervals.
- "Although" is allowed as a sentence opener under the target journal style.
- Long dashes are allowed, but use at most two per paragraph.
```

## Terminology Preferences

```text
preferred                  avoid
-------------------------  -------------------------
flood damage               GUL, gross loss
adaptation scenario        worst-case scenario
two-way coupled            fully coupled
out-of-pocket loss         uncompensated loss
```

## Domain Vocabulary Swaps

Use this section when the manuscript imports text from a different
sub-field (method paper, software repository, neighbouring-discipline
co-author, internal technical documentation) and the target journal's
reviewers use different terminology. What counts as "field-foreign" is
defined by the target audience, not the source field. Source the
target-field-native side from a sample of recent papers in the journal —
two or three Methods and Discussion sections is usually enough to
identify the vocabulary the reviewer pool uses.

Format the table with the source-field term on the left and the
target-field replacement on the right:

```text
field-foreign (source: <source field>)          target-field native (<target journal field>)
----------------------------------------------  ----------------------------------------------------------
<source-field term 1>                           <target-field replacement 1>
<source-field term 2>                           <target-field replacement 2>
...
```

Worked illustration — a manuscript that imported CS / software-engineering
terminology from an underlying agent-based-modelling repository, now being
refocused for a water-resources journal:

```text
field-foreign (source: CS / software)             water-resources native
------------------------------------------------  ---------------------------------------------------------
validator stack                                   institutional rule checks
intercepts proposals before execution             screens each proposed decision before the agent acts
numerical state in, numerical action out          takes observed conditions and returns a numerical action
compressed into coefficients                      absorbed into the equation's calibrated parameters
computational interior                            the model's parameter values
cross-theory portability                          same architecture hosts different behavioural theories
decomposed across self-reported cognitive coords  broken down by the agent's own reported appraisal
factor these (verb)                               separate the two
```

The same table format applies to any field pair the manuscript bridges —
ML / clinical, statistics / engineering, pharmacology / public health,
qualitative-research / computational, basic / translational, methods /
applied. The specific entries are paper-dependent.

Novel terms that name the paper's contribution (e.g., for the water
illustration above: "action layer" vs "cognitive layer" in human-water
ABM) are allowed even with no field-native equivalent, but they must be
defined inline at first use with a target-field concrete example.

## Figure Conventions

```text
- red = damage
- blue = insured or recovered loss
- gray = severe-event shading
- endpoint labels report uncovered share
- severe flood years: 2011, 2021
```

## Author Voice

```text
- Use "we", not "the authors".
- Methods use past tense.
- General model definitions use present tense.
- Do not restructure Methods without explicit approval.
```

## Paper-Specific Notes

```text
- Table S2 is the authoritative parameter table.
- Sensitivity analysis belongs in Section 4.3, not the supplement.
- The accepted manuscript baseline is commit abc1234.
```
