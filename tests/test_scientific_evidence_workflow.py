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
        "references/russian-scientific-style.md",
        "assets/evidence-bundle.schema.json",
        "assets/evidence-bundle.template.json",
        "assets/qa-output.template.md",
        "assets/literature-review-output.template.md",
        "assets/manuscript-output.template.md",
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
)

ID_FIELDS = {
    "sources": "source_id",
    "evidence": "evidence_id",
    "results": "result_id",
    "structure": "unit_id",
    "claims": "claim_id",
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


def test_implemented_genres_accept_their_own_shape() -> None:
    builders = (
        annotation_bundle,
        micro_review_bundle,
        stage_report_bundle,
        experiment_bundle,
        procedure_bundle,
        decision_bundle,
    )

    assert len(builders) == len(VALIDATOR.GENRES)
    for build in builders:
        report = VALIDATOR.validate_bundle(build())
        assert report["valid"] is True, f"{build.__name__}: {report['errors']}"


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


def test_unknown_genre_is_rejected() -> None:
    bundle = load_template()
    bundle["task"]["genre"] = "dissertation-introduction"

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
    for genre_id in VALIDATOR.GENRES:
        assert (SKILL_DIR / "references" / "genres" / f"{genre_id}.md").is_file(), genre_id
        assert (SKILL_DIR / "assets" / f"{genre_id}.template.md").is_file(), genre_id
        assert f"`{genre_id}`" in (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8"), genre_id


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
        STYLE_AUDITOR.audit_text("Текст.", ["genre-dissertation"])


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
