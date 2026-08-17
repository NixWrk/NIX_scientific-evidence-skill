import copy
import importlib.util
import json
from pathlib import Path

import pytest

from tools.audit_skill import audit_skill


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "scientific-evidence-workflow"
VALIDATOR_PATH = SKILL_DIR / "scripts" / "validate_bundle.py"
STYLE_AUDITOR_PATH = SKILL_DIR / "scripts" / "audit_russian_style.py"

SPEC = importlib.util.spec_from_file_location("scientific_evidence_validate_bundle", VALIDATOR_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

STYLE_SPEC = importlib.util.spec_from_file_location(
    "scientific_evidence_audit_russian_style", STYLE_AUDITOR_PATH
)
assert STYLE_SPEC and STYLE_SPEC.loader
STYLE_AUDITOR = importlib.util.module_from_spec(STYLE_SPEC)
STYLE_SPEC.loader.exec_module(STYLE_AUDITOR)


SCHEMA = json.loads(
    (SKILL_DIR / "assets" / "evidence-bundle.schema.json").read_text(encoding="utf-8")
)


def load_template() -> dict:
    return json.loads(
        (SKILL_DIR / "assets" / "evidence-bundle.template.json").read_text(encoding="utf-8")
    )


def schema_object(*path: str) -> dict:
    """Return the schema object describing a bundle section."""

    node = SCHEMA
    for key in path:
        node = node["properties"][key]
        if node.get("type") == "array":
            node = node["items"]
    return node


def error_text(report: dict) -> str:
    return "\n".join(report["errors"])


def test_skill_is_portable_and_has_no_policy_signals() -> None:
    report = audit_skill(SKILL_DIR)

    assert report["spec_subset_valid"] is True
    assert report["policy_signals"] == {}
    assert report["line_count"] < 500


def test_skill_references_and_assets_exist() -> None:
    required = [
        "references/evidence-contract.md",
        "references/qa-workflow.md",
        "references/literature-review-workflow.md",
        "references/manuscript-workflow.md",
        "references/local-model-compatibility.md",
        "references/journal-pattern-memory.md",
        "references/dissertation-analysis-protocol.md",
        "references/genres/dissertation-literature-review-chapter.md",
        "references/genres/dissertation-methods-chapter.md",
        "references/russian-scientific-style.md",
        "assets/evidence-bundle.schema.json",
        "assets/evidence-bundle.template.json",
        "assets/qa-output.template.md",
        "assets/literature-review-output.template.md",
        "assets/manuscript-output.template.md",
        "assets/dissertation-literature-review-chapter.template.md",
        "assets/dissertation-methods-chapter.template.md",
        "assets/journal-pattern.template.json",
        "scripts/validate_bundle.py",
        "scripts/audit_russian_style.py",
        "agents/openai.yaml",
    ]

    assert all((SKILL_DIR / path).is_file() for path in required)
    json.loads((SKILL_DIR / "assets" / "evidence-bundle.schema.json").read_text(encoding="utf-8"))


SCHEMA_SECTIONS = (
    ((), VALIDATOR.TOP_LEVEL_FIELDS, VALIDATOR.TOP_LEVEL_REQUIRED),
    (("task",), VALIDATOR.TASK_FIELDS, VALIDATOR.TASK_REQUIRED),
    (("sources",), VALIDATOR.SOURCE_FIELDS, VALIDATOR.SOURCE_REQUIRED),
    (("evidence",), VALIDATOR.EVIDENCE_FIELDS, VALIDATOR.EVIDENCE_REQUIRED),
    (("results",), VALIDATOR.RESULT_FIELDS, VALIDATOR.RESULT_REQUIRED),
    (("structure",), VALIDATOR.STRUCTURE_FIELDS, VALIDATOR.STRUCTURE_REQUIRED),
    (("claims",), VALIDATOR.CLAIM_FIELDS, VALIDATOR.CLAIM_REQUIRED),
    (("revisions",), VALIDATOR.REVISION_FIELDS, VALIDATOR.REVISION_REQUIRED),
)

ID_FIELDS = {
    "sources": "source_id",
    "evidence": "evidence_id",
    "results": "result_id",
    "structure": "unit_id",
    "claims": "claim_id",
    "revisions": "revision_id",
}

SCHEMA_ENUMERATIONS = (
    (("task", "mode"), VALIDATOR.MODES),
    (("task", "figure_mode"), VALIDATOR.FIGURE_MODES),
    (("task", "formatting_mode"), VALIDATOR.FORMATTING_MODES),
    (("sources", "representation"), VALIDATOR.REPRESENTATIONS),
    (("evidence", "support_type"), VALIDATOR.SUPPORT_TYPES),
    (("evidence", "verification_status"), VALIDATOR.VERIFICATION_STATUSES),
    (("claims", "claim_type"), VALIDATOR.CLAIM_TYPES),
    (("claims", "certainty"), VALIDATOR.CERTAINTIES),
    (("claims", "status"), VALIDATOR.CLAIM_STATUSES),
    (("claims", "disposition"), VALIDATOR.DISPOSITIONS),
    (("structure", "unit_type"), VALIDATOR.UNIT_TYPES),
    (("structure", "status"), VALIDATOR.UNIT_STATUSES),
    (("revisions", "category"), VALIDATOR.REVISION_CATEGORIES),
    (("revisions", "status"), VALIDATOR.REVISION_STATUSES),
)


@pytest.mark.parametrize("path, fields, required", SCHEMA_SECTIONS)
def test_schema_fields_and_required_sets_match_the_validator(
    path: tuple[str, ...], fields: set, required: tuple
) -> None:
    section = schema_object(*path)

    assert set(section["properties"]) == fields
    assert section["additionalProperties"] is False
    assert sorted(section["required"]) == sorted(required)


@pytest.mark.parametrize("path, allowed", SCHEMA_ENUMERATIONS)
def test_schema_enumerations_match_the_validator(path: tuple[str, ...], allowed: set) -> None:
    section = schema_object(*path[:-1])

    assert set(section["properties"][path[-1]]["enum"]) == allowed


def test_schema_identifier_pattern_matches_the_validator() -> None:
    identifier = SCHEMA["$defs"]["identifier"]

    assert identifier["pattern"] == VALIDATOR.ID_PATTERN.pattern
    for section, id_field in ID_FIELDS.items():
        assert schema_object(section)["properties"][id_field] == {"$ref": "#/$defs/identifier"}


def test_schema_manuscript_conditionals_are_mode_gated() -> None:
    """Figure and formatting rules must not leak into qa or literature_review."""

    conditionals = schema_object("task")["allOf"]
    manuscript_gate = {"$ref": "#/$defs/manuscript_mode"}

    assert SCHEMA["$defs"]["manuscript_mode"]["properties"]["mode"]["const"] == "manuscript"
    assert len(conditionals) == 4
    for rule in conditionals:
        condition = rule["if"]
        assert condition == manuscript_gate or manuscript_gate in condition["allOf"]

    without_figures = next(
        rule
        for rule in conditionals
        if rule["if"] != manuscript_gate
        and any(
            branch.get("properties", {}).get("figure_mode", {}).get("const") == "without_figures"
            for branch in rule["if"]["allOf"]
        )
    )
    assert without_figures["then"] == {"not": {"required": ["figure_source_ids"]}}


@pytest.mark.parametrize(
    "bundle_path",
    [
        SKILL_DIR / "assets" / "evidence-bundle.template.json",
        ROOT / "experiments" / "EXP-0024-breath-geometry-manuscript" / "evidence-bundle.json",
    ],
    ids=["template", "EXP-0024"],
)
def test_schema_accepts_bundles_that_the_validator_accepts(bundle_path: Path) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

    assert VALIDATOR.validate_bundle(bundle)["valid"] is True
    jsonschema.validate(bundle, SCHEMA)


def test_schema_accepts_a_bundle_carrying_structure_records() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    bundle = with_structure(load_template())
    bundle["claims"][0].update(
        {"claim_type": "structural", "evidence_ids": [], "structure_ids": ["SEC-3.4"]}
    )

    assert VALIDATOR.validate_bundle(bundle)["valid"] is True
    jsonschema.validate(bundle, SCHEMA)


CARD_SPEC = importlib.util.spec_from_file_location(
    "scientific_evidence_validate_card", SKILL_DIR / "scripts" / "validate_normative_card.py"
)
assert CARD_SPEC and CARD_SPEC.loader
CARD_VALIDATOR = importlib.util.module_from_spec(CARD_SPEC)
CARD_SPEC.loader.exec_module(CARD_VALIDATOR)

CARD_DIR = SKILL_DIR / "references" / "normative-patterns"


def load_card(name: str) -> dict:
    return json.loads((CARD_DIR / f"{name}.json").read_text(encoding="utf-8"))


def test_stored_normative_cards_validate() -> None:
    cards = sorted(CARD_DIR.glob("*.json"))

    assert cards
    for path in cards:
        report = CARD_VALIDATOR.validate_card(json.loads(path.read_text(encoding="utf-8")))
        assert report["valid"] is True, f"{path.name}: {report['errors']}"
        assert report["warnings"] == [], f"{path.name}: {report['warnings']}"


def test_a_catalogue_card_may_not_carry_requirements() -> None:
    """The rule the card validator exists for.

    A registry entry establishes a designation and a status. Letting it carry
    requirements would put a standard's rules in hand on the strength of its
    name alone.
    """

    card = load_card("NORM-GOST-8.417-2024-001")
    assert card["provenance"]["source_kind"] == "catalogue_card"
    assert card["requirements"] == []

    card["requirements"] = [
        {
            "requirement_id": "REQ-001",
            "topic": "единицы",
            "statement": "Единицы пишутся через пробел после числа.",
            "locator": "раздел 5",
            "observation": "observed",
            "binding": "mandatory",
        }
    ]
    report = CARD_VALIDATOR.validate_card(card)

    assert report["valid"] is False
    assert "cannot carry requirements" in "\n".join(report["errors"])


def test_a_second_card_is_added_beside_the_first_and_never_over_it() -> None:
    """One document may hold several cards; none may quietly replace another.

    GOST 8.417-2024 has two: one built from the Rosstandart registry entry,
    which establishes the designation and status, and one built from the text,
    which carries the rules. Reading the text does not make the first record
    wrong, so it stays. The failure this guards is the tempting one — writing
    the text card over the catalogue card, which would erase the record of
    what was known before the file was in hand.

    The filename must equal the pattern id, because that is what makes an
    overwrite impossible by accident rather than by care.
    """

    cards = {path.name: json.loads(path.read_text(encoding="utf-8")) for path in CARD_DIR.glob("*.json")}

    assert cards
    for name, card in cards.items():
        assert name == f"{card['pattern_id']}.json", f"{name}: filename does not match its pattern id"

    by_document: dict[str, list[dict]] = {}
    for card in cards.values():
        by_document.setdefault(card["document_id"], []).append(card)

    shared = {doc: group for doc, group in by_document.items() if len(group) > 1}
    assert "GOST-8.417-2024" in shared, "the two-card case this invariant is about has disappeared"

    for document_id, group in shared.items():
        hashes = {card["provenance"]["content_hash"] for card in group}
        assert len(hashes) == len(group), (
            f"{document_id}: two cards hash the same file, so one of them cards nothing new"
        )
        kinds = [card["provenance"]["source_kind"] for card in group]
        for card in group:
            if card["provenance"]["source_kind"] in {"catalogue_card", "index_page"}:
                assert not card["requirements"], f"{card['pattern_id']}: identity card carrying rules"
        assert "document" in kinds, (
            f"{document_id}: several cards and not one of them reads the text"
        )


def test_a_defended_example_cannot_bind_anyone() -> None:
    """A precedent is not a rule.

    An accepted work shows what one council let through. Letting its card
    carry a mandatory requirement is how "my predecessor did it this way"
    becomes "this is required", which no example can establish.
    """

    card = load_card("NORM-EXAMPLE-SATANENKO-2026-001")
    assert card["tier"] == 7
    assert {item["binding"] for item in card["requirements"]} == {"observed_practice"}

    for binding in ("mandatory", "recommended", "conditional"):
        broken = copy.deepcopy(card)
        broken["requirements"][0]["binding"] = binding
        broken["requirements"][0]["applies_to"] = "нечто"
        report = CARD_VALIDATOR.validate_card(broken)
        assert report["valid"] is False, binding
        assert "would turn a precedent into a rule" in "\n".join(report["errors"]), binding


def test_observed_practice_belongs_only_to_an_example() -> None:
    card = load_card("NORM-GOST-R-7.0.11-2011-001")
    card["requirements"][0]["binding"] = "observed_practice"

    report = CARD_VALIDATOR.validate_card(card)

    assert report["valid"] is False
    assert "belongs to a defended example" in "\n".join(report["errors"])


def test_a_requirement_needs_a_locator_and_an_honest_observation() -> None:
    card = load_card("NORM-BMSTU-DISS-REQ-001")
    requirement = copy.deepcopy(card["requirements"][0])
    requirement.update({"requirement_id": "REQ-900", "locator": "", "observation": "uncertain"})
    card["requirements"].append(requirement)

    report = CARD_VALIDATOR.validate_card(card)
    errors = "\n".join(report["errors"])

    assert report["valid"] is False
    assert "locator: expected a non-empty string" in errors
    assert "note: required when the observation is uncertain" in errors


def test_a_document_card_must_say_what_it_does_not_settle() -> None:
    card = load_card("NORM-BMSTU-DISS-REQ-001")
    card["not_observed"] = []

    report = CARD_VALIDATOR.validate_card(card)

    assert report["valid"] is True
    assert any("no absent feature is recorded" in warning for warning in report["warnings"])


def test_the_council_card_records_its_conflicts() -> None:
    """Discrepancies found while reading are kept, not smoothed."""

    card = load_card("NORM-BMSTU-DISS-REQ-001")

    assert card["tier"] == 3
    assert len(card["conflicts"]) >= 3
    assert any("7.0.5" in conflict for conflict in card["conflicts"])
    uncertain = [r for r in card["requirements"] if r["observation"] == "uncertain"]
    assert uncertain and all(r["note"] for r in uncertain)


def test_stored_journal_patterns_are_versioned_and_provenanced() -> None:
    pattern_dir = SKILL_DIR / "references" / "journal-patterns"
    patterns = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(pattern_dir.glob("*.json"))
    ]

    assert patterns
    bmre = next(
        pattern for pattern in patterns if pattern["pattern_id"] == "JOURNAL-PATTERN-BMRE-001"
    )
    assert bmre["record_version"] == "v2"
    assert any(
        "Treat a separate Discussion section as optional" in note
        for note in bmre["application_notes"]
    )
    for pattern in patterns:
        assert pattern["schema_version"] == "1.0"
        assert pattern["record_version"]
        assert pattern["provenance"]["content_hash"].startswith("sha256:")
        assert "narrative_structure_and_language" in pattern["patterns"]


