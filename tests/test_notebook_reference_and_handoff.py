import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "scientific-evidence-workflow"


def load_module(name: str, relative_path: str):
    path = SKILL / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


HANDOFF = load_module("validate_artifact_handoff", "scripts/validate_artifact_handoff.py")
REFERENCES = load_module(
    "validate_notebook_references", "scripts/validate_notebook_references.py"
)


def handoff_template() -> dict:
    return json.loads(
        (SKILL / "assets" / "artifact-handoff.template.json").read_text(
            encoding="utf-8"
        )
    )


def notebook_with_references() -> dict:
    return {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "Величина определяется по формуле (1) с параметрами из [1].\n",
                    "\\[y = ax \\tag{1}\\]\n",
                    "Исходная таблица: [локальные данные](input.md). "
                    "Запись источника приведена в [списке](#список-литературы).",
                ],
            },
            {
                "cell_type": "markdown",
                "metadata": {"tags": ["bibliography"]},
                "source": [
                    "## Список литературы\n\n",
                    "[1] Author A. Exact source title. Journal. 2024. Vol. 1. P. 1–5.",
                ],
            },
        ],
        "metadata": {
            "scientific_report": {
                "artifact_status": "working",
                "bibliography_status": "complete",
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def rule_ids(report: dict) -> set[str]:
    return {finding["rule_id"] for finding in report["findings"]}


def test_versioned_handoff_template_passes_contract():
    report = HANDOFF.validate_handoff(handoff_template())
    assert report == {"valid": True, "errors": []}


def test_handoff_schema_matches_automation_conflict_gate():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (SKILL / "assets" / "artifact-handoff.schema.json").read_text(
            encoding="utf-8"
        )
    )
    valid = handoff_template()
    jsonschema.validate(valid, schema)

    conflicted = copy.deepcopy(valid)
    conflicted["selection_policy"].update(
        {"status": "conflicted", "conflict_refs": ["a.json", "b.json"]}
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(conflicted, schema)


def test_later_handoff_version_requires_predecessor_reference():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (SKILL / "assets" / "artifact-handoff.schema.json").read_text(
            encoding="utf-8"
        )
    )
    handoff = handoff_template()
    handoff["record_version"] = "v2"
    report = HANDOFF.validate_handoff(handoff)
    assert report["valid"] is False
    assert any("predecessor reference" in error for error in report["errors"])
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(handoff, schema)

    handoff["supersedes"] = "HANDOFF-001:v1"
    assert HANDOFF.validate_handoff(handoff)["valid"] is True
    jsonschema.validate(handoff, schema)


def test_unresolved_selection_conflict_blocks_automation():
    handoff = handoff_template()
    handoff["selection_policy"].update(
        {
            "status": "conflicted",
            "conflict_refs": ["policy-a.json", "policy-b.json"],
            "resolution_ref": None,
        }
    )
    handoff["automation_status"] = "permitted"
    report = HANDOFF.validate_handoff(handoff)
    assert report["valid"] is False
    assert any("must block automation" in error for error in report["errors"])


def test_resolved_selection_conflict_requires_resolution_reference():
    handoff = handoff_template()
    handoff["selection_policy"].update(
        {
            "status": "resolved",
            "conflict_refs": ["policy-a.json", "policy-b.json"],
            "resolution_ref": None,
        }
    )
    report = HANDOFF.validate_handoff(handoff)
    assert report["valid"] is False
    assert any("requires resolution_ref" in error for error in report["errors"])


def test_permitted_handoff_requires_each_validation_axis():
    handoff = handoff_template()
    handoff["validation"]["computational"] = "partial"
    report = HANDOFF.validate_handoff(handoff)
    assert report["valid"] is False
    assert any("computational validation" in error for error in report["errors"])


def test_equations_links_citations_and_bibliography_resolve(tmp_path):
    notebook = notebook_with_references()
    (tmp_path / "input.md").write_text("fixture", encoding="utf-8")
    report = REFERENCES.validate_notebook_references(
        notebook, path=tmp_path / "report.ipynb"
    )
    assert report["status"] == "pass"
    assert report["findings"] == []


def test_reference_audit_reports_dangling_equation_link_and_citation(tmp_path):
    notebook = notebook_with_references()
    notebook["cells"][0]["source"] = [
        "По формуле (2) использованы [2], [отсутствующие данные](missing.csv) "
        "и [отсутствующий раздел](#нет-раздела).",
        "\\[y = ax \\tag{1}\\]",
    ]
    report = REFERENCES.validate_notebook_references(
        notebook, path=tmp_path / "report.ipynb"
    )
    assert {
        "NB-REF-EQ-002",
        "NB-REF-EQ-003",
        "NB-REF-LINK-001",
        "NB-REF-LINK-002",
        "NB-REF-BIB-001",
    } <= rule_ids(report)


def test_duplicate_equation_numbers_are_rejected(tmp_path):
    notebook = notebook_with_references()
    notebook["cells"][0]["source"].append("\n\\[z = bx \\tag{1}\\]")
    (tmp_path / "input.md").write_text("fixture", encoding="utf-8")
    report = REFERENCES.validate_notebook_references(
        notebook, path=tmp_path / "report.ipynb"
    )
    assert "NB-REF-EQ-001" in rule_ids(report)


def test_numbered_equation_must_be_used_in_prose(tmp_path):
    notebook = notebook_with_references()
    notebook["cells"][0]["source"][0] = "Параметры модели взяты из [1].\n"
    (tmp_path / "input.md").write_text("fixture", encoding="utf-8")
    report = REFERENCES.validate_notebook_references(
        notebook, path=tmp_path / "report.ipynb"
    )
    assert "NB-REF-EQ-003" in rule_ids(report)


def test_one_phrase_can_reference_multiple_numbered_equations(tmp_path):
    notebook = notebook_with_references()
    notebook["cells"][0]["source"] = [
        "Величины определяются по формулам (1) и (2) с параметрами из [1].\n",
        "\\[y = ax \\tag{1}\\]\n",
        "\\[z = by \\tag{2}\\]\n",
        "Исходная таблица: [локальные данные](input.md).",
    ]
    (tmp_path / "input.md").write_text("fixture", encoding="utf-8")
    report = REFERENCES.validate_notebook_references(
        notebook, path=tmp_path / "report.ipynb"
    )
    assert not {"NB-REF-EQ-002", "NB-REF-EQ-003"} & rule_ids(report)


def test_frozen_notebook_cannot_ship_incomplete_bibliography(tmp_path):
    notebook = notebook_with_references()
    notebook["metadata"]["scientific_report"].update(
        {"artifact_status": "frozen", "bibliography_status": "incomplete"}
    )
    (tmp_path / "input.md").write_text("fixture", encoding="utf-8")
    report = REFERENCES.validate_notebook_references(
        notebook, path=tmp_path / "report.ipynb"
    )
    assert "NB-REF-BIB-007" in rule_ids(report)


def test_reference_audit_discloses_semantic_and_gost_limits():
    report = REFERENCES.validate_notebook_references(
        copy.deepcopy(notebook_with_references())
    )
    assert "semantic_support_of_citations" in report["not_assessed"]
    assert "exact_bibliographic_title_against_source" in report["not_assessed"]
    assert "gost_punctuation_and_required_fields" in report["not_assessed"]

def test_companion_markdown_local_links_are_validated(tmp_path):
    path = tmp_path / "report.md"
    path.write_text("# Отчёт\n\n[Отсутствующее приложение](missing.md)", encoding="utf-8")
    report = REFERENCES.lint_path(path)
    assert report["status"] == "fail"
    assert "DOC-REF-LINK-001" in rule_ids(report)


def test_directory_expansion_includes_top_level_markdown_but_not_generated_subfolders(tmp_path):
    (tmp_path / "report.md").write_text("# Отчёт", encoding="utf-8")
    generated = tmp_path / "checks"
    generated.mkdir()
    (generated / "mirror.md").write_text("[Ошибка](missing.md)", encoding="utf-8")
    targets = REFERENCES._expand_paths([tmp_path])
    assert tmp_path / "report.md" in targets
    assert generated / "mirror.md" not in targets

