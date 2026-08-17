# Genre: thesis synopsis

`mode: manuscript` · `genre: thesis-synopsis` · frozen dissertation required

## Authority boundary

Treat the synopsis as a mandated qualification artifact only under the supplied
applicable regulatory and institutional profile. GOST R 7.0.11-2011 alone does
not authorize inventing its volume, circulation, cover, detailed layout, or
reader-facing heading scheme. The registry controls its scientific composition:
general characteristics, main content, conclusion, and the author's works. The
synopsis may not contain a claim absent from or stronger than the dissertation.

## Purpose

Produce a compact, traceable representation of the frozen dissertation for the
dissertation council and opponents. Compression may remove detail but may not
add evidence, results, novelty, significance, propositions, organizational
facts, or stronger certainty.

## Input

Require the frozen dissertation version and hash, its claim/result/structure
ledgers, approved introduction elements, chapter conclusions, final conclusion,
and verified organizational records. Require a verified author-publication list
and the applicable synopsis normative profile when formatting or volume is in
scope. Stop if the dissertation version is not frozen or a synopsis claim cannot
be mapped to it.

## Canonical control sections

| Function | `output_section` |
|---|---|
| source dissertation, profile, and compression boundary | `synopsis_scope` |
| general characteristics of the work | `general_characteristics` |
| chapter-by-chapter scientific content | `main_content` |
| dissertation conclusions without new claims | `synopsis_conclusion` |
| verified works of the author | `author_publications` |
| claim-to-dissertation mapping | `synopsis_traceability` |

Reader-facing names and order follow only a supplied applicable profile.

## Operations

### Generate

Freeze the dissertation and create a one-way mapping from each synopsis claim to
the exact dissertation claim and section. Compress within each required
component while preserving values, modality, boundary, and attribution. Build
the author's works list only from verified bibliographic and organizational
records.

### Critic

Compare every scientific and organizational statement with the frozen
dissertation and records. Flag additions, stronger wording, unmatched numbers,
changed terminology, omitted task closure, and unverified works. Use comments
for scientific or structural gaps; permit tracked changes only for exact local
corrections authorized by the dissertation.

## Procedure

1. Record the source dissertation hash, version, approval state, and applicable
   synopsis profile.
2. Map general characteristics to the approved introduction elements without
   creating new relevance, novelty, significance, or propositions.
3. Summarize the main content by addressable dissertation units and preserve the
   distinction between methods, results, interpretation, and comparison.
4. Reproduce only the necessary numeric detail and keep its unit, uncertainty,
   boundary, and `result_id`.
5. Form the synopsis conclusion as a subset or faithful compression of the
   dissertation conclusion; do not repair the dissertation inside the synopsis.
6. Verify each author work, identifier, publication status, and relation to the
   dissertation from supplied records.
7. Run a reverse audit: every synopsis claim must resolve to exactly one or more
   dissertation claims and existing sections.

## Scientific-formulation controls

- Never strengthen “may”, “associated”, “within the sample”, or an uncertainty
  statement during compression.
- Do not introduce a new novelty point, proposition, result, recommendation, or
  implementation fact for rhetorical completeness.
- Preserve author/source attribution and distinguish published from accepted,
  registered, or submitted works.
- Treat shortening that changes scientific scope as a semantic revision.
- Record every semantic correction in the revision ledger.

## Gates and stop conditions

- The source dissertation is frozen and identified by version and hash.
- Every synopsis claim and number resolves to the dissertation claim/result and
  structure ledgers; no synopsis claim is stronger than its source.
- All six control sections occur in the claim ledger.
- Organizational claims and author works have verified organizational or
  bibliographic records.
- Layout and volume claims use an applicable supplied normative profile.
- Stop on an unmatched claim, changed scientific boundary, unverified work, or
  unresolved dissertation version.

Apply `references/russian/genre-dissertation.md` after the evidence gate and run
the language auditor with `--profile genre-dissertation`. Use
`assets/thesis-synopsis.template.md` for a file artifact.
