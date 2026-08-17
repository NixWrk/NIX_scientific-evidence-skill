#!/usr/bin/env python3
"""Audit an existing DOCX title page against an explicit title-page payload.

The payload is deliberately the same JSON accepted by
``apply_dissertation_title_page.py``.  This auditor reads the DOCX package and
returns a PSES-DISS-001/v1 findings envelope; it never rewrites the source
document.  A first-page boundary is considered known only when the package
contains an explicit ``w:br w:type=\"page\"`` or ``w:lastRenderedPageBreak``.
Without that evidence the auditor reports a source-quality recommendation and
does not turn absent text into a normative violation.

The base title-page requirements come from GOST R 7.0.11-2011 REQ-007.  The
BMSTU applicant signature is checked only when its authority is explicitly
selected in ``local_profile.authority_ids``.  GOST is not used here to infer
ordering, alignment, typography, or other layout choices.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from lxml import etree

try:
    from apply_dissertation_title_page import (
        BMSTU_TITLE_PAGE_AUTHORITY,
        GOST_TITLE_PAGE_AUTHORITY,
        TitlePageError,
        normalize_payload,
    )
    from critic_common import finding, load_json, write_envelope
except ModuleNotFoundError:
    # ``importlib.util.spec_from_file_location`` callers do not necessarily
    # add the scripts directory to sys.path; CLI execution already does.
    _SCRIPT_DIR = str(Path(__file__).resolve().parent)
    if _SCRIPT_DIR not in sys.path:
        sys.path.insert(0, _SCRIPT_DIR)
    from apply_dissertation_title_page import (
        BMSTU_TITLE_PAGE_AUTHORITY,
        GOST_TITLE_PAGE_AUTHORITY,
        TitlePageError,
        normalize_payload,
    )
    from critic_common import finding, load_json, write_envelope


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W_NS}

MODULE = "title-page-critic"
SOURCE_RULE = "TITLE-SOURCE-001"
GOST_RULE = "NORM-GOST-R-7.0.11-2011-001:REQ-007"
BMSTU_RULE = "NORM-BMSTU-DISS-REQ-001:REQ-007"


class TitlePageAuditError(ValueError):
    """The source DOCX or expected payload cannot be audited safely."""


def _w(local: str) -> str:
    return f"{{{W_NS}}}{local}"


def _normalise_text(value: str) -> str:
    """Collapse Word whitespace for presence comparisons, not anchors."""

    return re.sub(r"\s+", " ", value.replace("\u00a0", " ")).strip()


@dataclass(frozen=True)
class _Paragraph:
    """A paragraph fragment before the first explicit page boundary."""

    text: str
    anchor_text: str
    element: etree._Element


@dataclass(frozen=True)
class _PageScope:
    paragraphs: tuple[_Paragraph, ...]
    all_paragraphs: tuple[str, ...]
    boundary_proven: bool

    @property
    def text(self) -> str:
        return "\n".join(item.text for item in self.paragraphs if item.text.strip())


def _ancestor_paragraph(node: etree._Element) -> etree._Element | None:
    parent = node.getparent()
    while parent is not None:
        if parent.tag == _w("p"):
            return parent
        parent = parent.getparent()
    return None


def _paragraph_anchor_text(paragraph: etree._Element) -> str:
    """Match the Word review adapter's concatenation of actual text nodes."""

    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))


def _all_paragraph_texts(root: etree._Element) -> tuple[str, ...]:
    return tuple(
        _paragraph_anchor_text(paragraph)
        for paragraph in root.xpath(".//w:p", namespaces=NS)
    )


def _page_scope(root: etree._Element) -> _PageScope:
    """Return text before the first explicit Word page break.

    The document order is walked at element level so a break in a table cell
    or in the middle of a paragraph ends the scope at the exact point at which
    Word records it.  A line break (``w:br`` without ``w:type=page``) is text
    layout and does not establish a page boundary.
    """

    body = root.find(".//" + _w("body"))
    if body is None:
        raise TitlePageAuditError("DOCX has no Word document body")

    records: list[dict[str, Any]] = []
    by_element: dict[int, dict[str, Any]] = {}
    boundary = False
    for node in body.iter():
        if node.tag == _w("br") and node.get(_w("type")) == "page":
            boundary = True
            break
        if node.tag == _w("lastRenderedPageBreak"):
            boundary = True
            break
        if node.tag == _w("p"):
            record = {"element": node, "parts": [], "anchor_parts": []}
            records.append(record)
            by_element[id(node)] = record
            continue
        if node.tag in {_w("t"), _w("tab"), _w("br")} and not boundary:
            paragraph = _ancestor_paragraph(node)
            if paragraph is not None and id(paragraph) in by_element:
                record = by_element[id(paragraph)]
                if node.tag == _w("t"):
                    value = node.text or ""
                    record["parts"].append(value)
                    record["anchor_parts"].append(value)
                else:
                    # Line breaks and tabs separate visible words, but are not
                    # part of an exact-text anchor used by apply_word_review.
                    record["parts"].append(" ")

    visible = tuple(
        _Paragraph(
            "".join(record["parts"]),
            "".join(record["anchor_parts"]),
            record["element"],
        )
        for record in records
    )
    return _PageScope(
        paragraphs=visible,
        all_paragraphs=_all_paragraph_texts(root),
        boundary_proven=boundary,
    )


