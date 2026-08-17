from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load(
    "dissertation_result_approval_validator",
    ROOT / "skills" / "scientific-evidence-workflow" / "scripts" / "validate_bundle.py",
)
BUILDERS = load(
    "dissertation_result_approval_builders",
    ROOT / "tests" / "test_remaining_dissertation_genres.py",
)


def test_dissertation_genre_rejects_unapproved_own_result() -> None:
    data = BUILDERS.bundle("dissertation-results-chapter")
    data["results"][0]["approved"] = False

    report = VALIDATOR.validate_bundle(data)

    assert "requires approved=true for every own result" in "\n".join(report["errors"])