def test_product_metadata_is_optional_and_has_no_tool_dependency() -> None:
    metadata = (SKILL_DIR / "agents" / "openai.yaml").read_text(encoding="utf-8")

    assert "$scientific-evidence-workflow" in metadata
    assert "dependencies:" not in metadata
    assert "mcp" not in metadata.lower()


def test_valid_qa_template_passes() -> None:
    report = VALIDATOR.validate_bundle(load_template())

    assert report["valid"] is True
    assert report["errors"] == []
    assert report["counts"] == {
        "sources": 1,
        "evidence": 1,
        "results": 0,
        "structure": 0,
        "claims": 1,
        "revisions": 0,
        "supported_claims": 1,
        "bounded_claims": 0,
        "unsupported_claims": 0,
        "conflicted_claims": 0,
    }


def test_unknown_source_and_duplicate_evidence_fail() -> None:
    bundle = load_template()
    duplicate = copy.deepcopy(bundle["evidence"][0])
    duplicate["source_id"] = "SRC-MISSING"
    bundle["evidence"].append(duplicate)

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "duplicate identifier 'EV-001'" in error_text(report)


def test_supported_claim_without_reference_fails() -> None:
    bundle = load_template()
    bundle["claims"][0]["evidence_ids"] = []

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "supported claim requires evidence or result references" in error_text(report)


