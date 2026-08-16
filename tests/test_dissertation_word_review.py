from __future__ import annotations

import importlib.util
import sys
import zipfile
from pathlib import Path

import pytest
from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/dissertation-formatting-and-apparatus/scripts/apply_word_review.py"
SPEC = importlib.util.spec_from_file_location("apply_word_review", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
review = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = review
SPEC.loader.exec_module(review)

W = review.W_NS
PR = review.PKG_REL_NS
CT = review.CT_NS
NS = {"w": W, "pr": PR, "ct": CT, "review": review.REVIEW_NS}


def _xml(root: etree._Element) -> bytes:
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)


def make_fixture(path: Path) -> None:
    document = etree.Element(review.w("document"), nsmap={"w": W})
    body = etree.SubElement(document, review.w("body"))
    paragraph = etree.SubElement(body, review.w("p"))
    for text in ("First sentence. ", "Second sentence."):
        run = etree.SubElement(paragraph, review.w("r"))
        node = etree.SubElement(run, review.w("t"))
        node.text = text
    section = etree.SubElement(body, review.w("sectPr"))
    page_size = etree.SubElement(section, review.w("pgSz"))
    page_size.set(review.qn(W, "w"), "12240")
    page_size.set(review.qn(W, "h"), "15840")

    settings = etree.Element(review.w("settings"), nsmap={"w": W})
    rels = etree.Element(review.qn(PR, "Relationships"), nsmap={"pr": PR})
    rel = etree.SubElement(rels, review.qn(PR, "Relationship"))
    rel.set("Id", "rId1")
    rel.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument")
    rel.set("Target", "document.xml")
    content_types = etree.Element(review.qn(CT, "Types"), nsmap={"ct": CT})
    default_xml = etree.SubElement(content_types, review.qn(CT, "Default"))
    default_xml.set("Extension", "xml")
    default_xml.set("ContentType", "application/xml")
    default_rels = etree.SubElement(content_types, review.qn(CT, "Default"))
    default_rels.set("Extension", "rels")
    default_rels.set("ContentType", "application/vnd.openxmlformats-package.relationships+xml")
    main_override = etree.SubElement(content_types, review.qn(CT, "Override"))
    main_override.set("PartName", "/word/document.xml")
    main_override.set(
        "ContentType",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml",
    )
    settings_override = etree.SubElement(content_types, review.qn(CT, "Override"))
    settings_override.set("PartName", "/word/settings.xml")
    settings_override.set(
        "ContentType",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml",
    )
    package_rels = etree.Element(review.qn(PR, "Relationships"), nsmap={"pr": PR})
    package_rel = etree.SubElement(package_rels, review.qn(PR, "Relationship"))
    package_rel.set("Id", "rId1")
    package_rel.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument")
    package_rel.set("Target", "word/document.xml")

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _xml(content_types))
        archive.writestr("_rels/.rels", _xml(package_rels))
        archive.writestr("word/document.xml", _xml(document))
        archive.writestr("word/_rels/document.xml.rels", _xml(rels))
        archive.writestr("word/settings.xml", _xml(settings))


def read_part(path: Path, name: str) -> etree._Element:
    with zipfile.ZipFile(path) as archive:
        return etree.fromstring(archive.read(name))


