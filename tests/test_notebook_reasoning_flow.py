import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "scientific-evidence-workflow"


def load_linter():
    path = SKILL / "scripts" / "lint_notebook.py"
    spec = importlib.util.spec_from_file_location("lint_notebook_flow", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


LINTER = load_linter()


def template() -> dict:
    path = SKILL / "assets" / "notebook-narrative.template.ipynb"
    return json.loads(path.read_text(encoding="utf-8"))


def rule_ids(report: dict) -> set[str]:
    return {finding["rule_id"] for finding in report["findings"]}


def test_reasoning_bridge_must_lead_to_a_marked_forward_task():
    notebook = template()
    notebook["cells"][3]["metadata"]["tags"].remove("forward-task")
    report = LINTER.lint_notebook(notebook)
    assert "NB-NARR-021" in rule_ids(report)


def test_reasoning_bridge_requires_basis_gap_decision_and_expectation():
    notebook = template()
    notebook["cells"][1]["source"] = ["No bridge signals are present."]
    report = LINTER.lint_notebook(notebook)
    assert {"NB-NARR-025", "NB-NARR-027"} <= rule_ids(report)


def test_second_forward_task_requires_an_intervening_reasoning_bridge():
    notebook = template()
    notebook["cells"][6]["metadata"]["tags"].append("forward-task")
    report = LINTER.lint_notebook(notebook)
    assert "NB-NARR-023" in rule_ids(report)
