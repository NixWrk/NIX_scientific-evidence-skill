# Genre: micro review

`mode: literature_review` · `genre: micro-review` · two to five sources

## Purpose

Answer one review question across a small set of publications. The result is a
comparison, not a sequence of summaries, and not a full thematic review.

## Input

Require the review question, the fixed source set, and the reason the set is
bounded the way it is. If the set was chosen by a search, the search record
belongs in the corpus boundary; this genre never expands the set itself.

## Procedure

1. Restate the review question in a form that a comparison can answer.
2. Build one card per source with the same fields: object, design, sample,
   method, outcome with units, stated limitations.
3. Compare the sources field by field. A field that cannot be compared is
   reported as incomparable, with the reason.
4. Separate agreement, disagreement, and absence of evidence. Absence is not
   agreement.
5. Deduplicate by study before counting support: two reports of one study are
   one study.
6. State what the set cannot establish.

## Why one question

A micro review is bounded so that its conclusion stays checkable in a single
reading. Two to five sources is the working range. Below two there is nothing
to compare and the genre is an annotation; above five the comparison stops
being verifiable at a glance and a full thematic review is the honest form. The
validator treats the lower bound as an error and the upper bound as a warning.

## Evidence-strength language

Name the actual pattern: how many independent studies, their designs, whether
results are consistent or conflicting, and whether the comparison is direct or
indirect. Do not substitute venue, citation count, or recency for
methodological relevance, and do not assign an opaque quality score.

## Gates

- Between two and five sources.
- No research result records: this genre reports others' work.
- Every synthesis claim cites evidence from at least two sources or is marked
  as resting on one.
- Every number matches its source exactly.

## Stop conditions

Stop and ask when the review question is not supplied, when the source set was
not fixed in advance, or when answering would require a publication outside the
set.

For Russian output, apply `references/russian/genre-review.md` after the
evidence gate and run the audit with `--profile genre-review`.

Use `assets/micro-review.template.md` for a file artifact.
