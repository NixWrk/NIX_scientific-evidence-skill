"""Contract tests for the portable final Word TOC module.

The fixtures are created in ``tmp_path`` only when pytest runs; no DOCX
fixture is checked into the repository and this module does not invoke Word.
"""

from __future__ import annotations

import hashlib
import io
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest


SCRIPT_DIR = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "dissertation-formatting-and-apparatus"
    / "scripts"
)
sys.path.insert(0, str(SCRIPT_DIR))

from finalize_word_toc import TocError, finalize_word_toc, inspect_cached_toc  # noqa: E402


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"
ET.register_namespace("w", W_NS)


def _element(tag: str, text: str | None = None, **attrs: str) -> ET.Element:
    node = ET.Element(W + tag)
    for name, value in attrs.items():
        node.set(W + name, value)
    node.text = text
    return node


def _paragraph(text: str, style: str | None = None) -> ET.Element:
    paragraph = _element("p")
    if style:
        ppr = _element("pPr")
        ppr.append(_element("pStyle", val=style))
        paragraph.append(ppr)
    run = _element("r")
    run.append(_element("t", text))
    paragraph.append(run)
    return paragraph


def _styles_xml(levels: int = 3) -> bytes:
    root = _element("styles")
    for level in range(1, levels + 1):
        style = _element("style", type="paragraph", styleId=f"Heading{level}")
        style.append(_element("name", val=f"Heading {level}"))
        ppr = _element("pPr")
        ppr.append(_element("outlineLvl", val=str(level - 1)))
        style.append(ppr)
        root.append(style)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def _docx_bytes(paragraphs: list[ET.Element], *, settings: bool = True) -> bytes:
    document = _element("document")
    body = _element("body")
    for paragraph in paragraphs:
        body.append(paragraph)
    body.append(_element("sectPr"))
    document.append(body)

    content_types = ET.Element("{http://schemas.openxmlformats.org/package/2006/content-types}Types")
    content_types.append(
        ET.Element(
            "{http://schemas.openxmlformats.org/package/2006/content-types}Override",
            {"PartName": "/word/document.xml", "ContentType": "document"},
        )
    )
    content_types.append(
        ET.Element(
            "{http://schemas.openxmlformats.org/package/2006/content-types}Override",
            {"PartName": "/word/styles.xml", "ContentType": "styles"},
        )
    )
    if settings:
        content_types.append(
            ET.Element(
                "{http://schemas.openxmlformats.org/package/2006/content-types}Override",
                {"PartName": "/word/settings.xml", "ContentType": "settings"},
            )
        )

    rels_ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    rels = ET.Element(f"{{{rels_ns}}}Relationships")
    relation = ET.Element(f"{{{rels_ns}}}Relationship")
    relation.set("Id", "rId1")
    relation.set(
        "Type",
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings",
    )
    relation.set("Target", "settings.xml")
    if settings:
        rels.append(relation)

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "word/document.xml",
            ET.tostring(document, encoding="utf-8", xml_declaration=True),
        )
        archive.writestr("word/styles.xml", _styles_xml())
        if settings:
            archive.writestr("word/settings.xml", ET.tostring(_element("settings"), encoding="utf-8", xml_declaration=True))
        archive.writestr(
            "word/_rels/document.xml.rels",
            ET.tostring(rels, encoding="utf-8", xml_declaration=True),
        )
        archive.writestr(
            "[Content_Types].xml",
            ET.tostring(content_types, encoding="utf-8", xml_declaration=True),
        )
    return output.getvalue()


def _write_fixture(path: Path, paragraphs: list[ET.Element], *, settings: bool = True) -> None:
    path.write_bytes(_docx_bytes(paragraphs, settings=settings))


def _document_root(path: Path) -> ET.Element:
    with zipfile.ZipFile(path) as archive:
        return ET.fromstring(archive.read("word/document.xml"))


