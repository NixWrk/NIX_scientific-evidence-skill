# Title page and final Word TOC

## Title page

Use `scripts/apply_dissertation_title_page.py` only with a source DOCX that
contains one standalone `[[TITLE_PAGE]]` paragraph before any explicit page or
section break. Supply every printed fact in JSON; the module does not infer a
name, specialty, degree, scientific field, supervisor, place, or year.

The supervisor or consultant must be a structured object with full name,
academic degree, and academic title. The base GOST profile requires the fields
listed in `NORM-GOST-R-7.0.11-2011-001:REQ-007`. Add local requirements through
`local_profile.authority_ids`. If
`NORM-BMSTU-DISS-REQ-001:REQ-007` is selected, a supplied signature line is
mandatory. The script writes a new DOCX and returns the applied and
`not_assessed` fields with their authority identifiers.

To criticise an existing title page, run:

```text
python scripts/audit_dissertation_title_page.py expected-title.json manuscript.docx --out title-findings.json
```

The expected JSON is the same approved fact set used by the generator. The
auditor checks only the text before an explicit Word page boundary. If neither
`w:br type=page` nor `w:lastRenderedPageBreak` proves that boundary, it returns
a source-quality recommendation and does not convert absent text into a
normative violation. It does not infer layout, field order, or typography from
the standard. Visible line breaks and tabs are whitespace for fact-presence
comparisons, while exact Word anchors retain the real text-node sequence.
Supervisor and consultant name, degree, title, and optional position are
checked as components; their display order is not normative unless a selected
local authority explicitly makes it so.

## Final Word TOC

Use `scripts/finalize_word_toc.py` only after the manuscript layout and Word
heading styles are stable. The source must contain one standalone `[[TOC]]`
paragraph. The module rejects an empty heading or a skipped hierarchy level,
then inserts a real complex field:

```text
TOC \o "1-N" \h \z \u
```

It also sets `w:updateFields`, but it does not calculate or promise page
numbers. Open the output in Word or another compatible layout engine, update
all fields, save, and then run `--check-cached` against the refreshed copy.
That check confirms field structure and exact heading inclusion; rendered page
inspection is still required to assess page-number currency and layout.

The TOC satisfies exact-heading and completeness requirements by deriving
entries from the same Word heading paragraphs that form the manuscript. A
manually typed TOC is not a supported final representation.


## Critic for an existing Word TOC

Run only after the field has been refreshed and saved by Word:

```text
python scripts/audit_existing_word_toc.py refreshed-manuscript.docx --out toc-findings.json
```

The auditor compares the cached field result with the register of Word heading
styles. A missing field, missing cache, or unreliable heading styles produce
only technical or source-quality findings. A level-1 heading absent as an exact
cached entry proves that at least one of REQ-008 (exact wording) and REQ-031
(complete main parts) is not met, but the structural check does not pretend to
distinguish omission from reformulation. Subheadings outside the field's `\o`
range are ignored; included subheading discrepancies remain non-normative
unless a local profile makes them mandatory. Dot-leader rendering and page
number currency require rendered inspection and remain outside this audit.
