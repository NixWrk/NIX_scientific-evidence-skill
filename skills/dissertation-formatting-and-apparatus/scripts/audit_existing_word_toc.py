#!/usr/bin/env python3
"""Conservatively audit an existing, Word-refreshed table of contents.

The auditor reads only the OOXML structure that is available in a DOCX:
Word heading styles, a real TOC field, and that field's cached result.  It
does not calculate page numbers and it does not treat a missing field as a
violation of GOST.  Normative findings are emitted only when both a reliable
heading register and a non-empty cached result make the comparison possible.

The command-line interface prints a ``PSES-DISS-001/v1`` findings envelope::

    python audit_existing_word_toc.py dissertation.docx --out toc-findings.json

The source document is never modified.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

from critic_common import finding, write_envelope
from finalize_word_toc import (
    TOC_FIELD_RE,
    TocError,
    W_NS,
    _body_paragraphs,
    _iter_field_infos,
    _parse_style_index,
    _parse_xml,
    _read_docx_parts,
    _text_from_paragraph,
    extract_headings,
)


MODULE = "dissertation-word-toc"
REQ_EXACT = "NORM-GOST-R-7.0.11-2011-001:REQ-008"
REQ_COMPLETE = "NORM-GOST-R-7.0.11-2011-001:REQ-031"

RULE_EXACT = "DISS-TOC-EXACT-001"
RULE_COMPLETE = "DISS-TOC-COMPLETENESS-001"
RULE_FIELD = "DISS-TOC-FIELD-001"
RULE_SOURCE = "DISS-TOC-SOURCE-QUALITY-001"

_TOC_SUFFIX_RE = re.compile(r"(?:\s*[.·…‥\u2024]+\s*(?:\d+\s*)?|\s+\d+\s*)$")


def _normalise(text: str) -> str:
    """Collapse layout whitespace without changing visible wording."""

    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()


def _cached_candidates(cached_text: str) -> Iterable[str]:
    """Yield conservative line-level representations of a cached TOC.

    Word commonly stores each TOC entry in a separate paragraph and puts the
    page number after a tab and dot leaders.  Removing only that terminal
    page-number shape lets us compare heading wording while deliberately
    leaving page-number correctness unassessed.
    """

    for raw_line in re.split(r"[\r\n]+", cached_text):
        for raw_segment in re.split(r"\t", raw_line):
            line = _normalise(raw_segment)
            if not line:
                continue
            yield line
            without_suffix = _TOC_SUFFIX_RE.sub("", line).strip()
            if without_suffix and without_suffix != line:
                yield without_suffix



def _cached_contains(cached_text: str, heading_text: str) -> bool:
    """Return whether *heading_text* occurs as an exact TOC entry.

    Whitespace differences introduced by OOXML layout are ignored.  A
    heading may be followed by dot leaders, a tab, or a page number.  The
    comparison remains line/segment based, so a heading prefix in another
    sentence is not treated as an exact TOC entry.
    """

    expected = _normalise(heading_text)
    if not expected:
        return False
    for candidate in _cached_candidates(cached_text):
        if candidate == expected:
            return True

    return False



def _source_quality_finding(
    *,
    observed: object,
    expected: object,
    suggested_fix: str,
    issue_id: str,
    severity: str = "note",
) -> dict:
    """Build a non-normative, non-Word-actionability source-quality finding."""

    return finding(
        issue_id,
        RULE_SOURCE,
        MODULE,
        observed,
        expected,
        severity=severity,
        issue_class="evidence_gap",
        suggested_fix=suggested_fix,
        word_action="none",
    )


def _error_finding(path: Path, message: str) -> dict:
    return finding(
        "TOC-SOURCE-ERROR-001",
        RULE_SOURCE,
        MODULE,
        {"path": str(path), "error": message},
        "a readable DOCX with inspectable Word structure",
        severity="major",
        issue_class="evidence_gap",
        suggested_fix="Проверить целостность DOCX и повторить аудит после восстановления исходного файла.",
        word_action="none",
    )


_W_FLD_SIMPLE = f"{{{W_NS}}}fldSimple"
_W_INSTR = f"{{{W_NS}}}instr"
_W_T = f"{{{W_NS}}}t"
_W_DELTEXT = f"{{{W_NS}}}delText"


def _simple_toc_fields(document_root) -> Iterable[dict]:
    """Read simple-field TOCs as a compatibility path for Word variants."""

    for node in document_root.iter():
        if node.tag != _W_FLD_SIMPLE:
            continue
        instruction = _normalise(node.get(_W_INSTR, ""))
        if not TOC_FIELD_RE.match(instruction):
            continue
        cached_parts = [
            child.text or ""
            for child in node.iter()
            if child.tag in {_W_T, _W_DELTEXT}
        ]
        cached_text = "".join(cached_parts).strip()
        yield {
            "instruction": instruction,
            "cached_text": cached_text,
            "has_separator": bool(cached_text),
        }


def _toc_title_anchor(document_root) -> tuple[str, int] | None:
    """Return a unique visible TOC-title word safe for the Word adapter."""

    matches: list[str] = []
    pattern = re.compile(r"^(оглавление|содержание)(?:\s*стр\.?)?$", re.IGNORECASE)
    for paragraph in _body_paragraphs(document_root):
        visible = _normalise(_text_from_paragraph(paragraph))
        match = pattern.fullmatch(visible)
        if match:
            matches.append(match.group(1))
    if len(matches) == 1:
        return matches[0], 1
    return None


def _toc_fields(document_root) -> list[dict]:
    fields = [
        field
        for field in _iter_field_infos(document_root)
        if TOC_FIELD_RE.match(str(field.get("instruction", "")))
    ]
    fields.extend(_simple_toc_fields(document_root))
    return fields


def audit(docx_path: str | Path) -> list[dict]:
    """Audit a DOCX and return a PSES-compatible list of findings.

    A clean refreshed field with reliable styled headings returns an empty
    list.  Missing styles or a missing/empty cached result produce only an
    evidence-gap finding.  A missing Word field produces a recommendation
    without authority; it is never promoted to a GOST violation.
    """

    path = Path(docx_path)
    try:
        entries = _read_docx_parts(path)
        document_root = _parse_xml(entries["word/document.xml"], "word/document.xml")
        styles = _parse_style_index(entries.get("word/styles.xml"))
        headings = [heading for heading in extract_headings(document_root, styles) if heading.text]
        fields = _toc_fields(document_root)
    except (TocError, OSError, KeyError, ValueError) as exc:
        return [_error_finding(path, str(exc))]

    findings: list[dict] = []
    reliable_headings = bool(headings) and bool([heading for heading in headings if heading.level == 1])
    if not reliable_headings:
        findings.append(
            _source_quality_finding(
                observed={
                    "heading_count": len(headings),
                    "main_heading_count": sum(heading.level == 1 for heading in headings),
                    "toc_field_count": len(fields),
                },
                expected="at least one non-empty level-1 Word heading and an inspectable heading hierarchy",
                issue_id="TOC-SOURCE-STYLES-001",
                suggested_fix=(
                    "Сохранить заголовки как стили Heading/Заголовок с явным уровнем и повторить аудит; "
                    "ручное форматирование и визуальный текст не позволяют надёжно проверить оглавление."
                ),
            )
        )

    if not fields:
        # A missing field is a technical recommendation, not a GOST
        # violation.  Without it there is also no cached result to compare.
        toc_anchor = _toc_title_anchor(document_root)
        findings.append(
            finding(
                "TOC-FIELD-001",
                RULE_FIELD,
                MODULE,
                {"toc_field_count": 0},
                "a real Word TOC field is present when automatic refresh is required",
                exact_text=toc_anchor[0] if toc_anchor else None,
                occurrence=toc_anchor[1] if toc_anchor else 1,
                severity="note",
                issue_class="recommendation",
                suggested_fix=(
                    "При необходимости автоматического обновления вставить настоящее поле TOC; "
                    "само отсутствие поля не является нарушением ГОСТ."
                ),
                word_action="comment" if toc_anchor else "none",
            )
        )
        findings.append(
            _source_quality_finding(
                observed={"toc_field_count": 0, "cached_result_present": False},
                expected="a non-empty cached result from an externally refreshed Word TOC field",
                issue_id="TOC-SOURCE-CACHE-001",
                suggested_fix=(
                    "Вставить и обновить настоящее поле оглавления в Word перед проверкой его "
                    "согласованности с заголовками. Номера страниц не проверяются."
                ),
            )
        )
        return findings

    field = fields[0]
    field_match = TOC_FIELD_RE.match(str(field.get("instruction", "")))
    included_end_level = int(field_match.group("end")) if field_match else 1
    cached_text = str(field.get("cached_text", "") or "")
    if not field.get("has_separator") or not cached_text.strip():
        findings.append(
            _source_quality_finding(
                observed={
                    "toc_field_count": len(fields),
                    "field_code": field.get("instruction", ""),
                    "has_cached_separator": bool(field.get("has_separator")),
                    "cached_result_present": bool(cached_text.strip()),
                },
                expected="a non-empty cached result from an externally refreshed Word TOC field",
                issue_id="TOC-SOURCE-CACHE-001",
                suggested_fix=(
                    "Открыть копию DOCX в Word, обновить поле оглавления (Ctrl+A, F9), сохранить и "
                    "повторить аудит. Номера страниц этим структурным тестом не проверяются."
                ),
            )
        )

    if not reliable_headings or not field.get("has_separator") or not cached_text.strip():
        return findings

    # Count occurrences among the styled heading register so a Word comment
    # can target a duplicate heading without guessing an anchor.  The Word
    # adapter counts all visible paragraph text, including a cached TOC, so
    # use that same document-wide order when available.
    body_paragraphs = _body_paragraphs(document_root)
    occurrence_by_text: Counter[str] = Counter()
    for heading in headings:
        occurrence_by_text[heading.text] += 1
        occurrence = occurrence_by_text[heading.text]
        document_occurrence = 0
        for paragraph_number, paragraph in enumerate(body_paragraphs, start=1):
            paragraph_text = _text_from_paragraph(paragraph)
            if not paragraph_text:
                continue
            matches = list(re.finditer(re.escape(heading.text), paragraph_text))
            if paragraph_number < heading.paragraph:
                document_occurrence += len(matches)
            elif paragraph_number == heading.paragraph:
                if matches:
                    occurrence = document_occurrence + 1
                break
        if _cached_contains(cached_text, heading.text):
            continue

        # The \o range is an explicit local selection. A heading below that
        # range is intentionally outside the generated TOC and is not an omission.
        if heading.level > included_end_level:
            continue
        if heading.level > 1:
            findings.append(
                finding(
                    f"TOC-SUBHEADING-{len(findings)+1:03d}",
                    RULE_EXACT,
                    MODULE,
                    {
                        "heading": heading.text,
                        "level": heading.level,
                        "included_toc_range": f"1-{included_end_level}",
                        "cached_result_present": True,
                    },
                    "the included styled subheading is represented consistently in the refreshed TOC cache",
                    exact_text=heading.text,
                    occurrence=occurrence,
                    severity="minor",
                    issue_class="internal_inconsistency",
                    authority_ids=[],
                    suggested_fix=(
                        "Проверить, намеренно ли подзаголовок включён диапазоном поля TOC, затем "
                        "обновить поле в Word; нормативное нарушение без локального профиля не утверждается."
                    ),
                    word_action="comment",
                )
            )
            continue

        # For a missing exact level-1 entry OOXML alone cannot distinguish a
        # complete omission (REQ-031) from altered wording (REQ-008). It does
        # prove that at least one of the two requirements is not met.
        findings.append(
            finding(
                f"TOC-MISSING-{len(findings)+1:03d}",
                RULE_COMPLETE,
                MODULE,
                {
                    "heading": heading.text,
                    "level": heading.level,
                    "cached_result_present": True,
                    "field_code": field.get("instruction", ""),
                    "interpretation": "omission_or_rewording_not_distinguishable_structurally",
                },
                (
                    "every main part is represented and its cached wording exactly matches "
                    "the styled heading; the structural audit does not choose between omission "
                    "and reformulation"
                ),
                exact_text=heading.text,
                occurrence=occurrence,
                severity="major",
                issue_class="normative_violation",
                authority_ids=[REQ_EXACT, REQ_COMPLETE],
                suggested_fix=(
                    "Сопоставить основной заголовок с записью оглавления, исправить пропуск либо "
                    "формулировку и обновить поле в Word; номер страницы вручную не исправлять."
                ),
                word_action="comment",
            )
        )

    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_docx", type=Path, help="Existing DOCX to audit.")
    parser.add_argument("--out", type=Path, help="Optional JSON findings envelope path.")
    args = parser.parse_args(argv)
    rendered = write_envelope(audit(args.input_docx), args.out)
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
