import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments" / "EXP-0032-chernikov-independent-dissertation-critic"


def _json(name: str) -> dict:
    return json.loads((EXPERIMENT / name).read_text(encoding="utf-8"))


def test_exp0032_is_adjudicated_regression_not_gold() -> None:
    data = _json("evaluation.json")
    assert data["standard"] == "PSES-DISS-001/0.3.0"
    assert data["gold_status"] == "not_gold"
    assert data["adjudication"]["status"] == "completed"
    assert data["adjudication"]["summary"] == {
        "accepted": 9,
        "narrowed": 6,
        "corrected": 0,
        "rejected": 0,
        "gold_status": "not_gold",
    }


def test_exp0032_adjudicates_every_raw_finding() -> None:
    evaluation = _json("evaluation.json")
    manifest = _json("run-manifest.json")
    decisions = evaluation["adjudication"]["decisions"]

    assert manifest["finding_counts"]["total"] == 15
    assert len(decisions) == 15
    assert {item["finding_id"] for item in decisions} == {
        f"EXP0032-F{number:03d}" for number in range(1, 16)
    }


def test_exp0032_narrows_unproved_or_overstated_premises() -> None:
    decisions = {
        item["item"]: item for item in _json("evaluation.json")["adjudication"]["decisions"]
    }

    assert decisions[2]["adjudication"] == "narrowed"
    assert decisions[2]["severity"] == "major"
    assert "does not prove" in decisions[2]["reason"]

    assert decisions[8]["raw_claim_status"] == "ambiguous_not_contradictory"
    assert decisions[8]["severity"] == "minor"

    assert decisions[13]["adjudication"] == "narrowed"
    assert "possible repair" in decisions[13]["reason"]


def test_exp0032_source_is_frozen_with_provenance_limit() -> None:
    source = _json("source-manifest.json")
    representation = source["representations"][0]

    assert representation["content_hash"] == (
        "sha256:14c997ec93e9bcab3aa3db9c990b32496938577ab7e31ea3c6583656d448a4c5"
    )
    assert representation["pages"] == 178
    assert representation["suitability"] == "usable_with_provenance_limit"
    assert source["raw_source_committed"] is False