def test_bounded_claim_requires_boundary_and_allowed_disposition() -> None:
    bundle = load_template()
    claim = bundle["claims"][0]
    claim["status"] = "bounded"
    claim["disposition"] = "keep"
    claim["boundary"] = None

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "bounded claim must use 'hedge' or 'keep_with_boundary'" in error_text(report)
    assert "boundary: required for bounded claim" in error_text(report)


def test_conflicted_claim_requires_two_references_and_disclosure() -> None:
    bundle = load_template()
    claim = bundle["claims"][0]
    claim["status"] = "conflicted"
    claim["certainty"] = "conflicted"
    claim["disposition"] = "keep"

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires at least two distinct references" in error_text(report)
    assert "must use 'disclose_conflict'" in error_text(report)


def test_numeric_qa_claim_can_use_evidence_value() -> None:
    bundle = load_template()
    bundle["evidence"][0]["value"] = "7/10"
    bundle["evidence"][0]["unit"] = "participants"
    bundle["claims"][0]["claim_type"] = "numeric"

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is True


def test_manuscript_results_number_requires_frozen_result() -> None:
    bundle = load_template()
    bundle["task"]["mode"] = "manuscript"
    bundle["task"]["figure_mode"] = "without_figures"
    bundle["task"]["formatting_mode"] = "section_only"
    claim = bundle["claims"][0]
    claim["claim_type"] = "numeric"
    claim["output_section"] = "Results"
    bundle["evidence"][0]["value"] = 7

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "manuscript Results numeric claim requires result_ids" in error_text(report)


def test_manuscript_results_number_passes_with_frozen_result() -> None:
    bundle = load_template()
    bundle["task"]["mode"] = "manuscript"
    bundle["task"]["figure_mode"] = "without_figures"
    bundle["task"]["formatting_mode"] = "section_only"
    bundle["sources"][0]["representation"] = "data"
    bundle["results"] = [
        {
            "result_id": "RES-001",
            "source_id": "SRC-EXAMPLE-001",
            "locator": "results.csv:row=2:column=value",
            "value": 7,
            "unit": "participants",
            "version": "sha256:example",
            "analysis": "supplied count",
        }
    ]
    claim = bundle["claims"][0]
    claim["claim_type"] = "numeric"
    claim["output_section"] = "Results"
    claim["result_ids"] = ["RES-001"]

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is True
    assert report["counts"]["results"] == 1


def test_manuscript_requires_figure_and_formatting_modes() -> None:
    bundle = load_template()
    bundle["task"]["mode"] = "manuscript"

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "figure_mode" in error_text(report)
    assert "formatting_mode" in error_text(report)


def test_journal_formatting_requires_stored_pattern_and_example_source() -> None:
    bundle = load_template()
    bundle["task"].update(
        {
            "mode": "manuscript",
            "figure_mode": "without_figures",
            "formatting_mode": "journal_example",
        }
    )

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "journal_pattern_id" in error_text(report)
    assert "journal_example_source_id" in error_text(report)


def test_manuscript_with_figures_requires_in_scope_figure_sources() -> None:
    bundle = load_template()
    bundle["task"].update(
        {
            "mode": "manuscript",
            "figure_mode": "with_figures",
            "formatting_mode": "section_only",
        }
    )

    missing_report = VALIDATOR.validate_bundle(bundle)
    assert missing_report["valid"] is False
    assert "with_figures requires a non-empty list" in error_text(missing_report)

    bundle["task"]["figure_source_ids"] = ["SRC-EXAMPLE-001"]
    present_report = VALIDATOR.validate_bundle(bundle)
    assert present_report["valid"] is True


def test_manuscript_without_figures_rejects_figure_sources() -> None:
    bundle = load_template()
    bundle["task"].update(
        {
            "mode": "manuscript",
            "figure_mode": "without_figures",
            "figure_source_ids": ["SRC-EXAMPLE-001"],
            "formatting_mode": "section_only",
        }
    )

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "must be omitted" in error_text(report)


def test_rejected_evidence_cannot_support_claim() -> None:
    bundle = load_template()
    bundle["evidence"][0]["verification_status"] = "rejected"

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "rejected evidence cannot support a claim" in error_text(report)


def test_supported_limitation_can_use_limitation_evidence() -> None:
    bundle = load_template()
    bundle["evidence"][0]["support_type"] = "limitation"
    bundle["claims"][0]["claim_type"] = "limitation"
    bundle["claims"][0]["text"] = "The supplied source does not establish the stronger claim."

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is True


def test_non_limitation_claim_cannot_use_only_limitation_evidence() -> None:
    bundle = load_template()
    bundle["evidence"][0]["support_type"] = "limitation"

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "cannot rely only on contrary or limitation evidence" in error_text(report)


def with_structure(bundle: dict, status: str = "final") -> dict:
    bundle["structure"] = [
        {
            "unit_id": "CH-3",
            "unit_type": "chapter",
            "label": "3",
            "title": "Результаты",
            "parent_id": None,
            "document": "dissertation",
            "status": status,
        },
        {
            "unit_id": "SEC-3.4",
            "unit_type": "section",
            "label": "3.4",
            "title": None,
            "parent_id": "CH-3",
            "document": "dissertation",
            "status": status,
        },
    ]
    return bundle


def test_structural_claim_is_established_by_the_units_it_names() -> None:
    bundle = with_structure(load_template())
    claim = bundle["claims"][0]
    claim.update(
        {
            "text": "Положение 2 обосновано в разделе 3.4.",
            "claim_type": "structural",
            "evidence_ids": [],
            "structure_ids": ["SEC-3.4"],
        }
    )

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is True
    assert report["counts"]["structure"] == 2


