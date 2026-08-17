from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "zotero-living-review"
SCRIPT = SKILL / "scripts" / "update_review.py"
SPEC = importlib.util.spec_from_file_location("zotero_living_review_update", SCRIPT)
assert SPEC and SPEC.loader
UPDATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(UPDATE)


def context(char: str = "0") -> str:
    return "sha256:" + char * 64


def item(key: str, source: str = "1", annotation: str = "2", status: str = "validated", ctx: str | None = None) -> dict:
    record = {
        "zotero_key": key,
        "source_content_hash": f"sha256:{source * 64}" if len(source) == 1 else source,
        "annotation_hash": f"sha256:{annotation * 64}" if len(annotation) == 1 else annotation,
        "annotation_status": status,
    }
    if ctx is not None:
        record["project_context_hash"] = ctx
    return record


def inventory(*items: dict, ctx: str | None = None) -> dict:
    ctx = ctx or context()
    return {
        "schema_version": "ZLR-INV-001/v1",
        "review_id": "LR-001",
        "project_id": "PRJ-001",
        "corpus_id": "COR-001",
        "collection": {"library_id": "user", "collection_key": "COLL-1", "collection_name": "Corpus"},
        "project_context_hash": ctx,
        "items": list(items),
    }


def empty_state() -> dict:
    return {
        "schema_version": "ZLR-001/v1",
        "review_id": "LR-001",
        "project_id": "PRJ-001",
        "corpus_id": "COR-001",
        "collection": {"library_id": "user", "collection_key": "COLL-1", "collection_name": "Corpus"},
        "project_context_hash": context(),
        "items": {},
        "snapshots": [],
        "current_artifact": None,
    }


def first_state() -> tuple[dict, dict]:
    inv = inventory(item("AAAA", ctx=context()))
    result = UPDATE.build_update_plan(empty_state(), inv)
    assert result["synthesis_blocked"] is False
    return result["state"], inv


def test_initial_add_creates_snapshot_and_allows_validated_annotation() -> None:
    state = empty_state()
    result = UPDATE.build_update_plan(state, inventory(item("AAAA", ctx=context())))

    assert result["changes"]["added"] == ["AAAA"]
    assert result["snapshot_required"] is True
    assert result["resynthesis_required"] is True
    assert result["synthesis_blocked"] is False
    assert len(result["state"]["snapshots"]) == 1
    assert result["state"]["snapshots"][0]["immutable"] is True


def test_added_item_without_validated_annotation_blocks_synthesis() -> None:
    result = UPDATE.build_update_plan(empty_state(), inventory(item("AAAA", status="pending", ctx=context())))

    assert result["synthesis_blocked"] is True
    assert result["blocking_reasons"][0]["code"] == "annotation_not_validated"
    assert result["state"]["current_artifact"]["status"] == "blocked"


def test_source_change_requires_new_validated_annotation() -> None:
    previous, _ = first_state()
    changed = inventory(item("AAAA", source="3", annotation="2", status="validated", ctx=context()))
    result = UPDATE.build_update_plan(previous, changed)

    assert result["changes"]["source_changed"] == ["AAAA"]
    assert result["changes"]["annotation_changed"] == []
    assert result["synthesis_blocked"] is True
    assert any(reason["code"] == "annotation_not_rebuilt" for reason in result["blocking_reasons"])

    rebuilt = inventory(item("AAAA", source="3", annotation="4", status="validated", ctx=context()))
    allowed = UPDATE.build_update_plan(previous, rebuilt)
    assert allowed["synthesis_blocked"] is False


def test_annotation_change_is_blocked_until_validated() -> None:
    previous, _ = first_state()
    changed = inventory(item("AAAA", annotation="5", status="pending", ctx=context()))
    result = UPDATE.build_update_plan(previous, changed)

    assert result["changes"]["annotation_changed"] == ["AAAA"]
    assert result["synthesis_blocked"] is True


def test_removed_item_is_retained_in_history_and_snapshot_is_new() -> None:
    previous, _ = first_state()
    old_snapshot = copy.deepcopy(previous["snapshots"][0])
    result = UPDATE.build_update_plan(previous, inventory())

    assert result["changes"]["removed"] == ["AAAA"]
    assert result["snapshot_required"] is True
    assert result["state"]["items"]["AAAA"]["status"] == "removed"
    assert result["state"]["items"]["AAAA"]["removed_in_snapshot_id"] == result["snapshot_id"]
    assert result["state"]["items"]["AAAA"]["history"][-1]["event"] == "removed"
    assert result["state"]["snapshots"][0] == old_snapshot
    assert result["state"]["snapshots"][1]["item_keys"] == []


