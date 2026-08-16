"""Offline contract and benchmark smoke tests for PSES-DISS-001."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "dissertation-formatting-and-apparatus" / "scripts"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_module("critic_findings_validator", SCRIPT_DIR / "validate_critic_findings.py")
BENCHMARK = _load_module("dissertation_benchmark", SCRIPT_DIR / "run_dissertation_benchmark.py")
EXPERIMENT = ROOT / "experiments" / "EXP-0027-dissertation-critic-benchmark"


def _finding(**overrides):
    finding = {
        "issue_id": "ISSUE-001",
        "rule_id": "RULE-001",
        "module": "dissertation-critic",
        "severity": "minor",
        "issue_class": "recommendation",
        "locator": {"kind": "word", "exact_text": "слово", "occurrence": 1},
        "observed": "Наблюдение.",
        "expected": "Ожидаемое состояние.",
        "authority_ids": [],
        "evidence_ids": [],
        "suggested_fix": "Уточнить формулировку.",
        "confidence": 0.8,
        "autofix_safe": False,
        "word_action": "comment",
    }
    finding.update(overrides)
    return finding


def test_validator_accepts_word_comment_with_exact_anchor() -> None:
    report = VALIDATOR.validate_findings({"findings": [_finding()]})

    assert report["valid"] is True
    assert report["counts"]["findings"] == 1


def test_validator_rejects_normative_violation_without_authority() -> None:
    report = VALIDATOR.validate_findings(
        {"findings": [_finding(issue_class="normative_violation")]}
    )

    assert report["valid"] is False
    assert any(error["code"] == "NORMATIVE_AUTHORITY_REQUIRED" for error in report["errors"])


def test_validator_rejects_tracked_change_without_exact_old_new() -> None:
    report = VALIDATOR.validate_findings(
        {
            "findings": [
                _finding(
                    word_action="tracked_change",
                    suggested_fix="заменить слово",
                )
            ]
        }
    )

    assert report["valid"] is False
    assert any(
        error["code"] == "TRACKED_CHANGE_EXACT_REPLACEMENT_REQUIRED"
        for error in report["errors"]
    )


def test_validator_rejects_duplicate_issue_ids() -> None:
    report = VALIDATOR.validate_findings(
        {"findings": [_finding(), _finding(rule_id="RULE-002")]}
    )

    assert report["valid"] is False
    assert any(error["code"] == "DUPLICATE_ISSUE_ID" for error in report["errors"])


def test_experiment_runs_all_four_stages_without_external_model(tmp_path: Path) -> None:
    report = BENCHMARK.run_benchmark(EXPERIMENT, output=tmp_path / "status.json")

    assert report["status"] == "passed"
    assert report["release_decision"] == "pass"
    assert report["stages"] == ["regression", "mutation", "clean_control", "holdout"]
    assert report["frozen_hashes"]["frozen"] is True
    assert report["execution_policy"] == {
        "external_llm_called": False,
        "network_used": False,
        "gold_exposed_to_critic": False,
    }
    assert report["metrics"]["skill"]["tp"] == 3
    assert report["metrics"]["skill"]["fp"] == 0
    assert report["metrics"]["skill"]["fn"] == 0
    assert set(report["metrics"]["skill"]["per_stage"]) == {
        "regression",
        "mutation",
        "clean_control",
        "holdout",
    }
    status = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))
    assert status["gold_protection"]["hidden_from_runner_output"] is True


def test_experiment_detects_frozen_input_drift(tmp_path: Path) -> None:
    # Copy only the experiment so the committed fixture remains untouched.
    import shutil

    copied = tmp_path / EXPERIMENT.name
    shutil.copytree(EXPERIMENT, copied)
    fixture = copied / "fixtures" / "mutation.json"
    fixture.write_text(fixture.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    report = BENCHMARK.run_benchmark(copied)

    assert report["status"] == "blocked"
    assert any(error["code"] == "FROZEN_HASH_MISMATCH" for error in report["stop_errors"])
