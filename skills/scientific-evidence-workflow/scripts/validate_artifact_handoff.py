"""Validate a versioned cross-notebook scientific artifact handoff."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


TOP_FIELDS = {
    "schema_version",
    "handoff_id",
    "record_version",
    "supersedes",
    "artifact",
    "producer",
    "validation",
    "selection_policy",
    "automation_status",
    "consumers",
}
ARTIFACT_FIELDS = {
    "artifact_id",
    "artifact_version",
    "content_hash",
    "path",
    "media_type",
    "schema_ref",
    "units",
    "scientific_status",
    "applicability_limits",
}
PRODUCER_FIELDS = {"notebook_id", "run_id", "code_version"}
VALIDATION_FIELDS = {"technical", "computational", "scientific"}
SELECTION_FIELDS = {
    "policy_id",
    "policy_version",
    "status",
    "rule_ids",
    "conflict_refs",
    "resolution_ref",
}
CONSUMER_FIELDS = {"consumer_id", "purpose", "acceptance_criterion"}

IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")
VERSION_RE = re.compile(r"^v[1-9][0-9]*$")
HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

TECHNICAL = {"not_checked", "passed", "failed", "blocked"}
COMPUTATIONAL = {"not_checked", "partial", "passed", "failed", "blocked"}
SCIENTIFIC = {"not_reviewed", "bounded", "approved", "rejected", "conflicted"}
SCIENTIFIC_STATUSES = {
    "measurement",
    "estimate",
    "bound",
    "reference",
    "approximation",
    "model_prediction",
    "placeholder",
    "hypothesis",
    "decision",
}
SELECTION_STATUSES = {"clear", "conflicted", "resolved"}
AUTOMATION_STATUSES = {"blocked", "permitted"}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _object(
    value: Any,
    *,
    path: str,
    fields: set[str],
    errors: list[str],
) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        errors.append(f"{path}: expected an object")
        return None
    for field in sorted(set(value) - fields):
        errors.append(f"{path}: unexpected field {field!r}")
    for field in sorted(fields - set(value)):
        errors.append(f"{path}: missing field {field!r}")
    return value


def _identifier(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not IDENTIFIER_RE.fullmatch(value):
        errors.append(f"{path}: expected a stable identifier")


def _version(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not VERSION_RE.fullmatch(value):
        errors.append(f"{path}: expected v<positive integer>")


def _hash(value: Any, path: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not HASH_RE.fullmatch(value):
        errors.append(f"{path}: expected sha256:<64 lowercase hex digits>")


def _nonempty_list(value: Any, path: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list) or not value:
        errors.append(f"{path}: expected a non-empty list")
        return []
    return value


def validate_handoff(data: Any) -> dict[str, Any]:
    errors: list[str] = []
    root = _object(data, path="handoff", fields=TOP_FIELDS, errors=errors)
    if root is None:
        return {"valid": False, "errors": errors}

    if root.get("schema_version") != "1.0":
        errors.append("schema_version: expected '1.0'")
    _identifier(root.get("handoff_id"), "handoff_id", errors)
    record_version = root.get("record_version")
    _version(record_version, "record_version", errors)
    supersedes = root.get("supersedes")
    if supersedes is not None:
        _identifier(supersedes, "supersedes", errors)
        if supersedes == root.get("handoff_id"):
            errors.append("supersedes: a handoff cannot supersede itself")
    if record_version == "v1" and supersedes is not None:
        errors.append("supersedes: v1 must not declare a predecessor")
    if (
        isinstance(record_version, str)
        and VERSION_RE.fullmatch(record_version)
        and record_version != "v1"
        and supersedes is None
    ):
        errors.append("supersedes: later record versions require a predecessor reference")

    artifact = _object(
        root.get("artifact"), path="artifact", fields=ARTIFACT_FIELDS, errors=errors
    )
    if artifact is not None:
        _identifier(artifact.get("artifact_id"), "artifact.artifact_id", errors)
        _version(artifact.get("artifact_version"), "artifact.artifact_version", errors)
        _hash(artifact.get("content_hash"), "artifact.content_hash", errors)
        for field in ("path", "media_type", "schema_ref", "units"):
            if not _nonempty(artifact.get(field)):
                errors.append(f"artifact.{field}: expected a non-empty string")
        if artifact.get("scientific_status") not in SCIENTIFIC_STATUSES:
            errors.append("artifact.scientific_status: unknown status")
        limits = _nonempty_list(
            artifact.get("applicability_limits"),
            "artifact.applicability_limits",
            errors,
        )
        if any(not _nonempty(item) for item in limits):
            errors.append("artifact.applicability_limits: entries must be non-empty strings")

    producer = _object(
        root.get("producer"), path="producer", fields=PRODUCER_FIELDS, errors=errors
    )
    if producer is not None:
        _identifier(producer.get("notebook_id"), "producer.notebook_id", errors)
        _identifier(producer.get("run_id"), "producer.run_id", errors)
        _hash(producer.get("code_version"), "producer.code_version", errors)

    validation = _object(
        root.get("validation"), path="validation", fields=VALIDATION_FIELDS, errors=errors
    )
    if validation is not None:
        if validation.get("technical") not in TECHNICAL:
            errors.append("validation.technical: unknown status")
        if validation.get("computational") not in COMPUTATIONAL:
            errors.append("validation.computational: unknown status")
        if validation.get("scientific") not in SCIENTIFIC:
            errors.append("validation.scientific: unknown status")

    policy = root.get("selection_policy")
    if policy is not None:
        policy = _object(
            policy, path="selection_policy", fields=SELECTION_FIELDS, errors=errors
        )
        if policy is not None:
            _identifier(policy.get("policy_id"), "selection_policy.policy_id", errors)
            _version(policy.get("policy_version"), "selection_policy.policy_version", errors)
            status = policy.get("status")
            if status not in SELECTION_STATUSES:
                errors.append("selection_policy.status: unknown status")
            rules = _nonempty_list(
                policy.get("rule_ids"), "selection_policy.rule_ids", errors
            )
            if any(not isinstance(item, str) or not IDENTIFIER_RE.fullmatch(item) for item in rules):
                errors.append("selection_policy.rule_ids: entries must be stable identifiers")
            conflicts = policy.get("conflict_refs")
            if not isinstance(conflicts, list):
                errors.append("selection_policy.conflict_refs: expected a list")
                conflicts = []
            elif any(not _nonempty(item) for item in conflicts):
                errors.append("selection_policy.conflict_refs: entries must be non-empty strings")
            resolution = policy.get("resolution_ref")
            if status == "clear" and (conflicts or resolution is not None):
                errors.append("selection_policy: clear status forbids conflicts and a resolution")
            if status == "conflicted":
                if len(conflicts) < 2:
                    errors.append("selection_policy: conflicted status requires at least two conflict_refs")
                if resolution is not None:
                    errors.append("selection_policy: unresolved conflict cannot have resolution_ref")
            if status == "resolved":
                if len(conflicts) < 2:
                    errors.append("selection_policy: resolved status requires the conflicting records")
                if not _nonempty(resolution):
                    errors.append("selection_policy: resolved status requires resolution_ref")

    automation = root.get("automation_status")
    if automation not in AUTOMATION_STATUSES:
        errors.append("automation_status: unknown status")
    if isinstance(policy, dict) and policy.get("status") == "conflicted" and automation != "blocked":
        errors.append("automation_status: unresolved selection conflict must block automation")
    if automation == "permitted" and isinstance(validation, dict):
        if validation.get("technical") != "passed":
            errors.append("automation_status: permitted use requires technical validation 'passed'")
        if validation.get("computational") != "passed":
            errors.append("automation_status: permitted use requires computational validation 'passed'")
        if validation.get("scientific") not in {"bounded", "approved"}:
            errors.append("automation_status: permitted use requires bounded or approved scientific validation")

    consumers = _nonempty_list(root.get("consumers"), "consumers", errors)
    consumer_ids: set[str] = set()
    for index, raw in enumerate(consumers):
        consumer = _object(
            raw,
            path=f"consumers[{index}]",
            fields=CONSUMER_FIELDS,
            errors=errors,
        )
        if consumer is None:
            continue
        consumer_id = consumer.get("consumer_id")
        _identifier(consumer_id, f"consumers[{index}].consumer_id", errors)
        if isinstance(consumer_id, str):
            if consumer_id in consumer_ids:
                errors.append(f"consumers[{index}].consumer_id: duplicate identifier")
            consumer_ids.add(consumer_id)
        for field in ("purpose", "acceptance_criterion"):
            if not _nonempty(consumer.get(field)):
                errors.append(f"consumers[{index}].{field}: expected a non-empty string")

    return {"valid": not errors, "errors": errors}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        data = json.loads(args.path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        report = {"valid": False, "errors": [f"cannot read JSON: {error}"]}
    else:
        report = validate_handoff(data)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("PASS" if report["valid"] else "FAIL")
        for error in report["errors"]:
            print(f"  {error}")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
