# Genre: approbation record

`mode: record` · `genre: approbation-record` · organizational evidence required

## Authority boundary

GOST R 7.0.11-2011 includes reliability and approbation among the normative
elements of the dissertation introduction, but it does not authorize inventing
events, publication status, registrations, implementation acts, or a universal
heading layout. Applicable degree and institutional cards determine exact
reporting requirements. This genre records organizational facts; it does not
establish the scientific truth, validity, novelty, or reliability of a claim.

## Purpose

Create a verifiable inventory of conference reports, publications,
registrations, and implementation acts connected to the dissertation. Preserve
the documentary status, dates, identifiers, participant role, and relationship
to dissertation sections without treating existence of the record as scientific
evidence.

## Input

Require organizational records with stable identifiers and locators. Use
verified bibliographic records for publications and supplied regulatory cards
for classification. Scientific literature and own result records are forbidden
as substitutes for organizational proof. Stop on an event, status, role, date,
identifier, or implementation claim absent from the supplied record.

## Canonical control sections

| Function | `output_section` |
|---|---|
| conference reports | `conference_reports` |
| publications and verified statuses | `publication_records` |
| registrations and protected outputs | `registration_records` |
| implementation acts | `implementation_records` |
| links to dissertation units without evidentiary promotion | `approbation_crossrefs` |

All five categories remain addressable in the record. Empty categories are
reported as not evidenced, not filled from assumptions.

## Operations

### Generate

Normalize supplied organizational records, deduplicate them by identifier and
event, classify their status conservatively, and render only verified facts.
Link each record to relevant dissertation units when the link is supplied. Keep
patents and software registration certificates available for any separate
publication-equivalence audit required by the applicable PP-842 profile; do not
reduce that audit to a count of journal articles.

### Critic

Check every name, event, venue, date, role, publication status, identifier, and
implementation statement against organizational records. Flag unsupported or
inflated status and any use of approbation as proof of a scientific claim. Use
comments for missing documentary support; tracked changes are allowed only for
exact factual corrections authorized by a record.

## Procedure

1. Freeze record identifiers, versions, dates, and locators.
2. For conference reports, record event, date, place or format, presentation
   title, role, and evidence only when supplied.
3. For publications, preserve exact bibliographic identity and status; do not
   convert submitted or accepted work into published work.
4. For registrations, preserve type, number, date, holder/authors, and object;
   apply publication equivalence only through the supplied normative rule.
5. For implementation acts, record organization, document identity, date,
   implemented object, and stated scope without inferring effectiveness.
6. Add internal cross-references only to existing dissertation units.
7. Separate the inventory from any scientific claim ledger and label its
   evidence dimension `organizational`.

## Scientific-formulation controls

- “Апробировано”, “представлено”, “опубликовано”, “зарегистрировано”, and
  “внедрено” are different statuses and are never interchangeable.
- Participation in an event does not prove validity, novelty, acceptance, or
  effectiveness of a result.
- An implementation act establishes only the organizational fact and scope
  stated in that act, not a scientific or economic effect unless separately
  evidenced in the proper genre.
- Do not infer author role, publication status, or relation to the dissertation.
- Record every semantic factual correction in the revision ledger.

## Gates and stop conditions

- Every rendered fact cites an organizational record and exact locator.
- Every internal cross-reference resolves to an existing dissertation unit.
- No organizational record is used as evidence of scientific truth.
- All five control sections occur in the record ledger, with unsupported
  categories explicitly marked `not_evidenced`.
- Publication and registration classification follows only a supplied
  applicable normative profile.
- Stop on an unverified event, role, status, date, identifier, or effect claim.

Apply `references/russian/genre-dissertation.md` after the evidence gate and run
the language auditor with `--profile genre-dissertation`. Use
`assets/approbation-record.template.md` for a file artifact.