def _source_quality_finding(*, observed: str, expected: str, issue_id: str = "TITLE-SOURCE-001", suggested_fix: str) -> dict[str, Any]:
    return finding(
        issue_id,
        SOURCE_RULE,
        MODULE,
        observed,
        expected,
        severity="note",
        issue_class="recommendation",
        authority_ids=[],
        suggested_fix=suggested_fix,
        word_action="none",
    )


def _anchor(scope: _PageScope) -> tuple[str, int] | None:
    """Choose an exact, unique paragraph anchor for a Word comment.

    ``apply_word_review.py`` anchors within one paragraph.  We therefore never
    return a cross-paragraph string.  A full paragraph is preferred; if no
    paragraph is unique, a longest unique whitespace-delimited phrase is used.
    """

    candidates: list[str] = []
    for paragraph in scope.paragraphs:
        raw = paragraph.anchor_text
        if raw.strip():
            candidates.append(raw)

    def occurrences(needle: str) -> list[int]:
        """Return Word-review-style occurrence ordinals, not paragraph indexes."""

        hits: list[int] = []
        for paragraph in scope.all_paragraphs:
            if not needle:
                continue
            start = 0
            while True:
                position = paragraph.find(needle, start)
                if position < 0:
                    break
                hits.append(position)
                start = position + max(1, len(needle))
        return hits

    for candidate in candidates:
        hits = occurrences(candidate)
        if len(hits) == 1:
            return candidate, 1

    # Repeated paragraph text is unusual on a title page, but a unique phrase
    # remains safe and still gives the Word adapter a same-paragraph anchor.
    for paragraph in candidates:
        words = paragraph.split()
        for width in range(len(words) - 1, 0, -1):
            for start in range(0, len(words) - width + 1):
                phrase = " ".join(words[start : start + width])
                hits = occurrences(phrase)
                if len(hits) == 1:
                    return phrase, 1
    return None


@dataclass(frozen=True)
class _RequiredField:
    key: str
    label: str
    expected: str
    authority: str = GOST_RULE


def _required_fields(payload: Mapping[str, Any]) -> tuple[_RequiredField, ...]:
    fields: list[_RequiredField] = [
        _RequiredField("status", "статус «на правах рукописи»", str(payload["status"])),
        _RequiredField("organization", "наименование организации", str(payload["organization"])),
        _RequiredField("author", "ФИО диссертанта", str(payload["author"])),
        _RequiredField("title", "название диссертации", str(payload["title"])),
        _RequiredField("specialty_code", "шифр специальности", str(payload["specialty_code"])),
        _RequiredField("specialty_name", "наименование специальности", str(payload["specialty_name"])),
        _RequiredField("degree", "искомая учёная степень", str(payload["degree"])),
        _RequiredField("science_field", "отрасль науки", str(payload["science_field"])),
    ]
    for index, supervisor in enumerate(payload["supervisors"], start=1):
        role = str(supervisor["role"])
        # The generator stores a structured person's display as comma-separated
        # components. GOST requires the facts, not this local presentation order,
        # so the critic checks each component independently.
        components = [part.strip() for part in str(supervisor["display"]).split(",") if part.strip()]
        component_labels = ("ФИО", "учёная степень", "учёное звание", "должность")
        for component_index, component in enumerate(components, start=1):
            label = component_labels[min(component_index - 1, len(component_labels) - 1)]
            fields.append(
                _RequiredField(
                    f"supervisor_{index}_{component_index}",
                    f"{label} ({role})",
                    component,
                )
            )
    fields.extend(
        (
            _RequiredField("place", "место написания", str(payload["city"])),
            _RequiredField("year", "год написания", str(payload["year"])),
        )
    )
    if BMSTU_TITLE_PAGE_AUTHORITY in payload.get("authority_ids", []):
        signature = payload.get("signature_line")
        if not isinstance(signature, str) or not signature.strip():
            # normalize_payload normally rejects this, but keep the invariant
            # local in case a caller supplies a pre-normalised mapping.
            raise TitlePageAuditError(
                "BMSTU title-page authority requires a non-empty signature_line"
            )
        fields.append(
            _RequiredField(
                "signature_line",
                "подпись соискателя",
                signature,
                authority=BMSTU_RULE,
            )
        )
    return tuple(fields)


def _presence_text(scope: _PageScope) -> str:
    return _normalise_text(scope.text)


def _contains(page_text: str, expected: str) -> bool:
    return _normalise_text(expected) in page_text


