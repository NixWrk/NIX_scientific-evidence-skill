from pathlib import Path

from tools.audit_skill import audit_skill
from tools.validate_block_references import validate_references


def write_skill(directory: Path, body: str) -> None:
    directory.mkdir()
    (directory / "SKILL.md").write_text(body, encoding="utf-8")


def test_accepts_minimal_portable_skill(tmp_path: Path) -> None:
    skill_dir = tmp_path / "evidence-audit"
    write_skill(
        skill_dir,
        """---
name: evidence-audit
description: Audit claims against a supplied local evidence table.
---

# Evidence audit

Use only the supplied evidence table and report unsupported claims.
""",
    )

    report = audit_skill(skill_dir)

    assert report["spec_subset_valid"] is True
    assert report["manual_policy_review_required"] is False


def test_reports_name_mismatch_and_network_signal(tmp_path: Path) -> None:
    skill_dir = tmp_path / "wrong-directory"
    write_skill(
        skill_dir,
        """---
name: paper-review
description: Review a supplied paper and search for additional literature.
---

# Paper review

Use web search before writing the review.
""",
    )

    report = audit_skill(skill_dir)

    assert report["spec_subset_valid"] is False
    assert any("parent directory" in error for error in report["spec_errors"])
    assert "network_access" in report["policy_signals"]
    assert "corpus_expansion" in report["policy_signals"]


def test_validates_block_references(tmp_path: Path) -> None:
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    (normalized_dir / "SRC-TEST-001.json").write_text(
        '{"blocks":[{"block_id":"SRC-TEST-001-B0001"}]}',
        encoding="utf-8",
    )
    artifact = tmp_path / "result.md"
    artifact.write_text(
        "Supported [SRC-TEST-001-B0001], missing [SRC-TEST-001-B0002].",
        encoding="utf-8",
    )

    report = validate_references(artifact, normalized_dir)

    assert report["valid"] is False
    assert report["references"] == 2
    assert report["missing"] == ["SRC-TEST-001-B0002"]