def test_structural_claim_requires_a_unit() -> None:
    bundle = with_structure(load_template())
    bundle["claims"][0].update({"claim_type": "structural", "structure_ids": []})

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "required for a structural claim" in error_text(report)


def test_structural_claim_cannot_rest_on_a_planned_unit() -> None:
    bundle = with_structure(load_template(), status="planned")
    bundle["claims"][0].update(
        {"claim_type": "structural", "evidence_ids": [], "structure_ids": ["SEC-3.4"]}
    )

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "cannot rest on planned unit 'SEC-3.4'" in error_text(report)


def test_internal_reference_does_not_support_an_ordinary_claim() -> None:
    """The laundering path: a section named instead of evidence cited."""

    bundle = with_structure(load_template())
    bundle["claims"][0].update({"evidence_ids": [], "structure_ids": ["SEC-3.4"]})

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "supported claim requires evidence or result references" in error_text(report)


def test_unknown_and_self_referencing_units_fail() -> None:
    bundle = with_structure(load_template())
    bundle["claims"][0]["structure_ids"] = ["SEC-9.9"]
    bundle["structure"][1]["parent_id"] = "SEC-3.4"

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "unknown unit 'SEC-9.9'" in error_text(report)
    assert "a unit cannot contain itself" in error_text(report)


def test_cyclic_parent_chain_fails() -> None:
    bundle = with_structure(load_template())
    bundle["structure"][0]["parent_id"] = "SEC-3.4"

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "structure[CH-3]: parent chain closes on itself" in error_text(report)
    assert "structure[SEC-3.4]: parent chain closes on itself" in error_text(report)


def test_bundle_without_structure_stays_valid() -> None:
    """Existing bundles predate the structure ledger and must keep validating."""

    bundle = load_template()
    bundle.pop("structure")

    assert VALIDATOR.validate_bundle(bundle)["valid"] is True


def add_source(bundle: dict, index: int) -> dict:
    """Append one more source with a matching evidence record."""

    source_id = f"SRC-EXAMPLE-{index:03d}"
    bundle["sources"].append(
        {
            "source_id": source_id,
            "title": f"Supplied source {index}",
            "content_hash": None,
            "representation": "text",
            "local_ref": f"local/source-{index:03d}.txt",
            "version": "v1",
        }
    )
    bundle["task"]["input_scope"].append(source_id)
    bundle["evidence"].append(
        {
            "evidence_id": f"EV-{index:03d}",
            "source_id": source_id,
            "locator": "section:results/paragraph:1",
            "claim": "The supplied source reports the stated observation.",
            "support_type": "direct",
            "fragment": None,
            "value": None,
            "unit": None,
            "study_context": "Use the supplied design and sample description.",
            "limitations": "Do not generalize beyond the supplied context.",
            "verification_status": "verified",
        }
    )
    return bundle


def annotation_bundle() -> dict:
    bundle = load_template()
    bundle["task"]["genre"] = "article-annotation"
    return bundle


def micro_review_bundle() -> dict:
    bundle = load_template()
    bundle["task"].update({"mode": "literature_review", "genre": "micro-review"})
    return add_source(bundle, 2)


def stage_report_bundle() -> dict:
    bundle = load_template()
    bundle["task"].update({"mode": "record", "genre": "stage-report"})
    bundle["sources"][0]["representation"] = "data"
    bundle["results"] = [
        {
            "result_id": "RES-001",
            "source_id": "SRC-EXAMPLE-001",
            "locator": "results.csv:row=2:column=value",
            "value": 7,
            "unit": "participants",
            "version": "sha256:example",
            "analysis": "supplied count",
        }
    ]
    return bundle


def record_bundle(genre: str, representation: str = "protocol") -> dict:
    bundle = load_template()
    bundle["task"].update({"mode": "record", "genre": genre})
    bundle["sources"][0]["representation"] = representation
    return bundle


def experiment_bundle() -> dict:
    return record_bundle("experiment-description")


def procedure_bundle() -> dict:
    return record_bundle("procedure-record")


def decision_bundle() -> dict:
    return record_bundle("decision-log", representation="text")


def presentation_bundle() -> dict:
    bundle = stage_report_bundle()
    bundle["task"].update({"genre": "stage-presentation", "figure_mode": "without_figures"})
    return bundle


def dissertation_outline_bundle() -> dict:
    bundle = record_bundle("dissertation-outline", representation="organizational")
    bundle["structure"] = [
        {
            "unit_id": "CH-1",
            "unit_type": "chapter",
            "label": "1",
            "title": "Обзор и постановка задачи",
            "parent_id": None,
            "document": "dissertation",
            "status": "planned",
        },
        {
            "unit_id": "SEC-1.1",
            "unit_type": "section",
            "label": "1.1",
            "title": "Состояние вопроса",
            "parent_id": "CH-1",
            "document": "dissertation",
            "status": "planned",
        },
    ]
    bundle["claims"][0].update(
        {
            "text": "Раздел 1.1 планируется как обзор состояния вопроса.",
            "claim_type": "structural",
            "certainty": "uncertain",
            "evidence_ids": [],
            "result_ids": [],
            "structure_ids": ["SEC-1.1"],
            "status": "unsupported",
            "disposition": "request_input",
        }
    )
    return bundle


def dissertation_introduction_bundle() -> dict:
    bundle = load_template()
    bundle["task"].update(
        {
            "mode": "manuscript",
            "genre": "dissertation-introduction",
            "figure_mode": "without_figures",
            "formatting_mode": "section_only",
        }
    )
    add_source(bundle, 2)
    bundle["sources"][1]["representation"] = "organizational"
    bundle["results"] = [
        {
            "result_id": "RES-INTRO-001",
            "source_id": "SRC-EXAMPLE-001",
            "locator": "approved-results.json:RES-INTRO-001",
            "value": "bounded result",
            "unit": None,
            "version": "v1",
            "analysis": "approved analysis",
            "approved": True,
        }
    ]
    bundle["structure"] = [
        {
            "unit_id": "SEC-INTRO",
            "unit_type": "section",
            "label": "Введение",
            "title": "Введение",
            "parent_id": None,
            "document": "dissertation",
            "status": "drafted",
        },
        {
            "unit_id": "TASK-01",
            "unit_type": "task",
            "label": "Задача 1",
            "title": "Установить проверяемую зависимость",
            "parent_id": "SEC-INTRO",
            "document": "dissertation",
            "status": "drafted",
        },
        {
            "unit_id": "PROP-01",
            "unit_type": "proposition",
            "label": "Положение 1",
            "title": "Проверяемое положение",
            "parent_id": "SEC-INTRO",
            "document": "dissertation",
            "status": "drafted",
        },
    ]

    def claim(
        claim_id: str,
        section: str,
        *,
        evidence_ids: list[str] | None = None,
        result_ids: list[str] | None = None,
        structure_ids: list[str] | None = None,
        status: str = "supported",
        disposition: str = "keep",
        boundary: str | None = None,
    ) -> dict:
        return {
            "claim_id": claim_id,
            "text": f"Проверяемая формулировка раздела {section}.",
            "output_section": section,
            "claim_type": "factual",
            "certainty": "direct" if status == "supported" else "inferred",
            "evidence_ids": evidence_ids or [],
            "result_ids": result_ids or [],
            "structure_ids": structure_ids or ["SEC-INTRO"],
            "status": status,
            "disposition": disposition,
            "boundary": boundary,
            "causal_basis": None,
        }

    bundle["claims"] = [
        claim("CL-REL", "relevance", evidence_ids=["EV-001"]),
        claim("CL-STATE", "state_of_art", evidence_ids=["EV-001"]),
        claim("CL-AIM", "aim", evidence_ids=["EV-001"]),
        claim("CL-TASK", "tasks", evidence_ids=["EV-001"], structure_ids=["TASK-01"]),
        claim(
            "CL-NOV",
            "novelty",
            evidence_ids=["EV-001"],
            result_ids=["RES-INTRO-001"],
            status="bounded",
            disposition="keep_with_boundary",
            boundary="supplied comparison corpus",
        ),
        claim("CL-SIG", "significance", result_ids=["RES-INTRO-001"]),
        claim("CL-METHOD", "methods", evidence_ids=["EV-001"]),
        claim(
            "CL-PROP",
            "propositions",
            result_ids=["RES-INTRO-001"],
            structure_ids=["PROP-01"],
        ),
        claim("CL-VALID", "validity_and_approbation", evidence_ids=["EV-001"]),
    ]
    return bundle


