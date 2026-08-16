#!/usr/bin/env python3
"""Materialize a dissertation title page in a DOCX copy.

The input document is a template containing exactly one ``[[TITLE_PAGE]]``
placeholder on its first page.  The JSON payload supplies every scientific and
personal fact that is printed on the title page; this module never fills in a
name, specialty, degree, or other fact from local defaults.  The source DOCX
is read-only from the caller's point of view and the result is written to a
separate path.

The implementation intentionally uses the OOXML package layer rather than a
renderer or an image.  The generated title block consists only of native Word
paragraphs and one native Word table used for the supervisor/consultant row.
That keeps the script portable and preserves parts of the input package that
are not needed to understand the title page.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_NS = "http://www.w3.org/XML/1998/namespace"
NS = {"w": W_NS}
PLACEHOLDER = "[[TITLE_PAGE]]"
STATUS = "На правах рукописи"

GOST_TITLE_PAGE_AUTHORITY = "NORM-GOST-R-7.0.11-2011-001:REQ-007"
BMSTU_TITLE_PAGE_AUTHORITY = "NORM-BMSTU-DISS-REQ-001:REQ-007"


class TitlePageError(ValueError):
    """Raised when the JSON or DOCX cannot be materialized without guessing."""


def qn(local: str) -> str:
    """Return a qualified WordprocessingML name."""

    return f"{{{W_NS}}}{local}"


def _as_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TitlePageError(f"{label} must be a JSON object")
    return value


def _text(value: Any, label: str, *, required: bool = True) -> str | None:
    if value is None:
        if required:
            raise TitlePageError(f"{label} is required")
        return None
    if not isinstance(value, str):
        raise TitlePageError(f"{label} must be a string")
    if not value.strip():
        raise TitlePageError(f"{label} must not be empty")
    # XML 1.0 cannot represent these characters.  Rejecting them is safer than
    # silently deleting part of a supplied scientific or personal value.
    if any(
        ord(char) < 0x20 and char not in {"\t", "\n", "\r"}
        for char in value
    ):
        raise TitlePageError(f"{label} contains an XML control character")
    return value


def _first_value(data: Mapping[str, Any], keys: Sequence[str]) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


def _required_alias(data: Mapping[str, Any], keys: Sequence[str], label: str) -> str:
    value = _first_value(data, keys)
    result = _text(value, label)
    assert result is not None
    return result


def _person_name(value: Any, label: str) -> str:
    """Read a person supplied as a string or an explicit name object.

    A structured name is joined only when all supplied components are present;
    no patronymic or academic detail is inferred.  The string form is useful
    for a local profile that already stores the complete display line.
    """

    if isinstance(value, str):
        result = _text(value, label)
        assert result is not None
        return result
    obj = _as_mapping(value, label)
    direct = _first_value(obj, ("full_name", "name", "fio", "ФИО"))
    if direct is not None:
        result = _text(direct, f"{label}.full_name")
        assert result is not None
        return result

    surname = _first_value(obj, ("surname", "last_name", "family_name", "фамилия"))
    given = _first_value(obj, ("given_name", "first_name", "name", "имя"))
    patronymic = _first_value(obj, ("patronymic", "middle_name", "отчество"))
    if surname is None or given is None or patronymic is None:
        raise TitlePageError(
            f"{label} must contain full_name or surname, given_name, and patronymic"
        )
    parts = [
        _text(surname, f"{label}.surname"),
        _text(given, f"{label}.given_name"),
        _text(patronymic, f"{label}.patronymic"),
    ]
    return " ".join(part for part in parts if part is not None)


def _person_line(value: Any, label: str, default_role: str) -> tuple[str, str]:
    """Return a normatively complete supervisor or consultant line."""

    if isinstance(value, str):
        raise TitlePageError(
            f"{label} must be an object with full name, academic degree, and academic title"
        )
    obj = _as_mapping(value, label)
    role = _text(obj.get("role"), f"{label}.role", required=False) or default_role
    name = _person_name(obj, label)
    degree = _required_alias(
        obj,
        ("degree", "academic_degree", "учёная степень", "степень"),
        f"{label}.degree",
    )
    academic_title = _required_alias(
        obj,
        ("title", "academic_title", "учёное звание", "звание"),
        f"{label}.title",
    )
    details = [name, degree, academic_title]
    position = _text(
        _first_value(obj, ("position", "должность")),
        f"{label}.position",
        required=False,
    )
    if position is not None:
        details.append(position)
    return role, ", ".join(details)


def _specialty(data: Mapping[str, Any]) -> tuple[str, str]:
    value = _first_value(data, ("specialty", "speciality"))
    if value is not None:
        obj = _as_mapping(value, "specialty")
        code = _text(
            _first_value(obj, ("code", "cipher", "шифр")),
            "specialty.code",
        )
        name = _text(
            _first_value(obj, ("name", "title", "наименование")),
            "specialty.name",
        )
        assert code is not None and name is not None
        return code, name
    code = _required_alias(
        data,
        ("specialty_code", "speciality_code", "specialty_cipher", "шифр_специальности"),
        "specialty_code",
    )
    name = _required_alias(
        data,
        ("specialty_name", "speciality_name", "specialty_title", "наименование_специальности"),
        "specialty_name",
    )
    return code, name


def _degree(data: Mapping[str, Any]) -> tuple[str, str]:
    value = data.get("degree")
    if isinstance(value, Mapping):
        degree = _text(
            _first_value(value, ("name", "degree", "title", "наименование")),
            "degree.name",
        )
        field = _text(
            _first_value(value, ("field", "science_field", " отрасль", "отрасль")),
            "degree.field",
        )
        assert degree is not None and field is not None
        return degree, field

    degree = _text(value, "degree")
    if degree is None:
        degree = _text(
            _first_value(data, ("degree_name", "requested_degree", "искомая_степень")),
            "degree",
        )
    field = _required_alias(
        data,
        ("science_field", "field", "degree_field", "отрасль_науки"),
        "science_field",
    )
    assert degree is not None
    return degree, field


def _extract_payload(raw: Any) -> Mapping[str, Any]:
    obj = _as_mapping(raw, "title-page JSON")
    for key in ("title_page", "title-page", "data"):
        if key in obj:
            nested = _as_mapping(obj[key], key)
            # A wrapper may carry schema metadata alongside the actual fields.
            return nested
    return obj


def normalize_payload(raw: Any) -> dict[str, Any]:
    """Validate and normalize a title-page payload.

    Accepted aliases are limited to equivalent spellings of the same field;
    unknown keys are ignored and never copied into the DOCX.  This lets a
    caller carry profile metadata without allowing accidental personal or
    scientific fields to leak onto the title page.
    """

    data = _extract_payload(raw)

    supplied_status = _text(data.get("status"), "status", required=False)
    if supplied_status is not None and supplied_status != STATUS:
        raise TitlePageError(f"status must be exactly {STATUS!r}")

    organization = _required_alias(
        data,
        ("organization", "institution", "организация", "organization_name"),
        "organization",
    )
    author_value = _first_value(data, ("author", "author_name", "applicant", "author_fio", "ФИО"))
    if author_value is None:
        raise TitlePageError("author is required")
    author = _person_name(author_value, "author")
    title = _required_alias(
        data,
        ("title", "topic", "dissertation_title", "тема"),
        "title",
    )
    specialty_code, specialty_name = _specialty(data)
    degree, science_field = _degree(data)

    supervisors: list[dict[str, str]] = []
    supervisor = _first_value(data, ("supervisor", "scientific_supervisor", "руководитель"))
    consultant = _first_value(data, ("consultant", "scientific_consultant", "консультант"))
    if supervisor is not None:
        role, display = _person_line(supervisor, "supervisor", "Научный руководитель")
        supervisors.append({"role": role, "display": display})
    if consultant is not None:
        role, display = _person_line(consultant, "consultant", "Научный консультант")
        supervisors.append({"role": role, "display": display})
    if not supervisors:
        raise TitlePageError("supervisor or consultant is required")

    city = _required_alias(data, ("city", "place", "location", "город"), "city")
    year_value = _first_value(data, ("year", "written_year", "год"))
    if isinstance(year_value, bool):
        raise TitlePageError("year must be a four-digit year")
    if isinstance(year_value, int):
        year = str(year_value)
    elif isinstance(year_value, str):
        year = year_value.strip()
    else:
        raise TitlePageError("year must be a four-digit year")
    if not re.fullmatch(r"\d{4}", year):
        raise TitlePageError("year must be a four-digit year")

    profile = data.get("local_profile", data.get("profile"))
    profile_obj: Mapping[str, Any] = {}
    if profile is not None:
        profile_obj = _as_mapping(profile, "local_profile")
    raw_authorities = profile_obj.get("authority_ids", [])
    if not isinstance(raw_authorities, list) or not all(
        isinstance(item, str) and item.strip() for item in raw_authorities
    ):
        raise TitlePageError("local_profile.authority_ids must be a list of non-empty strings")
    local_authorities = list(dict.fromkeys(item.strip() for item in raw_authorities))

    signature = _first_value(
        data,
        ("signature_line", "signature", "applicant_signature", "строка_подписи"),
    )
    if signature is None:
        signature = _first_value(
            profile_obj,
            ("signature_line", "signature", "applicant_signature", "строка_подписи"),
        )
    signature_line = _text(signature, "signature_line", required=False)
    bmstu_selected = BMSTU_TITLE_PAGE_AUTHORITY in local_authorities
    signature_required = profile_obj.get("signature_required", bmstu_selected)
    if not isinstance(signature_required, bool):
        raise TitlePageError("local_profile.signature_required must be boolean")
    if bmstu_selected and not signature_required:
        raise TitlePageError(
            "local_profile.signature_required=false conflicts with the selected BMSTU authority"
        )
    if signature_required and signature_line is None:
        raise TitlePageError("signature_line is required by local_profile")

    return {
        "status": STATUS,
        "organization": organization,
        "author": author,
        "title": title,
        "specialty_code": specialty_code,
        "specialty_name": specialty_name,
        "degree": degree,
        "science_field": science_field,
        "supervisors": supervisors,
        "city": city,
        "year": year,
        "signature_line": signature_line,
        "signature_required": signature_required,
        "authority_ids": [GOST_TITLE_PAGE_AUTHORITY, *local_authorities],
    }


def _paragraph_text(paragraph: etree._Element) -> str:
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))


def _iter_paragraphs(root: etree._Element) -> Iterable[etree._Element]:
    yield from root.xpath(".//w:p", namespaces=NS)


def _count_placeholder(root: etree._Element) -> int:
    count = 0
    for paragraph in _iter_paragraphs(root):
        count += _paragraph_text(paragraph).count(PLACEHOLDER)
    return count


def _placeholder_paragraph(document_root: etree._Element) -> etree._Element:
    body = document_root.find(".//" + qn("body"))
    if body is None:
        raise TitlePageError("DOCX has no Word document body")
    matches = [
        paragraph
        for paragraph in body.xpath("./w:p", namespaces=NS)
        if PLACEHOLDER in _paragraph_text(paragraph)
    ]
    if len(matches) != 1 or _count_placeholder(document_root) != 1:
        raise TitlePageError(
            "DOCX must contain exactly one [[TITLE_PAGE]] placeholder in the body"
        )
    paragraph = matches[0]
    if _paragraph_text(paragraph).strip() != PLACEHOLDER:
        raise TitlePageError(
            "[[TITLE_PAGE]] must be the only text in its paragraph; refusing to drop neighboring text"
        )
    if paragraph.getparent() is not body:
        raise TitlePageError("[[TITLE_PAGE]] must be a top-level document paragraph")

    # OOXML has no reliable page-number API without rendering.  The explicit
    # page-break signals that can be checked structurally are sufficient for
    # the template contract: a placeholder after one is not on page one.
    index = body.index(paragraph)
    for previous in body[:index]:
        if previous.xpath(
            ".//w:br[@w:type='page'] | .//w:lastRenderedPageBreak | .//w:sectPr",
            namespaces=NS,
        ):
            raise TitlePageError("[[TITLE_PAGE]] is not on the first page")
    if paragraph.xpath("./w:pPr/w:pageBreakBefore", namespaces=NS):
        raise TitlePageError("[[TITLE_PAGE]] starts after a page break")
    return paragraph


def _set_attr(element: etree._Element, local: str, value: str) -> None:
    element.set(qn(local), value)


def _spacing(ppr: etree._Element, *, before: int = 0, after: int = 0, line: int = 240) -> None:
    spacing = etree.SubElement(ppr, qn("spacing"))
    spacing.set(qn("before"), str(before))
    spacing.set(qn("after"), str(after))
    spacing.set(qn("line"), str(line))
    spacing.set(qn("lineRule"), "auto")


def _run(
    text: str,
    *,
    size: int = 28,
    bold: bool = False,
    italic: bool = False,
) -> etree._Element:
    run = etree.Element(qn("r"))
    rpr = etree.SubElement(run, qn("rPr"))
    fonts = etree.SubElement(rpr, qn("rFonts"))
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        fonts.set(qn(attr), "Times New Roman")
    size_node = etree.SubElement(rpr, qn("sz"))
    size_node.set(qn("val"), str(size))
    size_cs = etree.SubElement(rpr, qn("szCs"))
    size_cs.set(qn("val"), str(size))
    if bold:
        etree.SubElement(rpr, qn("b"))
        etree.SubElement(rpr, qn("bCs"))
    if italic:
        etree.SubElement(rpr, qn("i"))
        etree.SubElement(rpr, qn("iCs"))

    # Preserve line breaks as Word-native breaks instead of embedding an
    # image, text box, or a renderer-specific layout object.
    chunks = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for index, chunk in enumerate(chunks):
        if index:
            etree.SubElement(run, qn("br"))
        if chunk:
            text_node = etree.SubElement(run, qn("t"))
            text_node.text = chunk
            if chunk[:1].isspace() or chunk[-1:].isspace():
                text_node.set(f"{{{XML_NS}}}space", "preserve")
    return run


def _paragraph(
    text: str = "",
    *,
    align: str = "center",
    size: int = 28,
    bold: bool = False,
    italic: bool = False,
    before: int = 0,
    after: int = 0,
    line: int = 240,
) -> etree._Element:
    paragraph = etree.Element(qn("p"))
    ppr = etree.SubElement(paragraph, qn("pPr"))
    jc = etree.SubElement(ppr, qn("jc"))
    jc.set(qn("val"), align)
    _spacing(ppr, before=before, after=after, line=line)
    if text:
        paragraph.append(_run(text, size=size, bold=bold, italic=italic))
    return paragraph


def _cell(text: str, width: int, *, bold: bool = False) -> etree._Element:
    cell = etree.Element(qn("tc"))
    tcpr = etree.SubElement(cell, qn("tcPr"))
    tcw = etree.SubElement(tcpr, qn("tcW"))
    tcw.set(qn("w"), str(width))
    tcw.set(qn("type"), "dxa")
    cell_margins = etree.SubElement(tcpr, qn("tcMar"))
    for side in ("top", "start", "bottom", "end"):
        node = etree.SubElement(cell_margins, qn(side))
        node.set(qn("w"), "80")
        node.set(qn("type"), "dxa")
    cell.append(_paragraph(text, align="left", size=24, bold=bold, line=276))
    return cell


def _title_table(rows: Sequence[Mapping[str, str]]) -> etree._Element:
    table = etree.Element(qn("tbl"))
    tblpr = etree.SubElement(table, qn("tblPr"))
    tblw = etree.SubElement(tblpr, qn("tblW"))
    tblw.set(qn("w"), "9000")
    tblw.set(qn("type"), "dxa")
    layout = etree.SubElement(tblpr, qn("tblLayout"))
    layout.set(qn("type"), "fixed")
    indent = etree.SubElement(tblpr, qn("tblInd"))
    indent.set(qn("w"), "0")
    indent.set(qn("type"), "dxa")
    borders = etree.SubElement(tblpr, qn("tblBorders"))
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        border = etree.SubElement(borders, qn(side))
        border.set(qn("val"), "nil")
    cell_margins = etree.SubElement(tblpr, qn("tblCellMar"))
    for side in ("top", "start", "bottom", "end"):
        node = etree.SubElement(cell_margins, qn(side))
        node.set(qn("w"), "80")
        node.set(qn("type"), "dxa")

    grid = etree.SubElement(table, qn("tblGrid"))
    for width in (3000, 6000):
        column = etree.SubElement(grid, qn("gridCol"))
        column.set(qn("w"), str(width))

    for row in rows:
        tr = etree.SubElement(table, qn("tr"))
        tr.append(_cell(row["role"], 3000, bold=True))
        tr.append(_cell(row["display"], 6000))
    return table


def _title_nodes(payload: Mapping[str, Any]) -> list[etree._Element]:
    nodes: list[etree._Element] = [
        _paragraph(payload["status"], size=28, before=240, after=120),
        _paragraph(payload["organization"], size=28, after=420),
        _paragraph(payload["author"], size=28, bold=True, after=420),
        _paragraph(payload["title"], size=28, bold=True, after=360, line=300),
        _paragraph(
            f"Шифр и наименование специальности: {payload['specialty_code']} — {payload['specialty_name']}",
            size=26,
            after=180,
            line=276,
        ),
        _paragraph(
            f"На соискание учёной степени {payload['degree']} по отрасли науки {payload['science_field']}",
            size=26,
            after=480,
            line=276,
        ),
        _title_table(payload["supervisors"]),
        _paragraph("", after=180),
    ]
    if payload["signature_line"] is not None:
        nodes.append(
            _paragraph(
                payload["signature_line"],
                align="right",
                size=24,
                before=120,
                after=120,
            )
        )
    nodes.append(
        _paragraph(
            f"{payload['city']}, {payload['year']}",
            size=28,
            before=1800,
            after=120,
        )
    )
    return nodes


def _package_placeholder_count(entries: Mapping[str, bytes]) -> int:
    total = 0
    for name, content in entries.items():
        if not (name.startswith("word/") and name.endswith(".xml")):
            continue
        try:
            root = etree.fromstring(content)
        except etree.XMLSyntaxError:
            continue
        total += _count_placeholder(root)
    return total


def apply_title_page(
    input_docx: str | os.PathLike[str],
    payload: Mapping[str, Any] | Any,
    output_docx: str | os.PathLike[str],
) -> dict[str, Any]:
    """Apply a normalized title page and return the JSON report."""

    source = Path(input_docx)
    output = Path(output_docx)
    try:
        if source.resolve() == output.resolve():
            raise TitlePageError("output DOCX must be a separate copy; source is never modified")
    except OSError:
        # If a path cannot be resolved, the later read/write errors are more
        # useful than risking an in-place write.
        raise TitlePageError("cannot resolve input/output DOCX paths")

    normalized = normalize_payload(payload)
    try:
        with zipfile.ZipFile(source, "r") as archive:
            entries = {name: archive.read(name) for name in archive.namelist()}
    except (OSError, zipfile.BadZipFile) as exc:
        raise TitlePageError(f"cannot read source DOCX: {exc}") from exc

    document_bytes = entries.get("word/document.xml")
    if document_bytes is None:
        raise TitlePageError("source DOCX has no word/document.xml")
    if _package_placeholder_count(entries) != 1:
        raise TitlePageError("source DOCX must contain exactly one [[TITLE_PAGE]] placeholder")
    try:
        document_root = etree.fromstring(document_bytes)
    except etree.XMLSyntaxError as exc:
        raise TitlePageError(f"word/document.xml is not valid XML: {exc}") from exc

    paragraph = _placeholder_paragraph(document_root)
    parent = paragraph.getparent()
    if parent is None:
        raise TitlePageError("placeholder paragraph has no parent")
    index = parent.index(paragraph)
    parent.remove(paragraph)
    nodes = _title_nodes(normalized)
    for node in reversed(nodes):
        parent.insert(index, node)
    entries["word/document.xml"] = etree.tostring(
        document_root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=True,
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".docx", prefix=f".{output.stem}.", dir=output.parent, delete=False
        ) as temporary:
            temporary_name = temporary.name
        with zipfile.ZipFile(temporary_name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in entries.items():
                archive.writestr(name, content)
        os.replace(temporary_name, output)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except OSError:
                pass

    applied = [
        "status",
        "organization",
        "author",
        "title",
        "specialty_code",
        "specialty_name",
        "degree",
        "science_field",
        "supervisor_or_consultant",
        "city",
        "year",
    ]
    not_assessed: list[str] = []
    not_assessed_details: list[dict[str, Any]] = []
    if normalized["signature_line"] is not None:
        applied.append("signature_line")
    else:
        not_assessed.append("signature_line")
        not_assessed_details.append(
            {
                "field": "signature_line",
                "reason": "no applicable local signature requirement was selected",
                "authority_ids": [],
            }
        )

    authority_ids = normalized["authority_ids"]
    return {
        "schema_version": "PSES-DISS-TITLE-PAGE-001/v1",
        "status": "applied",
        "result": "applied",
        "output": str(output),
        "output_docx": str(output),
        "placeholder": PLACEHOLDER,
        "applied": applied,
        "not_assessed": not_assessed,
        "not_assessed_details": not_assessed_details,
        "authority_ids": authority_ids,
    }


def apply_title_page_from_files(
    json_path: str | os.PathLike[str],
    input_docx: str | os.PathLike[str],
    output_docx: str | os.PathLike[str],
) -> dict[str, Any]:
    """Load JSON from disk and apply it to a DOCX copy."""

    path = Path(json_path)
    try:
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TitlePageError(f"cannot read title-page JSON {path}: {exc}") from exc
    return apply_title_page(input_docx, raw, output_docx)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", help="title-page JSON or source DOCX")
    parser.add_argument("second", help="source DOCX or title-page JSON")
    parser.add_argument("--out", "--output", required=True, dest="output", help="output DOCX copy")
    parser.add_argument(
        "--report",
        "--report-json",
        dest="report",
        help="optional path for the JSON report (the report is always printed)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    first = Path(args.first)
    second = Path(args.second)
    if first.suffix.lower() == ".docx" and second.suffix.lower() != ".docx":
        input_docx, json_path = first, second
    elif second.suffix.lower() == ".docx" and first.suffix.lower() != ".docx":
        json_path, input_docx = first, second
    else:
        print(
            "apply_dissertation_title_page: exactly one positional input must be .docx and the other .json",
            file=sys.stderr,
        )
        return 2
    try:
        report = apply_title_page_from_files(json_path, input_docx, args.output)
    except (TitlePageError, OSError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
        print(f"apply_dissertation_title_page: error: {exc}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    print(rendered, end="")
    if args.report:
        Path(args.report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.report).write_text(rendered, encoding="utf-8")
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised through the CLI
    raise SystemExit(main())
