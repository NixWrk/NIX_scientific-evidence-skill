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
