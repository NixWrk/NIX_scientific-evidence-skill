from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "candidate-dissertation-workflow"
SCRIPT = SKILL / "scripts" / "validate_dissertation_project.py"
SPEC = importlib.util.spec_from_file_location("candidate_fail_closed", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def template() -> dict:
    return json.loads(
        (SKILL / "assets" / "dissertation-project.template.json").read_text(encoding="utf-8")
    )


def write_frozen(root: Path, relative: str, text: str) -> str:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_ready_stage_cannot_precede_dependency() -> None:
    data = template()
    outline = next(item for item in data["stages"] if item["stage_id"] == "outline")
    outline["status"] = "ready"

    report = VALIDATOR.validate(data)

    assert "ready before dependency corpus_freeze" in "\n".join(report["errors"])


def test_complete_stage_rejects_draft_and_wrong_genre() -> None:
    data = template()
    data["sources"] = [
        {
            "source_id": "SRC-1",
            "role": "literature",
            "local_ref": "source.txt",
            "content_hash": "sha256:" + "0" * 64,
            "frozen": True,
        }
    ]
    next(item for item in data["stages"] if item["stage_id"] == "corpus_freeze")[
        "status"
    ] = "complete"
    outline = next(item for item in data["stages"] if item["stage_id"] == "outline")
    outline.update({"status": "complete", "artifact_ids": ["ART-1"]})
    data["artifacts"] = [
        {
            "artifact_id": "ART-1",
            "genre": "dissertation-results-chapter",
            "path": "outline.md",
            "version": "v1",
            "status": "draft",
            "source_ids": ["SRC-1"],
        }
    ]

    report = VALIDATOR.validate(data)
    text = "\n".join(report["errors"])

    assert "genre does not match 'dissertation-outline'" in text
    assert "must be validated or final" in text


def test_fake_release_with_nonexistent_files_and_manual_gates_is_rejected(tmp_path: Path) -> None:
    data = template()
    data["sources"] = [
        {
            "source_id": "SRC-FAKE",
            "role": "result",
            "local_ref": "NO_SUCH_SOURCE.json",
            "content_hash": "sha256:" + "0" * 64,
            "frozen": True,
            "approved": True,
        }
    ]
    for stage in data["stages"]:
        stage["status"] = "complete"
        if stage["stage_id"] in VALIDATOR.CONTENT_STAGES:
            artifact_id = f"ART-{stage['stage_id'].upper()}"
            stage["artifact_ids"] = [artifact_id]
            data["artifacts"].append(
                {
                    "artifact_id": artifact_id,
                    "genre": stage["genre"] or "review-report",
                    "path": f"NO_SUCH_{stage['stage_id']}.md",
                    "version": "v1",
                    "status": "final",
                    "content_hash": "sha256:" + "1" * 64,
                    "source_ids": ["SRC-FAKE"],
                    "validation": {
                        "status": "pass",
                        "validator_id": "FAKE",
                        "report_path": f"NO_SUCH_{stage['stage_id']}.report.json",
                        "content_hash": "sha256:" + "2" * 64,
                    },
                }
            )
    data["gates"] = {gate: "pass" for gate in VALIDATOR.REQUIRED_GATES}

    report = VALIDATOR.validate(data, tmp_path)
    text = "\n".join(report["errors"])

    assert report["valid"] is False
    assert "file does not exist" in text
    assert "has no validation report" in text


def test_real_files_hashes_validator_reports_and_gate_reports_can_release(tmp_path: Path) -> None:
    data = template()
    source_specs = [
        ("LIT-1", "literature", False),
        ("LIT-2", "literature", False),
        ("LIT-3", "literature", False),
        ("PROTOCOL-1", "protocol", False),
        ("RESULT-1", "result", True),
        ("ORG-1", "organizational", False),
    ]
    for source_id, role, approved in source_specs:
        relative = f"sources/{source_id}.txt"
        source = {
            "source_id": source_id,
            "role": role,
            "local_ref": relative,
            "content_hash": write_frozen(tmp_path, relative, source_id),
            "frozen": True,
        }
        if approved:
            source["approved"] = True
        data["sources"].append(source)

    all_source_ids = [item["source_id"] for item in data["sources"]]
    for stage in data["stages"]:
        stage["status"] = "complete"
        if stage["stage_id"] not in VALIDATOR.CONTENT_STAGES:
            continue
        artifact_id = f"ART-{stage['stage_id'].upper()}"
        artifact_path = f"artifacts/{stage['stage_id']}.md"
        report_path = f"reports/{stage['stage_id']}.json"
        stage["artifact_ids"] = [artifact_id]
        data["artifacts"].append(
            {
                "artifact_id": artifact_id,
                "genre": stage["genre"] or "review-report",
                "path": artifact_path,
                "version": "v1",
                "status": "final",
                "content_hash": write_frozen(tmp_path, artifact_path, stage["stage_id"]),
                "source_ids": all_source_ids,
                "validation": {
                    "status": "pass",
                    "validator_id": (
                        VALIDATOR.SCIENTIFIC_VALIDATOR
                        if (stage["genre"] or "review-report")
                        in VALIDATOR.SCIENTIFIC_ARTIFACT_GENRES
                        else VALIDATOR.MANUAL_VALIDATOR
                    ),
                    "report_path": report_path,
                    "content_hash": write_frozen(tmp_path, report_path, '{"valid": true}'),
                },
            }
        )

    data["gates"] = {gate: "pass" for gate in VALIDATOR.REQUIRED_GATES}
    for gate in sorted(VALIDATOR.REQUIRED_GATES):
        report_path = f"gate-reports/{gate}.json"
        data["gate_reports"].append(
            {
                "gate_id": gate,
                "status": "pass",
                "validator_id": sorted(VALIDATOR.GATE_VALIDATORS[gate])[0],
                "report_path": report_path,
                "content_hash": write_frozen(tmp_path, report_path, '{"valid": true}'),
            }
        )

    report = VALIDATOR.validate(data, tmp_path)

    assert report["valid"] is True, report["errors"]
