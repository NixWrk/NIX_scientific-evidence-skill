from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "candidate-dissertation-workflow"
SPEC = importlib.util.spec_from_file_location(
    "candidate_report_semantics", SKILL / "scripts" / "validate_dissertation_project.py"
)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_report_must_be_consistent_error_free_and_from_permitted_validator(tmp_path: Path) -> None:
    data = json.loads(
        (SKILL / "assets" / "dissertation-project.template.json").read_text(encoding="utf-8")
    )
    artifact = tmp_path / "artifact.md"
    artifact.write_text("artifact", encoding="utf-8")
    report = tmp_path / "report.json"
    report.write_text('{"valid": true, "status": "fail", "errors": ["boom"]}', encoding="utf-8")
    data["artifacts"] = [
        {
            "artifact_id": "ART-1",
            "genre": "dissertation-outline",
            "path": artifact.name,
            "version": "v1",
            "status": "validated",
            "content_hash": digest(artifact),
            "source_ids": [],
            "validation": {
                "status": "pass",
                "validator_id": "dissertation-formatting-and-apparatus/audit_bibliography.py",
                "report_path": report.name,
                "content_hash": digest(report),
            },
        }
    ]

    validation = VALIDATOR.validate(data, tmp_path)
    text = "\n".join(validation["errors"])

    assert "is not permitted here" in text
    assert "report pass fields are inconsistent" in text
    assert "report declares non-empty errors" in text
