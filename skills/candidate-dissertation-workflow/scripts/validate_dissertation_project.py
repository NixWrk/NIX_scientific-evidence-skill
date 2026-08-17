#!/usr/bin/env python3
"""Validate a candidate-dissertation workflow project manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
SHA256_RE = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
STAGE_STATUSES = {"pending", "ready", "in_progress", "blocked", "complete", "not_applicable"}
ARTIFACT_STATUSES = {"draft", "validated", "final"}
GATE_STATUSES = {"pass", "fail", "not_assessed"}
SOURCE_ROLES = {"literature", "protocol", "data", "result", "organizational", "normative", "practice"}
TRUSTED_VALIDATORS = {
    "scientific-evidence-workflow/validate_bundle.py",
    "candidate-dissertation-workflow/validate_dissertation_project.py",
    "dissertation-formatting-and-apparatus/validate_critic_findings.py",
    "dissertation-formatting-and-apparatus/audit_abbreviations.py",
    "dissertation-formatting-and-apparatus/audit_terminology.py",
    "dissertation-formatting-and-apparatus/audit_bibliography.py",
    "dissertation-formatting-and-apparatus/audit_illustration_register.py",
    "dissertation-formatting-and-apparatus/audit_appendix_register.py",
    "dissertation-formatting-and-apparatus/audit_dissertation_title_page.py",
    "dissertation-formatting-and-apparatus/audit_existing_word_toc.py",
    "dissertation-formatting-and-apparatus/apply_word_review.py",
    "manual-review/PSES-DISS-001",
}
SCIENTIFIC_VALIDATOR = "scientific-evidence-workflow/validate_bundle.py"
MANUAL_VALIDATOR = "manual-review/PSES-DISS-001"
SCIENTIFIC_ARTIFACT_GENRES = {
    "dissertation-outline", "dissertation-introduction",
    "dissertation-literature-review-chapter", "dissertation-methods-chapter",
    "dissertation-results-chapter", "dissertation-synthesis-chapter",
    "dissertation-conclusion", "defense-propositions", "novelty-statement",
    "approbation-record", "thesis-synopsis",
}
ARTIFACT_VALIDATORS_BY_GENRE = {
    **{genre: {SCIENTIFIC_VALIDATOR} for genre in SCIENTIFIC_ARTIFACT_GENRES},
    "dissertation-apparatus": {MANUAL_VALIDATOR},
    "review-report": {MANUAL_VALIDATOR},
    "dissertation": {MANUAL_VALIDATOR},
}
GATE_VALIDATORS = {
    "normative_profile": {MANUAL_VALIDATOR},
    "corpus_frozen": {"candidate-dissertation-workflow/validate_dissertation_project.py"},
    "evidence": {SCIENTIFIC_VALIDATOR},
    "numbers_units": {SCIENTIFIC_VALIDATOR, MANUAL_VALIDATOR},
    "task_conclusion": {SCIENTIFIC_VALIDATOR, MANUAL_VALIDATOR},
    "terminology": {"dissertation-formatting-and-apparatus/audit_terminology.py"},
    "cross_references": {
        "dissertation-formatting-and-apparatus/audit_illustration_register.py",
        "dissertation-formatting-and-apparatus/audit_appendix_register.py",
        MANUAL_VALIDATOR,
    },
    "bibliography": {"dissertation-formatting-and-apparatus/audit_bibliography.py"},
    "word_structure": {
        "dissertation-formatting-and-apparatus/audit_dissertation_title_page.py",
        "dissertation-formatting-and-apparatus/audit_existing_word_toc.py",
        "dissertation-formatting-and-apparatus/apply_word_review.py",
        MANUAL_VALIDATOR,
    },
    "rendered_pages": {MANUAL_VALIDATOR},
}
REQUIRED_GATES = {
    "normative_profile",
    "corpus_frozen",
    "evidence",
    "numbers_units",
    "task_conclusion",
    "terminology",
    "cross_references",
    "bibliography",
    "word_structure",
    "rendered_pages",
}
CONTENT_STAGES = {
    "outline",
    "introduction",
    "literature_review",
    "methods",
    "results",
    "synthesis",
    "conclusion",
    "propositions",
    "novelty",
    "approbation",
    "synopsis",
    "apparatus",
    "final_review",
    "release",
}
STAGE_SPECS = {
    "source_search": {"genre": None, "depends_on": set(), "mandatory": False},
    "corpus_freeze": {"genre": None, "depends_on": set(), "mandatory": True},
    "outline": {"genre": "dissertation-outline", "depends_on": {"corpus_freeze"}, "mandatory": True},
    "introduction": {"genre": "dissertation-introduction", "depends_on": {"outline"}, "mandatory": True},
    "literature_review": {"genre": "dissertation-literature-review-chapter", "depends_on": {"corpus_freeze", "outline"}, "mandatory": True},
    "methods": {"genre": "dissertation-methods-chapter", "depends_on": {"outline"}, "mandatory": True},
    "results": {"genre": "dissertation-results-chapter", "depends_on": {"methods"}, "mandatory": True},
    "synthesis": {"genre": "dissertation-synthesis-chapter", "depends_on": {"results", "literature_review"}, "mandatory": False},
    "conclusion": {"genre": "dissertation-conclusion", "depends_on": {"results"}, "mandatory": True},
    "propositions": {"genre": "defense-propositions", "depends_on": {"results"}, "mandatory": True},
    "novelty": {"genre": "novelty-statement", "depends_on": {"literature_review", "results"}, "mandatory": True},
    "approbation": {"genre": "approbation-record", "depends_on": set(), "mandatory": True},
    "synopsis": {"genre": "thesis-synopsis", "depends_on": {"conclusion", "propositions", "novelty", "approbation"}, "mandatory": False},
    "apparatus": {"genre": "dissertation-apparatus", "depends_on": {"conclusion"}, "mandatory": True},
    "final_review": {"genre": None, "depends_on": {"apparatus"}, "mandatory": True},
    "release": {"genre": "dissertation", "depends_on": {"final_review"}, "mandatory": True},
}


def _records(value: Any, path: str, errors: list[str]) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        errors.append(f"{path}: expected a list")
        return []
    records: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            errors.append(f"{path}[{index}]: expected an object")
        else:
            records.append(item)
    return records


def _unique_index(records: list[dict[str, Any]], key: str, path: str, errors: list[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(records):
        identifier = item.get(key)
        if not isinstance(identifier, str) or not ID_RE.fullmatch(identifier):
            errors.append(f"{path}[{index}].{key}: invalid identifier")
            continue
        if identifier in result:
            errors.append(f"{path}[{index}].{key}: duplicate {identifier}")
        else:
            result[identifier] = item
    return result


def _validate_file_ref(
    path_value: Any,
    hash_value: Any,
    label: str,
    errors: list[str],
    base_dir: Path | None,
) -> Path | None:
    if not isinstance(path_value, str) or not path_value.strip():
        errors.append(f"{label}.path: required")
        return None
    if not isinstance(hash_value, str) or not SHA256_RE.fullmatch(hash_value):
        errors.append(f"{label}.content_hash: expected sha256:<64 hex digits>")
        return None
    if base_dir is None:
        return None
    path = Path(path_value)
    if not path.is_absolute():
        path = base_dir / path
    if not path.is_file():
        errors.append(f"{label}.path: file does not exist: {path}")
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest().casefold() != hash_value.removeprefix("sha256:").casefold():
        errors.append(f"{label}.content_hash: does not match {path}")
        return None
    return path


def _validate_report_ref(
    path_value: Any,
    hash_value: Any,
    label: str,
    errors: list[str],
    base_dir: Path | None,
) -> None:
    path = _validate_file_ref(path_value, hash_value, label, errors, base_dir)
    if path is None:
        return
    if path.suffix.casefold() != ".json":
        errors.append(f"{label}.path: validation report must be JSON")
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label}.path: invalid JSON report: {exc}")
        return
    if not isinstance(payload, dict):
        errors.append(f"{label}: validation report must be a JSON object")
        return
    valid = payload.get("valid")
    status = payload.get("status")
    report_errors = payload.get("errors", [])
    if "valid" in payload and not isinstance(valid, bool):
        errors.append(f"{label}: report valid field must be boolean")
    if "status" in payload and status not in {"pass", "fail", "not_assessed"}:
        errors.append(f"{label}: report status must be pass, fail, or not_assessed")
    if "errors" in payload and not isinstance(report_errors, list):
        errors.append(f"{label}: report errors field must be a list")
        report_errors = [report_errors]
    positive = valid is True or status == "pass"
    negative = valid is False or status in {"fail", "not_assessed"}
    if positive and negative:
        errors.append(f"{label}: report pass fields are inconsistent")
    elif not positive:
        errors.append(f"{label}: report content does not declare valid=true or status=pass")
    if report_errors:
        errors.append(f"{label}: report declares non-empty errors")


def _validate_validator_id(
    value: Any, label: str, errors: list[str], allowed: set[str]
) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label}.validator_id: required")
    elif value not in TRUSTED_VALIDATORS:
        errors.append(f"{label}.validator_id: unknown validator {value!r}")
    elif value not in allowed:
        errors.append(f"{label}.validator_id: validator {value!r} is not permitted here")


def validate(data: Any, base_dir: Path | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return {"valid": False, "errors": ["manifest: expected an object"], "warnings": [], "counts": {}}
    if data.get("schema_version") != "CDW-001/v1":
        errors.append("schema_version: expected CDW-001/v1")
    if not isinstance(data.get("project_id"), str) or not ID_RE.fullmatch(data.get("project_id", "")):
        errors.append("project_id: invalid identifier")

    sources = _records(data.get("sources", []), "sources", errors)
    source_index = _unique_index(sources, "source_id", "sources", errors)
    for index, source in enumerate(sources):
        if source.get("role") not in SOURCE_ROLES:
            errors.append(f"sources[{index}].role: unknown role")
        if not isinstance(source.get("local_ref"), str) or not source.get("local_ref", "").strip():
            errors.append(f"sources[{index}].local_ref: required")
        if source.get("frozen") is not True and source.get("frozen") is not False:
            errors.append(f"sources[{index}].frozen: expected boolean")
        if "approved" in source and not isinstance(source.get("approved"), bool):
            errors.append(f"sources[{index}].approved: expected boolean")
        content_hash = source.get("content_hash")
        if source.get("frozen"):
            _validate_file_ref(
                source.get("local_ref"), content_hash, f"sources[{index}]", errors, base_dir
            )

    artifacts = _records(data.get("artifacts", []), "artifacts", errors)
    artifact_index = _unique_index(artifacts, "artifact_id", "artifacts", errors)
    for index, artifact in enumerate(artifacts):
        if artifact.get("status") not in ARTIFACT_STATUSES:
            errors.append(f"artifacts[{index}].status: unknown status")
        for key in ("genre", "path", "version"):
            if not isinstance(artifact.get(key), str) or not artifact.get(key, "").strip():
                errors.append(f"artifacts[{index}].{key}: required")
        if artifact.get("status") in {"validated", "final"}:
            _validate_file_ref(
                artifact.get("path"), artifact.get("content_hash"),
                f"artifacts[{index}]", errors, base_dir,
            )
            validation = artifact.get("validation")
            if not isinstance(validation, dict):
                errors.append(
                    f"artifacts[{index}].validation: required for validated/final artifact"
                )
            else:
                if validation.get("status") != "pass":
                    errors.append(f"artifacts[{index}].validation.status: expected pass")
                _validate_validator_id(
                    validation.get("validator_id"),
                    f"artifacts[{index}].validation",
                    errors,
                    ARTIFACT_VALIDATORS_BY_GENRE.get(artifact.get("genre"), set()),
                )
                _validate_report_ref(
                    validation.get("report_path"), validation.get("content_hash"),
                    f"artifacts[{index}].validation", errors, base_dir,
                )
        source_ids = artifact.get("source_ids", [])
        if not isinstance(source_ids, list):
            errors.append(f"artifacts[{index}].source_ids: expected a list")
        else:
            for source_id in source_ids:
                if not isinstance(source_id, str) or not ID_RE.fullmatch(source_id):
                    errors.append(f"artifacts[{index}].source_ids: invalid identifier")
                elif source_id not in source_index:
                    errors.append(f"artifacts[{index}].source_ids: unknown {source_id}")

    stages = _records(data.get("stages", []), "stages", errors)
    stage_index = _unique_index(stages, "stage_id", "stages", errors)
    for missing in sorted(set(STAGE_SPECS) - set(stage_index)):
        errors.append(f"stages: missing canonical stage {missing}")
    for extra in sorted(set(stage_index) - set(STAGE_SPECS)):
        errors.append(f"stages: unexpected stage {extra}")
    artifact_owners: dict[str, str] = {}
    for index, stage in enumerate(stages):
        stage_id = stage.get("stage_id")
        status = stage.get("status")
        if status not in STAGE_STATUSES:
            errors.append(f"stages[{index}].status: unknown status")
        required = stage.get("required")
        if not isinstance(required, bool):
            errors.append(f"stages[{index}].required: expected boolean")
        if required and status == "not_applicable":
            errors.append(f"stages[{index}]: required stage cannot be not_applicable")
        spec = STAGE_SPECS.get(stage_id)
        if spec:
            if spec["mandatory"] and required is not True:
                errors.append(f"stages[{index}].required: canonical stage {stage_id} is mandatory")
            if stage.get("genre") != spec["genre"]:
                errors.append(f"stages[{index}].genre: expected {spec['genre']!r} for {stage_id}")
        if status == "not_applicable" and (
            not isinstance(stage.get("reason"), str) or not stage.get("reason", "").strip()
        ):
            errors.append(f"stages[{index}].reason: required for not_applicable")
        artifact_ids = stage.get("artifact_ids", [])
        if not isinstance(artifact_ids, list):
            errors.append(f"stages[{index}].artifact_ids: expected a list")
            artifact_ids = []
        else:
            invalid_artifact_ids = [
                value for value in artifact_ids
                if not isinstance(value, str) or not ID_RE.fullmatch(value)
            ]
            if invalid_artifact_ids:
                errors.append(f"stages[{index}].artifact_ids: invalid identifier")
            artifact_ids = [
                value for value in artifact_ids
                if isinstance(value, str) and ID_RE.fullmatch(value)
            ]
            if len(set(artifact_ids)) != len(artifact_ids):
                errors.append(f"stages[{index}].artifact_ids: duplicate artifact identifiers")
        for artifact_id in artifact_ids:
            owner = artifact_owners.setdefault(artifact_id, str(stage_id))
            if owner != stage_id:
                errors.append(
                    f"stages[{index}].artifact_ids: {artifact_id} already belongs to stage {owner}"
                )
            if artifact_id not in artifact_index:
                errors.append(f"stages[{index}].artifact_ids: unknown {artifact_id}")
                continue
            artifact = artifact_index[artifact_id]
            if spec and spec["genre"] is not None and artifact.get("genre") != spec["genre"]:
                errors.append(
                    f"stages[{index}].artifact_ids: {artifact_id} genre does not match "
                    f"{spec['genre']!r}"
                )
            if status == "complete" and artifact.get("status") not in {"validated", "final"}:
                errors.append(
                    f"stages[{index}].artifact_ids: {artifact_id} must be validated or final"
                )
        if status == "complete" and stage.get("stage_id") in CONTENT_STAGES and not artifact_ids:
            errors.append(f"stages[{index}]: complete content stage requires an artifact")
        dependencies = stage.get("depends_on", [])
        if not isinstance(dependencies, list):
            errors.append(f"stages[{index}].depends_on: expected a list")
            dependencies = []
        else:
            invalid_dependencies = [
                value for value in dependencies
                if not isinstance(value, str) or not ID_RE.fullmatch(value)
            ]
            if invalid_dependencies:
                errors.append(f"stages[{index}].depends_on: invalid identifier")
            dependencies = [
                value for value in dependencies
                if isinstance(value, str) and ID_RE.fullmatch(value)
            ]
        for dependency in dependencies:
            if dependency not in stage_index:
                errors.append(f"stages[{index}].depends_on: unknown {dependency}")
            elif status in {"ready", "in_progress", "complete"} and stage_index[dependency].get(
                "status"
            ) not in {"complete", "not_applicable"}:
                state = "completed" if status == "complete" else status
                errors.append(f"stages[{index}]: {state} before dependency {dependency}")
        if spec and isinstance(dependencies, list) and set(dependencies) != spec["depends_on"]:
            errors.append(
                f"stages[{index}].depends_on: expected {sorted(spec['depends_on'])} for {stage_id}"
            )

    blockers = _records(data.get("blockers", []), "blockers", errors)
    blocker_index = _unique_index(blockers, "blocker_id", "blockers", errors)
    for index, blocker in enumerate(blockers):
        if blocker.get("stage_id") not in stage_index:
            errors.append(f"blockers[{index}].stage_id: unknown stage")
        if not isinstance(blocker.get("reason"), str) or not blocker.get("reason", "").strip():
            errors.append(f"blockers[{index}].reason: required")
        if not isinstance(blocker.get("required_input"), str) or not blocker.get("required_input", "").strip():
            errors.append(f"blockers[{index}].required_input: required")
        if blocker.get("status") not in {"open", "resolved"}:
            errors.append(f"blockers[{index}].status: expected open or resolved")
    open_blocked_stages = {item.get("stage_id") for item in blockers if item.get("status") == "open"}
    for stage_id, stage in stage_index.items():
        if stage.get("status") == "blocked" and stage_id not in open_blocked_stages:
            errors.append(f"stage[{stage_id}]: blocked without an open blocker")

    gates = data.get("gates")
    if not isinstance(gates, dict):
        errors.append("gates: expected an object")
        gates = {}
    missing_gates = REQUIRED_GATES - set(gates)
    extra_gates = set(gates) - REQUIRED_GATES
    for gate in sorted(missing_gates):
        errors.append(f"gates.{gate}: required")
    for gate in sorted(extra_gates):
        errors.append(f"gates.{gate}: unexpected gate")
    for gate, status in gates.items():
        if status not in GATE_STATUSES:
            errors.append(f"gates.{gate}: unknown status")

    gate_reports = _records(data.get("gate_reports", []), "gate_reports", errors)
    gate_report_index = _unique_index(gate_reports, "gate_id", "gate_reports", errors)
    for index, report in enumerate(gate_reports):
        gate_id = report.get("gate_id")
        if gate_id not in REQUIRED_GATES:
            errors.append(f"gate_reports[{index}].gate_id: unexpected gate")
        if report.get("status") not in GATE_STATUSES:
            errors.append(f"gate_reports[{index}].status: unknown status")
        if gate_id in gates and report.get("status") != gates.get(gate_id):
            errors.append(f"gate_reports[{index}].status: does not match gates.{gate_id}")
        _validate_validator_id(
            report.get("validator_id"),
            f"gate_reports[{index}]",
            errors,
            GATE_VALIDATORS.get(gate_id, set()),
        )
        _validate_report_ref(
            report.get("report_path"), report.get("content_hash"),
            f"gate_reports[{index}]", errors, base_dir,
        )

    if stage_index.get("corpus_freeze", {}).get("status") == "complete":
        if not sources:
            errors.append("corpus_freeze: no sources")
        for source_id, source in source_index.items():
            if not source.get("frozen"):
                errors.append(f"corpus_freeze: source {source_id} is not frozen")

    roles = {source.get("role") for source in sources}
    if stage_index.get("literature_review", {}).get("status") == "complete":
        if sum(source.get("role") == "literature" for source in sources) < 3:
            errors.append("literature_review: requires at least three literature sources")
    if stage_index.get("methods", {}).get("status") == "complete" and not roles.intersection({"protocol", "data"}):
        errors.append("methods: requires protocol or data source")
    approved_result_sources = {
        source_id
        for source_id, source in source_index.items()
        if source.get("role") in {"result", "data"} and source.get("approved") is True
    }
    if stage_index.get("results", {}).get("status") == "complete" and not approved_result_sources:
        errors.append("results: requires a source with role result/data and approved=true")
    if stage_index.get("results", {}).get("status") == "complete":
        result_artifact_sources = {
            source_id
            for artifact_id in stage_index["results"].get("artifact_ids", [])
            for source_id in artifact_index.get(artifact_id, {}).get("source_ids", [])
            if isinstance(source_id, str)
        }
        if not (result_artifact_sources & approved_result_sources):
            errors.append("results: artifact must trace to an approved result/data source")
    if stage_index.get("approbation", {}).get("status") == "complete" and "organizational" not in roles:
        errors.append("approbation: requires organizational source")

    release = stage_index.get("release", {})
    if release.get("status") == "complete":
        if base_dir is None:
            errors.append("release: filesystem validation requires manifest base_dir")
        for stage_id, stage in stage_index.items():
            if stage.get("required") and stage.get("status") != "complete":
                errors.append(f"release: required stage {stage_id} is not complete")
            if not stage.get("required") and stage.get("status") not in {"complete", "not_applicable"}:
                errors.append(f"release: optional stage {stage_id} is unresolved")
        if any(item.get("status") == "open" for item in blockers):
            errors.append("release: open blockers remain")
        for gate in sorted(REQUIRED_GATES):
            if gates.get(gate) != "pass":
                errors.append(f"release: gate {gate} is not pass")
            report = gate_report_index.get(gate)
            if report is None:
                errors.append(f"release: gate {gate} has no validation report")
            elif report.get("status") != "pass":
                errors.append(f"release: gate report {gate} is not pass")

    if not stage_index:
        warnings.append("no stages declared")
    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "sources": len(source_index),
            "artifacts": len(artifact_index),
            "stages": len(stage_index),
            "blockers": len(blocker_index),
            "gate_reports": len(gate_report_index),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
        report = validate(data, args.manifest.resolve().parent)
    except (OSError, json.JSONDecodeError) as exc:
        report = {"valid": False, "errors": [str(exc)], "warnings": [], "counts": {}}
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
