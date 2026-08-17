# Conditional critic verification protocol

Use this protocol only when a finding depends on a source fact, number, dataset,
absence claim, citation-coverage claim, scientific inference or normative rule.
Technical and editorial findings remain in the lightweight critic workflow.

## Verify the assertion

1. State the exact assertion that needs proof.
2. Re-open the relevant source representation.
3. Record the source ID/hash, representation, locator, short confirming fragment
   or calculation, and verification method.
4. Narrow or reject the finding if the source supports only part of it.
5. Attach the verification record to the ordinary critic finding.

Use visual PDF/DOCX for printed spelling, layout, headings and tables. Use
text/HTML for semantic search. Treat OCR and anchor indexes as search leads.
Conflicting representations block a categorical finding until resolved.

## Special checks

- Recalculate percentages, diagnostic metrics and other derivable numbers.
- For absence, declare the inspected scope and whether it was complete.
- For citation coverage, search actual in-text citations; an absent HTML anchor
  is insufficient.
- For a normative violation, resolve the applicable version and requirement.
- Distinguish participants, sessions, recordings, cycles and measurements.
- Distinguish development, threshold selection, internal checking and external
  validation samples.
- For nested anatomical or technical objects, state the compared levels rather
  than calling parent and child automatically incomparable.

## Stop conditions

Do not release the evidential assertion when the locator is missing, the source
representation is unsuitable, the calculation disagrees, the inspected scope
is incomplete for a global absence, or the authority/applicability is unknown.
Return a bounded recommendation or `not_assessed` instead.
