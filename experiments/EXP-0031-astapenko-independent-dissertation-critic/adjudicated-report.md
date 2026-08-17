# EXP-0031 — adjudicated critic report

`critic-report.md` is the immutable raw blind output. This file records a
separate expert recheck of every raw item against the PDF/HTML representations.
The result is regression adjudication, not a gold set.

## Method

- visual PDF was used for page facts, printed spelling, contents and layout;
- HTML was used for semantic text, DOM locators and bibliography coverage;
- arithmetic and diagnostic claims were independently recalculated;
- a conflict or missing representation was reported as a bounded limitation;
- confidence and severity were calibrated separately.

## Decisions

### 1 — accepted, `verified`, `critical`

The table reports 12 correct diagnoses out of 15, so sensitivity is 80%, not
75%. Fisher `p=0,25` cannot be converted to sensitivity by `1-p` and does not
mean that the null hypothesis has a 25% probability of being true. Source:
PDF pp. 107–109 and HTML `#section-4-5`.

### 2 — narrowed, `partially_verified`, `major`

The thresholds are derived from 10 healthy volunteers and then applied to the
patient group; those are distinct sample roles. The raw statement that the same
group was used is too broad. The independent validation sample, ROC/CI and
preregistration are not reported, and the `и/или` condition is ambiguous. This
is an evidence-boundary finding, not proof that the method is invalid. Source:
PDF pp. 88–90 and HTML `#section-4-4-1`.

### 3 — accepted, `verified`, `major`

The proposed system has ten channels, while the clinical patient tables use four
leads (FMd, OMd, OMs and FMs). This limits evidence for clinical performance of
the full ten-channel configuration; it does not establish that the ten-channel
system cannot work. Source: PDF pp. 83, 94–95, 99 and HTML sections 4.2,
4.4.2–4.4.3.

### 4 — accepted, `verified`, `major`

The reported 95% algorithm accuracy is not reproducible from the text: sample
size, reference standard, error definition, class distribution, train/test split
and confidence interval are not supplied. Source: PDF pp. 75–78 and HTML
`#section-3-5-1`, `#section-3-5-2`.

### 5 — narrowed, `partially_verified`, `major`

The work mentions 25 people, 160 records and more than 96,000 cycles, while
healthy participants are 20–45 and patients 45–82. The age imbalance and the
unreported transition from repeated records/cycles to the person-level test are
valid limitations. The raw report overstates this as established misuse of
Fisher: without the aggregation/model details, state that the analysis unit and
dependence handling are not reported. Source: PDF pp. 85–86 and HTML
`#section-4-3`.

### 6 — narrowed, `partially_verified`, `major`

The reference localizes disease in the middle cerebral artery (a branch of the
internal carotid artery), whereas the REG comparison is described at the parent
carotid-basin level. The endpoints are hierarchically related, not anatomically
incomparable. The supported conclusion is that cross-level agreement does not
establish exact lesion localization. Source: PDF pp. 94–96 and HTML
`#section-4-4-2`.

### 7 — accepted, `verified`, `major`

The therapeutic conclusion is based on one before/after case without a control,
repeat observations, treatment protocol or quantitative statistical comparison.
It cannot support a general treatment effect. Source: PDF pp. 104–106 and HTML
`#section-4-4-4`.

### 8 — accepted, `verified`, `major`

Ethics/consent, inclusion criteria, blinding, CT/ultrasound protocols, raw
signals, software version, scripts and a complete result ledger are not reported
in the checked scope. This is a reporting and reproducibility deficit; it is not
automatically a finding that ethics approval or consent was absent. Source: PDF
pp. 83–86 and HTML sections 4.2–4.3.

### 9 — accepted, `verified`, `minor`

The reference to “tables 4.2–4.7” is internally inconsistent with the document's
figure/table numbering. The raw `P1` priority was too high: absent evidence that
the reference changes interpretation, this is a minor navigational defect.
Source: PDF p. 110 and HTML `#section-4-6`.

### 10 — corrected, raw claim `rejected_as_stated`

The raw report incorrectly says that the table of contents contains
`классифицикации`; the visual PDF contains the correct `классификации`. Valid
observations remain: the 3.4 heading differs between contents and body, and
`иследований` is an actual typo. The corrected replacement is a bounded
`partially_verified`, `minor` finding, not the raw composite claim. Source: PDF
pp. 3–4, 63 and 68.

### 11 — accepted, `verified`, `minor`

The PDF contains `ампитудно-фазовая` where `амплитудно-фазовая` is expected. The
visual source supports this as a local typographical issue. Source: PDF p. 5.

### 12 — corrected, raw claim `rejected_as_stated`

The bibliography has 72 records. A fresh coverage check leaves records 2, 34 and
44 as potential uncited entries, while record 20 is explicitly cited in
`[19, 20, 41]`. Lack of an HTML anchor is not proof of absent citation, and the
finding cannot be normative without a versioned authority. The corrected
replacement is a `partially_verified`, `note`/`minor` coverage recommendation.

## Summary

| adjudication | count | raw items |
|---|---:|---|
| accepted | 7 | 1, 3, 4, 7, 8, 9, 11 |
| narrowed | 3 | 2, 5, 6 |
| corrected | 2 | 10, 12 |

No item is marked `gold`. `expert_adjudication` is complete for this regression
run; the raw report remains available for future calibration and error analysis.
