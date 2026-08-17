# EXP-0034 lifecycle experiment

Command: `python experiments/EXP-0034-project-literature-lifecycle/run_experiment.py`

All inputs are local synthetic text/JSON records; no network or Zotero calls were made.

| Scenario | Result | Evidence |
|---|---|---|
| project context repair and validation | PASS | `sha256:d58e67cac76c1fc44452471e6fc4de3981d20c6afadd4bd72847fed82726aa93` |
| annotation 1 validation | PASS | `sha256:b2b6b89dcdbb8c4e985903c598cab72c4578eea9034b44743b6a5910f3354273` |
| snapshot 1 publish | PASS | `SNAP-995badaa3bf8988c` |
| snapshot 2 blocks missing annotation 2 | PASS | `SNAP-4f9d27fa9f1e9480` |
| annotation 2 validation | PASS | `sha256:4cf95fa66f41ef064d9c778de4c4a018d668f3e2ac7d8c1c840cb6c4086163a8` |
| snapshot 3 resynthesis and publish | PASS | `SNAP-78e9607b58c8e36f` |
| identical inventory byte-stable no-op | PASS | `3 snapshots retained` |

Canonical project context hash: `sha256:d58e67cac76c1fc44452471e6fc4de3981d20c6afadd4bd72847fed82726aa93`.
Review artifacts: `output/literature-review-v1.md` (sha256:0217ccba751f9211f6bf7e0527a680e0935093ebbe9507b614ad8ba1042fae2d) and `output/literature-review-v2.md` (sha256:6ef81e3f97508e1ca461e48083b33e1a6c3b8c328dfac5637a575c2f513bf416).