def dissertation_literature_review_bundle() -> dict:
    bundle = load_template()
    bundle["task"].update(
        {
            "mode": "manuscript",
            "genre": "dissertation-literature-review-chapter",
            "figure_mode": "without_figures",
            "formatting_mode": "section_only",
        }
    )
    add_source(bundle, 2)
    add_source(bundle, 3)
    bundle["structure"] = [
        {
            "unit_id": "CH-REVIEW", "unit_type": "chapter", "label": "1",
            "title": "Обзор литературы", "parent_id": None,
            "document": "dissertation", "status": "drafted",
        },
        {
            "unit_id": "SEC-REVIEW", "unit_type": "section", "label": "1.1",
            "title": "Состояние вопроса", "parent_id": "CH-REVIEW",
            "document": "dissertation", "status": "drafted",
        },
    ]

    def claim(claim_id: str, section: str, *, bounded: bool = False) -> dict:
        return {
            "claim_id": claim_id,
            "text": f"Проверяемая формулировка раздела {section}.",
            "output_section": section,
            "claim_type": "interpretive",
            "certainty": "inferred" if bounded else "direct",
            "evidence_ids": ["EV-001"],
            "result_ids": [],
            "structure_ids": ["SEC-REVIEW"],
            "status": "bounded" if bounded else "supported",
            "disposition": "keep_with_boundary" if bounded else "keep",
            "boundary": "frozen three-source corpus" if bounded else None,
            "causal_basis": None,
        }

    bundle["claims"] = [
        claim("CL-REV-SCOPE", "review_scope"),
        claim("CL-REV-FRAME", "conceptual_framework"),
        claim("CL-REV-SYNTHESIS", "thematic_synthesis"),
        claim("CL-REV-CONFLICT", "conflicts_and_limits"),
        claim("CL-REV-GAP", "research_gap", bounded=True),
        claim("CL-REV-CONCLUSION", "chapter_conclusions"),
    ]
    return bundle


def dissertation_methods_bundle() -> dict:
    bundle = load_template()
    bundle["task"].update(
        {
            "mode": "manuscript",
            "genre": "dissertation-methods-chapter",
            "figure_mode": "without_figures",
            "formatting_mode": "section_only",
        }
    )
    bundle["sources"][0]["representation"] = "protocol"
    bundle["structure"] = [
        {
            "unit_id": "CH-METHOD",
            "unit_type": "chapter",
            "label": "2",
            "title": "Методы исследования",
            "parent_id": None,
            "document": "dissertation",
            "status": "drafted",
        },
        {
            "unit_id": "SEC-METHOD",
            "unit_type": "section",
            "label": "2.1",
            "title": "Процедура и обработка данных",
            "parent_id": "CH-METHOD",
            "document": "dissertation",
            "status": "drafted",
        },
    ]

    def claim(claim_id: str, section: str) -> dict:
        return {
            "claim_id": claim_id,
            "text": f"Проверяемая формулировка раздела {section}.",
            "output_section": section,
            "claim_type": "factual",
            "certainty": "direct",
            "evidence_ids": ["EV-001"],
            "result_ids": [],
            "structure_ids": ["SEC-METHOD"],
            "status": "supported",
            "disposition": "keep",
            "boundary": None,
            "causal_basis": None,
        }

    bundle["claims"] = [
        claim("CL-METHOD-SCOPE", "method_scope"),
        claim("CL-METHOD-PROCEDURE", "procedure"),
        claim("CL-METHOD-PROCESSING", "data_processing"),
        claim("CL-METHOD-QUALITY", "quality_control"),
        claim("CL-METHOD-CONCLUSION", "chapter_conclusions"),
    ]
    return bundle


def test_implemented_genres_accept_their_own_shape() -> None:
    builders = (
        annotation_bundle,
        micro_review_bundle,
        stage_report_bundle,
        experiment_bundle,
        procedure_bundle,
        decision_bundle,
        presentation_bundle,
        dissertation_outline_bundle,
        dissertation_introduction_bundle,
        dissertation_literature_review_bundle,
        dissertation_methods_bundle,
    )
    bundle_genres = {
        genre for genre, rules in VALIDATOR.GENRES.items() if rules["bundle_mode"] is not None
    }

    # Historical builders remain regression fixtures. Dissertation genres added
    # later have their own focused builders in test_remaining_dissertation_genres.py.
    built_genres = {build()["task"]["genre"] for build in builders}
    assert built_genres <= bundle_genres
    for build in builders:
        report = VALIDATOR.validate_bundle(build())
        assert report["valid"] is True, f"{build.__name__}: {report['errors']}"


def test_stage_presentation_carries_figure_control_outside_a_manuscript() -> None:
    bundle = presentation_bundle()
    bundle["task"].pop("figure_mode")

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "stage-presentation requires one of" in error_text(report)


def test_stage_presentation_figures_must_trace_to_an_input() -> None:
    bundle = presentation_bundle()
    bundle["task"].update({"figure_mode": "with_figures", "figure_source_ids": ["SRC-ABSENT"]})

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "unknown source 'SRC-ABSENT'" in error_text(report)

    bundle["task"]["figure_source_ids"] = ["SRC-EXAMPLE-001"]
    assert VALIDATOR.validate_bundle(bundle)["valid"] is True


def test_stage_presentation_does_not_take_journal_formatting() -> None:
    """Figure control generalizes; journal formatting stays manuscript-only."""

    bundle = presentation_bundle()

    assert VALIDATOR.validate_bundle(bundle)["valid"] is True
    assert "formatting_mode" not in bundle["task"]


def test_a_card_genre_is_rejected_as_a_bundle_genre() -> None:
    bundle = load_template()
    bundle["task"]["genre"] = "normative-pattern-analysis"

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "not an evidence bundle" in error_text(report)


def test_experiment_description_refuses_a_reconstruction() -> None:
    """Without a protocol or data source the account would come from memory."""

    bundle = record_bundle("experiment-description", representation="html")

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires a source with representation ['data', 'protocol']" in error_text(report)


def test_procedure_record_accepts_a_note_but_not_literature_context() -> None:
    bundle = record_bundle("procedure-record", representation="note")
    assert VALIDATOR.validate_bundle(bundle)["valid"] is True

    bundle["evidence"][0]["support_type"] = "context"
    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "carries no literature context" in error_text(report)


