# Dissertation critic workflow

Critique the artifact against the rules of the skill that owns it. The primary
question is whether the text performs its genre correctly: structure, logic,
scientific formulation, narrative progression, consistency and formatting.

## Three check classes

### Technical

Use for formatting, numbering, references, registers, required sections and
other mechanically testable rules. Run the owning skill's deterministic audit
when one exists. Record the rule, locator, observed state and expected state.

### Editorial

Use for logic, scientific wording, cohesion, sequence of exposition, genre fit
and readability. Give a precise locator and explain why the passage impairs the
argument or genre. A reasoned editorial judgment does not need a source hash,
expert adjudicator or normative authority. Do not present stylistic preference
as a violation.

### Evidential

Use only when the criticism asserts a fact about a source, number, dataset,
absence, citation coverage, scientific inference or normative requirement.
Also load `critic-verification-protocol.md`; load
`scientific-judgment-calibration.md` when sample roles, unit of analysis,
hierarchy, inference strength or severity is involved.

## Lightweight finding

For every released finding record:

- `issue_id`;
- owning `skill_id` and `rule_id`;
- class: `technical`, `editorial` or `evidential`;
- exact locator;
- observed text or structure;
- concise rationale;
- severity: `critical`, `major`, `minor` or `note`;
- proposed correction, comment or `null` when author input is required.

Add a deterministic audit result only for a technical check. Add a verification
record only for an evidential check. Do not burden technical or editorial
findings with evidence machinery they do not need.

## Critic sequence

1. Select the owning skill and its relevant genre/reference.
2. Check required parts and hard gates.
3. Check logic, formulation and narrative progression.
4. Run applicable deterministic audits.
5. Escalate only evidence-dependent findings to source verification.
6. Merge duplicate findings and calibrate severity by effect on the work.
7. Return the report in the requested format; a delivery adapter must not alter
   the finding.

Keep observations separate from suggested rewrites. A rewrite that changes a
scientific claim still requires the ordinary claim/evidence gate.
