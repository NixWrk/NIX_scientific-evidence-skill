# Four-stage evaluation

Run the same frozen configuration through four stages:

1. `regression`: works already used to build pattern memory; detect known
   cases and drift, but do not claim independent generalization.
2. `mutation`: blind controlled defects with a hidden mutation ledger.
3. `clean_control`: matching unmodified fragments for false-positive
   measurement.
4. `holdout`: works never used for memory, rule design, or mutation design.

Compare a no-skill baseline, generator output, critic-on-generator, and
critic-on-human-text. Keep gold and mutation records unavailable to the critic.

Report per-rule TP, FP, FN, locator accuracy, authority resolution, class and
severity accuracy, accepted-comment rate, safe-fix precision, and preservation
of numbers, units, terms, references, and causal strength. List stop errors
separately; do not hide them in one aggregate score.
