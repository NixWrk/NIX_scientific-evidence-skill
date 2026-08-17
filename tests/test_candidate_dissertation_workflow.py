from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "candidate-dissertation-workflow"
SCRIPT = SKILL / "scripts" / "validate_dissertation_project.py"
SPEC = importlib.util.spec_from_file_location("validate_dissertation_project", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def template() -> dict:
    return json.loads((SKILL / "assets" / "dissertation-project.template.json").read_text(encoding="utf-8"))


def test_template_is_a_valid_non_release_project() -> None:
    report = VALIDATOR.validate(template())

    assert report["valid"] is True
    assert report["counts"]["stages"] == 16


def test_completed_stage_requires_existing_artifact_and_dependencies() -> None:
    data = template()
    outline = next(item for item in data["stages"] if item["stage_id"] == "outline")
    outline.update({"status": "complete", "artifact_ids": ["ART-MISSING"]})

    report = VALIDATOR.validate(data)

    text = "\n".join(report["errors"])
    assert "unknown ART-MISSING" in text
    assert "completed before dependency corpus_freeze" in text


def test_results_cannot_complete_without_result_or_data_source() -> None:
    data = template()
    for stage_id in ("corpus_freeze", "outline", "methods"):
        stage = next(item for item in data["stages"] if item["stage_id"] == stage_id)
        stage.update({"status": "complete", "artifact_ids": [] if stage_id == "corpus_freeze" else [f"ART-{stage_id.upper()}"]})
    data["sources"] = [{"source_id": "SRC-P", "role": "protocol", "local_ref": "protocol.json", "content_hash": "sha256:p", "frozen": True}]
    data["artifacts"] = [
        {"artifact_id": "ART-OUTLINE", "genre": "dissertation-outline", "path": "outline.md", "version": "v1", "status": "final", "source_ids": ["SRC-P"]},
        {"artifact_id": "ART-METHODS", "genre": "dissertation-methods-chapter", "path": "methods.md", "version": "v1", "status": "final", "source_ids": ["SRC-P"]},
        {"artifact_id": "ART-RESULTS", "genre": "dissertation-results-chapter", "path": "results.md", "version": "v1", "status": "final", "source_ids": ["SRC-P"]},
    ]
    results = next(item for item in data["stages"] if item["stage_id"] == "results")
    results.update({"status": "complete", "artifact_ids": ["ART-RESULTS"]})

    report = VALIDATOR.validate(data)

    assert "results: requires a source with role result/data and approved=true" in report["errors"]


def test_unapproved_result_source_does_not_open_results_gate() -> None:
    data = template()
    data["sources"] = [{
        "source_id": "SRC-R", "role": "result", "local_ref": "result.json",
        "content_hash": "sha256:r", "frozen": True, "approved": False,
    }]
    for stage_id in ("corpus_freeze", "outline", "methods", "results"):
        stage = next(item for item in data["stages"] if item["stage_id"] == stage_id)
        artifact_ids = [] if stage_id == "corpus_freeze" else [f"ART-{stage_id.upper()}"]
        stage.update({"status": "complete", "artifact_ids": artifact_ids})
    data["artifacts"] = [
        {
            "artifact_id": f"ART-{stage_id.upper()}",
            "genre": next(item for item in data["stages"] if item["stage_id"] == stage_id)["genre"],
            "path": f"{stage_id}.md", "version": "v1", "status": "final",
            "source_ids": ["SRC-R"],
        }
        for stage_id in ("outline", "methods", "results")
    ]

    report = VALIDATOR.validate(data)

    assert "results: requires a source with role result/data and approved=true" in report["errors"]


def test_canonical_stage_cannot_be_removed_or_lose_dependency() -> None:
    data = template()
    data["stages"] = [item for item in data["stages"] if item["stage_id"] != "methods"]
    results = next(item for item in data["stages"] if item["stage_id"] == "results")
    results["depends_on"] = []

    report = VALIDATOR.validate(data)
    text = "\n".join(report["errors"])

    assert "stages: missing canonical stage methods" in text
    assert "expected ['methods'] for results" in text


def test_release_fails_closed_on_pending_stage_gate_and_blocker() -> None:
    data = template()
    release = next(item for item in data["stages"] if item["stage_id"] == "release")
    release.update({"status": "complete", "artifact_ids": ["ART-DISS"]})
    data["artifacts"] = [{"artifact_id": "ART-DISS", "genre": "dissertation", "path": "final.docx", "version": "v1", "status": "final", "source_ids": []}]
    data["blockers"] = [{"blocker_id": "BLK-1", "stage_id": "results", "reason": "Нет утверждённых результатов", "required_input": "Версионированный реестр результатов", "status": "open"}]

    report = VALIDATOR.validate(data)
    text = "\n".join(report["errors"])

    assert "release: open blockers remain" in text
    assert "release: gate evidence is not pass" in text
    assert "release: required stage results is not complete" in text


def test_routing_names_every_dissertation_content_genre_and_child_skill() -> None:
    routing = (SKILL / "references" / "routing.md").read_text(encoding="utf-8")
    for genre in (
        "dissertation-outline",
        "dissertation-introduction",
        "dissertation-literature-review-chapter",
        "dissertation-methods-chapter",
        "dissertation-results-chapter",
        "dissertation-synthesis-chapter",
        "dissertation-conclusion",
        "defense-propositions",
        "novelty-statement",
        "approbation-record",
        "thesis-synopsis",
    ):
        assert genre in routing
    assert "scientific-evidence-workflow" in routing
    assert "dissertation-formatting-and-apparatus" in routing