def _audit_scope(scope: _PageScope, payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    if not scope.boundary_proven:
        return [
            _source_quality_finding(
                observed="В word/document.xml не обнаружены w:br с type=page или w:lastRenderedPageBreak.",
                expected="Граница первой страницы должна быть доказана явным разрывом страницы для безопасной проверки реквизитов.",
                suggested_fix="Сохранить документ из Word с явной границей страницы или передать версию с w:br type=page / w:lastRenderedPageBreak.",
            )
        ]

    if not _presence_text(scope):
        return [
            _source_quality_finding(
                issue_id="TITLE-SOURCE-002",
                observed="До первого явного разрыва страницы текстовых абзацев не обнаружено.",
                expected="На проверяемой первой странице должен быть доступен текстовый слой реквизитов.",
                suggested_fix="Передать DOCX с текстовым слоем титульного листа; изображение без OCR не проверять как текст.",
            )
        ]

    page_text = _presence_text(scope)
    findings: list[dict[str, Any]] = []
    for field in _required_fields(payload):
        # Place and year are checked independently; this avoids requiring a
        # local comma or line-break convention that GOST does not prescribe.
        if field.key == "place":
            present = _contains(page_text, field.expected)
        elif field.key == "year":
            present = _contains(page_text, field.expected)
        else:
            present = _contains(page_text, field.expected)
        if present:
            continue

        anchor = _anchor(scope)
        if anchor is None:
            findings.append(
                _source_quality_finding(
                    issue_id=f"TITLE-SOURCE-{len(findings) + 3:03d}",
                    observed=f"Реквизит «{field.label}» не найден, но на первой странице нет уникального текстового якоря для Word-комментария.",
                    expected="Любое реальное замечание должно ссылаться на существующий уникальный текст первой страницы.",
                    suggested_fix="Проверить титульный лист вручную или передать DOCX с уникальным текстовым абзацем.",
                )
            )
            continue

        exact_text, occurrence = anchor
        findings.append(
            finding(
                f"TITLE-REQ-007-{len(findings) + 1:03d}",
                field.authority,
                MODULE,
                f"Реквизит «{field.label}» со значением «{field.expected}» не обнаружен на проверяемой первой странице.",
                f"На титульном листе присутствует реквизит «{field.label}».",
                exact_text=exact_text,
                occurrence=occurrence,
                severity="major",
                issue_class="normative_violation",
                authority_ids=[field.authority],
                suggested_fix=f"Добавить на титульный лист обязательный реквизит: {field.label} — «{field.expected}».",
                word_action="comment",
            )
        )
    return findings


def audit_title_page(
    input_docx: str | Path,
    expected_payload: Mapping[str, Any] | Any,
) -> list[dict[str, Any]]:
    """Return deterministic title-page findings without modifying ``input_docx``."""

    source = Path(input_docx)
    try:
        normalized = normalize_payload(expected_payload)
    except (TitlePageError, TypeError, KeyError) as exc:
        raise TitlePageAuditError(f"expected title-page JSON is invalid: {exc}") from exc

    try:
        with zipfile.ZipFile(source, "r") as archive:
            document_bytes = archive.read("word/document.xml")
    except KeyError as exc:
        raise TitlePageAuditError("DOCX has no word/document.xml") from exc
    except (OSError, zipfile.BadZipFile) as exc:
        raise TitlePageAuditError(f"cannot read source DOCX: {exc}") from exc

    try:
        root = etree.fromstring(document_bytes)
    except etree.XMLSyntaxError as exc:
        raise TitlePageAuditError(f"word/document.xml is not valid XML: {exc}") from exc
    return _audit_scope(_page_scope(root), normalized)


# The other deterministic auditors expose ``audit``; keep the short alias for
# callers that discover modules by convention.
audit = audit_title_page


def audit_title_page_from_files(
    json_path: str | Path,
    input_docx: str | Path,
) -> list[dict[str, Any]]:
    return audit_title_page(input_docx, load_json(Path(json_path)))


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", help="expected title-page JSON or source DOCX")
    parser.add_argument("second", help="source DOCX or expected title-page JSON")
    parser.add_argument("--out", "--output", dest="output", type=Path)
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = _parse_args(argv)
    first, second = Path(args.first), Path(args.second)
    if first.suffix.lower() == ".docx" and second.suffix.lower() != ".docx":
        input_docx, json_path = first, second
    elif second.suffix.lower() == ".docx" and first.suffix.lower() != ".docx":
        json_path, input_docx = first, second
    else:
        print(
            "audit_dissertation_title_page: exactly one positional input must be .docx and the other .json",
            file=sys.stderr,
        )
        return 2
    try:
        rendered = write_envelope(audit_title_page_from_files(json_path, input_docx), args.output)
    except (TitlePageAuditError, TitlePageError, OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        print(f"audit_dissertation_title_page: error: {exc}", file=sys.stderr)
        return 2
    print(rendered, end="")
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the CLI
    raise SystemExit(main())