def test_comments_preserve_source_and_wire_true_comments(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    output = tmp_path / "comments.docx"
    make_fixture(source)
    before = source.read_bytes()
    journal = [
        {
            "issue_id": "ISSUE-0001",
            "word_action": "comment",
            "locator": {"exact_text": "Second sentence."},
            "observed": "A sentence requiring evidence.",
        }
    ]

    result = review.apply_review(source, journal, output, profile="comments", author="Tester")

    assert result["comments_added"] == 1
    assert source.read_bytes() == before
    document = read_part(output, "word/document.xml")
    comments = read_part(output, "word/comments.xml")
    assert document.xpath(".//w:commentRangeStart", namespaces=NS)
    assert document.xpath(".//w:commentRangeEnd", namespaces=NS)
    assert document.xpath(".//w:commentReference", namespaces=NS)
    assert "ISSUE-0001" in "".join(comments.xpath(".//w:t/text()", namespaces=NS))
    assert not document.xpath(".//w:ins | .//w:del", namespaces=NS)
    rels = read_part(output, "word/_rels/document.xml.rels")
    assert rels.xpath(".//pr:Relationship[@Type=$kind]", namespaces=NS, kind=review.COMMENTS_REL_TYPE)
    content_types = read_part(output, "[Content_Types].xml")
    assert content_types.xpath(".//ct:Override[@PartName='/word/comments.xml']", namespaces=NS)
    assert review.audit_document(output, journal, source_docx=source)["valid"] is True


def test_track_changes_adds_real_redline_and_enables_tracking(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    output = tmp_path / "redline.docx"
    make_fixture(source)
    journal = [
        {
            "issue_id": "ISSUE-0002",
            "word_action": "tracked_change",
            "locator": {"exact_text": "Second sentence.", "occurrence": 1},
            "suggested_fix": {"old": "Second sentence.", "new": "Second supported sentence."},
        }
    ]

    result = review.apply_review(source, journal, output, profile="track-changes")

    assert result["tracked_changes_added"] == 1
    document = read_part(output, "word/document.xml")
    deleted = document.xpath(".//w:del", namespaces=NS)
    inserted = document.xpath(".//w:ins", namespaces=NS)
    assert len(deleted) == len(inserted) == 1
    assert deleted[0].xpath("string(.//w:delText)", namespaces=NS) == "Second sentence."
    assert inserted[0].xpath("string(.//w:t)", namespaces=NS) == "Second supported sentence."
    assert inserted[0].get(review.qn(review.REVIEW_NS, "issue_id")) == "ISSUE-0002"
    settings = read_part(output, "word/settings.xml")
    assert settings.xpath(".//w:trackRevisions", namespaces=NS)
    assert review.audit_document(output, journal)["valid"] is True


def test_hybrid_keeps_comment_and_redline_for_same_journal(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    output = tmp_path / "hybrid.docx"
    make_fixture(source)
    journal = [
        {
            "issue_id": "ISSUE-0003",
            "word_action": "comment",
            "locator": {"exact_text": "First sentence.", "occurrence": 1},
            "expected": "Provide an authority.",
        },
        {
            "issue_id": "ISSUE-0004",
            "word_action": "tracked_change_with_comment",
            "locator": {"exact_text": "Second sentence.", "occurrence": 1},
            "suggested_fix": {"old": "Second sentence.", "new": "Second supported sentence."},
            "observed": "Unsupported wording.",
        },
    ]

    result = review.apply_review(source, journal, output, profile="hybrid")

    assert result["comments_added"] == 2
    assert result["tracked_changes_added"] == 1
    document = read_part(output, "word/document.xml")
    comments = read_part(output, "word/comments.xml")
    text = "".join(comments.xpath(".//w:t/text()", namespaces=NS))
    assert "ISSUE-0003" in text and "ISSUE-0004" in text
    assert len(document.xpath(".//w:ins", namespaces=NS)) == 1
    assert len(document.xpath(".//w:del", namespaces=NS)) == 1
    assert review.audit_document(output, journal)["valid"] is True


def test_locator_missing_or_ambiguous_fails_without_output(tmp_path: Path) -> None:
    source = tmp_path / "source.docx"
    make_fixture(source)
    missing_output = tmp_path / "missing.docx"
    with pytest.raises(review.ReviewError, match="not found"):
        review.apply_review(
            source,
            [
                {
                    "issue_id": "ISSUE-MISSING",
                    "word_action": "comment",
                    "locator": {"exact_text": "No such text"},
                }
            ],
            missing_output,
            profile="comments",
        )
    assert not missing_output.exists()

    ambiguous_source = tmp_path / "ambiguous.docx"
    make_fixture(ambiguous_source)
    # Replace the fixture text with two identical phrases, preserving the
    # minimal package plumbing.
    with zipfile.ZipFile(ambiguous_source) as archive:
        entries = {name: archive.read(name) for name in archive.namelist()}
    document = etree.fromstring(entries["word/document.xml"])
    text_nodes = document.xpath(".//w:t", namespaces=NS)
    text_nodes[0].text = "Same phrase."
    text_nodes[1].text = "Same phrase."
    with zipfile.ZipFile(ambiguous_source, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, content in entries.items():
            archive.writestr(name, _xml(document) if name == "word/document.xml" else content)

    with pytest.raises(review.ReviewError, match="ambiguous"):
        review.apply_review(
            ambiguous_source,
            [
                {
                    "issue_id": "ISSUE-AMBIGUOUS",
                    "word_action": "comment",
                    "locator": {"exact_text": "Same phrase."},
                }
            ],
            tmp_path / "ambiguous-output.docx",
            profile="comments",
        )
