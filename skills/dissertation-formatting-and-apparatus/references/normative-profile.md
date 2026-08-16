# Normative profile

Resolve a profile before generating or auditing apparatus.

## Required fields

```json
{
  "profile_id": "PROFILE-...",
  "version": "v1",
  "applies_to": "dissertation",
  "authority_cards": [
    {"card_id": "NORM-...", "requirement_ids": ["REQ-..."]}
  ],
  "citation_standard": "GOST-R-7.0.5-2008",
  "description_standard": "GOST-R-7.0.100-2018",
  "citation_style": null,
  "sorting_strategy": "unspecified",
  "grouping_strategy": "unspecified",
  "sequential_numbering": null,
  "uncited_record_policy": "report",
  "supported_record_types": []
}
```

Use `unspecified` when no applicable requirement settles a choice. A validator
must then omit that check. Do not convert a local preference or defended-work
pattern into a standard requirement.

The current BMSTU profile requires sequential numbering and recommends against
grouping by publication type or dissertation chapter. The existing cards do
not establish alphabetical order or order of first citation.

Coverage is rule- and record-type-specific. Emit `not_assessed` for any type or
field outside the card coverage matrix.

## Title page and TOC authorities

The base dissertation title page resolves
`NORM-GOST-R-7.0.11-2011-001:REQ-007`. Pass local title-page requirements
explicitly as `local_profile.authority_ids`; selecting
`NORM-BMSTU-DISS-REQ-001:REQ-007` makes the applicant signature line
mandatory. Do not report that local authority when it was not selected.

A final single-volume TOC resolves REQ-008 (exact heading text and dot leaders)
and REQ-031 (complete list of main parts with starting pages). REQ-030 and
REQ-032 are conditional multi-volume requirements and remain `not_assessed`
unless the input declares a multi-volume dissertation.
