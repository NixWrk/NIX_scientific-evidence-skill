#!/usr/bin/env python3
"""Plan deterministic Zotero living-review state updates.

The script deliberately has no Zotero or third-party dependency.  A Zotero
adapter supplies a JSON inventory; this module compares hashes and maintains an
append-only snapshot history without mutating its inputs.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping


STATE_SCHEMA = "ZLR-001/v1"
INVENTORY_SCHEMA = "ZLR-INV-001/v1"
PLAN_SCHEMA = "ZLR-PLAN-001/v1"
VALID_ANNOTATION_STATUSES = {"validated", "pending", "missing", "invalidated", "draft", "rejected"}
CONTEXT_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class ReviewStateError(ValueError):
    """Raised when a state or inventory cannot be safely compared."""


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _collection_identity(collection: Mapping[str, Any]) -> tuple[Any, Any]:
    return (collection.get("library_id"), collection.get("collection_key"))


def _item_map(items: Any, *, source: str) -> dict[str, dict[str, Any]]:
    """Return item records keyed by Zotero key, preserving no caller objects."""

    if isinstance(items, Mapping):
        records: list[dict[str, Any]] = []
        for key, value in items.items():
            if not isinstance(value, Mapping):
                raise ReviewStateError(f"{source}: item {key!r} must be an object")
            record = copy.deepcopy(dict(value))
            record.setdefault("zotero_key", key)
            records.append(record)
    elif isinstance(items, list):
        records = []
        for index, value in enumerate(items):
            if not isinstance(value, Mapping):
                raise ReviewStateError(f"{source}: items[{index}] must be an object")
            records.append(copy.deepcopy(dict(value)))
    else:
        raise ReviewStateError(f"{source}: items must be an object or array")

    result: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        key = record.get("zotero_key")
        if not _is_nonempty_string(key):
            raise ReviewStateError(f"{source}: items[{index}] needs a non-empty zotero_key")
        if key in result:
            raise ReviewStateError(f"{source}: duplicate zotero_key {key!r}")
        result[key] = record
    return {key: result[key] for key in sorted(result)}


def _validate_context_hash(value: Any, where: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not CONTEXT_HASH_RE.fullmatch(value):
        errors.append(f"{where}: expected sha256:<64 lowercase hex characters>")


def validate_inventory(inventory: Mapping[str, Any]) -> dict[str, Any]:
    """Validate an inventory and return a report without changing it."""

    errors: list[str] = []
    if not isinstance(inventory, Mapping):
        return {"valid": False, "errors": ["inventory: expected an object"], "counts": {}}

    for field in ("review_id", "project_id", "corpus_id"):
        if not _is_nonempty_string(inventory.get(field)):
            errors.append(f"inventory: missing {field}")
    collection = inventory.get("collection")
    if not isinstance(collection, Mapping):
        errors.append("inventory: collection must be an object")
    else:
        for field in ("library_id", "collection_key"):
            if not _is_nonempty_string(collection.get(field)):
                errors.append(f"inventory.collection: missing {field}")
    _validate_context_hash(inventory.get("project_context_hash"), "inventory.project_context_hash", errors)

    try:
        items = _item_map(inventory.get("items"), source="inventory")
    except ReviewStateError as exc:
        errors.append(str(exc))
        items = {}
    for key, item in items.items():
        for field in ("source_content_hash", "annotation_hash"):
            if not _is_nonempty_string(item.get(field)):
                errors.append(f"inventory.items[{key}]: missing {field}")
        status = item.get("annotation_status")
        if status not in VALID_ANNOTATION_STATUSES:
            errors.append(
                f"inventory.items[{key}]: annotation_status must be one of "
                f"{sorted(VALID_ANNOTATION_STATUSES)}"
            )
        if "project_context_hash" in item:
            _validate_context_hash(item.get("project_context_hash"), f"inventory.items[{key}].project_context_hash", errors)

    return {"valid": not errors, "errors": errors, "counts": {"items": len(items)}}


def validate_state(state: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the structural invariants of a review state."""

    errors: list[str] = []
    if not isinstance(state, Mapping):
        return {"valid": False, "errors": ["state: expected an object"], "counts": {}}
    for field in ("review_id", "project_id", "corpus_id"):
        if not _is_nonempty_string(state.get(field)):
            errors.append(f"state: missing {field}")
    if state.get("schema_version") != STATE_SCHEMA:
        errors.append(f"state.schema_version: expected {STATE_SCHEMA!r}")
    collection = state.get("collection")
    if not isinstance(collection, Mapping):
        errors.append("state: collection must be an object")
    else:
        for field in ("library_id", "collection_key"):
            if not _is_nonempty_string(collection.get(field)):
                errors.append(f"state.collection: missing {field}")
    _validate_context_hash(state.get("project_context_hash"), "state.project_context_hash", errors)

    try:
        items = _item_map(state.get("items"), source="state")
    except ReviewStateError as exc:
        errors.append(str(exc))
        items = {}
    for key, item in items.items():
        if item.get("status", "active") not in {"active", "removed"}:
            errors.append(f"state.items[{key}]: status must be active or removed")
        for field in ("source_content_hash", "annotation_hash"):
            if not _is_nonempty_string(item.get(field)):
                errors.append(f"state.items[{key}]: missing {field}")
        if item.get("annotation_status") not in VALID_ANNOTATION_STATUSES:
            errors.append(f"state.items[{key}]: invalid annotation_status")

    snapshots = state.get("snapshots")
    if not isinstance(snapshots, list):
        errors.append("state: snapshots must be an array")
        snapshots = []
    snapshot_ids: set[str] = set()
    for index, snapshot in enumerate(snapshots):
        if not isinstance(snapshot, Mapping):
            errors.append(f"state.snapshots[{index}]: expected an object")
            continue
        snapshot_id = snapshot.get("snapshot_id")
        if not _is_nonempty_string(snapshot_id):
            errors.append(f"state.snapshots[{index}]: missing snapshot_id")
        elif snapshot_id in snapshot_ids:
            errors.append(f"state.snapshots: duplicate snapshot_id {snapshot_id!r}")
        else:
            snapshot_ids.add(snapshot_id)
        if snapshot.get("immutable") is not True:
            errors.append(f"state.snapshots[{index}]: immutable must be true")
        keys = snapshot.get("item_keys")
        if not isinstance(keys, list) or keys != sorted(keys) or len(keys) != len(set(keys)):
            errors.append(f"state.snapshots[{index}]: item_keys must be sorted and unique")

    artifact = state.get("current_artifact")
    if artifact is not None and not isinstance(artifact, Mapping):
        errors.append("state.current_artifact: expected an object or null")
    elif isinstance(artifact, Mapping) and artifact.get("status") not in {
        "needs_resynthesis",
        "blocked",
        "published",
    }:
        errors.append("state.current_artifact: invalid status")

    return {
        "valid": not errors,
        "errors": errors,
        "counts": {"items": len(items), "snapshots": len(snapshots)},
    }


