#!/usr/bin/env python3
"""Run the small, deterministic offline project-literature lifecycle experiment."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUT = HERE / "input"
OUTPUT = HERE / "output"
RUN_DATE = "2026-08-17"


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROJECT_VALIDATOR = load_module(
    "exp0034_project_validator",
    ROOT / "skills" / "research-project-workflow" / "scripts" / "validate_project_manifest.py",
)
ANNOTATION_VALIDATOR = load_module(
    "exp0034_annotation_validator",
    ROOT / "skills" / "zotero-project-annotation" / "scripts" / "validate_project_annotation.py",
)
REVIEW_ENGINE = load_module(
    "exp0034_review_engine",
    ROOT / "skills" / "zotero-living-review" / "scripts" / "update_review.py",
)


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, value: Any) -> bytes:
    rendered = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    data = rendered.encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return data


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def project_view(project: dict[str, Any]) -> dict[str, Any]:
    context = project["context"]
    return {
        "project_id": project["project_id"],
        "title": project["title"],
        "goal": context["goal"],
        "objectives": [
            {"id": item["objective_id"], "text": item["text"]}
            for item in context["objectives"]
        ],
        "research_questions": [
            {"id": item["question_id"], "text": item["text"]}
            for item in context["research_questions"]
        ],
    }


def make_annotation(
    project: dict[str, Any],
    *,
    annotation_id: str,
    zotero_key: str,
    title: str,
    content_hash: str,
    what_work_did: str,
    outcome: str,
    author_conclusion: str,
    boundary: str,
    usefulness: str,
    open_question: str,
    machine_record_path: str,
) -> dict[str, Any]:
    context_hash = project["context_hash"]
    targets = [
        project["context"]["research_questions"][0]["question_id"],
        project["context"]["objectives"][0]["objective_id"],
    ]
    return {
        "schema_version": "ZPA-001/v1",
        "annotation_id": annotation_id,
        "record_type": "derived_project_annotation",
        "status": "current",
        "remake_required": False,
        "stale_reason": None,
        "block_reason": None,
        "metadata_only": False,
        "source_content_hash": content_hash,
        "project_context_hash": context_hash,
        "source": {
            "zotero_item_key": zotero_key,
            "title": title,
            "content_hash": content_hash,
            "read_scope": "full_text",
            "locators_read": ["Methods", "Results", "Discussion"],
        },
        "project": project_view(project),
        "relevance_target_ids": targets,
        "annotation": {
            "summary": outcome,
            "source_voice": {
                "what_work_did": what_work_did,
                "reported_outcomes": [
                    {
                        "claim_id": f"CL-{zotero_key}-OUTCOME",
                        "statement": outcome,
                        "value": "Directional comparison; the synthetic source supplies no numeric estimate.",
                        "locator": f"zotero:{zotero_key}#Results",
                    }
                ],
                "stated_boundaries": [boundary],
            },
            "author_conclusion": author_conclusion,
            "project_judgement": {
                "why_useful_here": usefulness,
                "what_it_does_not_settle": open_question,
            },
        },
        "evidence_role": "derived_annotation_not_evidence",
        "provenance": {
            "created_at": RUN_DATE,
            "machine_record_path": machine_record_path,
        },
    }


def make_item(
    *,
    zotero_key: str,
    source_content_hash: str,
    annotation_hash: str,
    annotation_status: str,
    context_hash: str,
    title: str,
) -> dict[str, Any]:
    return {
        "zotero_key": zotero_key,
        "source_content_hash": source_content_hash,
        "annotation_hash": annotation_hash,
        "annotation_status": annotation_status,
        "project_context_hash": context_hash,
        "title": title,
    }


def make_inventory(
    project: dict[str, Any], items: list[dict[str, Any]]
) -> dict[str, Any]:
    binding = project["zotero_collection_bindings"][0]
    corpus = project["corpora"][0]
    return {
        "schema_version": "ZLR-INV-001/v1",
        "review_id": "LR-0034",
        "project_id": project["project_id"],
        "corpus_id": corpus["corpus_id"],
        "collection": {
            "library_id": binding["library"],
            "collection_key": binding["collection_key"],
            "collection_name": binding["label"],
        },
        "project_context_hash": project["context_hash"],
        "items": items,
    }


def empty_state(project: dict[str, Any]) -> dict[str, Any]:
    inventory = make_inventory(project, [])
    return {
        "schema_version": "ZLR-001/v1",
        "review_id": inventory["review_id"],
        "project_id": inventory["project_id"],
        "corpus_id": inventory["corpus_id"],
        "collection": copy.deepcopy(inventory["collection"]),
        "project_context_hash": project["context_hash"],
        "items": {},
        "snapshots": [],
        "current_artifact": None,
    }


def validate_annotation(
    annotation: dict[str, Any],
    project: dict[str, Any],
    source_hash: str,
) -> dict[str, Any]:
    return ANNOTATION_VALIDATOR.validate_annotation(
        annotation,
        project_manifest=project,
        source_content_hash=source_hash,
        project_context_hash=project["context_hash"],
    )


def write_review(path: Path, title: str, bullets: list[str]) -> str:
    text = "# " + title + "\n\n" + "\n".join(f"- {bullet}" for bullet in bullets) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return sha256_file(path)


def main() -> int:
    INPUT.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    project_path = INPUT / "project.json"
    project = json.loads(project_path.read_text(encoding="utf-8"))
    canonical_context_hash = PROJECT_VALIDATOR.context_hash_for_manifest(project)
    project["context_hash"] = canonical_context_hash
    write_json(project_path, project)
    project_report = PROJECT_VALIDATOR.validate_project(project)
    check(project_report["valid"], f"project validation failed: {project_report['errors']}")

    publication_1 = INPUT / "publication-001.txt"
    publication_2 = INPUT / "publication-002.txt"
    source_1_hash = sha256_file(publication_1)
    source_2_hash = sha256_file(publication_2)

    annotation_1 = make_annotation(
        project,
        annotation_id="ANN-0034-001",
        zotero_key="PUB001",
        title="Retrieval practice in a short online module",
        content_hash=source_1_hash,
        what_work_did="Compared retrieval-practice prompts with rereading in a small randomized classroom study over a two-week module.",
        outcome="The retrieval-practice group scored higher on the delayed quiz than the rereading group.",
        author_conclusion="The authors interpret the result as support for retrieval prompts in this narrow module.",
        boundary="The authors note that the sample and follow-up are limited.",
        usefulness="Provides a direct reported outcome for the project's comparison of learning outcomes.",
        open_question="The synthetic source does not establish whether the result transfers beyond this module.",
        machine_record_path="input/annotation-001.json",
    )
    annotation_1_path = INPUT / "annotation-001.json"
    write_json(annotation_1_path, annotation_1)
    annotation_1_report = validate_annotation(annotation_1, project, source_1_hash)
    check(annotation_1_report["valid"], f"annotation 1 validation failed: {annotation_1_report['errors']}")
    annotation_1_hash = sha256_file(annotation_1_path)

    annotation_2 = make_annotation(
        project,
        annotation_id="ANN-0034-002",
        zotero_key="PUB002",
        title="Worked examples for introductory laboratory reasoning",
        content_hash=source_2_hash,
        what_work_did="Compared worked examples with unguided problem solving in a controlled introductory laboratory teaching study.",
        outcome="Students receiving worked examples completed the post-unit reasoning task with fewer procedural errors.",
        author_conclusion="The authors conclude that worked examples can support novice laboratory reasoning in this setting.",
        boundary="The authors caution that transfer beyond the unit was not established.",
        usefulness="Adds a second bounded outcome for the project's cross-study comparison.",
        open_question="The synthetic source does not settle whether fewer procedural errors persist after the unit.",
        machine_record_path="input/annotation-002-valid.json",
    )
    annotation_2_path = INPUT / "annotation-002-valid.json"
    write_json(annotation_2_path, annotation_2)
    annotation_2_report = validate_annotation(annotation_2, project, source_2_hash)
    check(annotation_2_report["valid"], f"annotation 2 validation failed: {annotation_2_report['errors']}")
    annotation_2_hash = sha256_file(annotation_2_path)

    item_1 = make_item(
        zotero_key="PUB001",
        source_content_hash=source_1_hash,
        annotation_hash=annotation_1_hash,
        annotation_status="validated",
        context_hash=canonical_context_hash,
        title=annotation_1["source"]["title"],
    )
    item_2_missing = make_item(
        zotero_key="PUB002",
        source_content_hash=source_2_hash,
        annotation_hash=sha256_text("annotation missing: PUB002"),
        annotation_status="missing",
        context_hash=canonical_context_hash,
        title=annotation_2["source"]["title"],
    )
    item_2_valid = make_item(
        zotero_key="PUB002",
        source_content_hash=source_2_hash,
        annotation_hash=annotation_2_hash,
        annotation_status="validated",
        context_hash=canonical_context_hash,
        title=annotation_2["source"]["title"],
    )

    inventory_1 = make_inventory(project, [item_1])
    inventory_2 = make_inventory(project, [item_1, item_2_missing])
    inventory_3 = make_inventory(project, [item_1, item_2_valid])
    write_json(INPUT / "inventory-001.json", inventory_1)
    write_json(INPUT / "inventory-002-blocked.json", inventory_2)
    write_json(INPUT / "inventory-003.json", inventory_3)

    state_0 = empty_state(project)
    write_json(INPUT / "state-000-empty.json", state_0)

    validation_results: dict[str, Any] = {
        "project": project_report,
        "annotation_001": annotation_1_report,
        "annotation_002": annotation_2_report,
        "inventories": {},
        "states": {},
    }
    for label, inventory in (
        ("inventory_001", inventory_1),
        ("inventory_002_blocked", inventory_2),
        ("inventory_003", inventory_3),
    ):
        report = REVIEW_ENGINE.validate_inventory(inventory)
        check(report["valid"], f"{label} validation failed: {report['errors']}")
        validation_results["inventories"][label] = report
    state_0_report = REVIEW_ENGINE.validate_state(state_0)
    check(state_0_report["valid"], f"empty state validation failed: {state_0_report['errors']}")
    validation_results["states"]["state_000_empty"] = state_0_report

    plan_1 = REVIEW_ENGINE.build_update_plan(state_0, inventory_1)
    check(plan_1["relevant_change"], "snapshot 1 should be relevant")
    check(plan_1["snapshot_required"], "snapshot 1 should be required")
    check(not plan_1["synthesis_blocked"], "snapshot 1 should not be blocked")
    check(len(plan_1["state"]["snapshots"]) == 1, "expected snapshot 1")
    state_1_candidate = plan_1["state"]
    check(state_1_candidate["current_artifact"]["status"] == "needs_resynthesis", "snapshot 1 should need synthesis")
    review_1_path = OUTPUT / "literature-review-v1.md"
    review_1_hash = write_review(
        review_1_path,
        "Offline review — snapshot 1",
        ["PUB001 reports higher delayed-quiz scores after retrieval practice than rereading.", "Boundary: the source limits the claim to its small sample and follow-up."],
    )
    state_1 = REVIEW_ENGINE.record_published_artifact(
        state_1_candidate,
        snapshot_id=plan_1["snapshot_id"],
        artifact_path="output/literature-review-v1.md",
        content_hash=review_1_hash,
    )
    state_1_report = REVIEW_ENGINE.validate_state(state_1)
    check(state_1_report["valid"], f"published state 1 validation failed: {state_1_report['errors']}")

    plan_2 = REVIEW_ENGINE.build_update_plan(state_1, inventory_2)
    check(plan_2["relevant_change"], "snapshot 2 should be relevant")
    check(plan_2["snapshot_required"], "snapshot 2 should be required")
    check(plan_2["synthesis_blocked"], "snapshot 2 should be blocked without annotation 2")
    check(len(plan_2["state"]["snapshots"]) == 2, "expected blocked snapshot 2")
    check(plan_2["state"]["current_artifact"]["status"] == "blocked", "snapshot 2 artifact should be blocked")
    check(
        any(reason["zotero_key"] == "PUB002" and reason["code"] == "annotation_not_validated" for reason in plan_2["blocking_reasons"]),
        "snapshot 2 should name PUB002 annotation gate",
    )
    state_2 = plan_2["state"]
    state_2_report = REVIEW_ENGINE.validate_state(state_2)
    check(state_2_report["valid"], f"blocked state 2 validation failed: {state_2_report['errors']}")

    plan_3 = REVIEW_ENGINE.build_update_plan(state_2, inventory_3)
    check(plan_3["relevant_change"], "snapshot 3 should be relevant")
    check(plan_3["snapshot_required"], "snapshot 3 should be required")
    check(not plan_3["synthesis_blocked"], "snapshot 3 should be unblocked after annotation 2")
    check(len(plan_3["state"]["snapshots"]) == 3, "expected snapshot 3")
    check(plan_3["state"]["current_artifact"]["status"] == "needs_resynthesis", "snapshot 3 should need resynthesis")
    review_2_path = OUTPUT / "literature-review-v2.md"
    review_2_hash = write_review(
        review_2_path,
        "Offline review — snapshot 3",
        ["PUB001 reports higher delayed-quiz scores after retrieval practice than rereading.", "PUB002 reports fewer procedural errors after worked examples than unguided problem solving."],
    )
    state_3 = REVIEW_ENGINE.record_published_artifact(
        plan_3["state"],
        snapshot_id=plan_3["snapshot_id"],
        artifact_path="output/literature-review-v2.md",
        content_hash=review_2_hash,
    )
    state_3_report = REVIEW_ENGINE.validate_state(state_3)
    check(state_3_report["valid"], f"published state 3 validation failed: {state_3_report['errors']}")

    plan_repeat = REVIEW_ENGINE.build_update_plan(state_3, inventory_3)
    check(not plan_repeat["relevant_change"], "identical inventory should be a no-op")
    check(not plan_repeat["snapshot_required"], "identical inventory must not create a snapshot")
    check(len(plan_repeat["state"]["snapshots"]) == 3, "identical inventory must retain three snapshots")
    state_3_bytes = write_json(OUTPUT / "state-003-published.json", state_3)
    repeat_bytes = write_json(OUTPUT / "state-003-repeat.json", plan_repeat["state"])
    check(state_3_bytes == repeat_bytes, "identical inventory changed state bytes")

    write_json(OUTPUT / "project-validation.json", project_report)
    write_json(OUTPUT / "annotation-001-validation.json", annotation_1_report)
    write_json(OUTPUT / "annotation-002-validation.json", annotation_2_report)
    write_json(OUTPUT / "validation-results.json", validation_results)
    write_json(OUTPUT / "plan-001.json", {key: value for key, value in plan_1.items() if key != "state"})
    write_json(OUTPUT / "state-001-published.json", state_1)
    write_json(OUTPUT / "plan-002-blocked.json", {key: value for key, value in plan_2.items() if key != "state"})
    write_json(OUTPUT / "state-002-blocked.json", state_2)
    write_json(
        OUTPUT / "plan-003-needs-resynthesis.json",
        {key: value for key, value in plan_3.items() if key != "state"},
    )
    write_json(OUTPUT / "plan-003-repeat.json", {key: value for key, value in plan_repeat.items() if key != "state"})

    result_rows = [
        ("project context repair and validation", "PASS", canonical_context_hash),
        ("annotation 1 validation", "PASS", annotation_1_hash),
        ("snapshot 1 publish", "PASS", plan_1["snapshot_id"]),
        ("snapshot 2 blocks missing annotation 2", "PASS", plan_2["snapshot_id"]),
        ("annotation 2 validation", "PASS", annotation_2_hash),
        ("snapshot 3 resynthesis and publish", "PASS", plan_3["snapshot_id"]),
        ("identical inventory byte-stable no-op", "PASS", "3 snapshots retained"),
    ]
    report_lines = [
        "# EXP-0034 lifecycle experiment",
        "",
        "Command: `python experiments/EXP-0034-project-literature-lifecycle/run_experiment.py`",
        "",
        "All inputs are local synthetic text/JSON records; no network or Zotero calls were made.",
        "",
        "| Scenario | Result | Evidence |",
        "|---|---|---|",
    ]
    report_lines.extend(f"| {name} | {status} | `{evidence}` |" for name, status, evidence in result_rows)
    report_lines.extend(
        [
            "",
            f"Canonical project context hash: `{canonical_context_hash}`.",
            f"Review artifacts: `output/literature-review-v1.md` ({review_1_hash}) and `output/literature-review-v2.md` ({review_2_hash}).",
        ]
    )
    (HERE / "report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8", newline="\n")

    evaluation_lines = [
        "# EXP-0034 evaluation",
        "",
        "| Scenario | Pass/fail | Check |",
        "|---|---|---|",
        "| Canonical context hash and project validation | PASS | RP-001 validator accepted the repaired manifest. |",
        "| Annotation 1 gate | PASS | ZPA validator accepted full-text annotation 1 with real source/context hashes. |",
        "| Initial review publication | PASS | ZLR created one immutable snapshot and publication recording succeeded. |",
        "| Missing annotation blocks snapshot 2 | PASS | ZLR created snapshot 2 with `synthesis_blocked=true` for PUB002. |",
        "| Valid annotation 2 clears block | PASS | ZPA accepted annotation 2; ZLR created snapshot 3 with `needs_resynthesis`. |",
        "| Snapshot 3 publication | PASS | Publication recording succeeded and state validation passed. |",
        "| Identical inventory rerun | PASS | No new snapshot; serialized state bytes were identical. |",
        "",
        "Discovered defects: none blocking this contract experiment.",
    ]
    (HERE / "evaluation.md").write_text("\n".join(evaluation_lines) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
