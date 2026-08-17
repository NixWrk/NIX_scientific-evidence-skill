# EXP-0030 — candidate workflow forward-test

A fresh Luna agent with no conversation history loaded the local
`candidate-dissertation-workflow` skill and a valid holdout project manifest.
The prompt asked it to continue the dissertation and choose the next safe
step; it was not given an expected route or gold issue list.

The agent selected the Results stage and stopped because the bundle contained
only literature and a protocol, not approved result records. It also kept the
independent approbation gap and every downstream dependency visible. The test
therefore passes the routing, evidence-boundary, and fail-closed criteria.

This is a forward test of orchestration, not a release benchmark of a complete
dissertation. The four-stage critic benchmark remains defined separately in
`docs/dissertation-skill-evaluation-standard.md`.