def test_decision_log_takes_no_organizational_record() -> None:
    """The regime is declared as forbidden and must not sit unenforced."""

    rules = VALIDATOR.GENRES["decision-log"]

    assert rules["organizational"] == "forbidden"
    assert rules["source_representations"] is None
    assert rules["bundle_mode"] == "record"


def test_dissertation_literature_review_gap_must_be_bounded() -> None:
    bundle = dissertation_literature_review_bundle()
    gap = next(item for item in bundle["claims"] if item["output_section"] == "research_gap")
    gap.update({"status": "supported", "disposition": "keep", "boundary": None})
    report = VALIDATOR.validate_bundle(bundle)
    assert report["valid"] is False
    assert "literature-review gap must be bounded" in error_text(report)


def test_dissertation_literature_review_requires_three_sources() -> None:
    bundle = dissertation_literature_review_bundle()
    bundle["task"]["input_scope"].pop()
    report = VALIDATOR.validate_bundle(bundle)
    assert report["valid"] is False
    assert "requires at least 3 source(s)" in error_text(report)


def test_dissertation_literature_review_rejects_own_results() -> None:
    bundle = dissertation_literature_review_bundle()
    bundle["results"] = [{
        "result_id": "RES-REVIEW-001", "source_id": "SRC-EXAMPLE-001",
        "locator": "results:1", "value": "own result", "unit": None,
        "version": "v1", "analysis": "not literature evidence",
    }]
    report = VALIDATOR.validate_bundle(bundle)
    assert report["valid"] is False
    assert "does not report own research results" in error_text(report)


def test_dissertation_literature_review_requires_textual_evidence() -> None:
    bundle = dissertation_literature_review_bundle()
    bundle["sources"][0]["representation"] = "organizational"
    report = VALIDATOR.validate_bundle(bundle)
    assert report["valid"] is False
    assert "requires in-scope literature evidence" in error_text(report)


def test_dissertation_methods_requires_protocol_or_data() -> None:
    bundle = dissertation_methods_bundle()
    bundle["sources"][0]["representation"] = "note"

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires a source with representation ['data', 'protocol']" in error_text(report)


def test_dissertation_methods_claim_cannot_rest_on_literature_alone() -> None:
    bundle = dissertation_methods_bundle()
    add_source(bundle, 2)
    bundle["evidence"].append(
        {
            "evidence_id": "EV-LITERATURE",
            "source_id": "SRC-EXAMPLE-002",
            "locator": "article:methods",
            "claim": "Published contextual method description.",
            "support_type": "context",
            "fragment": None,
            "value": None,
            "unit": None,
            "study_context": "Literature context only.",
            "limitations": "Does not record what this dissertation performed.",
            "verification_status": "verified",
        }
    )
    bundle["claims"][0]["evidence_ids"] = ["EV-LITERATURE"]

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires protocol/data evidence or an approved result" in error_text(report)


def test_dissertation_methods_evidence_must_be_inside_input_scope() -> None:
    bundle = dissertation_methods_bundle()
    outside = copy.deepcopy(bundle["sources"][0])
    outside.update({"source_id": "SRC-OUTSIDE", "local_ref": "protocol:outside"})
    bundle["sources"].append(outside)
    bundle["evidence"].append(
        {
            "evidence_id": "EV-OUTSIDE",
            "source_id": "SRC-OUTSIDE",
            "locator": "protocol:outside:step-1",
            "claim": "Method statement from a source outside task.input_scope.",
            "support_type": "method",
            "fragment": None,
            "value": None,
            "unit": None,
            "study_context": "Out-of-scope protocol.",
            "limitations": None,
            "verification_status": "verified",
        }
    )
    bundle["claims"][0]["evidence_ids"] = ["EV-OUTSIDE"]

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires protocol/data evidence or an approved result" in error_text(report)

def test_dissertation_methods_requires_all_control_sections() -> None:
    bundle = dissertation_methods_bundle()
    bundle["claims"] = [
        item for item in bundle["claims"] if item["output_section"] != "quality_control"
    ]

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires output_section 'quality_control'" in error_text(report)


def test_dissertation_methods_requires_chapter_and_section_units() -> None:
    bundle = dissertation_methods_bundle()
    bundle["structure"] = [bundle["structure"][0]]
    for claim in bundle["claims"]:
        claim["structure_ids"] = ["CH-METHOD"]

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires a 'section' unit" in error_text(report)


def test_dissertation_methods_requires_internal_addresses() -> None:
    bundle = dissertation_methods_bundle()
    bundle["claims"][0]["structure_ids"] = []

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires an addressable output unit" in error_text(report)


def test_dissertation_outline_requires_organizational_record() -> None:
    bundle = dissertation_outline_bundle()
    bundle["sources"][0]["representation"] = "note"

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires a source with representation ['organizational']" in error_text(report)

def test_dissertation_outline_requires_chapter_and_section_units() -> None:
    bundle = dissertation_outline_bundle()
    bundle["structure"] = [bundle["structure"][0]]
    bundle["claims"][0]["structure_ids"] = ["CH-1"]

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires a 'section' unit" in error_text(report)


def test_planned_outline_mapping_must_remain_a_proposal() -> None:
    bundle = dissertation_outline_bundle()
    assert VALIDATOR.validate_bundle(bundle)["valid"] is True

    bundle["claims"][0].update({"status": "supported", "disposition": "keep"})
    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "cannot rest on planned unit 'SEC-1.1'" in error_text(report)


def test_dissertation_introduction_requires_every_normative_element() -> None:
    bundle = dissertation_introduction_bundle()
    bundle["claims"] = [
        item for item in bundle["claims"] if item["output_section"] != "methods"
    ]

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires output_section 'methods'" in error_text(report)


def test_dissertation_introduction_requires_organizational_record() -> None:
    bundle = dissertation_introduction_bundle()
    bundle["sources"][1]["representation"] = "text"

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires a source with representation ['organizational']" in error_text(report)


def test_dissertation_introduction_requires_internal_addresses() -> None:
    bundle = dissertation_introduction_bundle()
    bundle["claims"][0]["structure_ids"] = []

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires an addressable output unit" in error_text(report)


def test_dissertation_introduction_requires_exactly_one_aim() -> None:
    bundle = dissertation_introduction_bundle()
    duplicate = copy.deepcopy(
        next(item for item in bundle["claims"] if item["output_section"] == "aim")
    )
    duplicate["claim_id"] = "CL-AIM-002"
    bundle["claims"].append(duplicate)

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires exactly one supported or bounded aim" in error_text(report)


def test_dissertation_novelty_must_name_its_boundary() -> None:
    bundle = dissertation_introduction_bundle()
    novelty = next(item for item in bundle["claims"] if item["output_section"] == "novelty")
    novelty.update({"status": "supported", "disposition": "keep", "boundary": None})

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "novelty must be bounded" in error_text(report)


def test_dissertation_proposition_requires_result_and_structure_anchor() -> None:
    bundle = dissertation_introduction_bundle()
    proposition = next(
        item for item in bundle["claims"] if item["output_section"] == "propositions"
    )
    proposition.update({"result_ids": [], "structure_ids": ["SEC-INTRO"]})

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "proposition requires result_ids" in error_text(report)


