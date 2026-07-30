from pathlib import Path

from tools.validate_reference_subset import validate_subset


def test_accepts_only_references_present_in_frozen_source(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text(
        "Available [SRC-TEST-001-B0001] and [SRC-TEST-002-B0002].",
        encoding="utf-8",
    )
    output = tmp_path / "output.md"
    output.write_text("Cited twice [SRC-TEST-001-B0001; SRC-TEST-001-B0001].", encoding="utf-8")

    report = validate_subset(output, source)

    assert report["valid"] is True
    assert report["references"] == 2
    assert report["unique_references"] == 1


def test_rejects_reference_absent_from_frozen_source(tmp_path: Path) -> None:
    source = tmp_path / "source.md"
    source.write_text("Available [SRC-TEST-001-B0001].", encoding="utf-8")
    output = tmp_path / "output.md"
    output.write_text("Invented [SRC-TEST-001-B0002].", encoding="utf-8")

    report = validate_subset(output, source)

    assert report["valid"] is False
    assert report["missing"] == ["SRC-TEST-001-B0002"]
