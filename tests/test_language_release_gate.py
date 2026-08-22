import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "scientific-evidence-workflow"
AUDITOR_PATH = SKILL / "scripts" / "audit_russian_style.py"
GATE_PATH = SKILL / "scripts" / "validate_language_release.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDITOR = load_module("language_release_auditor", AUDITOR_PATH)
GATE = load_module("language_release_validator", GATE_PATH)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_release(tmp_path: Path, text: str = "Измерение выполнено при комнатной температуре."):
    artifact = tmp_path / "output.md"
    extracted = tmp_path / "output.text.md"
    audit_path = tmp_path / "output.audit.json"
    manifest_path = tmp_path / "language-release.json"
    artifact.write_text(text, encoding="utf-8")
    extracted.write_text(text, encoding="utf-8")
    text_hash = sha256(extracted)

    audit = AUDITOR.audit_text(text, ["genre-notebook"])
    audit["artifact"] = {"path": str(extracted), "sha256": text_hash}
    audit_path.write_text(json.dumps(audit, ensure_ascii=False), encoding="utf-8")

    manifest = {
        "schema_version": "1.0",
        "working_language": "ru",
        "status": "passed",
        "artifacts": [
            {
                "artifact_path": artifact.name,
                "artifact_sha256": sha256(artifact),
                "text_path": extracted.name,
                "text_sha256": text_hash,
                "audit_report": audit_path.name,
                "profiles": ["core", "genre-notebook"],
                "manual_review": {
                    "status": "passed",
                    "reviewed_text_sha256": text_hash,
                    "checks": {name: "passed" for name in GATE.REQUIRED_MANUAL_CHECKS},
                },
            }
        ],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return manifest, manifest_path, artifact


def test_final_gate_passes_only_clean_hash_bound_release(tmp_path: Path) -> None:
    manifest, manifest_path, _ = build_release(tmp_path)

    report = GATE.validate_manifest(manifest, manifest_path)

    assert report == {"status": "passed", "release_ready": True, "errors": []}


def test_final_gate_rejects_warning_even_when_manual_review_says_passed(tmp_path: Path) -> None:
    manifest, manifest_path, _ = build_release(
        tmp_path, "Следует отметить полученный результат."
    )

    report = GATE.validate_manifest(manifest, manifest_path)

    assert report["release_ready"] is False
    assert any("ноль ошибок и предупреждений" in error for error in report["errors"])


def test_final_gate_rejects_artifact_changed_after_review(tmp_path: Path) -> None:
    manifest, manifest_path, artifact = build_release(tmp_path)
    artifact.write_text("Изменённый итоговый текст.", encoding="utf-8")

    report = GATE.validate_manifest(manifest, manifest_path)

    assert report["release_ready"] is False
    assert any("изменён после проверки" in error for error in report["errors"])


def test_final_gate_rejects_incomplete_manual_reading(tmp_path: Path) -> None:
    manifest, manifest_path, _ = build_release(tmp_path)
    del manifest["artifacts"][0]["manual_review"]["checks"]["cohesion"]

    report = GATE.validate_manifest(manifest, manifest_path)

    assert report["release_ready"] is False
    assert any("checks.cohesion" in error for error in report["errors"])


def test_final_gate_rejects_non_object_audit_report(tmp_path: Path) -> None:
    manifest, manifest_path, _ = build_release(tmp_path)
    report_path = tmp_path / manifest["artifacts"][0]["audit_report"]
    report_path.write_text("[]", encoding="utf-8")

    report = GATE.validate_manifest(manifest, manifest_path)

    assert report["release_ready"] is False
    assert any("объектом JSON" in error for error in report["errors"])


def test_audit_cli_fingerprints_the_exact_checked_text(tmp_path: Path) -> None:
    text_path = tmp_path / "text.md"
    text_path.write_text("Проверка завершена после чтения текста.", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(AUDITOR_PATH), str(text_path), "--json"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    report = json.loads(completed.stdout)

    assert report["artifact"]["sha256"] == sha256(text_path)
    assert report["artifact"]["path"] == str(text_path)


def test_skill_forbids_completion_wording_before_final_gate() -> None:
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    language = (SKILL / "references" / "russian-scientific-style.md").read_text(
        encoding="utf-8"
    )

    assert "validate_language_release.py" in skill
    assert "never call the work ready, complete, released, or overall passed" in skill
    assert "работа не завершена" in language
