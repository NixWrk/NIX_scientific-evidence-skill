"""Validate an RP-001/v1 research project manifest without dependencies."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

SCHEMA_VERSION = "RP-001/v1"
PROJECT_KINDS = (
    "candidate_dissertation",
    "article",
    "study",
    "report",
    "exploratory",
    "other",
)
PROJECT_STATUSES = ("draft", "active", "paused", "completed", "archived")
ARTIFACT_STATUSES = ("planned", "draft", "active", "published", "archived")
CORPUS_POLICIES = ("dynamic", "frozen")
ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9]+)+$")
HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
RFC3339_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$"
)

CONTEXT_KEYS = (
    "problem",
    "goal",
    "objectives",
    "research_questions",
    "scope",
    "exclusions",
)
ROOT_KEYS = {
    "schema_version",
    "project_id",
    "context_hash",
    "project_kind",
    "parent_project_id",
    "title",
    "status",
    "context",
    "zotero_collection_bindings",
    "corpora",
    "artifacts",
    "linked_manifests",
}
OBJECTIVE_KEYS = {"objective_id", "text"}
QUESTION_KEYS = {"question_id", "text"}
BINDING_KEYS = {"binding_id", "library", "collection_key", "label"}
CORPUS_KEYS = {
    "corpus_id",
    "label",
    "policy",
    "binding_ids",
    "objective_ids",
    "question_ids",
    "snapshots",
    "active_snapshot_id",
}
SNAPSHOT_KEYS = {"snapshot_id", "captured_at", "item_keys", "content_hash"}
ARTIFACT_KEYS = {"artifact_id", "kind", "path", "status", "linked_manifest_ids"}
LINKED_MANIFEST_KEYS = {"manifest_id", "kind", "path", "relation"}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _unexpected(record: Mapping[str, Any], allowed: set[str], path: str, errors: list[str]) -> None:
    for key in sorted(set(record) - allowed):
        errors.append(f"{path}: unexpected field {key!r}")


def _required_strings(
    record: Mapping[str, Any], keys: tuple[str, ...], path: str, errors: list[str]
) -> None:
    for key in keys:
        if not _nonempty(record.get(key)):
            errors.append(f"{path}.{key}: expected a non-empty string")


def _check_id(value: Any, path: str, errors: list[str]) -> bool:
    if not _nonempty(value):
        errors.append(f"{path}: expected a non-empty stable identifier")
        return False
    if not ID_PATTERN.fullmatch(value):
        errors.append(
            f"{path}: invalid identifier; use letters/digits and hyphen-separated components"
        )
        return False
    return True


def _remember_id(value: Any, path: str, seen: set[str], errors: list[str]) -> None:
    if _check_id(value, path, errors):
        if value in seen:
            errors.append(f"{path}: duplicate identifier {value!r}")
        else:
            seen.add(value)


def _check_hash(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or not HASH_PATTERN.fullmatch(value):
        errors.append(f"{path}: expected lowercase 'sha256:<64 hex digits>'")
        return False
    return True


def _validate_text_list(value: Any, path: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{path}: expected a list of non-empty strings")
        return []
    result: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        here = f"{path}[{index}]"
        if not _nonempty(item):
            errors.append(f"{here}: expected a non-empty string")
            continue
        if item in seen:
            errors.append(f"{here}: duplicate value {item!r}")
        seen.add(item)
        result.append(item)
    return result


def _validate_ref_list(
    value: Any, path: str, target_ids: set[str], errors: list[str]
) -> list[str]:
    if not isinstance(value, list):
        errors.append(f"{path}: expected a list of identifiers")
        return []
    result: list[str] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        here = f"{path}[{index}]"
        if not _check_id(item, here, errors):
            continue
        if item in seen:
            errors.append(f"{here}: duplicate reference {item!r}")
        seen.add(item)
        if item not in target_ids:
            errors.append(f"{here}: broken reference to {item!r}")
        result.append(item)
    return result


def context_hash_for_context(context: Mapping[str, Any]) -> str:
    """Return the canonical RP-001 hash for project-relative context only."""

    if not isinstance(context, Mapping):
        raise ValueError("context must be an object")
    missing = [key for key in CONTEXT_KEYS if key not in context]
    extra = sorted(set(context) - set(CONTEXT_KEYS))
    if missing or extra:
        details: list[str] = []
        if missing:
            details.append(f"missing {', '.join(missing)}")
        if extra:
            details.append(f"unexpected {', '.join(extra)}")
        raise ValueError("context shape is invalid (" + "; ".join(details) + ")")
    payload = {key: context[key] for key in CONTEXT_KEYS}
    try:
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError(f"context is not canonical JSON: {error}") from error
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def context_hash_for_manifest(manifest: Mapping[str, Any]) -> str:
    """Return the expected context hash for a manifest-like mapping."""

    if not isinstance(manifest, Mapping):
        raise ValueError("manifest must be an object")
    return context_hash_for_context(manifest.get("context"))


def _validate_context(context: Any, errors: list[str]) -> bool:
    if not isinstance(context, dict):
        errors.append("manifest.context: expected an object")
        return False
    _unexpected(context, set(CONTEXT_KEYS), "manifest.context", errors)
    for key in ("problem", "goal", "scope"):
        if not _nonempty(context.get(key)):
            errors.append(f"manifest.context.{key}: expected a non-empty string")

    objectives = context.get("objectives")
    if not isinstance(objectives, list) or not objectives:
        errors.append("manifest.context.objectives: expected a non-empty list")
        objectives = []
    objective_ids: set[str] = set()
    for index, objective in enumerate(objectives):
        path = f"manifest.context.objectives[{index}]"
        if not isinstance(objective, dict):
            errors.append(f"{path}: expected an object")
            continue
        _unexpected(objective, OBJECTIVE_KEYS, path, errors)
        _required_strings(objective, ("text",), path, errors)
        _remember_id(objective.get("objective_id"), f"{path}.objective_id", objective_ids, errors)

    questions = context.get("research_questions")
    if not isinstance(questions, list) or not questions:
        errors.append("manifest.context.research_questions: expected a non-empty list")
        questions = []
    question_ids: set[str] = set()
    for index, question in enumerate(questions):
        path = f"manifest.context.research_questions[{index}]"
        if not isinstance(question, dict):
            errors.append(f"{path}: expected an object")
            continue
        _unexpected(question, QUESTION_KEYS, path, errors)
        _required_strings(question, ("text",), path, errors)
        _remember_id(question.get("question_id"), f"{path}.question_id", question_ids, errors)

    _validate_text_list(context.get("exclusions"), "manifest.context.exclusions", errors)
    return True


def _parse_rfc3339(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def validate_project(data: Any) -> dict[str, Any]:
    """Return a deterministic validation report for one project manifest."""

    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return {
            "valid": False,
            "errors": ["manifest: expected a JSON object"],
            "warnings": [],
            "counts": {},
        }

    _unexpected(data, ROOT_KEYS, "manifest", errors)
    _required_strings(
        data,
        ("schema_version", "project_id", "context_hash", "title", "status"),
        "manifest",
        errors,
    )
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"manifest.schema_version: expected {SCHEMA_VERSION!r}")

    project_id = data.get("project_id")
    project_id_valid = _check_id(project_id, "manifest.project_id", errors)
    if data.get("project_kind") not in PROJECT_KINDS:
        errors.append(f"manifest.project_kind: expected one of {list(PROJECT_KINDS)}")
    if data.get("status") not in PROJECT_STATUSES:
        errors.append(f"manifest.status: expected one of {list(PROJECT_STATUSES)}")

    parent = data.get("parent_project_id")
    if parent is not None:
        if _check_id(parent, "manifest.parent_project_id", errors) and project_id_valid and parent == project_id:
            errors.append("manifest.parent_project_id: self-link is not allowed")

    context = data.get("context")
    context_valid = _validate_context(context, errors)
    try:
        expected_context_hash = context_hash_for_context(context)
    except ValueError:
        expected_context_hash = None
    if _check_hash(data.get("context_hash"), "manifest.context_hash", errors) and expected_context_hash:
        if data["context_hash"] != expected_context_hash:
            errors.append(
                "manifest.context_hash: mismatch; recompute from project-relative context "
                f"(expected {expected_context_hash})"
            )

    binding_ids: set[str] = set()
    collection_keys: set[str] = set()
    bindings = data.get("zotero_collection_bindings")
    if not isinstance(bindings, list):
        errors.append("manifest.zotero_collection_bindings: expected a list")
        bindings = []
    for index, binding in enumerate(bindings):
        path = f"manifest.zotero_collection_bindings[{index}]"
        if not isinstance(binding, dict):
            errors.append(f"{path}: expected an object")
            continue
        _unexpected(binding, BINDING_KEYS, path, errors)
        _required_strings(binding, ("library", "collection_key", "label"), path, errors)
        _remember_id(binding.get("binding_id"), f"{path}.binding_id", binding_ids, errors)
        key = binding.get("collection_key")
        if _nonempty(key):
            if key in collection_keys:
                errors.append(f"{path}.collection_key: duplicate collection key {key!r}")
            collection_keys.add(key)

    linked_manifest_ids: set[str] = set()
    linked_manifests = data.get("linked_manifests")
    if not isinstance(linked_manifests, list):
        errors.append("manifest.linked_manifests: expected a list")
        linked_manifests = []
    for index, linked in enumerate(linked_manifests):
        path = f"manifest.linked_manifests[{index}]"
        if not isinstance(linked, dict):
            errors.append(f"{path}: expected an object")
            continue
        _unexpected(linked, LINKED_MANIFEST_KEYS, path, errors)
        _required_strings(linked, ("kind", "path", "relation"), path, errors)
        _remember_id(linked.get("manifest_id"), f"{path}.manifest_id", linked_manifest_ids, errors)

    objective_ids = {
        item.get("objective_id")
        for item in (context.get("objectives", []) if isinstance(context, dict) else [])
        if isinstance(item, dict) and _nonempty(item.get("objective_id"))
    }
    question_ids = {
        item.get("question_id")
        for item in (context.get("research_questions", []) if isinstance(context, dict) else [])
        if isinstance(item, dict) and _nonempty(item.get("question_id"))
    }

    corpus_ids: set[str] = set()
    snapshot_ids: set[str] = set()
    corpora = data.get("corpora")
    if not isinstance(corpora, list):
        errors.append("manifest.corpora: expected a list")
        corpora = []
    for index, corpus in enumerate(corpora):
        path = f"manifest.corpora[{index}]"
        if not isinstance(corpus, dict):
            errors.append(f"{path}: expected an object")
            continue
        _unexpected(corpus, CORPUS_KEYS, path, errors)
        _required_strings(corpus, ("label",), path, errors)
        if "active_snapshot_id" not in corpus:
            errors.append(f"{path}.active_snapshot_id: expected a string or null")
        _remember_id(corpus.get("corpus_id"), f"{path}.corpus_id", corpus_ids, errors)
        policy = corpus.get("policy")
        if policy not in CORPUS_POLICIES:
            errors.append(f"{path}.policy: expected one of {list(CORPUS_POLICIES)}")
        _validate_ref_list(corpus.get("binding_ids"), f"{path}.binding_ids", binding_ids, errors)
        _validate_ref_list(corpus.get("objective_ids"), f"{path}.objective_ids", objective_ids, errors)
        _validate_ref_list(corpus.get("question_ids"), f"{path}.question_ids", question_ids, errors)

        snapshots = corpus.get("snapshots")
        if not isinstance(snapshots, list):
            errors.append(f"{path}.snapshots: expected a list")
            snapshots = []
        local_snapshot_ids: set[str] = set()
        for snapshot_index, snapshot in enumerate(snapshots):
            snapshot_path = f"{path}.snapshots[{snapshot_index}]"
            if not isinstance(snapshot, dict):
                errors.append(f"{snapshot_path}: expected an object")
                continue
            _unexpected(snapshot, SNAPSHOT_KEYS, snapshot_path, errors)
            _required_strings(snapshot, ("captured_at",), snapshot_path, errors)
            snapshot_id = snapshot.get("snapshot_id")
            _remember_id(snapshot_id, f"{snapshot_path}.snapshot_id", local_snapshot_ids, errors)
            if _nonempty(snapshot_id):
                if snapshot_id in snapshot_ids:
                    errors.append(f"{snapshot_path}.snapshot_id: duplicate identifier {snapshot_id!r}")
                snapshot_ids.add(snapshot_id)
            captured_at = snapshot.get("captured_at")
            if _nonempty(captured_at) and (
                not RFC3339_PATTERN.fullmatch(captured_at) or _parse_rfc3339(captured_at) is None
            ):
                errors.append(
                    f"{snapshot_path}.captured_at: expected an RFC-3339 timestamp with timezone"
                )
            _validate_text_list(snapshot.get("item_keys"), f"{snapshot_path}.item_keys", errors)
            _check_hash(snapshot.get("content_hash"), f"{snapshot_path}.content_hash", errors)

        active = corpus.get("active_snapshot_id")
        if policy == "dynamic":
            if not snapshots:
                if active is not None:
                    errors.append(
                        f"{path}.active_snapshot_id: must be null before the first dynamic snapshot"
                    )
            elif not _nonempty(active):
                errors.append(
                    f"{path}.active_snapshot_id: expected a non-empty snapshot identifier when snapshots exist"
                )
            elif active not in local_snapshot_ids:
                errors.append(f"{path}.active_snapshot_id: broken reference to {active!r}")
        elif policy == "frozen":
            if len(snapshots) != 1:
                errors.append(f"{path}: frozen corpus requires exactly one snapshot")
            if not _nonempty(active):
                errors.append(
                    f"{path}.active_snapshot_id: frozen corpus requires a non-empty active snapshot"
                )
            elif active not in local_snapshot_ids:
                errors.append(f"{path}.active_snapshot_id: broken reference to {active!r}")

    artifact_ids: set[str] = set()
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("manifest.artifacts: expected a list")
        artifacts = []
    for index, artifact in enumerate(artifacts):
        path = f"manifest.artifacts[{index}]"
        if not isinstance(artifact, dict):
            errors.append(f"{path}: expected an object")
            continue
        _unexpected(artifact, ARTIFACT_KEYS, path, errors)
        _required_strings(artifact, ("kind", "path"), path, errors)
        _remember_id(artifact.get("artifact_id"), f"{path}.artifact_id", artifact_ids, errors)
        if artifact.get("status") not in ARTIFACT_STATUSES:
            errors.append(f"{path}.status: expected one of {list(ARTIFACT_STATUSES)}")
        _validate_ref_list(
            artifact.get("linked_manifest_ids"),
            f"{path}.linked_manifest_ids",
            linked_manifest_ids,
            errors,
        )

    counts = {
        "objectives": len(objective_ids),
        "research_questions": len(question_ids),
        "zotero_bindings": len(binding_ids),
        "corpora": len(corpus_ids),
        "snapshots": len(snapshot_ids),
        "artifacts": len(artifact_ids),
        "linked_manifests": len(linked_manifest_ids),
    }
    if not context_valid:
        warnings.append("manifest.context: context-dependent references may be incomplete")
    return {"valid": not errors, "errors": errors, "warnings": warnings, "counts": counts}


def _reject_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON constant {value!r} is not allowed")


def _load_manifest(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"), parse_constant=_reject_constant)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path to an RP-001/v1 JSON manifest")
    parser.add_argument(
        "--print-context-hash",
        action="store_true",
        help="Print the deterministic context hash instead of the validation report",
    )
    args = parser.parse_args(argv)
    try:
        data = _load_manifest(args.manifest)
        if args.print_context_hash:
            print(context_hash_for_manifest(data))
            return 0
        report = validate_project(data)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        report = {"valid": False, "errors": [str(error)], "warnings": [], "counts": {}}
    print(json.dumps(report, ensure_ascii=False, indent=2) + "\n", end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