def _add_cached_result(source: Path, target: Path, text: str) -> None:
    with zipfile.ZipFile(source) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(entries["word/document.xml"])
    separate = root.find(f".//{W}fldChar[@{{{W_NS}}}fldCharType='separate']")
    assert separate is not None
    parent = next(parent for parent in root.iter() if separate in list(parent))
    index = list(parent).index(separate)
    run = _element("r")
    run.append(_element("t", text))
    parent.insert(index + 1, run)
    entries["word/document.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)


def test_finalize_inserts_field_updates_settings_and_preserves_source(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    output = tmp_path / "finalized.docx"
    _write_fixture(
        source,
        [
            _paragraph("Введение", "Heading1"),
            _paragraph("Методы исследования", "Heading2"),
            _paragraph("[[TOC]]"),
        ],
    )
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()

    report = finalize_word_toc(source, output)

    assert report["status"] == "ok"
    assert report["field_inserted"] is True
    assert report["refresh_required"] is True
    assert report["pages_verified"] is False
    assert report["field_code"] == 'TOC \\o "1-2" \\h \\z \\u'
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hash

    root = _document_root(output)
    assert "[[TOC]]" not in "".join(node.text or "" for node in root.iter(f"{W}t"))
    assert [node.text for node in root.iter(f"{W}instrText")] == [report["field_code"]]
    with zipfile.ZipFile(output) as archive:
        settings = ET.fromstring(archive.read("word/settings.xml"))
    update = settings.find(f"./{W}updateFields")
    assert update is not None
    assert update.get(W + "val") == "true"


def test_preserves_namespace_prefixes_named_by_mc_ignorable(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    output = tmp_path / "finalized.docx"
    _write_fixture(
        source,
        [_paragraph("Введение", "Heading1"), _paragraph("[[TOC]]")],
    )
    with zipfile.ZipFile(source) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    document = entries["word/document.xml"].decode("utf-8")
    document = document.replace(
        "<w:document",
        '<w:document xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" '
        'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
        'mc:Ignorable="w14"',
        1,
    )
    entries["word/document.xml"] = document.encode("utf-8")
    with zipfile.ZipFile(source, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)

    finalize_word_toc(source, output)

    with zipfile.ZipFile(output) as archive:
        rewritten = archive.read("word/document.xml").decode("utf-8")
    assert 'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml"' in rewritten
    assert 'mc:Ignorable="w14"' in rewritten


def test_rejects_level_jump_and_does_not_write_output(tmp_path: Path) -> None:
    source = tmp_path / "jump.docx"
    output = tmp_path / "jump-finalized.docx"
    _write_fixture(
        source,
        [
            _paragraph("Глава 1", "Heading1"),
            _paragraph("Скачок", "Heading3"),
            _paragraph("[[TOC]]"),
        ],
    )

    with pytest.raises(TocError) as raised:
        finalize_word_toc(source, output)

    assert raised.value.code == "validation_failed"
    assert any(item["code"] == "heading_level_jump" for item in raised.value.details)
    assert not output.exists()


def test_rejects_empty_heading(tmp_path: Path) -> None:
    source = tmp_path / "empty.docx"
    output = tmp_path / "empty-finalized.docx"
    _write_fixture(
        source,
        [
            _paragraph("", "Heading1"),
            _paragraph("[[TOC]]"),
        ],
    )

    with pytest.raises(TocError) as raised:
        finalize_word_toc(source, output)

    assert raised.value.code == "validation_failed"
    assert any(item["code"] == "empty_heading" for item in raised.value.details)
    assert not output.exists()


def test_cached_result_spanning_word_paragraphs_is_detected(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    output = tmp_path / "finalized.docx"
    refreshed = tmp_path / "refreshed.docx"
    _write_fixture(
        source,
        [_paragraph("Введение", "Heading1"), _paragraph("Заключение", "Heading1"), _paragraph("[[TOC]]")],
    )
    finalize_word_toc(source, output)
    with zipfile.ZipFile(output) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    root = ET.fromstring(entries["word/document.xml"])
    body = root.find(f"./{W}body")
    assert body is not None
    field_paragraph = next(p for p in body.findall(f"./{W}p") if p.find(f".//{W}instrText") is not None)
    end_run = next(
        run
        for run in field_paragraph.findall(f"./{W}r")
        if run.find(f"./{W}fldChar[@{W}fldCharType='end']") is not None
    )
    field_paragraph.remove(end_run)
    field_paragraph.append(_paragraph("Введение	1").find(f"./{W}r"))
    second = _paragraph("Заключение	2")
    second.append(end_run)
    body.insert(list(body).index(field_paragraph) + 1, second)
    entries["word/document.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    with zipfile.ZipFile(refreshed, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)

    check = inspect_cached_toc(refreshed, expected_headings=["Введение", "Заключение"])

    assert check["status"] == "passed"
    assert check["field_count"] == 1


def test_cached_result_check_is_structural_and_does_not_verify_pages(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    output = tmp_path / "finalized.docx"
    refreshed = tmp_path / "refreshed.docx"
    _write_fixture(
        source,
        [
            _paragraph("Введение", "Heading1"),
            _paragraph("Методы исследования", "Heading2"),
            _paragraph("[[TOC]]"),
        ],
    )
    finalize_word_toc(source, output)
    _add_cached_result(output, refreshed, "Введение\t1 Методы исследования\t2")

    check = inspect_cached_toc(
        refreshed,
        expected_headings=["Введение", "Методы исследования"],
    )

    assert check["status"] == "passed"
    assert check["cached_text_present"] is True
    assert check["pages_verified"] is False
