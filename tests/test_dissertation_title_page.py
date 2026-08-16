from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest
from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/dissertation-formatting-and-apparatus/scripts/apply_dissertation_title_page.py"
SPEC = importlib.util.spec_from_file_location("apply_dissertation_title_page", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
title_page = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = title_page
SPEC.loader.exec_module(title_page)


W = title_page.W_NS
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
CT = "http://schemas.openxmlformats.org/package/2006/content-types"


def _xml(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def _minimal_docx(path: Path, *, duplicate_placeholder: bool = False) -> None:
    document = etree.Element(title_page.qn("document"), nsmap={"w": W})
    body = etree.SubElement(document, title_page.qn("body"))
    paragraph = etree.SubElement(body, title_page.qn("p"))
    run = etree.SubElement(paragraph, title_page.qn("r"))
    text = etree.SubElement(run, title_page.qn("t"))
    text.text = title_page.PLACEHOLDER
    if duplicate_placeholder:
        duplicate = etree.SubElement(body, title_page.qn("p"))
        duplicate_run = etree.SubElement(duplicate, title_page.qn("r"))
        duplicate_text = etree.SubElement(duplicate_run, title_page.qn("t"))
        duplicate_text.text = title_page.PLACEHOLDER
    sect = etree.SubElement(body, title_page.qn("sectPr"))
    pg_sz = etree.SubElement(sect, title_page.qn("pgSz"))
    pg_sz.set(title_page.qn("w"), "11906")
    pg_sz.set(title_page.qn("h"), "16838")

    content_types = etree.Element(etree.QName(CT, "Types"), nsmap={"ct": CT})
    default_xml = etree.SubElement(content_types, etree.QName(CT, "Default"))
    default_xml.set("Extension", "xml")
    default_xml.set("ContentType", "application/xml")
    default_rels = etree.SubElement(content_types, etree.QName(CT, "Default"))
    default_rels.set("Extension", "rels")
    default_rels.set(
        "ContentType",
        "application/vnd.openxmlformats-package.relationships+xml",
    )
    document_override = etree.SubElement(content_types, etree.QName(CT, "Override"))
    document_override.set("PartName", "/word/document.xml")
    document_override.set(
        "ContentType",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
    )

    package_rels = etree.Element(etree.QName(PR, "Relationships"), nsmap={"pr": PR})
    package_rel = etree.SubElement(package_rels, etree.QName(PR, "Relationship"))
    package_rel.set("Id", "rId1")
    package_rel.set(
        "Type",
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
    )
    package_rel.set("Target", "word/document.xml")

    document_rels = etree.Element(etree.QName(PR, "Relationships"), nsmap={"pr": PR})
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _xml(content_types))
        archive.writestr("_rels/.rels", _xml(package_rels))
        archive.writestr("word/document.xml", _xml(document))
        archive.writestr("word/_rels/document.xml.rels", _xml(document_rels))


def _payload() -> dict[str, object]:
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
    }


def _document_text(path: Path) -> str:
    with zipfile.ZipFile(path) as archive:
        root = etree.fromstring(archive.read("word/document.xml"))
    return "".join(root.xpath(".//w:t/text()", namespaces={"w": W}))


def test_title_page_replaces_placeholder_and_preserves_source(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    output = tmp_path / "output.docx"
    _minimal_docx(source)
    before = source.read_bytes()

    report = title_page.apply_title_page(source, _payload(), output)

    assert source.read_bytes() == before
    assert output.exists()
    text = _document_text(output)
    assert title_page.PLACEHOLDER not in text
    assert "На правах рукописи" in text
    assert "Петров Пётр Петрович" in text
    assert "2.2.12" in text
    assert "Иванов Иван Иванович" in text
    assert report["status"] == "applied"
    assert "signature_line" in report["not_assessed"]
    assert report["authority_ids"] == [
        "NORM-GOST-R-7.0.11-2011-001:REQ-007",
    ]
    with zipfile.ZipFile(output) as archive:
        document = etree.fromstring(archive.read("word/document.xml"))
    assert document.xpath(".//w:tbl", namespaces={"w": W})
    assert not document.xpath(".//w:drawing | .//w:pict", namespaces={"w": W})


def test_title_page_requires_all_normative_fields_and_does_not_write_output(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    output = tmp_path / "output.docx"
    _minimal_docx(source)
    payload = _payload()
    del payload["degree"]

    with pytest.raises(title_page.TitlePageError, match="degree"):
        title_page.apply_title_page(source, payload, output)
    assert not output.exists()


def test_title_page_rejects_ambiguous_placeholder(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    output = tmp_path / "output.docx"
    _minimal_docx(source, duplicate_placeholder=True)

    with pytest.raises(title_page.TitlePageError, match="exactly one"):
        title_page.apply_title_page(source, _payload(), output)
    assert not output.exists()


def test_signature_is_written_only_when_supplied_by_local_profile(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    output = tmp_path / "output.docx"
    _minimal_docx(source)
    payload = _payload()
    payload["local_profile"] = {"signature_line": "Подпись соискателя: ____________"}

    report = title_page.apply_title_page(source, payload, output)

    assert "signature_line" in report["applied"]
    assert "signature_line" not in report["not_assessed"]
    assert "Подпись соискателя" in _document_text(output)


def test_bmstu_profile_requires_signature_and_resolves_authority(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    output = tmp_path / "output.docx"
    _minimal_docx(source)
    payload = _payload()
    payload["local_profile"] = {
        "authority_ids": ["NORM-BMSTU-DISS-REQ-001:REQ-007"]
    }

    with pytest.raises(title_page.TitlePageError, match="signature_line"):
        title_page.apply_title_page(source, payload, output)

    payload["local_profile"]["signature_line"] = "Подпись соискателя: ____________"
    report = title_page.apply_title_page(source, payload, output)
    assert report["authority_ids"] == [
        "NORM-GOST-R-7.0.11-2011-001:REQ-007",
        "NORM-BMSTU-DISS-REQ-001:REQ-007",
    ]


def test_supervisor_degree_and_title_are_required(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    output = tmp_path / "output.docx"
    _minimal_docx(source)
    payload = _payload()
    del payload["supervisor"]["title"]

    with pytest.raises(title_page.TitlePageError, match="supervisor.title"):
        title_page.apply_title_page(source, payload, output)
    assert not output.exists()


def test_cli_accepts_json_then_docx_and_emits_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    source = tmp_path / "source.docx"
    payload_path = tmp_path / "title-page.json"
    output = tmp_path / "output.docx"
    _minimal_docx(source)
    payload_path.write_text(json.dumps(_payload(), ensure_ascii=False), encoding="utf-8")

    assert title_page.main([str(payload_path), str(source), "--out", str(output)]) == 0
    rendered = json.loads(capsys.readouterr().out)
    assert rendered["status"] == "applied"
    assert rendered["output_docx"] == str(output)
