# Stored work-pattern records

Each `WORK-*.json` cards one defended work: how it is built and how it argues.
Each `PATTERN-*.json` collects features across several of them.

Records are created according to `../work-pattern-memory.md` and validated by
`../../scripts/validate_work_card.py`.

A work shows what one council accepted. It establishes nothing, and the schema
enforces that rather than trusting it: there is no field here in which a
requirement could be written, and the validator refuses obligation both in keys
and in prose.

Three strata decide what a record can support:

- `council` — defended in the target council; the only stratum that can speak
  about that council's practice;
- `specialty` — the same specialty, including the superseded code 05.11.17,
  but another or unrecorded council;
- `outside` — another specialty, another genre, or foreign literature.

An aggregate declares the stratum its scope demands, and the validator refuses
a feature supported by a work too weak to bear it.

Counts live nowhere. An aggregate names the works behind each feature; how many
there are is recomputed, because a stored count outlives the evidence that
produced it.
