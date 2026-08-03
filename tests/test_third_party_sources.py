import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
THIRD_PARTY = ROOT / "third_party"
MANIFEST = json.loads((THIRD_PARTY / "manifest.json").read_text(encoding="utf-8"))


def test_third_party_manifest_has_unique_pinned_entries() -> None:
    entries = MANIFEST["entries"]
    ids = [entry["id"] for entry in entries]
    paths = [entry["local_path"] for entry in entries]

    assert MANIFEST["schema_version"] == 1
    assert len(entries) == 17
    assert len(ids) == len(set(ids))
    assert len(paths) == len(set(paths))
    assert all(re.fullmatch(r"[0-9a-f]{40}", entry["commit"]) for entry in entries)
    assert all(entry["repository"].startswith("https://github.com/") for entry in entries)


def test_source_snapshots_exist_and_keep_upstream_license() -> None:
    snapshots = [
        entry for entry in MANIFEST["entries"] if entry["inclusion_mode"] == "source_snapshot"
    ]

    assert len(snapshots) == 16
    for entry in snapshots:
        path = ROOT / entry["local_path"]
        assert path.is_dir(), entry["id"]
        assert (path / "LICENSE").is_file() or (path / "LICENSE.md").is_file(), entry["id"]


def test_unlicensed_project_is_only_a_pinned_submodule() -> None:
    entry = next(item for item in MANIFEST["entries"] if item["id"] == "paper-skills")
    gitmodules = (ROOT / ".gitmodules").read_text(encoding="utf-8")

    assert entry["license"] == "not_found"
    assert entry["inclusion_mode"] == "git_submodule"
    assert entry["commit"] == "9b9c4a57138501d17992fa639ff44d469b3a9f3e"
    assert "path = third_party/paper-skills" in gitmodules
    assert "https://github.com/mjkmain/paper_skills.git" in gitmodules


def test_recorded_snapshot_validation_passed() -> None:
    validation = json.loads((THIRD_PARTY / "validation.json").read_text(encoding="utf-8"))

    assert validation["valid"] is True
    assert validation["source_snapshots"] == 16
    assert validation["snapshot_files"] == 1417
    assert validation["git_blob_comparison"]["content_mismatches"] == 0
    assert validation["license_files"]["unlicensed_projects_redistributed_as_source"] == 0


def test_no_nested_git_metadata_in_copied_snapshots() -> None:
    copied = [
        ROOT / entry["local_path"]
        for entry in MANIFEST["entries"]
        if entry["inclusion_mode"] == "source_snapshot"
    ]

    assert not any(path.name == ".git" for root in copied for path in root.rglob(".git"))
