#!/usr/bin/env python3
"""Replace a ``[[TOC]]`` placeholder with a real Word TOC field.

The module deliberately does not calculate a table of contents.  It validates
the heading hierarchy from paragraph styles in ``word/document.xml``, inserts
the OOXML field, and asks Word (or another compatible editor) to refresh it.
Consequently, a successful run is not a claim that page numbers are current.

The public helpers are intentionally dependency-free so the script can be
used from a checked-out skill directory::

    report = finalize_word_toc(input_docx, output_docx)
    cached = inspect_cached_toc(output_docx)

The CLI prints the same report as JSON.  ``--report`` writes a sidecar JSON
file as well.  ``--check-cached`` is an optional structural check for a copy
that has already been refreshed by Word; it checks field/result structure and
heading text, not page-number correctness.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
XML_NS = "http://www.w3.org/XML/1998/namespace"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
MC_NS = "http://schemas.openxmlformats.org/markup-compatibility/2006"

W = f"{{{W_NS}}}"
R = f"{{{R_NS}}}"
CT = f"{{{CT_NS}}}"
PKG_REL = f"{{{PKG_REL_NS}}}"

W_DOCUMENT = W + "document"
W_BODY = W + "body"
W_P = W + "p"
W_PPR = W + "pPr"
W_PSTYLE = W + "pStyle"
W_R = W + "r"
W_T = W + "t"
W_DELTEXT = W + "delText"
W_TAB = W + "tab"
W_BR = W + "br"
W_STYLE = W + "style"
W_NAME = W + "name"
W_BASED_ON = W + "basedOn"
W_OUTLINE_LVL = W + "outlineLvl"
W_FLD_CHAR = W + "fldChar"
W_INSTR_TEXT = W + "instrText"
W_UPDATE_FIELDS = W + "updateFields"
W_SETTINGS = W + "settings"
W_VAL = W + "val"
W_TYPE = W + "type"
W_STYLE_ID = W + "styleId"
W_FLD_CHAR_TYPE = W + "fldCharType"
W_DIRTY = W + "dirty"
W_ID = "Id"
W_TARGET = "Target"
W_REL_TYPE = "Type"
W_PART_NAME = "PartName"
W_CONTENT_TYPE = "ContentType"

DOCUMENT_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
    "settings"
)
SETTINGS_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"
)

TOC_FIELD_RE = re.compile(
    r'^TOC\s+\\o\s+"(?P<start>\d+)-(?P<end>\d+)"\s+\\h\s+\\z\s+\\u$',
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^(?:heading|заголовок)\s*[-_]?\s*(\d+)$", re.IGNORECASE)

ET.register_namespace("w", W_NS)
ET.register_namespace("r", R_NS)
ET.register_namespace("mc", "http://schemas.openxmlformats.org/markup-compatibility/2006")


class TocError(Exception):
    """An input or validation error that prevents creating an output DOCX."""

    def __init__(self, message: str, *, code: str = "error", details: list[dict] | None = None):
        super().__init__(message)
        self.code = code
        self.details = details or []


@dataclass(frozen=True)
class StyleInfo:
    style_id: str
    name: str
    outline_level: int | None
    based_on: str | None


@dataclass(frozen=True)
class Heading:
    paragraph: int
    level: int
    style_id: str
    style_name: str
    text: str

    def as_dict(self) -> dict:
        return {
            "paragraph": self.paragraph,
            "level": self.level,
            "style_id": self.style_id,
            "style_name": self.style_name,
            "text": self.text,
        }


def _namespace_map(data: bytes) -> dict[str, str]:
    result: dict[str, str] = {}
    for _event, namespace in ET.iterparse(io.BytesIO(data), events=("start-ns",)):
        prefix, uri = namespace
        result[prefix or ""] = uri
    return result


def _xml_bytes(root: ET.Element, source_data: bytes | None = None) -> bytes:
    """Serialize OOXML and retain prefixes named by ``mc:Ignorable``."""

    rendered = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    if source_data is None:
        return rendered
    prefixes = (root.get(f"{{{MC_NS}}}Ignorable") or "").split()
    if not prefixes:
        return rendered
    source_namespaces = _namespace_map(source_data)
    declarations: list[bytes] = []
    for prefix in prefixes:
        uri = source_namespaces.get(prefix)
        declaration = f'xmlns:{prefix}="'.encode("ascii")
        if uri and declaration not in rendered:
            declarations.append(f' xmlns:{prefix}="{uri}"'.encode("utf-8"))
    if not declarations:
        return rendered
    root_start = __import__("re").search(rb"<[^!?][^>]*", rendered)
    if root_start is None:
        return rendered
    offset = root_start.end()
    return rendered[:offset] + b"".join(declarations) + rendered[offset:]


def _parse_xml(data: bytes, part_name: str) -> ET.Element:
    # Preserve the source prefix map.  Word stores prefix names (not namespace
    # URIs) in values such as mc:Ignorable="w14 w15".  If ElementTree assigns
    # synthetic ns1/ns2 prefixes while serializing, those values point to
    # undeclared names and Word reports the package as damaged.
    try:
        for _event, namespace in ET.iterparse(io.BytesIO(data), events=("start-ns",)):
            prefix, uri = namespace
            if prefix and not re.fullmatch(r"ns\d+", prefix):
                ET.register_namespace(prefix, uri)
            elif not prefix:
                ET.register_namespace("", uri)
        return ET.fromstring(data)
    except (ET.ParseError, ValueError) as exc:
        raise TocError(
            f"Invalid XML in {part_name}: {exc}",
            code="invalid_xml",
        ) from exc


def _attr(element: ET.Element, local_name: str, namespace: str = W_NS) -> str | None:
    return element.get(f"{{{namespace}}}{local_name}")


def _text_from_paragraph(paragraph: ET.Element) -> str:
    """Return visible paragraph text, including text nested in hyperlinks."""

    chunks: list[str] = []
    for node in paragraph.iter():
        if node.tag in {W_T, W_DELTEXT}:
            chunks.append(node.text or "")
        elif node.tag == W_TAB:
            chunks.append("\t")
        elif node.tag == W_BR:
            chunks.append("\n")
    return "".join(chunks)


def _body_paragraphs(document_root: ET.Element) -> list[ET.Element]:
    body = document_root.find(f"./{W_BODY}")
    if body is None:
        raise TocError("word/document.xml has no w:body element", code="missing_body")
    return list(body.iter(W_P))


def _parse_style_index(styles_data: bytes | None) -> dict[str, StyleInfo]:
    if not styles_data:
        return {}
    root = _parse_xml(styles_data, "word/styles.xml")
    result: dict[str, StyleInfo] = {}
    for style in root.findall(f"./{W_STYLE}"):
        style_id = _attr(style, "styleId") or ""
        if not style_id:
            continue
        name_el = style.find(f"./{W_NAME}")
        name = _attr(name_el, "val") if name_el is not None else None
        outline_el = style.find(f"./{W_PPR}/{W_OUTLINE_LVL}")
        outline_level: int | None = None
        if outline_el is not None:
            raw = _attr(outline_el, "val")
            try:
                if raw is not None:
                    outline_level = int(raw) + 1
            except ValueError:
                outline_level = None
        based_on_el = style.find(f"./{W_BASED_ON}")
        result[style_id] = StyleInfo(
            style_id=style_id,
            name=name or style_id,
            outline_level=outline_level,
            based_on=_attr(based_on_el, "val") if based_on_el is not None else None,
        )
    return result


def _level_from_label(value: str | None) -> int | None:
    if not value:
        return None
    candidate = value.strip()
    match = HEADING_RE.match(candidate)
    if match:
        return int(match.group(1))
    # Built-in style IDs conventionally omit the space (Heading1).  Accept
    # this form, but do not treat arbitrary direct formatting as a heading.
    compact = re.sub(r"[\s_-]+", "", candidate).casefold()
    for prefix in ("heading", "заголовок"):
        if compact.startswith(prefix):
            suffix = compact[len(prefix) :]
            if suffix.isdigit():
                return int(suffix)
    return None


def _style_level(style_id: str, styles: Mapping[str, StyleInfo]) -> tuple[int | None, str]:
    """Resolve a paragraph style to a TOC level.

    Built-in Heading styles are recognized even when the optional styles part
    omits their definitions.  Custom paragraph styles can participate only if
    their Word style explicitly carries an outline level (or inherits one from
    another Word style); no run formatting or manually typed numbering is used.
    """

    visiting: set[str] = set()

    def resolve(current_id: str) -> tuple[int | None, str]:
        if current_id in visiting:
            return None, current_id
        visiting.add(current_id)
        info = styles.get(current_id)
        if info is None:
            return _level_from_label(current_id), current_id
        direct = _level_from_label(info.name) or _level_from_label(info.style_id)
        if direct is not None:
            return direct, info.name
        if info.outline_level is not None:
            return info.outline_level, info.name
        if info.based_on:
            inherited, inherited_name = resolve(info.based_on)
            if inherited is not None:
                return inherited, info.name
            return None, inherited_name
        return None, info.name

    return resolve(style_id)


def extract_headings(document_root: ET.Element, styles: Mapping[str, StyleInfo]) -> list[Heading]:
    """Extract non-empty headings using only paragraph Word styles."""

    headings: list[Heading] = []
    for paragraph_number, paragraph in enumerate(_body_paragraphs(document_root), start=1):
        p_style = paragraph.find(f"./{W_PPR}/{W_PSTYLE}")
        if p_style is None:
            continue
        style_id = _attr(p_style, "val") or ""
        if not style_id:
            continue
        level, style_name = _style_level(style_id, styles)
        if level is None:
            continue
        text = _text_from_paragraph(paragraph).strip()
        headings.append(
            Heading(
                paragraph=paragraph_number,
                level=level,
                style_id=style_id,
                style_name=style_name,
                text=text,
            )
        )
    return headings


def validate_headings(headings: Iterable[Heading]) -> list[dict]:
    """Return deterministic validation findings for the heading hierarchy."""

    items = list(headings)
    findings: list[dict] = []
    if not items:
        findings.append(
            {
                "code": "no_headings",
                "message": "No Heading 1..N paragraphs were found in Word styles.",
            }
        )
        return findings

    previous_level = 0
    for heading in items:
        if not heading.text:
            findings.append(
                {
                    "code": "empty_heading",
                    "paragraph": heading.paragraph,
                    "level": heading.level,
                    "style_id": heading.style_id,
                    "message": "A heading paragraph has no visible text.",
                }
            )
        if heading.level < 1:
            findings.append(
                {
                    "code": "invalid_heading_level",
                    "paragraph": heading.paragraph,
                    "level": heading.level,
                    "message": "Heading levels must be positive integers.",
                }
            )
        elif heading.level > previous_level + 1:
            findings.append(
                {
                    "code": "heading_level_jump",
                    "paragraph": heading.paragraph,
                    "from_level": previous_level,
                    "to_level": heading.level,
                    "message": (
                        f"Heading level jumps from {previous_level} to {heading.level}; "
                        "an intermediate Word heading style is missing."
                    ),
                }
            )
        previous_level = heading.level
    return findings


def _placeholder_paragraphs(
    document_root: ET.Element, placeholder: str
) -> tuple[list[ET.Element], int]:
    matches: list[ET.Element] = []
    occurrences = 0
    for paragraph in _body_paragraphs(document_root):
        text = _text_from_paragraph(paragraph)
        count = text.count(placeholder)
        if count:
            occurrences += count
            if text.strip() == placeholder:
                matches.append(paragraph)
    return matches, occurrences


def _clear_paragraph_content(paragraph: ET.Element) -> None:
    for child in list(paragraph):
        if child.tag != W_PPR:
            paragraph.remove(child)


def _new_run_with(child: ET.Element) -> ET.Element:
    run = ET.Element(W_R)
    run.append(child)
    return run


def _insert_toc_field(paragraph: ET.Element, levels: str) -> str:
    """Replace paragraph content with a complex TOC field and return its code."""

    _clear_paragraph_content(paragraph)
    field_code = f'TOC \\o "{levels}" \\h \\z \\u'

    begin = ET.Element(W_FLD_CHAR)
    begin.set(W_FLD_CHAR_TYPE, "begin")
    begin.set(W_DIRTY, "true")
    paragraph.append(_new_run_with(begin))

    instruction = ET.Element(W_INSTR_TEXT)
    instruction.set(f"{{{XML_NS}}}space", "preserve")
    instruction.text = field_code
    paragraph.append(_new_run_with(instruction))

    separate = ET.Element(W_FLD_CHAR)
    separate.set(W_FLD_CHAR_TYPE, "separate")
    paragraph.append(_new_run_with(separate))

    # Leave the cached result empty.  Any visible result must come from Word
    # (or another compatible editor) refreshing this field, never from a
    # manually generated TOC copy.
    end = ET.Element(W_FLD_CHAR)
    end.set(W_FLD_CHAR_TYPE, "end")
    paragraph.append(_new_run_with(end))
    return field_code


def _ensure_update_fields(settings_root: ET.Element) -> None:
    update = settings_root.find(f"./{W_UPDATE_FIELDS}")
    if update is None:
        update = ET.Element(W_UPDATE_FIELDS)
        settings_root.insert(0, update)
    update.set(W_VAL, "true")


def _new_settings_part() -> bytes:
    root = ET.Element(W_SETTINGS)
    _ensure_update_fields(root)
    return _xml_bytes(root)


def _next_relationship_id(root: ET.Element) -> str:
    used: set[str] = set()
    for relation in root.findall(f"./{PKG_REL}Relationship"):
        value = relation.get(W_ID)
        if value:
            used.add(value)
    number = 1
    while f"rId{number}" in used:
        number += 1
    return f"rId{number}"


def _ensure_settings_relationship(entries: dict[str, bytes]) -> None:
    """Add settings relationship/content type only for malformed minimal DOCX inputs."""

    rels_name = "word/_rels/document.xml.rels"
    if rels_name in entries:
        rels_root = _parse_xml(entries[rels_name], rels_name)
    else:
        rels_root = ET.Element(f"{{{PKG_REL_NS}}}Relationships")
    has_settings = any(
        relation.get(W_REL_TYPE) == DOCUMENT_REL_TYPE
        for relation in rels_root.findall(f"./{PKG_REL}Relationship")
    )
    if not has_settings:
        relation = ET.Element(f"{{{PKG_REL_NS}}}Relationship")
        relation.set(W_ID, _next_relationship_id(rels_root))
        relation.set(W_REL_TYPE, DOCUMENT_REL_TYPE)
        relation.set(W_TARGET, "settings.xml")
        rels_root.append(relation)
        entries[rels_name] = _xml_bytes(rels_root)

    content_types_name = "[Content_Types].xml"
    if content_types_name not in entries:
        return
    content_root = _parse_xml(entries[content_types_name], content_types_name)
    has_override = any(
        override.get(W_PART_NAME) == "/word/settings.xml"
        for override in content_root.findall(f"./{CT}Override")
    )
    if not has_override:
        override = ET.Element(f"{{{CT_NS}}}Override")
        override.set(W_PART_NAME, "/word/settings.xml")
        override.set(W_CONTENT_TYPE, SETTINGS_CONTENT_TYPE)
        content_root.append(override)
        entries[content_types_name] = _xml_bytes(content_root)


def _field_code_text(parts: Iterable[str]) -> str:
    return re.sub(r"\s+", " ", "".join(parts)).strip()


def _iter_field_infos(document_root: ET.Element) -> Iterable[dict]:
    """Yield complex fields, including Word-refreshed multi-paragraph TOCs."""

    body = document_root.find(f"./{W_BODY}")
    if body is None:
        return
    stack: list[dict] = []
    for node in body.iter():
        if node.tag == W_P:
            for item in stack:
                if item["phase"] == "cached" and item["cached"]:
                    item["cached"].append("\n")
        elif node.tag == W_FLD_CHAR:
            field_type = _attr(node, "fldCharType")
            if field_type == "begin":
                stack.append({"instruction": [], "cached": [], "phase": "instruction"})
            elif field_type == "separate" and stack:
                stack[-1]["phase"] = "cached"
            elif field_type == "end" and stack:
                item = stack.pop()
                yield {
                    "instruction": _field_code_text(item["instruction"]),
                    "cached_text": "".join(item["cached"]).strip(),
                    "has_separator": item["phase"] == "cached",
                }
        elif node.tag == W_INSTR_TEXT and stack:
            stack[-1]["instruction"].append(node.text or "")
        elif node.tag in {W_T, W_DELTEXT} and stack:
            for item in stack:
                if item["phase"] == "cached":
                    item["cached"].append(node.text or "")
        elif node.tag == W_TAB and stack:
            for item in stack:
                if item["phase"] == "cached":
                    item["cached"].append("\t")


def _read_docx_parts(path: Path) -> dict[str, bytes]:
    if not path.exists():
        raise TocError(f"Input DOCX does not exist: {path}", code="missing_input")
    if not path.is_file():
        raise TocError(f"Input path is not a file: {path}", code="invalid_input")
    try:
        with zipfile.ZipFile(path, "r") as archive:
            if "word/document.xml" not in archive.namelist():
                raise TocError("DOCX has no word/document.xml part", code="missing_document")
            return {name: archive.read(name) for name in archive.namelist()}
    except zipfile.BadZipFile as exc:
        raise TocError(f"Input is not a valid DOCX/ZIP: {path}", code="invalid_docx") from exc


def _same_path(first: Path, second: Path) -> bool:
    try:
        return first.resolve() == second.resolve()
    except OSError:
        return str(first.absolute()).casefold() == str(second.absolute()).casefold()


def _write_docx_parts(entries: Mapping[str, bytes], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            archive.writestr(name, data)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _base_report(input_path: Path, output_path: Path | None, placeholder: str) -> dict:
    return {
        "status": "error",
        "input": str(input_path),
        "output": str(output_path) if output_path is not None else None,
        "placeholder": placeholder,
        "field_inserted": False,
        "refresh_required": False,
        "pages_verified": False,
        "cached_result": {"status": "not_checked"},
    }


def inspect_cached_toc(
    docx_path: str | Path,
    *,
    expected_headings: Iterable[str] | None = None,
) -> dict:
    """Structurally inspect a cached TOC result after an external refresh.

    This function intentionally reports ``pages_verified=False``.  It cannot
    prove that cached page numbers are correct without a layout engine and it
    never treats a non-empty result as such proof.
    """

    path = Path(docx_path)
    try:
        entries = _read_docx_parts(path)
        document_root = _parse_xml(entries["word/document.xml"], "word/document.xml")
    except TocError as exc:
        return {
            "status": "error",
            "path": str(path),
            "pages_verified": False,
            "message": str(exc),
            "code": exc.code,
        }
    fields = [field for field in _iter_field_infos(document_root) if TOC_FIELD_RE.match(field["instruction"])]
    expected = [text.strip() for text in (expected_headings or []) if text.strip()]
    if not fields:
        return {
            "status": "failed",
            "path": str(path),
            "pages_verified": False,
            "message": "No TOC field with the required switches was found.",
            "field_count": 0,
        }

    field = fields[0]
    cached = field["cached_text"]
    missing = [heading for heading in expected if heading not in cached]
    if not field["has_separator"] or not cached:
        status = "failed"
        message = "TOC field has no non-empty cached result; refresh it in Word first."
    elif missing:
        status = "failed"
        message = "Cached TOC result is missing one or more styled headings."
    else:
        status = "passed"
        message = "Cached TOC result contains the expected styled heading text."
    return {
        "status": status,
        "path": str(path),
        "field_count": len(fields),
        "field_code": field["instruction"],
        "cached_text_present": bool(cached),
        "cached_text_length": len(cached),
        "expected_heading_count": len(expected),
        "missing_headings": missing,
        "message": message,
        "pages_verified": False,
    }


def finalize_word_toc(
    input_path: str | Path,
    output_path: str | Path | None = None,
    *,
    placeholder: str = "[[TOC]]",
    report_path: str | Path | None = None,
    check_cached: bool = False,
    cached_docx: str | Path | None = None,
) -> dict:
    """Validate and finalize a DOCX TOC placeholder.

    ``TocError`` is raised for invalid input or validation failures and no
    output DOCX is written.  On success the returned JSON-compatible mapping
    records ``field_inserted=True`` and ``refresh_required=True``.  Callers
    should treat the latter as a hard hand-off to Word/another compatible
    editor; the function does not manufacture page numbers.
    """

    input_file = Path(input_path)
    output_file = (
        Path(output_path)
        if output_path is not None
        else input_file.with_name(f"{input_file.stem}_finalized.docx")
    )
    if _same_path(input_file, output_file):
        raise TocError(
            "Output DOCX must be a new path; the input source is never modified.",
            code="in_place_output",
        )
    if not placeholder:
        raise TocError("Placeholder must not be empty.", code="invalid_placeholder")

    source_hash = _sha256(input_file) if input_file.exists() else None
    entries = _read_docx_parts(input_file)
    document_root = _parse_xml(entries["word/document.xml"], "word/document.xml")
    styles = _parse_style_index(entries.get("word/styles.xml"))
    headings = extract_headings(document_root, styles)
    heading_findings = validate_headings(headings)
    matches, placeholder_occurrences = _placeholder_paragraphs(document_root, placeholder)
    validation_findings = list(heading_findings)
    if placeholder_occurrences != 1 or len(matches) != 1:
        validation_findings.append(
            {
                "code": "placeholder_not_unique",
                "occurrences": placeholder_occurrences,
                "standalone_paragraphs": len(matches),
                "message": (
                    f"Expected exactly one standalone {placeholder!r} paragraph; "
                    f"found {placeholder_occurrences} token occurrence(s)."
                ),
            }
        )
    if validation_findings:
        raise TocError(
            "DOCX failed TOC validation.",
            code="validation_failed",
            details=validation_findings,
        )

    max_level = max(heading.level for heading in headings)
    levels = f"1-{max_level}"
    field_code = _insert_toc_field(matches[0], levels)
    original_document_data = entries["word/document.xml"]
    entries["word/document.xml"] = _xml_bytes(document_root, original_document_data)

    settings_name = "word/settings.xml"
    if settings_name in entries:
        original_settings_data = entries[settings_name]
        settings_root = _parse_xml(original_settings_data, settings_name)
        _ensure_update_fields(settings_root)
        entries[settings_name] = _xml_bytes(settings_root, original_settings_data)
    else:
        entries[settings_name] = _new_settings_part()
        _ensure_settings_relationship(entries)

    _write_docx_parts(entries, output_file)
    output_hash = _sha256(output_file)
    report = {
        "status": "ok",
        "input": str(input_file),
        "output": str(output_file),
        "placeholder": placeholder,
        "placeholder_occurrences": placeholder_occurrences,
        "heading_count": len(headings),
        "heading_levels": sorted({heading.level for heading in headings}),
        "headings": [heading.as_dict() for heading in headings],
        "toc_levels": levels,
        "field_code": field_code,
        "field_inserted": True,
        "update_fields": True,
        "refresh_required": True,
        "refresh_instruction": "Open the output in Word and update fields (Ctrl+A, F9), then save.",
        "pages_verified": False,
        "cached_result": {"status": "not_checked", "pages_verified": False},
        "source_sha256": source_hash,
        "output_sha256": output_hash,
        "authority_ids": [
            "NORM-GOST-R-7.0.11-2011-001:REQ-008",
            "NORM-GOST-R-7.0.11-2011-001:REQ-031",
        ],
        "warnings": [
            "Field inserted only; current TOC entries and page numbers are not promised until an external field refresh."
        ],
    }
    if check_cached or cached_docx is not None:
        cached_target = Path(cached_docx) if cached_docx is not None else output_file
        report["cached_result"] = inspect_cached_toc(
            cached_target,
            expected_headings=[heading.text for heading in headings],
        )
    if report_path is not None:
        report_file = Path(report_path)
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _error_report(
    input_path: Path,
    output_path: Path | None,
    placeholder: str,
    error: TocError,
) -> dict:
    report = _base_report(input_path, output_path, placeholder)
    report["error"] = {"code": error.code, "message": str(error)}
    if error.details:
        report["validation_findings"] = error.details
    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_docx", type=Path, help="Source DOCX containing a standalone [[TOC]] paragraph.")
    parser.add_argument(
        "--out",
        "--output",
        dest="output_docx",
        type=Path,
        help="New output DOCX path (default: <input>_finalized.docx).",
    )
    parser.add_argument("--placeholder", default="[[TOC]]", help="Standalone paragraph token to replace.")
    parser.add_argument("--report", type=Path, help="Optional JSON report sidecar path.")
    parser.add_argument(
        "--check-cached",
        action="store_true",
        help="Structurally inspect a cached TOC result after the output has been externally refreshed.",
    )
    parser.add_argument(
        "--cached-docx",
        "--check-cached-result",
        dest="cached_docx",
        type=Path,
        help="Refreshed DOCX to inspect; implies --check-cached.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    output_path = args.output_docx or args.input_docx.with_name(f"{args.input_docx.stem}_finalized.docx")
    try:
        report = finalize_word_toc(
            args.input_docx,
            output_path,
            placeholder=args.placeholder,
            report_path=args.report,
            check_cached=args.check_cached,
            cached_docx=args.cached_docx,
        )
    except TocError as exc:
        report = _error_report(args.input_docx, output_path, args.placeholder, exc)
        if args.report is not None:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 2
    except (OSError, PermissionError, ValueError) as exc:
        error = TocError(str(exc), code="io_error")
        report = _error_report(args.input_docx, output_path, args.placeholder, error)
        if args.report is not None:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
