from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/dissertation-formatting-and-apparatus/scripts"
sys.path.insert(0, str(SCRIPTS))
import finalize_word_toc
SCRIPT = SCRIPTS / "audit_existing_word_toc.py"
SPEC = importlib.util.spec_from_file_location("audit_existing_word_toc", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
toc_audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = toc_audit
SPEC.loader.exec_module(toc_audit)


W = finalize_word_toc.W_NS


def _w(local: str) -> str:
    return f"{{{W}}}{local}"


def _xml(root: etree._Element) -> bytes:
    return etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)


def _paragraph(body: etree._Element, text: str, style: str | None = "Heading1") -> None:
    paragraph = etree.SubElement(body, _w("p"))
    if style is not None:
        ppr = etree.SubElement(paragraph, _w("pPr"))
        pstyle = etree.SubElement(ppr, _w("pStyle"))
        pstyle.set(_w("val"), style)
    run = etree.SubElement(paragraph, _w("r"))
    node = etree.SubElement(run, _w("t"))
    node.text = text


def _field(body: etree._Element, cached: str | None, *, levels: str = "1-1") -> None:
    paragraph = etree.SubElement(body, _w("p"))

    def run_with(child: etree._Element) -> None:
        run = etree.SubElement(paragraph, _w("r"))
        run.append(child)

    begin = etree.Element(_w("fldChar"))
    begin.set(_w("fldCharType"), "begin")
    run_with(begin)
    instruction = etree.Element(_w("instrText"))
    instruction.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    instruction.text = f'TOC \\o "{levels}" \\h \\z \\u'
    run_with(instruction)
    separate = etree.Element(_w("fldChar"))
    separate.set(_w("fldCharType"), "separate")
    run_with(separate)
    if cached is not None:
        result = etree.SubElement(paragraph, _w("r"))
        text = etree.SubElement(result, _w("t"))
        text.text = cached
    end = etree.Element(_w("fldChar"))
    end.set(_w("fldCharType"), "end")
    run_with(end)


def _write_docx(
    path: Path,
    *,
    headings: list[tuple[str, str]] | None,
    cached: str | None,
    field: bool = True,
    levels: str = "1-1",
) -> None:
    document = etree.Element(_w("document"), nsmap={"w": W})
    body = etree.SubElement(document, _w("body"))
    for text, style in headings or []:
        _paragraph(body, text, style)
    if field:
        _field(body, cached, levels=levels)
    section = etree.SubElement(body, _w("sectPr"))
    page_size = etree.SubElement(section, _w("pgSz"))
    page_size.set(_w("w"), "11906")
    page_size.set(_w("h"), "16838")

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", _xml(document))


def _normative(findings: list[dict]) -> list[dict]:
    return [item for item in findings if item["issue_class"] == "normative_violation"]


def test_clean_refreshed_field_has_no_findings(tmp_path: Path) -> None:
    source = tmp_path / "clean.docx"
    _write_docx(
        source,
        headings=[("Введение", "Heading1"), ("Глава 1", "Heading1")],
        cached="Введение\t1\nГлава 1\t2",
    )

    assert toc_audit.audit(source) == []


def test_missing_cached_heading_is_normative_and_anchorable(tmp_path: Path) -> None:
    source = tmp_path / "missing.docx"
    _write_docx(
        source,
        headings=[("Введение", "Heading1"), ("Глава 1", "Heading1")],
        cached="Введение\t1",
    )

    findings = toc_audit.audit(source)
    normative = _normative(findings)
    assert len(normative) == 1
    item = normative[0]
    assert item["authority_ids"] == [toc_audit.REQ_EXACT, toc_audit.REQ_COMPLETE]
    assert item["locator"] == {"kind": "text", "exact_text": "Глава 1", "occurrence": 1}
    assert item["word_action"] == "comment"
    assert item["issue_class"] == "normative_violation"


def test_no_field_is_only_a_non_normative_recommendation(tmp_path: Path) -> None:
    source = tmp_path / "no-field.docx"
    _write_docx(
        source,
        headings=[("Введение", "Heading1")],
        cached=None,
        field=False,
    )

    findings = toc_audit.audit(source)
    assert findings
    assert not _normative(findings)
    field_finding = next(item for item in findings if item["rule_id"] == toc_audit.RULE_FIELD)
    assert field_finding["issue_class"] == "recommendation"
    assert field_finding["authority_ids"] == []
    assert field_finding["word_action"] == "none"


def test_unique_manual_toc_title_anchors_non_normative_field_recommendation(tmp_path: Path) -> None:
    source = tmp_path / "manual-toc.docx"
    _write_docx(
        source,
        headings=[("ОГЛАВЛЕНИЕ", "Normal"), ("Введение", "Heading1")],
        cached=None,
        field=False,
    )

    findings = toc_audit.audit(source)
    item = next(finding for finding in findings if finding["rule_id"] == toc_audit.RULE_FIELD)
    assert item["issue_class"] == "recommendation"
    assert item["authority_ids"] == []
    assert item["word_action"] == "comment"
    assert item["locator"] == {"kind": "text", "exact_text": "ОГЛАВЛЕНИЕ", "occurrence": 1}


def test_no_styles_and_no_cached_result_are_not_assessed(tmp_path: Path) -> None:
    source = tmp_path / "not-assessed.docx"
    _write_docx(
        source,
        headings=[("Введение", "Normal")],
        cached=None,
    )

    findings = toc_audit.audit(source)
    assert findings
    assert not _normative(findings)
    assert any(item["rule_id"] == toc_audit.RULE_SOURCE for item in findings)
    assert all(item["word_action"] == "none" for item in findings)
    assert all(item["authority_ids"] == [] for item in findings)


def test_subheading_outside_toc_range_is_not_reported(tmp_path: Path) -> None:
    source = tmp_path / "level-1-only.docx"
    _write_docx(
        source,
        headings=[("Глава 1", "Heading1"), ("Методы", "Heading2")],
        cached="Глава 1\t1",
        levels="1-1",
    )

    assert toc_audit.audit(source) == []


def test_included_missing_subheading_is_non_normative_inconsistency(tmp_path: Path) -> None:
    source = tmp_path / "level-2-included.docx"
    _write_docx(
        source,
        headings=[("Глава 1", "Heading1"), ("Методы", "Heading2")],
        cached="Глава 1\t1",
        levels="1-2",
    )

    findings = toc_audit.audit(source)
    assert len(findings) == 1
    item = findings[0]
    assert item["issue_class"] == "internal_inconsistency"
    assert item["authority_ids"] == []
    assert item["locator"] == {"kind": "text", "exact_text": "Методы", "occurrence": 1}


def test_cli_writes_the_standard_envelope(tmp_path: Path, capsys) -> None:
    source = tmp_path / "no-field.docx"
    output = tmp_path / "findings.json"
    _write_docx(source, headings=[("Введение", "Heading1")], cached=None, field=False)

    assert toc_audit.main([str(source), "--out", str(output)]) == 0
    rendered = json.loads(capsys.readouterr().out)
    assert rendered["schema_version"] == "PSES-DISS-001/v1"
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8"))["schema_version"] == "PSES-DISS-001/v1"
