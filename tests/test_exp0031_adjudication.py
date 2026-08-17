"""Keep the disclosed EXP-0031 critic errors as regression constraints."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "EXP-0031-astapenko-independent-dissertation-critic"


def _evaluation() -> dict:
    return json.loads((EXPERIMENT / "evaluation.json").read_text(encoding="utf-8"))


def test_exp0031_is_adjudicated_regression_not_gold() -> None:
    data = _evaluation()
    assert data["standard"] == "PSES-DISS-001/0.3.0"
    assert data["gold_status"] == "not_gold"
    assert data["adjudication"]["status"] == "completed"
    assert data["adjudication"]["summary"] == {
        "accepted": 7,
        "narrowed": 3,
        "corrected": 2,
        "gold_status": "not_gold",
    }


def test_exp0031_false_premises_cannot_return_as_verified() -> None:
    decisions = {item["item"]: item for item in _evaluation()["adjudication"]["decisions"]}

    # The visual PDF has the correct TOC word; only the heading mismatch and
    # another printed typo survive the split finding.
    assert decisions[10]["adjudication"] == "corrected"
    assert decisions[10]["raw_claim_status"] == "rejected_as_stated"
    assert "классификации" in decisions[10]["reason"]

    # Reference 20 is explicitly cited.  Missing HTML anchors are discovery
    # leads, not evidence that a bibliography entry is uncited.
    assert decisions[12]["adjudication"] == "corrected"
    assert decisions[12]["severity"] == "note"
    assert "Record 20 is cited" in decisions[12]["reason"]


def test_exp0031_numeric_and_severity_calibration_are_preserved() -> None:
    data = _evaluation()
    numeric = data["scientific_critic"]["critical_numeric_consistency_check"]
    assert numeric == {
        "observed": "12/15",
        "computed_percent": 80.0,
        "reported_percent": 75.0,
        "status": "confirmed_internal_inconsistency",
    }
    decisions = {item["item"]: item for item in data["adjudication"]["decisions"]}
    assert decisions[1]["severity"] == "critical"
    assert decisions[9]["severity"] == "minor"
