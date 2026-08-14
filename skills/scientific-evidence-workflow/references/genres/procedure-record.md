# Genre: procedure record

`mode: record` · `genre: procedure-record` · no literature context

## Purpose

Record one performed procedure at the moment it was performed: the date, what
was done, how it departed from the protocol, and what came out of it. The entry
is short, factual, and written for a reader who will need it months later
without remembering the day.

## Input

Require the protocol or note the procedure follows, and the outputs produced
with their versions.

## Procedure

1. Record the date and the procedure identity.
2. Record what was performed, referring to the protocol step rather than
   restating it.
3. Record every deviation with its extent, and the reason when known.
4. Record the outputs: file names, versions or hashes, and where they are.
5. Record what failed or was not completed.

## No literature context

This genre argues from nothing. It does not justify the method, compare it with
the field, or cite what is accepted practice. Evidence carrying literature
context is rejected by the validator for exactly this reason: a record of what
happened must not quietly become an argument that it was the right thing to do.
Method justification belongs in the decision log.

## Deviations

A deviation recorded as "minor", "as usual", or "broadly per protocol" is not
recorded. Give the extent: what was changed, by how much, at which step. A
deviation whose effect is unknown is recorded as unknown, not as negligible.

## Outputs are versioned

An output referenced without a version cannot be found again once the file is
overwritten. Record the version, run identifier, or hash at the time of
writing, not later.

## Gates

- At least one `protocol`, `data`, or `note` source.
- No evidence with literature-context support type.
- Internal references resolve to existing units.

For Russian output, apply `references/russian/genre-micro-report.md` after the
evidence gate and run the audit with `--profile genre-micro-report`.

Use `assets/procedure-record.template.md` for a file artifact.