def test_context_change_invalidates_stale_project_relative_annotations() -> None:
    previous, _ = first_state()
    new_context = context("f")
    stale = inventory(item("AAAA", ctx=context()), ctx=new_context)
    result = UPDATE.build_update_plan(previous, stale)

    assert result["changes"]["context_changed"] is True
    assert result["synthesis_blocked"] is True
    assert any(reason["code"] == "stale_project_context" for reason in result["blocking_reasons"])

    current = inventory(item("AAAA", ctx=new_context), ctx=new_context)
    allowed = UPDATE.build_update_plan(previous, current)
    assert allowed["synthesis_blocked"] is False


def test_noop_is_idempotent_and_does_not_add_snapshot() -> None:
    previous, inv = first_state()
    before = copy.deepcopy(previous)
    result = UPDATE.build_update_plan(previous, inv)

    assert result["relevant_change"] is False
    assert result["snapshot_required"] is False
    assert result["resynthesis_required"] is True  # the first sync still needs synthesis
    assert result["state"] == before
    assert len(result["state"]["snapshots"]) == 1

    published = UPDATE.record_published_artifact(
        previous,
        snapshot_id=previous["current_artifact"]["snapshot_id"],
        artifact_path="review-v1.md",
        content_hash=context("e"),
    )
    published_result = UPDATE.build_update_plan(published, inv)
    assert published_result["resynthesis_required"] is False
    assert published_result["state"] == published


def test_update_does_not_mutate_input_and_old_snapshots_are_immutable() -> None:
    previous, _ = first_state()
    before = copy.deepcopy(previous)
    result = UPDATE.build_update_plan(previous, inventory(item("AAAA", source="7", annotation="8", ctx=context())))

    assert previous == before
    assert result["state"]["snapshots"][0] == before["snapshots"][0]
    assert result["state"]["snapshots"][1]["snapshot_id"] != result["state"]["snapshots"][0]["snapshot_id"]


def test_state_and_inventory_validators_fail_closed_on_bad_context_hash() -> None:
    inv = inventory(item("AAAA", ctx="context-v1"))
    inv["project_context_hash"] = "context-v1"
    report = UPDATE.validate_inventory(inv)
    assert report["valid"] is False
    assert "project_context_hash" in " ".join(report["errors"])

    state = empty_state()
    state["project_context_hash"] = "context-v1"
    report = UPDATE.validate_state(state)
    assert report["valid"] is False


def test_initial_missing_or_wrong_item_context_blocks_synthesis() -> None:
    for record in (item("AAAA"), item("AAAA", ctx=context("f"))):
        result = UPDATE.build_update_plan(empty_state(), inventory(record))
        assert result["synthesis_blocked"] is True
        assert any(reason["code"] == "stale_project_context" for reason in result["blocking_reasons"])


def test_source_and_annotation_hashes_are_strict_sha256_values() -> None:
    inv = inventory(item("AAAA", ctx=context()))
    inv["items"][0]["source_content_hash"] = "source-v1"
    assert UPDATE.validate_inventory(inv)["valid"] is False
    inv["items"][0]["source_content_hash"] = context("1")
    inv["items"][0]["annotation_hash"] = "annotation-v1"
    assert UPDATE.validate_inventory(inv)["valid"] is False


def test_record_published_artifact_succeeds_and_copies_state() -> None:
    state, _ = first_state()
    before = copy.deepcopy(state)
    snapshot_id = state["current_artifact"]["snapshot_id"]
    published = UPDATE.record_published_artifact(
        state,
        snapshot_id=snapshot_id,
        artifact_path="artifacts/review-v1.md",
        content_hash=context("e"),
    )

    assert state == before
    assert published["current_artifact"]["status"] == "published"
    assert published["current_artifact"]["resynthesis_required"] is False
    assert published["current_artifact"]["artifact_path"] == "artifacts/review-v1.md"
    assert UPDATE.validate_state(published)["valid"] is True


def test_record_published_artifact_refuses_blocked_and_stale_candidates() -> None:
    blocked = UPDATE.build_update_plan(empty_state(), inventory(item("AAAA", status="pending", ctx=context())))
    blocked_state = blocked["state"]
    with pytest.raises(UPDATE.ReviewStateError, match="needs_resynthesis"):
        UPDATE.record_published_artifact(
            blocked_state,
            snapshot_id=blocked_state["current_artifact"]["snapshot_id"],
            artifact_path="review.md",
            content_hash=context("e"),
        )

    state, _ = first_state()
    with pytest.raises(UPDATE.ReviewStateError, match="does not match"):
        UPDATE.record_published_artifact(
            state,
            snapshot_id="SNAP-stale",
            artifact_path="review.md",
            content_hash=context("e"),
        )


def test_identity_mismatch_does_not_switch_collection_or_project() -> None:
    previous, _ = first_state()
    changed = inventory(item("AAAA", ctx=context()))
    changed["collection"]["collection_key"] = "OTHER"

    with pytest.raises(UPDATE.ReviewStateError, match="collection binding"):
        UPDATE.build_update_plan(previous, changed)
