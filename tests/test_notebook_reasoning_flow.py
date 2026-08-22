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

def tagged_index(notebook: dict, tag: str) -> int:
    for index, cell in enumerate(notebook["cells"]):
        if tag in cell.get("metadata", {}).get("tags", []):
            return index
    raise AssertionError(f"Missing tag: {tag}")



def test_reasoning_bridge_must_lead_to_a_marked_forward_task():
    notebook = template()
    notebook["cells"][tagged_index(notebook, "forward-task")]["metadata"]["tags"].remove("forward-task")
    report = LINTER.lint_notebook(notebook)
    assert "NB-NARR-021" in rule_ids(report)


def test_reasoning_bridge_requires_basis_gap_decision_and_expectation():
    notebook = template()
    notebook["cells"][tagged_index(notebook, "reasoning-bridge")]["source"] = ["No bridge signals are present."]
    report = LINTER.lint_notebook(notebook)
    assert {"NB-NARR-025", "NB-NARR-027"} <= rule_ids(report)


def test_second_forward_task_requires_an_intervening_reasoning_bridge():
    notebook = template()
    first_forward = tagged_index(notebook, "forward-task")
    next_markdown = next(
        index for index in range(first_forward + 1, len(notebook["cells"]))
        if notebook["cells"][index].get("cell_type") == "markdown"
    )
    notebook["cells"][next_markdown]["metadata"]["tags"].append("forward-task")
    report = LINTER.lint_notebook(notebook)
    assert "NB-NARR-023" in rule_ids(report)


def test_reasoning_bridge_must_be_a_dedicated_concluding_paragraph():
    notebook = template()
    bridge = notebook["cells"][tagged_index(notebook, "reasoning-bridge")]
    bridge["metadata"]["tags"].append("interpretation-and-limits")
    report = LINTER.lint_notebook(notebook)
    assert "NB-NARR-029" in rule_ids(report)


def test_reasoning_bridge_requires_an_explicit_synthesis():
    notebook = template()
    bridge = notebook["cells"][tagged_index(notebook, "reasoning-bridge")]
    bridge["source"] = [
        "Результаты §1 устанавливают исходное положение, однако сохраняют ограничение. "
        "Поэтому в §2 будет выполнен расчёт; критерием считается достижение заданного порога."
    ]
    report = LINTER.lint_notebook(notebook)
    assert "NB-NARR-030" in rule_ids(report)

def test_reasoning_bridge_rejects_unattributed_expected_phrase():
    notebook = template()
    bridge = notebook["cells"][tagged_index(notebook, "reasoning-bridge")]
    bridge["source"] = [
        "Таким образом, результаты §1 устанавливают исходное положение, однако сохраняют ограничение. "
        "Поэтому в §2 будет выполнен расчёт. Ожидается получить положительное значение; "
        "критерием считается достижение заданного порога."
    ]
    report = LINTER.lint_notebook(notebook)
    assert "NB-NARR-031" in rule_ids(report)