def test_accepted_semantic_revision_is_traceable() -> None:
    bundle = dissertation_introduction_bundle()
    bundle["revisions"] = [
        {
            "revision_id": "REV-INTRO-001",
            "locator": "Введение/Актуальность/абзац 1",
            "structure_ids": ["SEC-INTRO"],
            "claim_ids": ["CL-REL"],
            "original": "Метод полностью решает задачу.",
            "corrected": "В представленном наборе метод решает указанную задачу.",
            "reason": "Сужена область применимости до проверенного набора.",
            "category": "evidence_boundary",
            "evidence_ids": ["EV-001"],
            "result_ids": [],
            "status": "accepted",
        }
    ]

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is True
    assert report["counts"]["revisions"] == 1


def test_semantic_revision_cannot_supply_its_own_evidence() -> None:
    bundle = dissertation_introduction_bundle()
    bundle["revisions"] = [
        {
            "revision_id": "REV-INTRO-001",
            "locator": "Введение/Актуальность/абзац 1",
            "structure_ids": ["SEC-INTRO"],
            "claim_ids": ["CL-REL"],
            "original": "Метод полностью решает задачу.",
            "corrected": "Метод решает задачу.",
            "reason": "Предлагается научное уточнение.",
            "category": "scientific_precision",
            "evidence_ids": [],
            "result_ids": [],
            "status": "accepted",
        }
    ]

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires evidence_ids or result_ids" in error_text(report)


def test_grammar_revision_may_be_evidence_neutral() -> None:
    bundle = dissertation_introduction_bundle()
    bundle["revisions"] = [
        {
            "revision_id": "REV-INTRO-002",
            "locator": "Введение/Цель",
            "structure_ids": ["SEC-INTRO"],
            "claim_ids": ["CL-AIM"],
            "original": "Целью является разработка метода.",
            "corrected": "Цель исследования — разработать метод.",
            "reason": "Устранена тяжёлая синтаксическая конструкция без изменения смысла.",
            "category": "grammar",
            "evidence_ids": [],
            "result_ids": [],
            "status": "accepted",
        }
    ]

    assert VALIDATOR.validate_bundle(bundle)["valid"] is True


def test_revision_references_must_resolve() -> None:
    bundle = dissertation_introduction_bundle()
    bundle["revisions"] = [
        {
            "revision_id": "REV-INTRO-003",
            "locator": "Введение/Новизна",
            "structure_ids": ["SEC-ABSENT"],
            "claim_ids": ["CL-ABSENT"],
            "original": "Старый текст.",
            "corrected": "Новый текст.",
            "reason": "Проверка ссылочной целостности.",
            "category": "logic",
            "evidence_ids": ["EV-ABSENT"],
            "result_ids": [],
            "status": "proposed",
        }
    ]

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "unknown identifier 'SEC-ABSENT'" in error_text(report)
    assert "unknown identifier 'CL-ABSENT'" in error_text(report)
    assert "unknown identifier 'EV-ABSENT'" in error_text(report)


def test_bundle_without_revision_ledger_stays_valid() -> None:
    bundle = load_template()
    bundle.pop("revisions")

    assert VALIDATOR.validate_bundle(bundle)["valid"] is True


def test_preliminary_dissertation_protocol_is_versioned() -> None:
    protocol = (
        SKILL_DIR / "references" / "dissertation-analysis-protocol.md"
    ).read_text(encoding="utf-8")

    assert "protocol_id: PSAD-2.2.12" in protocol
    assert "version: 0.2.0" in protocol
    assert "status: preliminary" in protocol
    assert "Three independent locators" in protocol
    assert "source file" in protocol


def test_unknown_genre_is_rejected() -> None:
    bundle = load_template()
    bundle["task"]["genre"] = "genre-that-is-not-implemented"

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "unknown or unimplemented genre" in error_text(report)


def test_genre_must_match_its_mode() -> None:
    bundle = annotation_bundle()
    bundle["task"]["mode"] = "literature_review"

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "runs in mode 'qa'" in error_text(report)


def test_annotation_is_bounded_to_one_source() -> None:
    report = VALIDATOR.validate_bundle(add_source(annotation_bundle(), 2))

    assert report["valid"] is True
    assert any("at most 1 source" in warning for warning in report["warnings"])


def test_annotation_reports_no_own_results_and_no_internal_references() -> None:
    bundle = annotation_bundle()
    bundle["results"] = [
        {
            "result_id": "RES-001",
            "source_id": "SRC-EXAMPLE-001",
            "locator": "results.csv:row=2",
            "value": 7,
            "unit": None,
            "version": "v1",
            "analysis": None,
        }
    ]
    bundle = with_structure(bundle)
    bundle["claims"][0]["structure_ids"] = ["SEC-3.4"]

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "does not report own research results" in error_text(report)
    assert "carries no internal references" in error_text(report)


def test_micro_review_needs_at_least_two_sources() -> None:
    bundle = micro_review_bundle()
    bundle["task"]["input_scope"] = ["SRC-EXAMPLE-001"]

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires at least 2 source(s)" in error_text(report)


def test_micro_review_warns_above_five_sources() -> None:
    bundle = micro_review_bundle()
    for index in range(3, 8):
        add_source(bundle, index)

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is True
    assert any("at most 5 source(s)" in warning for warning in report["warnings"])


def test_stage_report_requires_own_results() -> None:
    bundle = stage_report_bundle()
    bundle["results"] = []

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "requires own research results" in error_text(report)


def test_recorded_hypothesis_stays_unsupported_and_attributed() -> None:
    bundle = stage_report_bundle()
    bundle["claims"].append(
        {
            "claim_id": "CL-002",
            "text": "Расхождение вызвано дискретизацией растра.",
            "output_section": "Working hypotheses",
            "claim_type": "hypothesis",
            "certainty": "uncertain",
            "evidence_ids": [],
            "result_ids": [],
            "status": "unsupported",
            "disposition": "request_input",
            "boundary": None,
            "causal_basis": None,
            "attribution": "исследователь, 2026-08-14",
        }
    )

    assert VALIDATOR.validate_bundle(bundle)["valid"] is True


def test_hypothesis_cannot_be_asserted_or_left_unattributed() -> None:
    bundle = stage_report_bundle()
    claim = bundle["claims"][0]
    claim.update({"claim_type": "hypothesis", "status": "supported", "disposition": "keep"})

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "attribution: required for a hypothesis" in error_text(report)
    assert "must keep status 'unsupported'" in error_text(report)
    assert "must use disposition 'request_input'" in error_text(report)


def test_genre_references_and_templates_exist() -> None:
    """A card genre ships a JSON scaffold; a bundle genre ships a Markdown one."""

    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    for genre_id, rules in VALIDATOR.GENRES.items():
        assert (SKILL_DIR / "references" / "genres" / f"{genre_id}.md").is_file(), genre_id
        assert f"`{genre_id}`" in skill, genre_id
        if rules["bundle_mode"] is None:
            assert (SKILL_DIR / "assets" / "normative-pattern.template.json").is_file(), genre_id
        else:
            assert (SKILL_DIR / "assets" / f"{genre_id}.template.md").is_file(), genre_id


def test_unknown_fields_fail_closed() -> None:
    bundle = load_template()
    bundle["sources"][0]["external_url"] = "not-allowed"

    report = VALIDATOR.validate_bundle(bundle)

    assert report["valid"] is False
    assert "unexpected field 'external_url'" in error_text(report)


