# Four-stage evaluation

Run the same frozen configuration through four stages:

1. `regression`: known works and disclosed failures;
2. `mutation`: blind controlled defects with a hidden mutation ledger;
3. `clean_control`: matching unmodified fragments for false positives;
4. `holdout`: works not used to design the rule or mutation.

Compare baseline, generator output, critic-on-generator and critic-on-human-text.
Keep gold and mutation records unavailable to the critic.

Report recall and precision by technical, editorial and evidential class;
locator, class and severity accuracy; false positives on clean controls;
preservation of numbers, units, terms, references and causal strength. For
evidential findings additionally report source/calculation/coverage/authority
accuracy. Test delivery-format integrity only for adapters actually used.
