from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "skills" / "research-project-workflow" / "scripts" / "validate_project_manifest.py"
TEMPLATE_PATH = ROOT / "skills" / "research-project-workflow" / "assets" / "project-manifest.template.json"
SKILL_PATH = ROOT / "skills" / "research-project-workflow" / "SKILL.md"
CONTRACT_PATH = ROOT / "skills" / "research-project-workflow" / "references" / "project-manifest-contract.md"

spec = importlib.util.spec_from_file_location("project_manifest_validator", VALIDATOR_PATH)
assert spec and spec.loader
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def valid_manifest() -> dict:
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


def refresh_context_hash(manifest: dict) -> None:
    manifest["context_hash"] = validator.context_hash_for_manifest(manifest)


def snapshot(snapshot_id: str, captured_at: str) -> dict:
    return {
        "snapshot_id": snapshot_id,
        "captured_at": captured_at,
        "item_keys": [f"ITEM-{snapshot_id}"],
        "content_hash": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
    }


def test_russian_template_and_contract_require_human_readable_project_language() -> None:
    manifest = valid_manifest()
    skill = SKILL_PATH.read_text(encoding="utf-8")
    contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert manifest["title"] == "Название исследовательского проекта"
    assert manifest["context"]["problem"].startswith("Сформулируйте научную проблему")
    assert manifest["context"]["goal"].startswith("Сформулируйте планируемый")
    assert manifest["corpora"][0]["label"] == "Пополняемый корпус научной литературы"
    assert "every natural-language text created by this skill" in skill
    assert "A Russian project requires an" in skill
    assert "accepted Russian title" in skill
    assert "working language" in contract
    assert "English placeholder" in contract
    assert "Research project title" not in json.dumps(manifest, ensure_ascii=False)
    assert "Living literature corpus" not in json.dumps(manifest, ensure_ascii=False)


def test_template_is_valid_and_hash_is_current() -> None:
    manifest = valid_manifest()

    report = validator.validate_project(manifest)

    assert report["valid"] is True
    assert report["errors"] == []
    assert manifest["context_hash"] == validator.context_hash_for_manifest(manifest)


def test_context_hash_is_project_relative_and_detects_stale_context() -> None:
    manifest = valid_manifest()
    manifest["project_id"] = "PRJ-999"
    assert validator.validate_project(manifest)["valid"] is True

    manifest["context"]["goal"] = "A changed goal makes the previous context hash stale."
    report = validator.validate_project(manifest)

    assert report["valid"] is False
    assert any("context_hash" in error and "mismatch" in error for error in report["errors"])


def test_duplicate_objective_and_question_ids_are_rejected() -> None:
    manifest = valid_manifest()
    manifest["context"]["objectives"].append(copy.deepcopy(manifest["context"]["objectives"][0]))
    manifest["context"]["research_questions"].append(
        copy.deepcopy(manifest["context"]["research_questions"][0])
    )
    refresh_context_hash(manifest)

    report = validator.validate_project(manifest)

    assert report["valid"] is False
    assert any("duplicate identifier 'OBJ-001'" in error for error in report["errors"])
    assert any("duplicate identifier 'RQ-001'" in error for error in report["errors"])


def test_broken_local_references_are_rejected() -> None:
    manifest = valid_manifest()
    manifest["corpora"][0]["binding_ids"] = ["ZCB-404"]
    manifest["corpora"][0]["objective_ids"] = ["OBJ-404"]
    manifest["artifacts"][0]["linked_manifest_ids"] = ["MAN-404"]

    report = validator.validate_project(manifest)

    assert report["valid"] is False
    assert sum("broken reference" in error for error in report["errors"]) == 3


def test_missing_context_fails_closed() -> None:
    manifest = valid_manifest()
    manifest.pop("context")

    report = validator.validate_project(manifest)

    assert report["valid"] is False
    assert any(error.startswith("manifest.context: expected an object") for error in report["errors"])


def test_parent_project_self_link_is_rejected() -> None:
    manifest = valid_manifest()
    manifest["parent_project_id"] = manifest["project_id"]

    report = validator.validate_project(manifest)

    assert report["valid"] is False
    assert any("self-link is not allowed" in error for error in report["errors"])


def test_unsynced_dynamic_corpus_is_valid() -> None:
    manifest = valid_manifest()

    assert manifest["corpora"][0]["snapshots"] == []
    assert manifest["corpora"][0]["active_snapshot_id"] is None
    assert validator.validate_project(manifest)["valid"] is True


def test_dynamic_active_without_snapshot_is_invalid() -> None:
    manifest = valid_manifest()
    manifest["corpora"][0]["active_snapshot_id"] = "SNAP-001"

    report = validator.validate_project(manifest)

    assert report["valid"] is False
    assert any("must be null before the first dynamic snapshot" in error for error in report["errors"])


def test_dynamic_and_frozen_snapshot_invariants() -> None:
    manifest = valid_manifest()
    first = snapshot("SNAP-001", "2026-08-17T10:00:00Z")
    second = snapshot("SNAP-002", "2026-08-18T10:00:00Z")
    manifest["corpora"][0]["snapshots"] = [first]
    manifest["corpora"][0]["active_snapshot_id"] = "SNAP-001"
    assert validator.validate_project(manifest)["valid"] is True

    manifest["corpora"][0]["snapshots"].append(second)
    assert validator.validate_project(manifest)["valid"] is True

    manifest["corpora"][0]["policy"] = "frozen"
    report = validator.validate_project(manifest)
    assert report["valid"] is False
    assert any("frozen corpus requires exactly one snapshot" in error for error in report["errors"])

    manifest["corpora"][0]["snapshots"] = [first]
    assert validator.validate_project(manifest)["valid"] is True


def test_unknown_fields_are_rejected() -> None:
    manifest = valid_manifest()
    manifest["context"]["evidence"] = []

    report = validator.validate_project(manifest)

    assert report["valid"] is False
    assert any("unexpected field 'evidence'" in error for error in report["errors"])
