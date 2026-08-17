#!/usr/bin/env python3
"""Validate a candidate-dissertation workflow project manifest."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
STAGE_STATUSES = {"pending", "ready", "in_progress", "blocked", "complete", "not_applicable"}
ARTIFACT_STATUSES = {"draft", "validated", "final"}
GATE_STATUSES = {"pass", "fail", "not_assessed"}
SOURCE_ROLES = {"literature", "protocol", "data", "result", "organizational", "normative", "practice"}
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


def validate(data: Any) -> dict[str, Any]:
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
        if source.get("frozen") and (not isinstance(content_hash, str) or not content_hash.strip()):
            errors.append(f"sources[{index}].content_hash: required when frozen")

    artifacts = _records(data.get("artifacts", []), "artifacts", errors)
    artifact_index = _unique_index(artifacts, "artifact_id", "artifacts", errors)
    for index, artifact in enumerate(artifacts):
        if artifact.get("status") not in ARTIFACT_STATUSES:
            errors.append(f"artifacts[{index}].status: unknown status")
        for key in ("genre", "path", "version"):
            if not isinstance(artifact.get(key), str) or not artifact.get(key, "").strip():
                errors.append(f"artifacts[{index}].{key}: required")
        source_ids = artifact.get("source_ids", [])
        if not isinstance(source_ids, list):
            errors.append(f"artifacts[{index}].source_ids: expected a list")
        else:
            for source_id in source_ids:
                if source_id not in source_index:
                    errors.append(f"artifacts[{index}].source_ids: unknown {source_id}")

    stages = _records(data.get("stages", []), "stages", errors)
    stage_index = _unique_index(stages, "stage_id", "stages", errors)
    for missing in sorted(set(STAGE_SPECS) - set(stage_index)):
        errors.append(f"stages: missing canonical stage {missing}")
    for extra in sorted(set(stage_index) - set(STAGE_SPECS)):
        errors.append(f"stages: unexpected stage {extra}")
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
        for artifact_id in artifact_ids:
            if artifact_id not in artifact_index:
                errors.append(f"stages[{index}].artifact_ids: unknown {artifact_id}")
        if status == "complete" and stage.get("stage_id") in CONTENT_STAGES and not artifact_ids:
            errors.append(f"stages[{index}]: complete content stage requires an artifact")
        dependencies = stage.get("depends_on", [])
        if not isinstance(dependencies, list):
            errors.append(f"stages[{index}].depends_on: expected a list")
            dependencies = []
        for dependency in dependencies:
            if dependency not in stage_index:
                errors.append(f"stages[{index}].depends_on: unknown {dependency}")
            elif status == "complete" and stage_index[dependency].get("status") not in {"complete", "not_applicable"}:
                errors.append(f"stages[{index}]: completed before dependency {dependency}")
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
    if stage_index.get("approbation", {}).get("status") == "complete" and "organizational" not in roles:
        errors.append("approbation: requires organizational source")

    release = stage_index.get("release", {})
    if release.get("status") == "complete":
        for stage_id, stage in stage_index.items():
            if stage.get("required") and stage.get("status") != "complete":
                errors.append(f"release: required stage {stage_id} is not complete")
        if any(item.get("status") == "open" for item in blockers):
            errors.append("release: open blockers remain")
        for gate in sorted(REQUIRED_GATES):
            if gates.get(gate) != "pass":
                errors.append(f"release: gate {gate} is not pass")

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
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8-sig"))
        report = validate(data)
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
