import copy
import importlib.util
import json
from pathlib import Path

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


def load_template() -> dict:
    return json.loads(
        (SKILL_DIR / "assets" / "evidence-bundle.template.json").read_text(encoding="utf-8")
    )


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


def test_russian_style_auditor_ignores_code_and_machine_values() -> None:
    report = STYLE_AUDITOR.audit_text(
        "Статус — `bounded`.\n```text\nworkflow fallback retry\n```\n"
        "Функция `append()` сохраняет запись."
    )

    assert report["valid"] is True
    assert report["counts"]["issues"] == 0
