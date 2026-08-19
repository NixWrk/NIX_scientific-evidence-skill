#!/usr/bin/env python3
"""Validate one Zotero project annotation without external packages."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
TARGET_RE = re.compile(r"^(?:RQ|OBJ)-[A-Za-z0-9][A-Za-z0-9._:-]*$")
STATUSES = {"current", "stale", "blocked_metadata_only"}
READ_SCOPES = {"full_text", "sections", "metadata_only"}

TOP_FIELDS = {
    "schema_version",
    "annotation_id",
    "record_type",
    "status",
    "remake_required",
    "stale_reason",
    "block_reason",
    "metadata_only",
    "source_content_hash",
    "project_context_hash",
    "source",
    "project",
    "relevance_target_ids",
    "annotation",
    "evidence_role",
    "provenance",
}
SOURCE_FIELDS = {"zotero_item_key", "title", "content_hash", "read_scope", "locators_read"}
PROJECT_FIELDS = {"project_id", "title", "goal", "objectives", "research_questions", "project_context_hash"}
TARGET_FIELDS = {"id", "text"}
ANNOTATION_FIELDS = {"summary", "source_voice", "author_conclusion", "project_judgement"}
SOURCE_VOICE_FIELDS = {"what_work_did", "reported_outcomes", "stated_boundaries"}
OUTCOME_FIELDS = {"claim_id", "statement", "value", "locator"}
JUDGEMENT_FIELDS = {"why_useful_here", "what_it_does_not_settle"}
PROVENANCE_FIELDS = {"created_at", "machine_record_path", "supersedes_annotation_id", "zotero_note_key"}


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _unexpected(value: Any, allowed: set[str], path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key in sorted(set(value) - allowed):
            errors.append(f"{path}: unexpected field {key!r}")


def _required(value: dict[str, Any], keys: tuple[str, ...], path: str, errors: list[str]) -> None:
    for key in keys:
        if not _nonempty(value.get(key)):
            errors.append(f"{path}.{key}: expected a non-empty string")


def _hash(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or not HASH_RE.fullmatch(value):
        errors.append(f"{path}: expected sha256:<64 lowercase hex digits>")
        return False
    return True


def _id(value: Any, path: str, errors: list[str]) -> bool:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        errors.append(f"{path}: invalid identifier")
        return False
    return True


def _record_list(value: Any, path: str, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        errors.append(f"{path}: expected a list")
        return []
    result: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"{path}[{index}]: expected an object")
        else:
            result.append(item)
    return result


def _project_targets(project: dict[str, Any], errors: list[str]) -> dict[str, str]:
    declared: dict[str, str] = {}
    for field, prefix in (("objectives", "OBJ-"), ("research_questions", "RQ-")):
        records = _record_list(project.get(field), f"project.{field}", errors)
        seen: set[str] = set()
        for index, item in enumerate(records):
            path = f"project.{field}[{index}]"
            _unexpected(item, TARGET_FIELDS, path, errors)
            identifier = item.get("id")
            if not _id(identifier, f"{path}.id", errors):
                continue
            if not identifier.startswith(prefix):
                errors.append(f"{path}.id: expected {prefix}<id>")
            if identifier in seen:
                errors.append(f"{path}.id: duplicate {identifier!r}")
            seen.add(identifier)
            _required(item, ("text",), path, errors)
            declared[identifier] = item.get("text") if isinstance(item.get("text"), str) else ""
    return declared


def _manifest_targets(manifest: Any) -> tuple[str | None, str | None, dict[str, str]]:
    """Collect RP target texts and context hash, while tolerating legacy shapes."""

    if not isinstance(manifest, dict):
        return None, None, {}
    project_id = manifest.get("project_id")
    context_hash = next(
        (
            manifest.get(key)
            for key in ("context_hash", "project_context_hash")
            if isinstance(manifest.get(key), str)
        ),
        None,
    )
    targets: dict[str, str] = {}
    containers = [manifest]
    for key in ("context", "project"):
        if isinstance(manifest.get(key), dict):
            containers.append(manifest[key])
    for container in containers:
        if context_hash is None:
            context_hash = next(
                (
                    container.get(key)
                    for key in ("context_hash", "project_context_hash")
                    if isinstance(container.get(key), str)
                ),
                None,
            )
        for field, prefixes in (("objectives", ("OBJ-",)), ("research_questions", ("RQ-",)), ("questions", ("RQ-",))):
            values = container.get(field)
            if not isinstance(values, list):
                continue
            for item in values:
                if not isinstance(item, dict):
                    continue
                identifier = item.get("id") or item.get("objective_id") or item.get("question_id")
                if isinstance(identifier, str) and any(identifier.startswith(prefix) for prefix in prefixes):
                    text = item.get("text")
                    targets.setdefault(identifier, text if isinstance(text, str) else "")
    return project_id if isinstance(project_id, str) else None, context_hash, targets


def _check_expected_hash(
    stored: str,
    expected: str | None,
    label: str,
    status: str,
    errors: list[str],
) -> None:
    if expected is None:
        return
    if not _hash(expected, f"expected_{label}", errors):
        return
    if stored != expected and status != "stale":
        errors.append(
            f"{label}: current value differs from expected hash; record must be status 'stale' "
            "with remake_required=true"
        )


def validate_annotation(
    data: Any,
    *,
    project_manifest: dict[str, Any] | None = None,
    source_content_hash: str | None = None,
    project_context_hash: str | None = None,
    require_project_manifest: bool = False,
) -> dict[str, Any]:
    """Return a machine-readable validation report for one derived annotation."""

    errors: list[str] = []
    warnings: list[str] = []
    if require_project_manifest and project_manifest is None:
        errors.append("project_manifest: required for operational annotation validation")
    if not isinstance(data, dict):
        return {"valid": False, "errors": ["annotation: expected an object"], "warnings": [], "counts": {}}

    _unexpected(data, TOP_FIELDS, "annotation", errors)
    if data.get("schema_version") != "ZPA-001/v1":
        errors.append("annotation.schema_version: expected 'ZPA-001/v1'")
    _required(data, ("annotation_id", "record_type", "evidence_role"), "annotation", errors)
    if _nonempty(data.get("annotation_id")):
        _id(data["annotation_id"], "annotation.annotation_id", errors)
    if data.get("record_type") != "derived_project_annotation":
        errors.append("annotation.record_type: expected 'derived_project_annotation'")
    if data.get("evidence_role") != "derived_annotation_not_evidence":
        errors.append(
            "annotation.evidence_role: expected 'derived_annotation_not_evidence'; "
            "an annotation cannot stand in for the publication"
        )

    status = data.get("status")
    if status not in STATUSES:
        errors.append(f"annotation.status: expected one of {sorted(STATUSES)}")
        status = ""
    remake_required = data.get("remake_required")
    if not isinstance(remake_required, bool):
        errors.append("annotation.remake_required: expected a boolean")
        remake_required = False
    if status == "current":
        if remake_required:
            errors.append("annotation.remake_required: current record must be false")
        if data.get("stale_reason") not in (None, ""):
            errors.append("annotation.stale_reason: current record cannot have a stale reason")
    elif status == "stale":
        if not remake_required:
            errors.append("annotation.remake_required: stale record must be true")
        if not _nonempty(data.get("stale_reason")):
            errors.append("annotation.stale_reason: required for stale record")

    metadata_only = data.get("metadata_only")
    if not isinstance(metadata_only, bool):
        errors.append("annotation.metadata_only: expected a boolean")
        metadata_only = False

    source = data.get("source")
    if not isinstance(source, dict):
        errors.append("annotation.source: expected an object")
        source = {}
    else:
        _unexpected(source, SOURCE_FIELDS, "annotation.source", errors)
    _required(source, ("zotero_item_key", "title"), "annotation.source", errors)
    if _nonempty(source.get("zotero_item_key")):
        _id(source["zotero_item_key"], "annotation.source.zotero_item_key", errors)
    read_scope = source.get("read_scope")
    if read_scope not in READ_SCOPES:
        errors.append(f"annotation.source.read_scope: expected one of {sorted(READ_SCOPES)}")
    locators = source.get("locators_read")
    if not isinstance(locators, list) or any(not _nonempty(item) for item in locators):
        errors.append("annotation.source.locators_read: expected a list of non-empty strings")

    nested_source_hash = source.get("content_hash")
    top_source_hash = data.get("source_content_hash")
    stored_source_hash = nested_source_hash or top_source_hash
    if not _hash(stored_source_hash, "annotation.source.content_hash", errors):
        stored_source_hash = ""
    if nested_source_hash is not None and top_source_hash is not None and nested_source_hash != top_source_hash:
        errors.append("annotation.source.content_hash: does not match source_content_hash")
    if top_source_hash is None:
        warnings.append("annotation.source_content_hash: top-level mirror is absent; source.content_hash remains authoritative")

    project = data.get("project")
    if not isinstance(project, dict):
        errors.append("annotation.project: expected an object")
        project = {}
    else:
        _unexpected(project, PROJECT_FIELDS, "annotation.project", errors)
    _required(project, ("project_id", "title", "goal"), "annotation.project", errors)
    if _nonempty(project.get("project_id")):
        _id(project["project_id"], "annotation.project.project_id", errors)
    declared_targets = _project_targets(project, errors)

    nested_context_hash = project.get("project_context_hash")
    top_context_hash = data.get("project_context_hash")
    stored_context_hash = top_context_hash or nested_context_hash
    if not _hash(stored_context_hash, "annotation.project_context_hash", errors):
        stored_context_hash = ""
    if nested_context_hash is not None and top_context_hash is not None and nested_context_hash != top_context_hash:
        errors.append("annotation.project_context_hash: nested and top-level values differ")

    targets = data.get("relevance_target_ids")
    if not isinstance(targets, list) or not targets:
        errors.append("annotation.relevance_target_ids: expected a non-empty list")
        targets = []
    seen_targets: set[str] = set()
    for index, target in enumerate(targets):
        path = f"annotation.relevance_target_ids[{index}]"
        if not isinstance(target, str) or not TARGET_RE.fullmatch(target):
            errors.append(f"{path}: expected an RQ- or OBJ-identifier")
            continue
        if target in seen_targets:
            errors.append(f"{path}: duplicate {target!r}")
        seen_targets.add(target)
        if target not in declared_targets:
            errors.append(f"{path}: {target!r} is not declared in annotation.project")
    if (
        require_project_manifest
        and not any(target.startswith("RQ-") for target in seen_targets)
    ):
        errors.append(
            "annotation.relevance_target_ids: operational annotation requires at least one RQ- target"
        )

    annotation = data.get("annotation")
    if not isinstance(annotation, dict):
        errors.append("annotation.annotation: expected an object")
        annotation = {}
    else:
        _unexpected(annotation, ANNOTATION_FIELDS, "annotation.annotation", errors)
    _required(annotation, ("summary", "author_conclusion"), "annotation.annotation", errors)
    source_voice = annotation.get("source_voice")
    if not isinstance(source_voice, dict):
        errors.append("annotation.annotation.source_voice: expected an object")
        source_voice = {}
    else:
        _unexpected(source_voice, SOURCE_VOICE_FIELDS, "annotation.annotation.source_voice", errors)
    _required(source_voice, ("what_work_did",), "annotation.annotation.source_voice", errors)
    outcomes = source_voice.get("reported_outcomes")
    if not isinstance(outcomes, list):
        errors.append("annotation.annotation.source_voice.reported_outcomes: expected a list")
        outcomes = []
    for index, outcome in enumerate(outcomes):
        path = f"annotation.annotation.source_voice.reported_outcomes[{index}]"
        if not isinstance(outcome, dict):
            errors.append(f"{path}: expected an object")
            continue
        _unexpected(outcome, OUTCOME_FIELDS, path, errors)
        _required(outcome, ("claim_id", "statement", "value", "locator"), path, errors)
        if _nonempty(outcome.get("claim_id")):
            _id(outcome["claim_id"], f"{path}.claim_id", errors)
    boundaries = source_voice.get("stated_boundaries")
    if not isinstance(boundaries, list) or any(not _nonempty(item) for item in boundaries):
        errors.append("annotation.annotation.source_voice.stated_boundaries: expected a list of non-empty strings")

    judgement = annotation.get("project_judgement")
    if not isinstance(judgement, dict):
        errors.append("annotation.annotation.project_judgement: expected an object")
        judgement = {}
    else:
        _unexpected(judgement, JUDGEMENT_FIELDS, "annotation.annotation.project_judgement", errors)
    _required(judgement, ("why_useful_here", "what_it_does_not_settle"), "annotation.annotation.project_judgement", errors)

    if metadata_only != (read_scope == "metadata_only"):
        errors.append("annotation.metadata_only: must agree with source.read_scope")
    if read_scope == "metadata_only":
        if status != "blocked_metadata_only":
            errors.append("annotation.status: metadata-only source must be blocked_metadata_only")
        if not remake_required:
            errors.append("annotation.remake_required: metadata-only record must require a remake")
        if not _nonempty(data.get("block_reason")):
            errors.append("annotation.block_reason: required for metadata-only record")
        if outcomes:
            errors.append("annotation.annotation.source_voice.reported_outcomes: metadata-only record cannot report outcomes")
    elif status == "blocked_metadata_only":
        errors.append("annotation.status: blocked_metadata_only requires source.read_scope metadata_only")

    provenance = data.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("annotation.provenance: expected an object")
        provenance = {}
    else:
        _unexpected(provenance, PROVENANCE_FIELDS, "annotation.provenance", errors)
    _required(provenance, ("created_at", "machine_record_path"), "annotation.provenance", errors)
    if _nonempty(provenance.get("supersedes_annotation_id")):
        _id(provenance["supersedes_annotation_id"], "annotation.provenance.supersedes_annotation_id", errors)
    note_key = provenance.get("zotero_note_key")
    if note_key not in (None, ""):
        _id(note_key, "annotation.provenance.zotero_note_key", errors)


    _check_expected_hash(stored_source_hash, source_content_hash, "source.content_hash", status, errors)
    _check_expected_hash(stored_context_hash, project_context_hash, "project_context_hash", status, errors)

    manifest_id, manifest_hash, manifest_targets = _manifest_targets(project_manifest)
    if project_manifest is not None:
        if manifest_id and manifest_id != project.get("project_id"):
            errors.append("project_manifest.project_id: does not match annotation.project.project_id")
        if manifest_hash and stored_context_hash and manifest_hash != stored_context_hash:
            errors.append(
                "project_manifest.context_hash: does not match annotation.project_context_hash"
            )
        if not manifest_targets:
            errors.append("project_manifest: no OBJ-/RQ- identifiers available for relevance validation")
        else:
            for target in seen_targets:
                if target not in manifest_targets:
                    errors.append(f"annotation.relevance_target_ids: {target!r} is absent from project manifest")
        for target, accepted_text in manifest_targets.items():
            recorded_text = declared_targets.get(target)
            if _nonempty(accepted_text) and recorded_text is not None and recorded_text != accepted_text:
                errors.append(
                    f"annotation.project target {target!r}: text differs from the accepted project manifest; "
                    "preserve the project question or objective instead of reshaping it around the source"
                )

    counts = {
        "relevance_targets": len(seen_targets),
        "reported_outcomes": len(outcomes),
        "stated_boundaries": len(boundaries) if isinstance(boundaries, list) else 0,
    }
    return {"valid": not errors, "errors": errors, "warnings": warnings, "counts": counts}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("annotation", type=Path)
    parser.add_argument("--project-manifest", type=Path, required=True)
    parser.add_argument("--source-content-hash")
    parser.add_argument("--project-context-hash")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.annotation.read_text(encoding="utf-8-sig"))
        manifest = json.loads(args.project_manifest.read_text(encoding="utf-8-sig"))
        report = validate_annotation(
            data,
            project_manifest=manifest,
            source_content_hash=args.source_content_hash,
            project_context_hash=args.project_context_hash,
            require_project_manifest=True,
        )
    except (OSError, json.JSONDecodeError) as error:
        report = {"valid": False, "errors": [str(error)], "warnings": [], "counts": {}}
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
