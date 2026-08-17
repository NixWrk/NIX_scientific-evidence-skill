#!/usr/bin/env python3
"""Audit appendix headings and main-text references against an explicit registry."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping, Sequence

try:
    from audit_illustration_register import (
        RegisterAuditError,
        SourceDocument,
        _anchor_at,
        _fallback_anchor,
        _fold,
        _versioned_authorities,
        load_source,
    )
    from critic_common import finding, load_json, write_envelope
except ModuleNotFoundError:  # pragma: no cover - importlib callers
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from audit_illustration_register import (
        RegisterAuditError,
        SourceDocument,
        _anchor_at,
        _fallback_anchor,
        _fold,
        _versioned_authorities,
        load_source,
    )
    from critic_common import finding, load_json, write_envelope


MODULE = "appendix-register-critic"


def _validate_registry(registry: Any) -> list[dict[str, Any]]:
    if not isinstance(registry, Mapping):
        raise RegisterAuditError("registry JSON must be an object")
    items = registry.get("items")
    if not isinstance(items, list):
        raise RegisterAuditError("registry.items must be an array")
    validated: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        if not isinstance(item, Mapping):
            raise RegisterAuditError(f"registry.items[{index}] must be an object")
        values: dict[str, Any] = {}
        for key in ("appendix_id", "designation", "title"):
            raw = item.get(key)
            if not isinstance(raw, (str, int)) or not str(raw).strip():
                raise RegisterAuditError(f"registry.items[{index}].{key} must be non-empty")
            values[key] = str(raw).strip()
        values["authority_ids"] = item.get("authority_ids")
        if "page" in item:
            values["page"] = item["page"]
        if "page_number" in item:
            values["page_number"] = item["page_number"]
        validated.append(values)
    return validated


def _designation_pattern(designation: str, *, heading: bool) -> re.Pattern[str]:
    escaped = re.escape(_fold(designation))
    prefix = r"^\s*" if heading else ""
    # The non-heading form covers common Russian inflections used in prose.
    word = r"приложение" if heading else r"приложени(?:е|я|ю|и|ем|ях|ями|й)"
    return re.compile(prefix + word + rf"\s+{escaped}(?!\w)", re.IGNORECASE)


def _all_heading_indices(document: SourceDocument) -> list[int]:
    pattern = re.compile(r"^\s*приложение\s+[A-Za-zА-Яа-яЁё0-9.-]+(?:\s|$)", re.IGNORECASE)
    return [index for index, paragraph in enumerate(document.paragraphs) if pattern.search(_fold(paragraph.visible))]


def _heading_indices(document: SourceDocument, designation: str) -> list[int]:
    pattern = _designation_pattern(designation, heading=True)
    return [index for index, paragraph in enumerate(document.paragraphs) if pattern.search(_fold(paragraph.visible))]


def _heading_has_title(document: SourceDocument, index: int, title: str) -> bool:
    expected = _fold(title)
    if expected in _fold(document.paragraphs[index].visible):
        return True
    # A separate status line such as "обязательное" may stand between the
    # designation and title. Stop before the next appendix heading.
    for following in range(index + 1, min(index + 4, len(document.paragraphs))):
        if re.search(r"^\s*приложение\s+", _fold(document.paragraphs[following].visible)):
            break
        if expected in _fold(document.paragraphs[following].visible):
            return True
    return False


def _reference_indices(document: SourceDocument, designation: str, boundary: int) -> list[int]:
    escaped = re.escape(_fold(designation))
    pattern = re.compile(r"приложен\w*" + rf"\s+{escaped}(?!\w)", re.IGNORECASE)
    return [
        index
        for index, paragraph in enumerate(document.paragraphs[:boundary])
        if pattern.search(_fold(paragraph.visible))
    ]


def _build_finding(
    issue_id: str,
    rule_id: str,
    document: SourceDocument,
    *,
    anchor_index: int | None,
    observed: Any,
    expected: Any,
    authorities: list[str],
    severity: str,
    suggested_fix: str,
    fallback_class: str = "internal_inconsistency",
    action: bool = True,
) -> dict[str, Any]:
    issue_class = "normative_violation" if authorities else fallback_class
    resolved_rule = authorities[0] if authorities else rule_id
    anchor = (_anchor_at(document, anchor_index) or _fallback_anchor(document)) if action else None
    return finding(
        issue_id,
        resolved_rule,
        MODULE,
        observed,
        expected,
        exact_text=anchor[0] if anchor else None,
        occurrence=anchor[1] if anchor else 1,
        severity=severity,
        issue_class=issue_class,
        authority_ids=authorities,
        suggested_fix=suggested_fix,
        word_action="comment" if anchor else "none",
    )


def audit(source: str | Path | SourceDocument, registry: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return deterministic appendix findings without changing the source."""

    document = source if isinstance(source, SourceDocument) else load_source(source)
    items = _validate_registry(registry)
    root_authorities = registry.get("authority_ids") if isinstance(registry, Mapping) else None
    findings: list[dict[str, Any]] = []
    all_headings = _all_heading_indices(document)
    boundary = min(all_headings) if all_headings else None

    designations = [_fold(item["designation"]) for item in items]
    duplicates = {designation for designation, count in Counter(designations).items() if count > 1}
    for designation in sorted(duplicates):
        related = [item for item in items if _fold(item["designation"]) == designation]
        authorities = _versioned_authorities(root_authorities, *(item.get("authority_ids") for item in related))
        indices = _heading_indices(document, related[0]["designation"])
        findings.append(
            _build_finding(
                f"APPENDIX-REGISTER-DUPLICATE-{len(findings)+1:03d}",
                "APPENDIX-DESIGNATION-001",
                document,
                anchor_index=indices[0] if indices else None,
                observed={"designation": related[0]["designation"], "appendix_ids": [item["appendix_id"] for item in related]},
                expected="one registry item for each appendix designation",
                authorities=authorities,
                severity="major",
                suggested_fix="Назначить каждому приложению уникальное обозначение в утверждённом реестре.",
            )
        )

    seen: set[str] = set()
    for item in items:
        designation_key = _fold(item["designation"])
        if designation_key in seen:
            continue
        seen.add(designation_key)
        authorities = _versioned_authorities(root_authorities, item.get("authority_ids"))
        indices = _heading_indices(document, item["designation"])
        matching = [index for index in indices if _heading_has_title(document, index, item["title"])]

        if not matching:
            findings.append(
                _build_finding(
                    f"APPENDIX-HEADING-MISSING-{len(findings)+1:03d}",
                    "APPENDIX-HEADING-001",
                    document,
                    anchor_index=indices[0] if indices else None,
                    observed={"appendix_id": item["appendix_id"], "designation": item["designation"], "title": item["title"], "matching_heading_count": 0},
                    expected="an appendix heading with the approved designation and title",
                    authorities=authorities,
                    severity="major",
                    suggested_fix="Добавить или согласовать заголовок приложения с утверждённым реестром.",
                )
            )
        if len(indices) > 1:
            findings.append(
                _build_finding(
                    f"APPENDIX-SOURCE-DUPLICATE-{len(findings)+1:03d}",
                    "APPENDIX-DESIGNATION-001",
                    document,
                    anchor_index=indices[1],
                    observed={"appendix_id": item["appendix_id"], "designation": item["designation"], "heading_occurrences": len(indices)},
                    expected="one appendix heading carrying this designation",
                    authorities=authorities,
                    severity="major",
                    suggested_fix="Исправить повтор обозначения или удалить дублирующий заголовок после сверки с реестром.",
                )
            )

        if boundary is None:
            findings.append(
                _build_finding(
                    f"APPENDIX-REFERENCE-NOT-ASSESSED-{len(findings)+1:03d}",
                    "APPENDIX-REFERENCE-SCOPE-001",
                    document,
                    anchor_index=None,
                    observed={"appendix_id": item["appendix_id"], "status": "not_assessed", "reason": "first appendix boundary not found"},
                    expected="an identifiable first appendix heading delimiting the main text",
                    authorities=[],
                    severity="note",
                    suggested_fix="Обозначить заголовок первого приложения, затем повторить проверку ссылок из основной части.",
                    fallback_class="recommendation",
                    action=False,
                )
            )
        elif not _reference_indices(document, item["designation"], boundary):
            findings.append(
                _build_finding(
                    f"APPENDIX-REFERENCE-MISSING-{len(findings)+1:03d}",
                    "APPENDIX-REFERENCE-001",
                    document,
                    anchor_index=matching[0] if matching else (indices[0] if indices else boundary),
                    observed={"appendix_id": item["appendix_id"], "designation": item["designation"], "main_text_reference_count": 0, "first_appendix_paragraph": boundary + 1},
                    expected="at least one textual reference in the main text before the first appendix",
                    authorities=authorities,
                    severity="minor",
                    suggested_fix="Добавить в основной текст отдельную ссылку на приложение до заголовка первого приложения.",
                )
            )

        if "page" in item or "page_number" in item:
            findings.append(
                _build_finding(
                    f"APPENDIX-PAGE-NOT-ASSESSED-{len(findings)+1:03d}",
                    "APPENDIX-PAGE-001",
                    document,
                    anchor_index=matching[0] if matching else (indices[0] if indices else None),
                    observed={"appendix_id": item["appendix_id"], "status": "not_assessed", "declared_page": item.get("page", item.get("page_number"))},
                    expected="page numbers are outside this structural auditor's scope",
                    authorities=[],
                    severity="note",
                    suggested_fix="Проверить номер страницы после финальной пагинации отдельным рендерным контролем.",
                    fallback_class="recommendation",
                    action=False,
                )
            )
    return findings


def audit_from_files(source_path: str | Path, registry_path: str | Path) -> list[dict[str, Any]]:
    return audit(source_path, load_json(Path(registry_path)))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Source .docx or UTF-8 .txt file.")
    parser.add_argument("registry", type=Path, help="Appendix registry JSON.")
    parser.add_argument("--out", type=Path, help="Optional findings envelope path.")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        rendered = write_envelope(audit_from_files(args.source, args.registry), args.out)
    except (RegisterAuditError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"audit_appendix_register: error: {exc}", file=sys.stderr)
        return 2
    print(rendered, end="")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
