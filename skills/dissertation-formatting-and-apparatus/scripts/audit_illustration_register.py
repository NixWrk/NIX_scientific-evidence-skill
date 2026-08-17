#!/usr/bin/env python3
"""Audit figure/table captions and cross-references against an explicit registry."""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from lxml import etree

try:
    from critic_common import finding, load_json, write_envelope
except ModuleNotFoundError:  # pragma: no cover - importlib callers
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from critic_common import finding, load_json, write_envelope


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}
MODULE = "illustration-register-critic"
AUTHORITY_RE = re.compile(
    r"^(?:NORM|LOCAL)-[A-Za-z0-9][A-Za-z0-9._-]*(?:/v\d+(?:\.\d+)*)?:REQ-[A-Za-z0-9][A-Za-z0-9._-]*$"
)


class RegisterAuditError(ValueError):
    """The source or registry cannot be audited deterministically."""


@dataclass(frozen=True)
class Paragraph:
    visible: str
    anchor: str


@dataclass(frozen=True)
class SourceDocument:
    paragraphs: tuple[Paragraph, ...]
    kind: str


def _normalise(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip()


def _fold(value: str) -> str:
    return _normalise(value).casefold().replace("ё", "е")


def _docx_paragraphs(path: Path) -> tuple[Paragraph, ...]:
    try:
        with zipfile.ZipFile(path, "r") as archive:
            raw = archive.read("word/document.xml")
    except KeyError as exc:
        raise RegisterAuditError("DOCX has no word/document.xml") from exc
    except (OSError, zipfile.BadZipFile) as exc:
        raise RegisterAuditError(f"cannot read source DOCX: {exc}") from exc
    try:
        root = etree.fromstring(raw)
    except etree.XMLSyntaxError as exc:
        raise RegisterAuditError(f"word/document.xml is not valid XML: {exc}") from exc

    paragraphs: list[Paragraph] = []
    for paragraph in root.xpath(".//w:body//w:p", namespaces=NS):
        visible_parts: list[str] = []
        anchor_parts: list[str] = []
        for node in paragraph.iter():
            local = etree.QName(node).localname
            if local in {"t", "delText"}:
                value = node.text or ""
                visible_parts.append(value)
                anchor_parts.append(value)
            elif local in {"tab", "br", "cr"}:
                visible_parts.append(" ")
        paragraphs.append(Paragraph("".join(visible_parts), "".join(anchor_parts)))
    return tuple(paragraphs)


def _txt_paragraphs(path: Path) -> tuple[Paragraph, ...]:
    try:
        text = path.read_text(encoding="utf-8-sig", errors="strict")
    except (OSError, UnicodeError) as exc:
        raise RegisterAuditError(f"cannot read UTF-8 source text: {exc}") from exc
    return tuple(Paragraph(line, line) for line in text.splitlines())


def load_source(path: str | Path) -> SourceDocument:
    source = Path(path)
    suffix = source.suffix.casefold()
    if suffix == ".docx":
        return SourceDocument(_docx_paragraphs(source), "docx")
    if suffix == ".txt":
        return SourceDocument(_txt_paragraphs(source), "txt")
    raise RegisterAuditError("source must be a .docx or UTF-8 .txt file")


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
        for key in ("item_id", "kind", "number", "caption"):
            raw = item.get(key)
            if not isinstance(raw, (str, int)) or not str(raw).strip():
                raise RegisterAuditError(f"registry.items[{index}].{key} must be non-empty")
            values[key] = str(raw).strip()
        if values["kind"] not in {"figure", "table"}:
            raise RegisterAuditError(f"registry.items[{index}].kind must be figure or table")
        values["authority_ids"] = item.get("authority_ids")
        if "page" in item:
            values["page"] = item["page"]
        if "page_number" in item:
            values["page_number"] = item["page_number"]
        validated.append(values)
    return validated


def _versioned_authorities(*values: Any) -> list[str]:
    result: list[str] = []
    for value in values:
        if not isinstance(value, list):
            continue
        for authority in value:
            if isinstance(authority, str) and AUTHORITY_RE.fullmatch(authority.strip()):
                clean = authority.strip()
                if clean not in result:
                    result.append(clean)
    return result


def _classification(authorities: list[str], fallback: str = "internal_inconsistency") -> tuple[str, str]:
    return ("normative_violation", authorities[0]) if authorities else (fallback, "ILLUSTRATION-INTERNAL-001")


def _anchor_at(document: SourceDocument, index: int | None) -> tuple[str, int] | None:
    if index is None or not (0 <= index < len(document.paragraphs)):
        return None
    exact = document.paragraphs[index].anchor
    if not exact.strip():
        return None
    occurrence = 1
    for paragraph in document.paragraphs[:index]:
        occurrence += paragraph.anchor.count(exact)
    return exact, occurrence


def _fallback_anchor(document: SourceDocument) -> tuple[str, int] | None:
    for index, paragraph in enumerate(document.paragraphs):
        if paragraph.anchor.strip():
            return _anchor_at(document, index)
    return None


def _label_patterns(kind: str, number: str) -> tuple[re.Pattern[str], re.Pattern[str]]:
    escaped = re.escape(_fold(number))
    if kind == "figure":
        label = rf"(?:рис(?:унок|унка|унке|унку|унком|унки|унков|ункам|унками|унках)|рис\.)\s*{escaped}(?!\w)"
        caption = rf"^\s*(?:рисунок|рис\.)\s*{escaped}(?!\w)(?:\s*[-—–.:]\s*|\s+|$)"
    else:
        label = rf"таблиц(?:а|ы|е|у|ей|ам|ами|ах)\s*{escaped}(?!\w)"
        caption = rf"^\s*таблица\s*{escaped}(?!\w)(?:\s*[-—–.:]\s*|\s+|$)"
    return re.compile(label, re.IGNORECASE), re.compile(caption, re.IGNORECASE)


def _caption_indices(document: SourceDocument, kind: str, number: str) -> list[int]:
    _, caption_pattern = _label_patterns(kind, number)
    return [
        index
        for index, paragraph in enumerate(document.paragraphs)
        if caption_pattern.search(_fold(paragraph.visible))
    ]


def _caption_matches(document: SourceDocument, index: int, caption: str) -> bool:
    expected = _fold(caption)
    current = _fold(document.paragraphs[index].visible)
    if expected in current:
        return True
    # Word templates sometimes place the designation and caption on adjacent
    # paragraphs. Do not search beyond the immediately associated text.
    if index + 1 < len(document.paragraphs):
        return expected in _fold(document.paragraphs[index + 1].visible)
    return False


def _reference_indices(
    document: SourceDocument,
    kind: str,
    number: str,
    caption_indices: set[int],
) -> list[int]:
    label_pattern, _ = _label_patterns(kind, number)
    return [
        index
        for index, paragraph in enumerate(document.paragraphs)
        if index not in caption_indices and label_pattern.search(_fold(paragraph.visible))
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
) -> dict[str, Any]:
    issue_class, normative_rule = _classification(authorities, fallback_class)
    anchor = _anchor_at(document, anchor_index) or _fallback_anchor(document)
    return finding(
        issue_id,
        normative_rule if authorities else rule_id,
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
    """Return deterministic findings without changing the source."""

    document = source if isinstance(source, SourceDocument) else load_source(source)
    items = _validate_registry(registry)
    root_authorities = registry.get("authority_ids") if isinstance(registry, Mapping) else None
    findings: list[dict[str, Any]] = []

    keys = [(item["kind"], _fold(item["number"])) for item in items]
    duplicate_keys = {key for key, count in Counter(keys).items() if count > 1}
    for kind, number in sorted(duplicate_keys):
        related = [item for item in items if (item["kind"], _fold(item["number"])) == (kind, number)]
        authorities = _versioned_authorities(root_authorities, *(item.get("authority_ids") for item in related))
        source_indices = _caption_indices(document, kind, related[0]["number"])
        findings.append(
            _build_finding(
                f"ILLUSTRATION-REGISTER-DUPLICATE-{len(findings)+1:03d}",
                "ILLUSTRATION-NUMBER-001",
                document,
                anchor_index=source_indices[0] if source_indices else None,
                observed={"kind": kind, "number": related[0]["number"], "item_ids": [item["item_id"] for item in related]},
                expected="one registry item for each kind-and-number pair",
                authorities=authorities,
                severity="major",
                suggested_fix="Устранить дублирование номера в утверждённом реестре иллюстраций.",
            )
        )

    seen_items: set[tuple[str, str]] = set()
    for item in items:
        key = (item["kind"], _fold(item["number"]))
        if key in seen_items:
            continue
        seen_items.add(key)
        authorities = _versioned_authorities(root_authorities, item.get("authority_ids"))
        caption_indices = _caption_indices(document, item["kind"], item["number"])
        matching = [index for index in caption_indices if _caption_matches(document, index, item["caption"])]
        references = _reference_indices(document, item["kind"], item["number"], set(caption_indices))

        if not matching:
            findings.append(
                _build_finding(
                    f"ILLUSTRATION-CAPTION-MISSING-{len(findings)+1:03d}",
                    "ILLUSTRATION-CAPTION-001",
                    document,
                    anchor_index=caption_indices[0] if caption_indices else (references[0] if references else None),
                    observed={"item_id": item["item_id"], "kind": item["kind"], "number": item["number"], "caption": item["caption"], "matching_caption_count": 0},
                    expected="a caption/title matching the approved registry item",
                    authorities=authorities,
                    severity="major",
                    suggested_fix="Добавить или согласовать подпись/название с утверждённым реестром.",
                )
            )
        if len(caption_indices) > 1:
            findings.append(
                _build_finding(
                    f"ILLUSTRATION-SOURCE-DUPLICATE-{len(findings)+1:03d}",
                    "ILLUSTRATION-NUMBER-001",
                    document,
                    anchor_index=caption_indices[1],
                    observed={"item_id": item["item_id"], "kind": item["kind"], "number": item["number"], "caption_occurrences": len(caption_indices)},
                    expected="one caption/title carrying this kind-and-number pair",
                    authorities=authorities,
                    severity="major",
                    suggested_fix="Исправить повтор номера или удалить дублирующую подпись после сверки с реестром.",
                )
            )
        if not references:
            findings.append(
                _build_finding(
                    f"ILLUSTRATION-REFERENCE-MISSING-{len(findings)+1:03d}",
                    "ILLUSTRATION-REFERENCE-001",
                    document,
                    anchor_index=matching[0] if matching else (caption_indices[0] if caption_indices else None),
                    observed={"item_id": item["item_id"], "kind": item["kind"], "number": item["number"], "separate_reference_count": 0},
                    expected="at least one textual reference outside the caption/title paragraph",
                    authorities=authorities,
                    severity="minor",
                    suggested_fix="Добавить в основном тексте отдельную ссылку на иллюстрацию; подпись не считается ссылкой.",
                )
            )
    return findings


def audit_from_files(source_path: str | Path, registry_path: str | Path) -> list[dict[str, Any]]:
    return audit(source_path, load_json(Path(registry_path)))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Source .docx or UTF-8 .txt file.")
    parser.add_argument("registry", type=Path, help="Illustration registry JSON.")
    parser.add_argument("--out", type=Path, help="Optional findings envelope path.")
    args = parser.parse_args(list(argv) if argv is not None else None)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        rendered = write_envelope(audit_from_files(args.source, args.registry), args.out)
    except (RegisterAuditError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"audit_illustration_register: error: {exc}", file=sys.stderr)
        return 2
    print(rendered, end="")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
