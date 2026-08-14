# Stored normative-pattern records

Each file cards one normative document. A record is created by the
`normative-pattern-analysis` genre according to
`../normative-pattern-memory.md`, and validated by
`../../scripts/validate_normative_card.py`.

A card is what makes a requirement usable. Until a document has one, the
repository holds a pointer and no established rule.

Two source kinds behave differently and the difference is enforced:

- `document` — the text that states the requirements. It may carry them.
- `catalogue_card` — a registry entry establishing designation, status, and
  dates. It carries no requirements, and the validator rejects a card that
  claims otherwise.

Records are versioned. When a newer document changes a requirement, raise
`record_version` and describe the difference in `conflicts` instead of
overwriting the earlier observation.
