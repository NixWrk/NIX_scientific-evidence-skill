# Genre: experiment description

`mode: record` · `genre: experiment-description` · a protocol or data source required

## Purpose

Record what was actually set up and performed in one experiment, in enough
detail that the run could be repeated and that a Methods section can later be
written from this record alone. This is the mandatory stage between doing the
work and writing about it.

## Input

Require the protocol or the record of what was performed, the instrument and
software identities with versions and settings, and the data files produced.

The genre refuses to proceed without at least one `protocol` or `data` source.
That refusal is the point: an experiment described from memory or from what is
usual in the field is a reconstruction, and a reconstruction cannot support
Methods.

## Procedure

1. Record the object and materials: what was measured, on what, in what state.
2. Record instruments, models, and software with versions, settings, and
   calibration status as supplied.
3. Record the procedure as performed, in the order performed.
4. Record conditions and which factors were controlled. Name separately the
   factors that were not controlled or not recorded.
5. Record measured quantities with units, sampling, and resolution.
6. Record the sample: size, inclusion, exclusion, and what was discarded, with
   the reason for each exclusion.
7. Record quality control and its outcome.
8. Record ethical conditions when people are involved.
9. Record deviations from the protocol, each with its value or extent.

## Planned and performed

Keep the planned procedure and the performed procedure distinct throughout. A
description written in the future or conditional voice is a plan, and this
genre records only what happened. Where the two differ, both are recorded and
the difference is named.

## Ethical conditions

When people take part, do not assume the ethics committee of the author's own
organization. Establish the organization on whose base the experiment was
actually carried out and record its local approval. For instrument and device
work the experimental part is often performed jointly with a clinic, and the
approval belongs to that clinic.

## Do not generalize a single run

One run shows what happened in that run. Do not write that the method
"generally" or "typically" behaves a certain way from a single execution, and
do not smooth a deviation into a standard procedure.

## Gates

- At least one `protocol` or `data` source in `input_scope`.
- Every number cites an evidence value or a result record.
- Internal references resolve to existing units.

## Stop conditions

Stop and request input when the protocol is unavailable, when instrument or
software versions cannot be established, when the exclusion rule for discarded
data is unknown, or when people took part and the approving organization is not
identified.

For Russian output, apply `references/russian/genre-experiment.md` after the
evidence gate and run the audit with `--profile genre-experiment`.

Use `assets/experiment-description.template.md` for a file artifact.
