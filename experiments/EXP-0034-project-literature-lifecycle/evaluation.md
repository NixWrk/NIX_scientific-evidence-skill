# EXP-0034 evaluation

| Scenario | Pass/fail | Check |
|---|---|---|
| Canonical context hash and project validation | PASS | RP-001 validator accepted the repaired manifest. |
| Annotation 1 gate | PASS | ZPA validator accepted full-text annotation 1 with real source/context hashes. |
| Initial review publication | PASS | ZLR created one immutable snapshot and publication recording succeeded. |
| Missing annotation blocks snapshot 2 | PASS | ZLR created snapshot 2 with `synthesis_blocked=true` for PUB002. |
| Valid annotation 2 clears block | PASS | ZPA accepted annotation 2; ZLR created snapshot 3 with `needs_resynthesis`. |
| Snapshot 3 publication | PASS | Publication recording succeeded and state validation passed. |
| Identical inventory rerun | PASS | No new snapshot; serialized state bytes were identical. |

Discovered defects: none blocking this contract experiment.
