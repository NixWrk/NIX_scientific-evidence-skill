"""Check links, equation references, citations, and bibliography in notebooks and companion Markdown."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote


EQUATION_TAG_RE = re.compile(r"\\tag\{([^{}]+)\}")
DISPLAY_EQUATION_RE = re.compile(r"\$\$(.*?)\$\$|\\\[(.*?)\\\]", re.DOTALL)
COMMA_WHERE_RE = re.compile(r"[ \t]*,[ \t\r\n]*где\b")
INLINE_MATH_RE = re.compile(r"(?<!\$)\$(?!\$)(.*?)(?<!\$)\$(?!\$)|\\\((.*?)\\\)", re.DOTALL)
EQUATION_REF_RE = re.compile(
    r"(?i)\b(?:формул\w*|уравнен\w*|соотношен\w*|выражен\w*|"
    r"equation|formula)\s*(?:№\s*)?"
    r"((?:\([^()]+\))(?:\s*(?:,|;|и|and)\s*(?:№\s*)?\([^()]+\))*)"
)
EQUATION_LABEL_RE = re.compile(r"\(([^()]+)\)")
MARKDOWN_LINK_RE = re.compile(r"(!?)\[[^\]]*\]\(([^)]+)\)")
EXTERNAL_URL_RE = re.compile(r"(?i)https?://[^\s)>]+")
CITATION_RE = re.compile(r"(?<!\!)\[((?:\d+\s*;\s*)*\d+)\]")
BIBLIOGRAPHY_HEADING_RE = re.compile(
    r"(?im)^\s*#{1,4}\s*(?:литература|список\s+литературы|библиография|references)\s*$"
)
BIBLIOGRAPHY_ENTRY_RE = re.compile(r"(?m)^\s*(?:[-*]\s*)?\[(\d+)\]\s+\S.+$")
HEADING_RE = re.compile(r"(?m)^\s*#{1,6}\s+(.+?)\s*#*\s*$")
EXPLICIT_ANCHOR_RE = re.compile(r"(?i)<a\s+(?:id|name)=[\"']([^\"']+)[\"']")
VALID_BIBLIOGRAPHY_STATUSES = {"not_applicable", "incomplete", "complete"}

GREEK_VARIABLES = (
    "alpha|beta|gamma|delta|Delta|epsilon|varepsilon|zeta|eta|theta|vartheta|"
    "iota|kappa|lambda|mu|nu|xi|Xi|omicron|rho|varrho|sigma|Sigma|tau|"
    "upsilon|phi|varphi|chi|psi|Psi|omega|Omega|Phi"
)
SUBSCRIPT = r"(?:_\{(?:[^{}]|\{[^{}]*\})+\}|_[A-Za-zА-Яа-яЁё0-9])?"
LATEX_SYMBOL_RE = re.compile(
    rf"\\(?P<greek>{GREEK_VARIABLES})(?P<greek_sub>{SUBSCRIPT})|"
    rf"(?<![\\A-Za-z])(?P<latin>[A-Za-z]+)(?P<latin_sub>{SUBSCRIPT})"
)
FORMAT_COMMAND_RE = re.compile(
    r"\\(?:boxed|mathbf|boldsymbol|mathbb|mathit|mathsf|mathtt|hat|widehat|bar|overline|vec)\b"
)
SUBSCRIPT_TEXT_STYLE_RE = re.compile(
    r"_\{\\(?:text|mathrm)\{([^{}]*)\}\}"
)
PRESERVED_MATHRM_RE = re.compile(r"\\mathrm\{(FoM|Cov|RMS)\}")
MATHBB_OPERATOR_RE = re.compile(r"\\mathbb(?:\{(?:E|R)\}|[ \t]*(?:E|R))")
TEXT_STYLE_RE = re.compile(r"\\(?:text|mathrm)\{(?:[^{}]|\{[^{}]*\})*\}")
OPERATOR_RE = re.compile(r"\\operatorname\{(?:[^{}]|\{[^{}]*\})*\}")
ENVIRONMENT_RE = re.compile(r"\\(?:begin|end)\{[^{}]+\}")
NONVARIABLE_LATIN = {"d", "e", "func", "inf", "nan", "std"}


def _source_text(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    if isinstance(source, list):
        return "".join(part for part in source if isinstance(part, str))
    return source if isinstance(source, str) else ""


def _tags(cell: dict[str, Any]) -> set[str]:
    metadata = cell.get("metadata", {})
    raw = metadata.get("tags", []) if isinstance(metadata, dict) else []
    return {item for item in raw if isinstance(item, str)} if isinstance(raw, list) else set()


def _finding(
    rule_id: str,
    severity: str,
    message: str,
    *,
    cell_index: int | None = None,
    line_number: int | None = None,
) -> dict[str, Any]:
    finding: dict[str, Any] = {
        "rule_id": rule_id,
        "severity": severity,
        "message": message,
    }
    if cell_index is not None:
        finding["cell_index"] = cell_index
    if line_number is not None:
        finding["line_number"] = line_number
    return finding


def _normalise_symbol(name: str, subscript: str = "") -> str:
    token = name + subscript
    token = re.sub(r"\\(?:text|mathrm)", "", token)
    token = re.sub(r"[{}\\\s,]", "", token)
    return token


def _equation_symbols(text: str) -> set[str]:
    """Extract lexical symbols; the meaning of their definitions remains manual QA."""
    scrubbed = EQUATION_TAG_RE.sub(" ", text)
    previous = None
    while previous != scrubbed:
        previous = scrubbed
        scrubbed = SUBSCRIPT_TEXT_STYLE_RE.sub(lambda match: "_{" + match.group(1) + "}", scrubbed)
    scrubbed = PRESERVED_MATHRM_RE.sub(lambda match: match.group(1), scrubbed)
    scrubbed = MATHBB_OPERATOR_RE.sub(" ", scrubbed)
    scrubbed = TEXT_STYLE_RE.sub(" ", scrubbed)
    scrubbed = OPERATOR_RE.sub(" ", scrubbed)
    scrubbed = ENVIRONMENT_RE.sub(" ", scrubbed)
    scrubbed = FORMAT_COMMAND_RE.sub("", scrubbed)
    symbols: set[str] = set()
    for match in LATEX_SYMBOL_RE.finditer(scrubbed):
        if match.group("greek"):
            symbols.add(
                _normalise_symbol(
                    match.group("greek"), match.group("greek_sub") or ""
                )
            )
            continue
        name = match.group("latin")
        subscript = match.group("latin_sub") or ""
        if name.lower() in NONVARIABLE_LATIN and not subscript:
            continue
        if len(name) > 1 and name.islower() and not subscript:
            symbols.update(character for character in name if character not in {"d", "e"})
        else:
            symbols.add(_normalise_symbol(name, subscript))
    return symbols


def _definition_symbols(text: str) -> set[str]:
    symbols: set[str] = set()
    for match in INLINE_MATH_RE.finditer(text):
        symbols.update(_equation_symbols(match.group(1) or match.group(2) or ""))
    return symbols


def _equation_narrative_findings(
    text: str,
    *,
    prefix: str,
    cell_index: int | None = None,
) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for match in DISPLAY_EQUATION_RE.finditer(text):
        body = match.group(1) if match.group(1) is not None else match.group(2)
        if not body or not EQUATION_TAG_RE.search(body):
            continue
        after = text[match.end() :]
        syntax = COMMA_WHERE_RE.match(after)
        line_number = text.count("\n", 0, match.start()) + 1 if cell_index is None else None
        if syntax is None:
            findings.append(
                _finding(
                    f"{prefix}-EQ-004",
                    "error",
                    "A numbered displayed equation must end with a comma and be followed by lowercase 'где'.",
                    cell_index=cell_index,
                    line_number=line_number,
                )
            )
            continue
        definition = after[syntax.end() :]
        definition = re.split(r"\n\s*\n", definition, maxsplit=1)[0][:3000]
        expected = _equation_symbols(body)
        defined = _definition_symbols(definition)
        missing = sorted(expected - defined, key=str.lower)
        if missing:
            findings.append(
                _finding(
                    f"{prefix}-EQ-005",
                    "error",
                    "The 'где' clause does not name every equation symbol: "
                    + ", ".join(missing)
                    + ".",
                    cell_index=cell_index,
                    line_number=line_number,
                )
            )
    return findings


def _link_target(raw: str) -> str:
    target = raw.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    if re.search(r"\s+[\"']", target):
        target = re.split(r"\s+[\"']", target, maxsplit=1)[0]
    return target


def _is_external(target: str) -> bool:
    lowered = target.lower()
    return lowered.startswith(("http://", "https://", "mailto:", "doi:"))


def _heading_anchor(text: str) -> str:
    text = re.sub(r"[`*_~]", "", text).strip().lower()
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return re.sub(r"\s+", "-", text)


def _local_target_exists(target: str, notebook_path: Path) -> bool:
    clean = unquote(target.split("#", 1)[0]).strip()
    if not clean or clean.startswith("data:"):
        return True
    clean = clean.replace("\\", "/")
    path = Path(clean)
    if not path.is_absolute():
        path = notebook_path.parent / path
    return path.exists()


def validate_notebook_references(
    data: Any,
    *,
    path: str | Path = "<memory>",
) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    if not isinstance(data, dict) or not isinstance(data.get("cells"), list):
        findings.append(
            _finding("NB-REF-STRUCT-001", "error", "Notebook root must contain a cells list.")
        )
        return _report(path, findings)

    notebook_path = Path(path)
    equation_tags: dict[str, list[int]] = {}
    equation_refs: list[tuple[str, int]] = []
    citation_refs: list[tuple[str, int]] = []
    bibliography_entries: dict[str, list[int]] = {}
    external_links: list[tuple[str, int]] = []
    internal_links: list[tuple[str, int]] = []
    local_links: list[tuple[str, int]] = []
    bibliography_cells: set[int] = set()

    markdown_cells: list[tuple[int, str]] = []
    for index, cell in enumerate(data["cells"]):
        if not isinstance(cell, dict) or cell.get("cell_type") != "markdown":
            continue
        text = _source_text(cell)
        markdown_cells.append((index, text))
        if "bibliography" in _tags(cell) or BIBLIOGRAPHY_HEADING_RE.search(text):
            bibliography_cells.add(index)

    anchors = {
        anchor
        for _, text in markdown_cells
        for anchor in (
            [_heading_anchor(heading) for heading in HEADING_RE.findall(text)]
            + EXPLICIT_ANCHOR_RE.findall(text)
        )
        if anchor
    }

    for index, text in markdown_cells:
        findings.extend(
            _equation_narrative_findings(text, prefix="NB-REF", cell_index=index)
        )
        for label in EQUATION_TAG_RE.findall(text):
            equation_tags.setdefault(label.strip(), []).append(index)
        for group in EQUATION_REF_RE.findall(text):
            for label in EQUATION_LABEL_RE.findall(group):
                equation_refs.append((label.strip(), index))

        link_spans: list[tuple[int, int]] = []
        for match in MARKDOWN_LINK_RE.finditer(text):
            link_spans.append(match.span())
            target = _link_target(match.group(2))
            if _is_external(target):
                external_links.append((target, index))
            elif target.startswith("#"):
                internal_links.append((unquote(target[1:]).lower(), index))
            elif not target.startswith("data:"):
                local_links.append((target, index))

        scrubbed = text
        for start, end in reversed(link_spans):
            scrubbed = scrubbed[:start] + " " * (end - start) + scrubbed[end:]
        if index not in bibliography_cells:
            for group in CITATION_RE.findall(scrubbed):
                for label in re.split(r"\s*;\s*", group):
                    citation_refs.append((label, index))
            for url in EXTERNAL_URL_RE.findall(scrubbed):
                external_links.append((url, index))
        else:
            for label in BIBLIOGRAPHY_ENTRY_RE.findall(text):
                bibliography_entries.setdefault(label, []).append(index)

    for label, cells in sorted(equation_tags.items()):
        if len(cells) > 1:
            findings.append(
                _finding(
                    "NB-REF-EQ-001",
                    "error",
                    f"Equation label {label!r} is declared more than once.",
                    cell_index=cells[1],
                )
            )
    for label, index in equation_refs:
        if label not in equation_tags:
            findings.append(
                _finding(
                    "NB-REF-EQ-002",
                    "error",
                    f"Equation reference ({label}) has no matching equation tag.",
                    cell_index=index,
                )
            )

    referenced_equations = {label for label, _ in equation_refs}
    for label, cells in sorted(equation_tags.items()):
        if label not in referenced_equations:
            findings.append(
                _finding(
                    "NB-REF-EQ-003",
                    "error",
                    f"Equation label {label!r} is not referenced in notebook prose.",
                    cell_index=cells[0],
                )
            )

    for anchor, index in internal_links:
        if anchor not in anchors:
            findings.append(
                _finding(
                    "NB-REF-LINK-002",
                    "error",
                    f"Internal anchor does not exist: #{anchor}.",
                    cell_index=index,
                )
            )

    for target, index in local_links:
        if str(path) == "<memory>":
            findings.append(
                _finding(
                    "NB-REF-LINK-003",
                    "warning",
                    f"Local link {target!r} was not checked without a notebook path.",
                    cell_index=index,
                )
            )
        elif not _local_target_exists(target, notebook_path):
            findings.append(
                _finding(
                    "NB-REF-LINK-001",
                    "error",
                    f"Local link target does not exist: {target!r}.",
                    cell_index=index,
                )
            )

    for label, cells in sorted(bibliography_entries.items()):
        if len(cells) > 1:
            findings.append(
                _finding(
                    "NB-REF-BIB-002",
                    "error",
                    f"Bibliography label [{label}] is declared more than once.",
                    cell_index=cells[1],
                )
            )
    for label, index in citation_refs:
        if label not in bibliography_entries:
            findings.append(
                _finding(
                    "NB-REF-BIB-001",
                    "error",
                    f"Citation [{label}] has no matching bibliography entry.",
                    cell_index=index,
                )
            )
    used_labels = {label for label, _ in citation_refs}
    for label, cells in sorted(bibliography_entries.items()):
        if label not in used_labels:
            findings.append(
                _finding(
                    "NB-REF-BIB-003",
                    "warning",
                    f"Bibliography entry [{label}] is not cited in notebook prose.",
                    cell_index=cells[0],
                )
            )

    metadata = data.get("metadata", {})
    report_metadata = metadata.get("scientific_report", {}) if isinstance(metadata, dict) else {}
    bibliography_status = (
        report_metadata.get("bibliography_status") if isinstance(report_metadata, dict) else None
    )
    artifact_status = (
        report_metadata.get("artifact_status") if isinstance(report_metadata, dict) else None
    )
    if bibliography_status not in VALID_BIBLIOGRAPHY_STATUSES:
        findings.append(
            _finding(
                "NB-REF-BIB-004",
                "error",
                "scientific_report.bibliography_status must be not_applicable, incomplete, or complete.",
            )
        )
    if bibliography_status == "not_applicable" and (citation_refs or external_links):
        findings.append(
            _finding(
                "NB-REF-BIB-005",
                "error",
                "Bibliography cannot be not_applicable when the notebook cites external material.",
            )
        )
    if bibliography_status == "complete" and not bibliography_entries:
        findings.append(
            _finding(
                "NB-REF-BIB-006",
                "error",
                "Complete bibliography status requires at least one numbered bibliography entry.",
            )
        )
    if artifact_status == "frozen" and bibliography_status == "incomplete":
        findings.append(
            _finding(
                "NB-REF-BIB-007",
                "error",
                "A frozen notebook cannot retain an incomplete bibliography.",
            )
        )
    if external_links and not bibliography_entries:
        findings.append(
            _finding(
                "NB-REF-BIB-008",
                "warning",
                "External links are present without a numbered bibliography; classify and record scholarly sources.",
                cell_index=external_links[0][1],
            )
        )

    return _report(path, findings)


def _report(path: str | Path, findings: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {
        severity: sum(1 for item in findings if item["severity"] == severity)
        for severity in ("error", "warning", "note")
    }
    status = "fail" if counts["error"] else "review" if counts["warning"] else "pass"
    return {
        "path": str(path),
        "status": status,
        "valid": counts["error"] == 0,
        "counts": counts,
        "findings": findings,
        "not_assessed": [
            "semantic_support_of_citations",
            "exact_bibliographic_title_against_source",
            "gost_punctuation_and_required_fields",
            "semantic_correctness_of_equation_variable_definitions",
            "validity_of_external_urls",
            "fragment_anchors_in_linked_files",
        ],
    }



def validate_markdown_references(text: str, *, path: str | Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    document_path = Path(path)
    anchors = {
        anchor
        for anchor in (
            [_heading_anchor(heading) for heading in HEADING_RE.findall(text)]
            + EXPLICIT_ANCHOR_RE.findall(text)
        )
        if anchor
    }
    findings.extend(_equation_narrative_findings(text, prefix="DOC-REF"))
    for match in MARKDOWN_LINK_RE.finditer(text):
        target = _link_target(match.group(2))
        line_number = text.count("\n", 0, match.start()) + 1
        if _is_external(target) or target.startswith("data:"):
            continue
        if target.startswith("#"):
            anchor = unquote(target[1:]).lower()
            if anchor not in anchors:
                findings.append(
                    _finding(
                        "DOC-REF-LINK-002",
                        "error",
                        f"Internal anchor does not exist: #{anchor}.",
                        line_number=line_number,
                    )
                )
        elif not _local_target_exists(target, document_path):
            findings.append(
                _finding(
                    "DOC-REF-LINK-001",
                    "error",
                    f"Local link target does not exist: {target!r}.",
                    line_number=line_number,
                )
            )
    return _report(path, findings)

def lint_path(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".md":
        try:
            return validate_markdown_references(path.read_text(encoding="utf-8-sig"), path=path)
        except OSError as error:
            return _report(path, [_finding("DOC-REF-STRUCT-001", "error", f"Cannot read Markdown: {error}")])
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        return _report(
            path,
            [_finding("NB-REF-STRUCT-001", "error", f"Cannot read notebook JSON: {error}")],
        )
    return validate_notebook_references(data, path=path)


def _expand_paths(paths: list[Path]) -> list[Path]:
    targets: set[Path] = set()
    for path in paths:
        if path.is_dir():
            targets.update(
                item
                for item in path.rglob("*.ipynb")
                if ".ipynb_checkpoints" not in item.parts
            )
            targets.update(path.glob("*.md"))
        elif path.suffix.lower() in {".ipynb", ".md"}:
            targets.add(path)
    return sorted(targets, key=lambda item: str(item).lower())


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    targets = _expand_paths(args.paths)
    if not targets:
        print(json.dumps({"status": "input_error", "reports": []}, indent=2))
        return 2
    reports = [lint_path(path) for path in targets]
    status = (
        "fail"
        if any(report["status"] == "fail" for report in reports)
        else "review"
        if any(report["status"] == "review" for report in reports)
        else "pass"
    )
    aggregate = {"status": status, "reports": reports}
    if args.json:
        print(json.dumps(aggregate, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            print(f"{report['status'].upper():6} {report['path']}")
            for finding in report["findings"]:
                location = f" cell={finding['cell_index']}" if "cell_index" in finding else ""
                print(f"  {finding['severity']} {finding['rule_id']}{location}: {finding['message']}")
    return 1 if status == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
