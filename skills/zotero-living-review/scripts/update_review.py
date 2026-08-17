#!/usr/bin/env python3
"""Strict validation and publication gate for the living-review update engine."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from typing import Any, Mapping


_ENGINE_PATH = Path(__file__).with_name("update_review_impl.py")
_SPEC = importlib.util.spec_from_file_location("zotero_living_review_engine", _ENGINE_PATH)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - import failure is environmental
    raise ImportError(f"cannot load {_ENGINE_PATH}")
_ENGINE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_ENGINE)

ReviewStateError = _ENGINE.ReviewStateError
STATE_SCHEMA = _ENGINE.STATE_SCHEMA
INVENTORY_SCHEMA = _ENGINE.INVENTORY_SCHEMA
PLAN_SCHEMA = _ENGINE.PLAN_SCHEMA
VALID_ANNOTATION_STATUSES = _ENGINE.VALID_ANNOTATION_STATUSES
CONTEXT_HASH_RE = _ENGINE.CONTEXT_HASH_RE
CONTENT_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

_BASE_VALIDATE_INVENTORY = _ENGINE.validate_inventory
_BASE_VALIDATE_STATE = _ENGINE.validate_state
_BASE_BLOCKING_REASONS = _ENGINE._blocking_reasons


def _hash_error(where: str, field: str) -> str:
    return f"{where}: {field} must be sha256:<64 lowercase hex characters>"


def validate_inventory(inventory: Mapping[str, Any]) -> dict[str, Any]:
    """Validate inventory structure and require content hashes."""

    report = copy.deepcopy(_BASE_VALIDATE_INVENTORY(inventory))
    if not isinstance(inventory, Mapping):
        return report
    try:
        items = _ENGINE._item_map(inventory.get("items"), source="inventory")
    except ReviewStateError:
        return report
    for key, item in items.items():
        for field in ("source_content_hash", "annotation_hash"):
            value = item.get(field)
            if not isinstance(value, str) or not CONTENT_HASH_RE.fullmatch(value):
                message = _hash_error(f"inventory.items[{key}]", field)
                if message not in report["errors"]:
                    report["errors"].append(message)
    report["valid"] = not report["errors"]
    return report


def validate_state(state: Mapping[str, Any]) -> dict[str, Any]:
    """Validate state, including the fields required by a published artifact."""

    report = copy.deepcopy(_BASE_VALIDATE_STATE(state))
    if not isinstance(state, Mapping):
        return report
    try:
        items = _ENGINE._item_map(state.get("items"), source="state")
    except ReviewStateError:
        items = {}
    for key, item in items.items():
        for field in ("source_content_hash", "annotation_hash"):
            value = item.get(field)
            if not isinstance(value, str) or not CONTENT_HASH_RE.fullmatch(value):
                message = _hash_error(f"state.items[{key}]", field)
                if message not in report["errors"]:
                    report["errors"].append(message)

    artifact = state.get("current_artifact")
    snapshots = state.get("snapshots") if isinstance(state.get("snapshots"), list) else []
    snapshot_ids = {snapshot.get("snapshot_id") for snapshot in snapshots if isinstance(snapshot, Mapping)}
    if isinstance(artifact, Mapping) and artifact.get("status") == "published":
        if not isinstance(artifact.get("artifact_path"), str) or not artifact.get("artifact_path", "").strip():
            report["errors"].append("state.current_artifact: published artifact_path is required")
        content_hash = artifact.get("content_hash")
        if not isinstance(content_hash, str) or not CONTENT_HASH_RE.fullmatch(content_hash):
            report["errors"].append(
                "state.current_artifact: published content_hash must be sha256:<64 lowercase hex characters>"
            )
        if artifact.get("snapshot_id") not in snapshot_ids:
            report["errors"].append("state.current_artifact: published snapshot_id must reference an existing snapshot")
        if artifact.get("resynthesis_required") is not False:
            report["errors"].append("state.current_artifact: published artifact must set resynthesis_required to false")

    report["valid"] = not report["errors"]
    return report


def _context_for_item(item: Mapping[str, Any]) -> Any:
    return item.get("project_context_hash", item.get("annotation_context_hash"))


def _blocking_reasons(
    changes: Mapping[str, Any],
    previous_items: Mapping[str, Mapping[str, Any]],
    current_items: Mapping[str, Mapping[str, Any]],
    current_context: str,
) -> list[dict[str, str]]:
    """Add the current-context gate to the engine's annotation gate."""

    reasons = list(_BASE_BLOCKING_REASONS(changes, previous_items, current_items, current_context))
    existing = {(reason["zotero_key"], reason["code"]) for reason in reasons}
    for key, item in current_items.items():
        if _context_for_item(item) != current_context and (key, "stale_project_context") not in existing:
            reasons.append(
                {
                    "zotero_key": key,
                    "code": "stale_project_context",
                    "message": "annotation does not carry the current project_context_hash",
                }
            )
    return sorted(reasons, key=lambda reason: (reason["zotero_key"], reason["code"], reason["message"]))


# The engine resolves these names in its own module globals. Patch those
# references once, while keeping this strict facade as the public import path.
_ENGINE.validate_inventory = validate_inventory
_ENGINE.validate_state = validate_state
_ENGINE._blocking_reasons = _blocking_reasons


def classify_changes(previous_state: Mapping[str, Any] | None, inventory: Mapping[str, Any]) -> dict[str, Any]:
    return _ENGINE.classify_changes(previous_state, inventory)


def build_update_plan(previous_state: Mapping[str, Any] | None, inventory: Mapping[str, Any]) -> dict[str, Any]:
    return _ENGINE.build_update_plan(previous_state, inventory)


plan_update = build_update_plan
update_review = build_update_plan


def record_published_artifact(
    state: Mapping[str, Any],
    *,
    snapshot_id: str,
    artifact_path: str,
    content_hash: str,
) -> dict[str, Any]:
    """Publish the current synthesis candidate without mutating ``state``."""

    report = validate_state(state)
    if not report["valid"]:
        raise ReviewStateError("; ".join(report["errors"]))
    if not isinstance(artifact_path, str) or not artifact_path.strip():
        raise ReviewStateError("artifact_path must be a non-empty string")
    if not isinstance(content_hash, str) or not CONTENT_HASH_RE.fullmatch(content_hash):
        raise ReviewStateError("content_hash must be sha256:<64 lowercase hex characters>")
    artifact = state.get("current_artifact")
    if not isinstance(artifact, Mapping) or artifact.get("status") != "needs_resynthesis":
        raise ReviewStateError("only a current needs_resynthesis artifact can be published")
    if artifact.get("snapshot_id") != snapshot_id:
        raise ReviewStateError("snapshot_id does not match the current artifact")
    snapshot_ids = {
        snapshot.get("snapshot_id")
        for snapshot in state.get("snapshots", [])
        if isinstance(snapshot, Mapping)
    }
    if snapshot_id not in snapshot_ids:
        raise ReviewStateError("snapshot_id does not reference an existing immutable snapshot")

    next_state = copy.deepcopy(dict(state))
    next_artifact = copy.deepcopy(dict(artifact))
    next_artifact.update(
        {
            "status": "published",
            "resynthesis_required": False,
            "artifact_path": artifact_path,
            "content_hash": content_hash,
        }
    )
    next_state["current_artifact"] = next_artifact
    return next_state


def main(argv: list[str] | None = None) -> int:
    return _ENGINE.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