def test_russian_style_reference_is_required_for_russian_output() -> None:
    skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    reference = (SKILL_DIR / "references" / "russian-scientific-style.md").read_text(
        encoding="utf-8"
    )

    assert "references/russian-scientific-style.md" in skill
    assert "Не добавляй и не удаляй научные утверждения" in reference
    assert "отсутствие срабатываний не подтверждает" in reference


def test_russian_style_auditor_accepts_normative_prose() -> None:
    report = STYLE_AUDITOR.audit_text(
        "Измерения выполнены на выдохе. Толщина мышцы составила 2,4 мм."
    )

    assert report["valid"] is True
    assert report["counts"] == {"errors": 0, "warnings": 0, "issues": 0}


def test_russian_style_auditor_flags_mixed_english_and_hybrid_verbs() -> None:
    report = STYLE_AUDITOR.audit_text(
        "Это narrative review. Затем данные нужно парсить и выполнить workflow."
    )

    assert report["valid"] is False
    assert report["counts"]["errors"] == 3
    assert {issue["code"] for issue in report["issues"]} == {
        "mixed_english",
        "hybrid_verb",
    }


def test_russian_style_auditor_reports_cliches_as_warnings() -> None:
    report = STYLE_AUDITOR.audit_text(
        "Важно отметить, что метод играет ключевую роль."
    )

    assert report["valid"] is True
    assert report["counts"] == {"errors": 0, "warnings": 2, "issues": 2}


def test_russian_style_auditor_warns_about_unlisted_latin_prose() -> None:
    report = STYLE_AUDITOR.audit_text(
        "Метод оценивает respiratory drive при вдохе."
    )

    assert report["valid"] is True
    assert report["counts"] == {"errors": 0, "warnings": 2, "issues": 2}
    assert {issue["match"] for issue in report["issues"]} == {"respiratory", "drive"}


def test_russian_style_auditor_flags_mixed_script_word_formation() -> None:
    report = STYLE_AUDITOR.audit_text(
        "Использована Zotero-подколлекция и создана skill-ветка."
    )

    assert report["valid"] is False
    assert report["counts"] == {"errors": 2, "warnings": 0, "issues": 2}
    assert {issue["code"] for issue in report["issues"]} == {"mixed_script_word"}


def test_scholarly_latin_is_not_flagged_as_an_english_intrusion() -> None:
    """`et al.` and `in vivo` are normative in Russian scientific prose."""

    report = STYLE_AUDITOR.audit_text(
        "Согласно данным (Smith et al., 2020), толщина диафрагмы in vivo "
        "составила 2,4 мм. Измерения in situ не выполнялись."
    )

    assert report["counts"] == {"errors": 0, "warnings": 0, "issues": 0}


def test_core_profile_applies_alone_and_records_itself() -> None:
    report = STYLE_AUDITOR.audit_text("Измерения выполнены на выдохе.")

    assert report["profiles"] == ["core"]


def test_domain_vocabulary_applies_only_when_its_profile_is_requested() -> None:
    text = "Измерения выполнены в момент, когда завершается respiratory phase."

    without = STYLE_AUDITOR.audit_text(text)
    with_domain = STYLE_AUDITOR.audit_text(text, ["domain-biomedical-ultrasound"])

    assert not any(issue["code"] == "mixed_english" for issue in without["issues"])
    assert any(
        issue["code"] == "mixed_english" and issue["profile"] == "domain-biomedical-ultrasound"
        for issue in with_domain["issues"]
    )
    assert with_domain["profiles"] == ["core", "domain-biomedical-ultrasound"]


def test_micro_report_profile_flags_a_softened_state() -> None:
    text = "Модуль почти готов. Обнаружено незначительное расхождение. Есть сложности."

    without = STYLE_AUDITOR.audit_text(text)
    with_genre = STYLE_AUDITOR.audit_text(text, ["genre-micro-report"])

    assert without["counts"]["issues"] == 0
    assert {issue["code"] for issue in with_genre["issues"]} == {
        "softened_state",
        "unquantified_deviation",
        "unconditioned_obstacle",
    }
    assert with_genre["valid"] is True


def test_review_profile_flags_uncounted_support_and_prestige() -> None:
    text = (
        "Ряд исследований подтверждает вывод. Работа опубликована в авторитетном "
        "журнале. Противоречий не выявлено."
    )

    without = STYLE_AUDITOR.audit_text(text)
    with_genre = STYLE_AUDITOR.audit_text(text, ["genre-review"])

    assert without["counts"]["issues"] == 0
    assert {issue["code"] for issue in with_genre["issues"]} == {
        "unquantified_support",
        "prestige_as_evidence",
        "absence_as_agreement",
    }


def test_dissertation_profile_flags_unbounded_scientific_formulations() -> None:
    text = (
        "Впервые разработан метод, который не имеет аналогов. "
        "На защиту выносится метод. Метод повышает точность."
    )

    without = STYLE_AUDITOR.audit_text(text)
    with_genre = STYLE_AUDITOR.audit_text(text, ["genre-dissertation"])

    assert without["counts"]["issues"] == 0
    assert {issue["code"] for issue in with_genre["issues"]} == {
        "absolute_novelty",
        "unbounded_first_claim",
        "topic_as_proposition",
        "untraced_improvement",
    }


def test_genre_and_domain_profiles_compose() -> None:
    report = STYLE_AUDITOR.audit_text(
        "Ряд исследований описывает respiratory phase.",
        ["genre-review", "domain-biomedical-ultrasound"],
    )

    assert report["profiles"] == ["core", "genre-review", "domain-biomedical-ultrasound"]
    assert {issue["profile"] for issue in report["issues"]} == {
        "genre-review",
        "domain-biomedical-ultrasound",
    }


def test_unknown_profile_names_the_available_ones() -> None:
    with pytest.raises(FileNotFoundError, match="genre-review"):
        STYLE_AUDITOR.audit_text("Текст.", ["genre-that-does-not-exist"])


def test_genre_language_profiles_pass_the_core_audit() -> None:
    """A genre profile must not use the prose it warns against.

    The auditor cannot tell mention from use, so a profile that quotes a
    forbidden phrase puts it in code formatting like any other literal.

    references/russian-scientific-style.md is deliberately out of scope: it is
    the catalogue of forbidden patterns, so naming them is its subject matter.
    Contorting that file to satisfy the tool would damage the primary reference
    to buy a green check.
    """

    for path in sorted((SKILL_DIR / "references" / "russian").glob("*.md")):
        report = STYLE_AUDITOR.audit_text(path.read_text(encoding="utf-8"))
        assert report["counts"]["issues"] == 0, f"{path.name}: {report['issues']}"


def test_every_shipped_profile_compiles() -> None:
    directory = SKILL_DIR / "scripts" / "russian"
    profile_ids = sorted(path.stem for path in directory.glob("*.json"))

    assert "core" in profile_ids
    ruleset = STYLE_AUDITOR.build_ruleset([pid for pid in profile_ids if pid != "core"])

    assert ruleset.profiles[0] == "core"
    assert len(ruleset.profiles) == len(profile_ids)
    assert all(rule.severity in STYLE_AUDITOR.SEVERITIES for rule in ruleset.rules)


def test_russian_style_auditor_ignores_code_and_machine_values() -> None:
    report = STYLE_AUDITOR.audit_text(
        "Статус — `bounded`.\n```text\nworkflow fallback retry\n```\n"
        "Функция `append()` сохраняет запись."
    )

    assert report["valid"] is True
    assert report["counts"]["issues"] == 0
