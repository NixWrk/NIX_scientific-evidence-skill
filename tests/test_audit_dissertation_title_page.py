"""Contract tests for the deterministic title-page critic."""

from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "dissertation-formatting-and-apparatus" / "scripts"
SCRIPT = SCRIPT_DIR / "audit_dissertation_title_page.py"
sys.path.insert(0, str(SCRIPT_DIR))
SPEC = importlib.util.spec_from_file_location("audit_dissertation_title_page", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
title_page_audit = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = title_page_audit
SPEC.loader.exec_module(title_page_audit)


W_NS = title_page_audit.W_NS
PR_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"


def _w(local: str) -> str:
    return f"{{{W_NS}}}{local}"


def _xml(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _paragraph(body: etree._Element, text: str = "", *, page_break: bool = False) -> None:
    paragraph = etree.SubElement(body, _w("p"))
    parts = text.split("\n") if text else []
    for index, part in enumerate(parts):
        run = etree.SubElement(paragraph, _w("r"))
        if index:
            etree.SubElement(run, _w("br"))
        text_node = etree.SubElement(run, _w("t"))
        text_node.text = part
    if page_break:
        run = etree.SubElement(paragraph, _w("r"))
        br = etree.SubElement(run, _w("br"))
        br.set(_w("type"), "page")


def _minimal_docx(
    path: Path,
    *,
    omit: set[str] | None = None,
    page_break: bool = True,
    signature: bool = False,
    split_layout: bool = False,
) -> None:
    omitted = omit or set()
    document = etree.Element(_w("document"), nsmap={"w": W_NS})
    body = etree.SubElement(document, _w("body"))
    values = {
        "status": "На правах рукописи",
        "organization": "МГТУ им. Н. Э. Баумана",
        "author": "Петров Пётр Петрович",
        "title": "Контроль параметров медицинской системы",
        "specialty": "Шифр и наименование специальности: 2.2.12 — Приборы, системы и изделия медицинского назначения",
        "degree": "На соискание учёной степени кандидата технических наук по отрасли науки технических наук",
        "supervisor": "Иванов Иван Иванович, кандидат технических наук, доцент",
        "signature": "Подпись соискателя: ____________",
        "place_year": "Москва, 2026",
    }
    if split_layout:
        values["organization"] = "МГТУ им. Н. Э.\nБаумана"
        values["title"] = "Контроль параметров\nмедицинской системы"
        values["specialty"] = "Шифр и наименование специальности: 2.2.12 — Приборы, системы и изделия\nмедицинского назначения"
        values["supervisor"] = "кандидат технических наук,\nдоцент, Иванов Иван Иванович"
    for key in ("status", "organization", "author", "title", "specialty", "degree", "supervisor"):
        if key not in omitted:
            _paragraph(body, values[key])
    if signature and "signature" not in omitted:
        _paragraph(body, values["signature"])
    _paragraph(body, values["place_year"])
    if page_break:
        _paragraph(body, page_break=True)
        _paragraph(body, "Глава 1. Основной текст")
    sect = etree.SubElement(body, _w("sectPr"))
    pg_sz = etree.SubElement(sect, _w("pgSz"))
    pg_sz.set(_w("w"), "11906")
    pg_sz.set(_w("h"), "16838")

    content_types = etree.Element(etree.QName(CT_NS, "Types"), nsmap={"ct": CT_NS})
    default_xml = etree.SubElement(content_types, etree.QName(CT_NS, "Default"))
    default_xml.set("Extension", "xml")
    default_xml.set("ContentType", "application/xml")
    default_rels = etree.SubElement(content_types, etree.QName(CT_NS, "Default"))
    default_rels.set("Extension", "rels")
    default_rels.set(
        "ContentType",
        "application/vnd.openxmlformats-package.relationships+xml",
    )
    document_override = etree.SubElement(content_types, etree.QName(CT_NS, "Override"))
    document_override.set("PartName", "/word/document.xml")
    document_override.set(
        "ContentType",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
    )

    package_rels = etree.Element(etree.QName(PR_NS, "Relationships"), nsmap={"pr": PR_NS})
    package_rel = etree.SubElement(package_rels, etree.QName(PR_NS, "Relationship"))
    package_rel.set("Id", "rId1")
    package_rel.set(
        "Type",
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
    )
    package_rel.set("Target", "word/document.xml")
    document_rels = etree.Element(etree.QName(PR_NS, "Relationships"), nsmap={"pr": PR_NS})

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _xml(content_types))
        archive.writestr("_rels/.rels", _xml(package_rels))
        archive.writestr("word/document.xml", _xml(document))
        archive.writestr("word/_rels/document.xml.rels", _xml(document_rels))


def _payload(*, bmstu: bool = False) -> dict[str, object]:
    profile: dict[str, object] = {}
    if bmstu:
        profile = {
            "authority_ids": ["NORM-BMSTU-DISS-REQ-001:REQ-007"],
            "signature_line": "Подпись соискателя: ____________",
        }
    return {
        "organization": "МГТУ им. Н. Э. Баумана",
        "author": "Петров Пётр Петрович",
        "title": "Контроль параметров медицинской системы",
        "specialty": {
            "code": "2.2.12",
            "name": "Приборы, системы и изделия медицинского назначения",
        },
        "degree": {
            "name": "кандидата технических наук",
            "field": "технических наук",
        },
        "supervisor": {
            "full_name": "Иванов Иван Иванович",
            "degree": "кандидат технических наук",
            "title": "доцент",
        },
        "city": "Москва",
        "year": 2026,
        "local_profile": profile,
    }


def test_clean_title_page_has_no_findings_and_source_is_unchanged(tmp_path: Path) -> None:
    source = tmp_path / "clean.docx"
    _minimal_docx(source)
    before = source.read_bytes()

    findings = title_page_audit.audit_title_page(source, _payload())

    assert findings == []
    assert source.read_bytes() == before


def test_line_breaks_and_supervisor_component_order_do_not_create_false_violations(tmp_path: Path) -> None:
    source = tmp_path / "split-layout.docx"
    _minimal_docx(source, split_layout=True)

    assert title_page_audit.audit_title_page(source, _payload()) == []


def test_missing_required_field_is_normative_comment_with_unique_anchor(tmp_path: Path) -> None:
    source = tmp_path / "missing-organization.docx"
    _minimal_docx(source, omit={"organization"})

    findings = title_page_audit.audit_title_page(source, _payload())

    assert len(findings) == 1
    finding = findings[0]
    assert finding["issue_class"] == "normative_violation"
    assert finding["rule_id"] == "NORM-GOST-R-7.0.11-2011-001:REQ-007"
    assert finding["word_action"] == "comment"
    assert finding["locator"] == {
        "kind": "text",
        "exact_text": "На правах рукописи",
        "occurrence": 1,
    }
    assert finding["authority_ids"] == ["NORM-GOST-R-7.0.11-2011-001:REQ-007"]


def test_bmstu_signature_is_checked_only_when_selected(tmp_path: Path) -> None:
    source = tmp_path / "missing-signature.docx"
    _minimal_docx(source, signature=False)

    findings = title_page_audit.audit_title_page(source, _payload(bmstu=True))

    assert len(findings) == 1
    finding = findings[0]
    assert finding["issue_class"] == "normative_violation"
    assert finding["rule_id"] == "NORM-BMSTU-DISS-REQ-001:REQ-007"
    assert finding["authority_ids"] == ["NORM-BMSTU-DISS-REQ-001:REQ-007"]
    assert finding["word_action"] == "comment"
    assert finding["locator"]["exact_text"] == "На правах рукописи"


def test_unprovable_page_boundary_returns_source_quality_recommendation(tmp_path: Path) -> None:
    source = tmp_path / "no-boundary.docx"
    _minimal_docx(source, page_break=False)

    findings = title_page_audit.audit_title_page(source, _payload())

    assert len(findings) == 1
    finding = findings[0]
    assert finding["issue_class"] == "recommendation"
    assert finding["rule_id"] == "TITLE-SOURCE-001"
    assert finding["word_action"] == "none"
    assert finding["locator"] is None
    assert finding["authority_ids"] == []


def test_cli_prints_and_writes_pses_envelope(tmp_path: Path, capsys) -> None:
    source = tmp_path / "clean.docx"
    expected = tmp_path / "expected.json"
    output = tmp_path / "findings.json"
    _minimal_docx(source)
    expected.write_text(json.dumps(_payload(), ensure_ascii=False), encoding="utf-8")

    assert title_page_audit.main([str(expected), str(source), "--out", str(output)]) == 0
    printed = json.loads(capsys.readouterr().out)
    persisted = json.loads(output.read_text(encoding="utf-8"))
    assert printed == persisted
    assert printed["schema_version"] == "PSES-DISS-001/v1"
    assert printed["findings"] == []
