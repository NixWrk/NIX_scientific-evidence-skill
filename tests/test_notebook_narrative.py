import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "scientific-evidence-workflow"
FIXTURES = ROOT / "tests" / "fixtures" / "notebooks"


def load_linter():
    path = SKILL / "scripts" / "lint_notebook.py"
    spec = importlib.util.spec_from_file_location("lint_notebook", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


LINTER = load_linter()


def lint(relative_path: str) -> dict:
    path = FIXTURES / relative_path
    data = json.loads(path.read_text(encoding="utf-8"))
    return LINTER.lint_notebook(data, path=str(path))


def rule_ids(report: dict) -> set[str]:
    return {finding["rule_id"] for finding in report["findings"]}


def test_scenario_1_clean_single_task_passes():
    report = lint("clean-single-task.ipynb")
    assert report["status"] == "pass"
    assert report["valid"] is True
    assert report["findings"] == []


def test_scenario_2_hidden_state_stale_output_and_unit_gap_fail():
    report = lint("hidden-state-stale-unit.ipynb")
    assert report["status"] == "fail"
    assert {
        "NB-EXEC-001",
        "NB-EXEC-002",
        "NB-REPRO-003",
        "NB-NUMBER-001",
    } <= rule_ids(report)


def test_scenario_3_negative_result_and_hypothesis_are_preserved():
    report = lint("negative-result-hypothesis.ipynb")
    assert report["status"] == "pass"
    assert "NB-NUMBER-001" not in rule_ids(report)
    assert "NB-SPLIT-001" not in rule_ids(report)


def test_scenario_4_semantically_overloaded_notebook_requests_review():
    report = lint("split-needed.ipynb")
    assert report["status"] == "review"
    assert report["valid"] is True
    assert rule_ids(report) == {"NB-SPLIT-001"}


def test_scenario_5_split_pair_passes_as_two_bounded_reports():
    reports = [
        lint("split-pair/prepare-data.ipynb"),
        lint("split-pair/evaluate-model.ipynb"),
    ]
    assert all(report["status"] == "pass" for report in reports)
    assert all("NB-SPLIT-001" not in rule_ids(report) for report in reports)


def test_template_is_valid_notebook_with_working_report_metadata():
    path = SKILL / "assets" / "notebook-narrative.template.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    report = notebook["metadata"]["scientific_report"]
    assert notebook["nbformat"] == 4
    assert report == {
        "artifact_status": "working",
        "execution_status": "not_run",
        "schema_version": "1.0",
    }
    tags = {
        tag
        for cell in notebook["cells"]
        for tag in cell.get("metadata", {}).get("tags", [])
    }
    assert {"research-question", "observable-output", "report-summary"} <= tags


def test_frozen_snapshot_requires_release_identity_fields():
    path = FIXTURES / "clean-single-task.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    notebook["metadata"]["scientific_report"].pop("run_id")
    report = LINTER.lint_notebook(notebook)
    assert report["status"] == "fail"
    assert "NB-REPRO-002" in rule_ids(report)


def test_lint_report_states_what_static_analysis_does_not_assess():
    report = lint("clean-single-task.ipynb")
    assert "actual_clean_kernel_execution" in report["not_assessed"]
    assert "scientific_method_validity" in report["not_assessed"]


def test_notebook_evidence_bundle_accepts_its_canonical_shape():
    validator_path = SKILL / "scripts" / "validate_bundle.py"
    spec = importlib.util.spec_from_file_location("validate_bundle_for_notebook", validator_path)
    validator = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(validator)

    bundle = json.loads(
        (SKILL / "assets" / "evidence-bundle.template.json").read_text(encoding="utf-8")
    )
    bundle["task"].update({"mode": "record", "genre": "notebook-narrative"})
    bundle["sources"][0]["representation"] = "data"
    bundle["evidence"][0]["support_type"] = "method"
    bundle["results"] = [
        {
            "result_id": "RES-NB-001",
            "source_id": "SRC-EXAMPLE-001",
            "locator": "cell:4/output:0",
            "value": 2.0,
            "unit": "ms",
            "version": "sha256:example",
            "analysis": "mean duration",
            "approved": True,
        }
    ]
    bundle["structure"] = [
        {"unit_id": "TASK-NB", "unit_type": "task", "label": "Q1", "status": "final"},
        {
            "unit_id": "CONC-NB",
            "unit_type": "conclusion",
            "label": "C1",
            "status": "final",
        },
    ]
    sections = (
        "notebook_scope",
        "method_and_assumptions",
        "observed_outputs",
        "interpretation_and_limits",
        "notebook_summary",
    )
    bundle["claims"] = [
        {
            "claim_id": f"CL-NB-{index}",
            "text": f"Bounded notebook statement {index}.",
            "output_section": section,
            "claim_type": "structural" if index == 1 else "factual",
            "certainty": "direct",
            "evidence_ids": ["EV-001"] if index == 2 else [],
            "result_ids": ["RES-NB-001"] if index >= 3 else [],
            "structure_ids": ["TASK-NB" if index < 5 else "CONC-NB"],
            "status": "supported",
            "disposition": "keep",
            "boundary": "Only the supplied run.",
            "causal_basis": None,
        }
        for index, section in enumerate(sections, start=1)
    ]
    report = validator.validate_bundle(bundle)
    assert report["valid"] is True, report["errors"]