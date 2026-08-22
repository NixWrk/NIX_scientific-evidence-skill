#!/usr/bin/env python3
"""Финальный блокирующий шлюз для сохраняемых русскоязычных материалов."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


SHA256 = re.compile(r"[0-9a-f]{64}")
REQUIRED_MANUAL_CHECKS = (
    "full_text",
    "terminology",
    "syntax",
    "cohesion",
    "translation_calques",
    "genre_profile",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _path(base: Path, value: object, field: str, errors: list[str]) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field}: требуется непустой путь")
        return None
    return (base / value).resolve()


def validate_manifest(data: object, manifest_path: Path) -> dict:
    errors: list[str] = []
    if not isinstance(data, dict):
        return {"status": "failed", "release_ready": False, "errors": ["корень: требуется объект JSON"]}
    if data.get("schema_version") != "1.0":
        errors.append("schema_version: ожидается '1.0'")
    if data.get("working_language") != "ru":
        errors.append("working_language: ожидается 'ru'")
    if data.get("status") != "passed":
        errors.append("status: финальный реестр обязан запрашивать статус 'passed'")

    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        errors.append("artifacts: требуется непустой список всех русскоязычных материалов выпуска")
        artifacts = []

    base = manifest_path.resolve().parent
    seen: set[str] = set()
    for index, entry in enumerate(artifacts):
        here = f"artifacts[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{here}: требуется объект")
            continue

        artifact_path = _path(base, entry.get("artifact_path"), f"{here}.artifact_path", errors)
        text_path = _path(base, entry.get("text_path"), f"{here}.text_path", errors)
        report_path = _path(base, entry.get("audit_report"), f"{here}.audit_report", errors)
        declared_artifact_hash = entry.get("artifact_sha256")
        declared_text_hash = entry.get("text_sha256")

        if artifact_path is not None:
            identity = str(artifact_path).casefold()
            if identity in seen:
                errors.append(f"{here}.artifact_path: материал указан повторно")
            seen.add(identity)
            if not artifact_path.is_file():
                errors.append(f"{here}.artifact_path: файл не найден")
            elif not isinstance(declared_artifact_hash, str) or not SHA256.fullmatch(declared_artifact_hash):
                errors.append(f"{here}.artifact_sha256: требуется SHA-256")
            elif _sha256(artifact_path) != declared_artifact_hash:
                errors.append(f"{here}.artifact_sha256: материал изменён после проверки")

        actual_text_hash: str | None = None
        if text_path is not None:
            if not text_path.is_file():
                errors.append(f"{here}.text_path: извлечённый текст не найден")
            else:
                actual_text_hash = _sha256(text_path)
                if not isinstance(declared_text_hash, str) or not SHA256.fullmatch(declared_text_hash):
                    errors.append(f"{here}.text_sha256: требуется SHA-256")
                elif actual_text_hash != declared_text_hash:
                    errors.append(f"{here}.text_sha256: текст изменён после проверки")

        report: object = None
        if report_path is not None:
            if not report_path.is_file():
                errors.append(f"{here}.audit_report: отчёт не найден")
            else:
                try:
                    report = json.loads(report_path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                    errors.append(f"{here}.audit_report: отчёт не прочитан ({exc})")

        profiles = entry.get("profiles")
        if not isinstance(profiles, list) or "core" not in profiles:
            errors.append(f"{here}.profiles: требуется список с профилем 'core'")
            profiles = []
        if isinstance(report, dict):
            counts = report.get("counts")
            if counts != {"errors": 0, "warnings": 0, "issues": 0} or report.get("issues") != []:
                errors.append(f"{here}.audit_report: финальный машинный аудит должен содержать ноль ошибок и предупреждений")
            if report.get("profiles") != profiles:
                errors.append(f"{here}.profiles: профили не совпадают с отчётом аудита")
            report_artifact = report.get("artifact")
            report_hash = report_artifact.get("sha256") if isinstance(report_artifact, dict) else None
            if actual_text_hash is None or report_hash != actual_text_hash:
                errors.append(f"{here}.audit_report: отчёт относится к другой версии текста")
        else:
            errors.append(f"{here}.audit_report: корень отчёта должен быть объектом JSON")

        manual = entry.get("manual_review")
        if not isinstance(manual, dict):
            errors.append(f"{here}.manual_review: требуется запись сплошного ручного чтения")
            continue
        if manual.get("status") != "passed":
            errors.append(f"{here}.manual_review.status: ожидается 'passed'")
        if actual_text_hash is None or manual.get("reviewed_text_sha256") != actual_text_hash:
            errors.append(f"{here}.manual_review.reviewed_text_sha256: проверена другая версия текста")
        checks = manual.get("checks")
        if not isinstance(checks, dict):
            errors.append(f"{here}.manual_review.checks: требуется объект")
        else:
            for check in REQUIRED_MANUAL_CHECKS:
                if checks.get(check) != "passed":
                    errors.append(f"{here}.manual_review.checks.{check}: ожидается 'passed'")

    return {"status": "passed" if not errors else "failed", "release_ready": not errors, "errors": errors}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="финальный реестр языковой проверки в JSON")
    parser.add_argument("--json", action="store_true", help="вывести отчёт JSON")
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
        report = validate_manifest(data, args.manifest)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        report = {"status": "failed", "release_ready": False, "errors": [str(exc)]}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"status={report['status']} release_ready={str(report['release_ready']).lower()}")
        for error in report["errors"]:
            print(f"error: {error}")
    return 0 if report["release_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
