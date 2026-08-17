from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "candidate-dissertation-workflow"
SPEC = importlib.util.spec_from_file_location(
    "candidate_artifact_ownership", SKILL / "scripts" / "validate_dissertation_project.py"
)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def test_one_artifact_cannot_complete_two_stages() -> None:
    data = json.loads(
        (SKILL / "assets" / "dissertation-project.template.json").read_text(encoding="utf-8")
    )
    data["sources"] = [
        {
            "source_id": "SRC-1",
            "role": "organizational",
            "local_ref": "source.txt",
            "content_hash": "sha256:" + "0" * 64,
            "frozen": True,
        }
    ]
    data["artifacts"] = [
        {
            "artifact_id": "ART-SHARED",
            "genre": "dissertation-outline",
            "path": "shared.md",
            "version": "v1",
            "status": "draft",
            "source_ids": ["SRC-1"],
        }
    ]
    outline = next(item for item in data["stages"] if item["stage_id"] == "outline")
    introduction = next(item for item in data["stages"] if item["stage_id"] == "introduction")
    outline["artifact_ids"] = ["ART-SHARED", "ART-SHARED"]
    introduction["artifact_ids"] = ["ART-SHARED"]

    report = VALIDATOR.validate(data)
    text = "\n".join(report["errors"])

    assert "duplicate artifact identifiers" in text
    assert "already belongs to stage outline" in text
