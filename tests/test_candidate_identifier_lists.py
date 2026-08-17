from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "candidate-dissertation-workflow"
SPEC = importlib.util.spec_from_file_location(
    "candidate_identifier_lists", SKILL / "scripts" / "validate_dissertation_project.py"
)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def test_malformed_identifier_lists_return_errors_instead_of_crashing() -> None:
    data = json.loads(
        (SKILL / "assets" / "dissertation-project.template.json").read_text(encoding="utf-8")
    )
    data["artifacts"] = [
        {
            "artifact_id": "ART-1",
            "genre": "dissertation-outline",
            "path": "draft.md",
            "version": "v1",
            "status": "draft",
            "source_ids": [{}],
        }
    ]
    outline = next(item for item in data["stages"] if item["stage_id"] == "outline")
    outline["artifact_ids"] = [{}]
    outline["depends_on"] = [{}]

    report = VALIDATOR.validate(data)

    assert report["valid"] is False
    assert "invalid identifier" in "\n".join(report["errors"])