def _validated_inventory(inventory: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    report = validate_inventory(inventory)
    if not report["valid"]:
        raise ReviewStateError("; ".join(report["errors"]))
    normalized = copy.deepcopy(dict(inventory))
    normalized["items"] = list(_item_map(inventory["items"], source="inventory").values())
    return normalized, {item["zotero_key"]: item for item in normalized["items"]}


def _validated_previous(state: Mapping[str, Any] | None) -> tuple[dict[str, Any] | None, dict[str, dict[str, Any]]]:
    if state is None:
        return None, {}
    if not state:
        return None, {}
    report = validate_state(state)
    if not report["valid"]:
        raise ReviewStateError("; ".join(report["errors"]))
    normalized = copy.deepcopy(dict(state))
    items = _item_map(state["items"], source="state")
    normalized["items"] = items
    return normalized, items


def _identity_errors(previous: Mapping[str, Any] | None, inventory: Mapping[str, Any]) -> list[str]:
    if previous is None:
        return []
    errors: list[str] = []
    for field in ("review_id", "project_id", "corpus_id"):
        if previous.get(field) != inventory.get(field):
            errors.append(f"identity mismatch: {field} differs")
    if _collection_identity(previous.get("collection", {})) != _collection_identity(inventory.get("collection", {})):
        errors.append("identity mismatch: collection binding differs")
    return errors


def classify_changes(previous_state: Mapping[str, Any] | None, inventory: Mapping[str, Any]) -> dict[str, Any]:
    """Classify item and project-context changes without updating state."""

    normalized_inventory, current_items = _validated_inventory(inventory)
    previous, previous_items = _validated_previous(previous_state)
    identity_errors = _identity_errors(previous, normalized_inventory)
    if identity_errors:
        raise ReviewStateError("; ".join(identity_errors))

    active_previous = {
        key: item for key, item in previous_items.items() if item.get("status", "active") != "removed"
    }
    current_keys = set(current_items)
    previous_keys = set(active_previous)
    added = sorted(current_keys - previous_keys)
    removed = sorted(previous_keys - current_keys)
    source_changed: list[str] = []
    annotation_changed: list[str] = []
    unchanged: list[str] = []

    for key in sorted(current_keys & previous_keys):
        old = active_previous[key]
        new = current_items[key]
        if old.get("source_content_hash") != new.get("source_content_hash"):
            source_changed.append(key)
        if any(
            old.get(field) != new.get(field)
            for field in ("annotation_hash", "annotation_status", "project_context_hash", "annotation_context_hash")
        ):
            annotation_changed.append(key)
        if key not in source_changed and key not in annotation_changed:
            unchanged.append(key)

    context_changed = previous is not None and previous.get("project_context_hash") != normalized_inventory.get("project_context_hash")
    initial = previous is None or not previous.get("snapshots")
    return {
        "added": added,
        "source_changed": source_changed,
        "annotation_changed": annotation_changed,
        "removed": removed,
        "unchanged": unchanged,
        "context_changed": bool(context_changed),
        "initial": bool(initial),
    }


def _context_for_item(item: Mapping[str, Any]) -> Any:
    return item.get("project_context_hash", item.get("annotation_context_hash"))


def _blocking_reasons(
    changes: Mapping[str, Any],
    previous_items: Mapping[str, Mapping[str, Any]],
    current_items: Mapping[str, Mapping[str, Any]],
    current_context: str,
) -> list[dict[str, str]]:
    reasons: list[dict[str, str]] = []

    def add(key: str, code: str, message: str) -> None:
        reasons.append({"zotero_key": key, "code": code, "message": message})

    for key in changes["added"]:
        if current_items[key].get("annotation_status") != "validated":
            add(key, "annotation_not_validated", "added item has no validated annotation")

    for key in changes["source_changed"]:
        current = current_items[key]
        old = previous_items[key]
        if current.get("annotation_status") != "validated":
            add(key, "annotation_not_validated", "source changed without a validated annotation")
        if current.get("annotation_hash") == old.get("annotation_hash"):
            add(key, "annotation_not_rebuilt", "source changed but annotation_hash did not change")

    for key in changes["annotation_changed"]:
        if current_items[key].get("annotation_status") != "validated":
            add(key, "annotation_not_validated", "changed annotation is not validated")

    if changes["context_changed"]:
        for key, item in current_items.items():
            if item.get("annotation_status") != "validated":
                add(key, "context_annotation_not_validated", "project context changed and annotation is not validated")
            item_context = _context_for_item(item)
            if item_context != current_context:
                add(key, "stale_project_context", "annotation does not carry the current project_context_hash")

    # Keep deterministic output while retaining multiple independent reasons.
    return sorted(reasons, key=lambda reason: (reason["zotero_key"], reason["code"], reason["message"]))


def _snapshot_payload(inventory: Mapping[str, Any], current_items: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": INVENTORY_SCHEMA,
        "review_id": inventory["review_id"],
        "project_id": inventory["project_id"],
        "corpus_id": inventory["corpus_id"],
        "collection": copy.deepcopy(inventory["collection"]),
        "project_context_hash": inventory["project_context_hash"],
        "items": [copy.deepcopy(current_items[key]) for key in sorted(current_items)],
    }


def _snapshot_id(payload: Mapping[str, Any]) -> str:
    return "SNAP-" + hashlib.sha256(_canonical(payload).encode("utf-8")).hexdigest()[:16]


def _history_event(event: str, snapshot_id: str, item: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "event": event,
        "snapshot_id": snapshot_id,
        "source_content_hash": item.get("source_content_hash"),
        "annotation_hash": item.get("annotation_hash"),
        "annotation_status": item.get("annotation_status"),
    }


def build_update_plan(previous_state: Mapping[str, Any] | None, inventory: Mapping[str, Any]) -> dict[str, Any]:
    """Return a plan and next state for one deterministic inventory update."""

    normalized_inventory, current_items = _validated_inventory(inventory)
    previous, previous_items = _validated_previous(previous_state)
    identity_errors = _identity_errors(previous, normalized_inventory)
    if identity_errors:
        raise ReviewStateError("; ".join(identity_errors))
    changes = classify_changes(previous, normalized_inventory)
    reasons = _blocking_reasons(
        changes,
        {key: value for key, value in previous_items.items() if value.get("status", "active") != "removed"},
        current_items,
        normalized_inventory["project_context_hash"],
    )
    blocked = bool(reasons)

    if previous is None:
        next_state: dict[str, Any] = {
            "schema_version": STATE_SCHEMA,
            "review_id": normalized_inventory["review_id"],
            "project_id": normalized_inventory["project_id"],
            "corpus_id": normalized_inventory["corpus_id"],
            "collection": copy.deepcopy(normalized_inventory["collection"]),
            "project_context_hash": normalized_inventory["project_context_hash"],
            "items": {},
            "snapshots": [],
            "current_artifact": None,
        }
    else:
        next_state = copy.deepcopy(previous)

    relevant = bool(
        changes["initial"]
        or changes["added"]
        or changes["source_changed"]
        or changes["annotation_changed"]
        or changes["removed"]
        or changes["context_changed"]
    )
    snapshot_id: str | None = None
    if relevant:
        payload = _snapshot_payload(normalized_inventory, current_items)
        snapshot_id = _snapshot_id(payload)
        existing_snapshot_ids = {snapshot.get("snapshot_id") for snapshot in next_state.get("snapshots", [])}
        if snapshot_id not in existing_snapshot_ids:
            next_state["snapshots"] = copy.deepcopy(next_state.get("snapshots", []))
            next_state["snapshots"].append(
                {
                    "snapshot_id": snapshot_id,
                    "corpus_id": normalized_inventory["corpus_id"],
                    "project_context_hash": normalized_inventory["project_context_hash"],
                    "collection": copy.deepcopy(normalized_inventory["collection"]),
                    "inventory_hash": _digest(payload),
                    "item_keys": sorted(current_items),
                    "items": [copy.deepcopy(current_items[key]) for key in sorted(current_items)],
                    "immutable": True,
                }
            )

        previous_item_map = next_state.get("items", {})
        previous_item_map = _item_map(previous_item_map, source="state") if previous_item_map else {}
        updated_items: dict[str, dict[str, Any]] = {}
        for key in sorted(current_items):
            current = copy.deepcopy(current_items[key])
            old = previous_item_map.get(key)
            if old is None:
                record = current
                record["status"] = "active"
                record["first_seen_snapshot_id"] = snapshot_id
                record["last_seen_snapshot_id"] = snapshot_id
                record["history"] = [_history_event("added", snapshot_id, current)]
            else:
                record = copy.deepcopy(old)
                record.update(current)
                record["status"] = "active"
                record["last_seen_snapshot_id"] = snapshot_id
                record.pop("removed_in_snapshot_id", None)
                history = list(record.get("history", []))
                event: str | None = None
                if old.get("status") == "removed":
                    event = "reappeared"
                elif key in changes["source_changed"] and key in changes["annotation_changed"]:
                    event = "source_and_annotation_changed"
                elif key in changes["source_changed"]:
                    event = "source_changed"
                elif key in changes["annotation_changed"]:
                    event = "annotation_changed"
                elif changes["context_changed"]:
                    event = "context_changed"
                if event:
                    history.append(_history_event(event, snapshot_id, current))
                record["history"] = history
            updated_items[key] = record

        for key in changes["removed"]:
            old = previous_item_map[key]
            record = copy.deepcopy(old)
            record["status"] = "removed"
            record["removed_in_snapshot_id"] = snapshot_id
            history = list(record.get("history", []))
            history.append(_history_event("removed", snapshot_id, old))
            record["history"] = history
            updated_items[key] = record

        next_state["items"] = {key: updated_items[key] for key in sorted(updated_items)}
        next_state["project_context_hash"] = normalized_inventory["project_context_hash"]
        next_state["collection"] = copy.deepcopy(normalized_inventory["collection"])
        artifact_version = len(next_state["snapshots"])
        next_state["current_artifact"] = {
            "artifact_id": f"ART-{normalized_inventory['review_id']}-{snapshot_id}",
            "snapshot_id": snapshot_id,
            "version": artifact_version,
            "status": "blocked" if blocked else "needs_resynthesis",
            "resynthesis_required": True,
        }

    else:
        artifact = next_state.get("current_artifact")
        if isinstance(artifact, Mapping):
            snapshot_id = artifact.get("snapshot_id")

    artifact = next_state.get("current_artifact")
    pending_artifact = isinstance(artifact, Mapping) and artifact.get("status") in {
        "blocked",
        "needs_resynthesis",
    }
    plan = {
        "schema_version": PLAN_SCHEMA,
        "review_id": normalized_inventory["review_id"],
        "project_id": normalized_inventory["project_id"],
        "corpus_id": normalized_inventory["corpus_id"],
        "changes": changes,
        "relevant_change": relevant,
        "snapshot_required": relevant,
        "snapshot_id": snapshot_id,
        "resynthesis_required": bool(relevant or pending_artifact),
        "synthesis_blocked": bool(blocked or (not relevant and isinstance(artifact, Mapping) and artifact.get("status") == "blocked")),
        "blocking_reasons": reasons,
        "current_artifact": copy.deepcopy(artifact),
        "state": next_state,
    }
    return plan


# Friendly aliases for callers that describe this operation as a plan update.
plan_update = build_update_plan
update_review = build_update_plan


def _read_json(path: str) -> Any:
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str, value: Any) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path == "-":
        sys.stdout.write(text)
    else:
        Path(path).write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("previous_state", help="previous review state JSON, or - for an initial sync")
    parser.add_argument("current_inventory", help="current Zotero inventory JSON")
    parser.add_argument("--output", default="-", help="next state JSON path (default: stdout)")
    parser.add_argument("--plan-output", help="optional plan JSON path")
    args = parser.parse_args(argv)

    try:
        previous = None if args.previous_state == "-" else _read_json(args.previous_state)
        inventory = _read_json(args.current_inventory)
        result = build_update_plan(previous, inventory)
    except (OSError, json.JSONDecodeError, ReviewStateError) as exc:
        parser.error(str(exc))
        return 2

    _write_json(args.output, result["state"])
    if args.plan_output:
        plan = {key: copy.deepcopy(value) for key, value in result.items() if key != "state"}
        _write_json(args.plan_output, plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
