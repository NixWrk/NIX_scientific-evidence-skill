# Genre: article annotation

`mode: qa` · `genre: article-annotation` · exactly one source

## Purpose

Record what a single supplied publication did and how it bears on the current
research. The annotation is written for the researcher's own reference library,
typically as a note attached to the item.

## Input

Require one source, its version or content hash, and the current research
question the annotation is written against. Without that question the
usefulness statement has nothing to be relative to; ask for it instead of
inventing a generic summary.

## Procedure

1. Record the source identity: identifier, version or hash, and what portion was
   actually read. A metadata-only reading is annotated as metadata-only.
2. Extract what the work did: object, task, method, design, sample.
3. Extract the reported outcome with exact numbers, units, groups, and
   uncertainty. A number that cannot be quoted exactly is not carried over.
4. Extract the boundaries the authors themselves state.
5. Write the usefulness statement separately, as the current reader's judgement
   relative to the stated research question. Never attribute it to the authors.
6. Mark the annotation as derived.

## Separation of voices

Three voices must stay distinguishable in the finished note:

- what the source reports;
- what the source's authors conclude from it;
- what the current reader judges to be useful.

Collapsing the third into the first is the characteristic failure of this
genre: an opinion about relevance quietly becomes a finding of the paper.

## Derived-note marking

The note carries the source identifier, the version or hash it was made from,
and the date. An annotation is a derived record. It never becomes a source for
a later review or manuscript, and a claim may not cite it in place of the
publication. When the source version changes, the annotation is re-made rather
than silently reused.

## Gates

- Exactly one source in `input_scope`.
- No research result records: this genre reports someone else's work.
- No internal references: an annotation is not part of the author's own work.
- Every number matches the source string exactly.
- The usefulness statement is `interpretive`, not `factual`.

## Stop conditions

Stop and ask instead of guessing when the full text was unavailable and only
metadata was read, when the current research question was not supplied, or when
the source version cannot be identified.

For Russian output, apply `references/russian/genre-micro-report.md` after the
evidence gate and run the audit with `--profile genre-micro-report`.

Use `assets/article-annotation.template.md` for a file artifact.
