"""Lint research notebooks as small executable calculation reports.

The lint is deliberately static and dependency-free.  It checks the saved
notebook structure and selected reproducibility signals; it never claims that a
fresh-kernel execution or the scientific interpretation is correct.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


QUESTION_RE = re.compile(
    r"(?im)^\s*(?:#{1,4}\s*)?(?:\*\*)?"
    r"(?:исследовательский\s+вопрос|задача|research\s+question|task)\b"
)
SCOPE_RE = re.compile(r"(?i)\b(?:границ\w*|scope|не\s+проверяется|out\s+of\s+scope)\b")
COMPLETION_RE = re.compile(
    r"(?i)\b(?:критерий\s+завершения|completion\s+criterion|готово,?\s+когда)\b"
)
INPUT_RE = re.compile(r"(?i)\b(?:входные\s+данные|inputs?)\b")
METHOD_RE = re.compile(r"(?i)\b(?:метод\w*|method|допущен\w*|assumptions?)\b")
SUMMARY_RE = re.compile(r"(?im)^\s*#{1,4}\s*(?:итог|выводы?|summary|conclusions?)\b")
LIMIT_RE = re.compile(
    r"(?i)\b(?:ограничен\w*|не\s+установлено|не\s+проверено|limitations?|not\s+established)\b"
)

RANDOM_RE = re.compile(
    r"(?i)\b(?:np\.random|numpy\.random|random\.|torch\.(?:rand|randn|normal)|"
    r"sklearn\.utils\.shuffle)"
)
SEED_RE = re.compile(
    r"(?i)\b(?:np\.random\.seed|numpy\.random\.seed|random\.seed|"
    r"torch\.manual_seed)\s*\(|\brandom_state\s*="
)
SECRET_RE = re.compile(
    r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*"
    r"[\"'][^\"'\r\n]{8,}[\"']"
)
ABSOLUTE_PATH_RE = re.compile(r"(?:[A-Za-z]:\\|/(?:home|Users|mnt)/)")
NUMBER_RE = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)?(?!\w)")
STABLE_ID_RE = re.compile(r"\b[A-Z][A-Z0-9_-]*-\d+(?:[._-]\d+)*\b", re.IGNORECASE)
UNIT_AFTER_NUMBER_RE = re.compile(
    r"^\s*(?:%|°[CFКС]|мкс|мс|с|мин|ч|Гц|кГц|МГц|ГГц|мм|см|м|км|"
    r"мВ|В|кВ|мА|А|Па|кПа|МПа|мВт|Вт|кВт|мДж|Дж|мг|г|кг|мкл|мл|л|"
    r"раз(?:а|ов)?|объект\w*|наблюден\w*|образц\w*|единиц\w*)\b",
    re.IGNORECASE,
)
DIMENSIONLESS_RE = re.compile(
    r"(?i)(?:\b[pnr]\s*=|R[²2]\s*=|безразмерн\w*|dimensionless)"
)

REPORT_TAGS = {
    "research-question",
    "method-and-assumptions",
    "observable-output",
    "report-summary",
}
FROZEN_FIELDS = ("run_id", "executed_at", "code_version", "environment")
VALID_ARTIFACT_STATUSES = {"working", "frozen"}
VALID_EXECUTION_STATUSES = {"not_run", "partial", "clean_kernel_pass", "failed"}


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
) -> dict[str, Any]:
    item: dict[str, Any] = {"rule_id": rule_id, "severity": severity, "message": message}
    if cell_index is not None:
        item["cell_index"] = cell_index
    return item


def _has_plot_output(cell: dict[str, Any]) -> bool:
    outputs = cell.get("outputs", [])
    if not isinstance(outputs, list):
        return False
    for output in outputs:
        if not isinstance(output, dict):
            continue
        data = output.get("data", {})
        if isinstance(data, dict) and any(
            mime in data for mime in ("image/png", "image/jpeg", "image/svg+xml")
        ):
            return True
    return False


def _output_size(cell: dict[str, Any]) -> tuple[int, int]:
    outputs = cell.get("outputs", [])
    if not isinstance(outputs, list):
        return 0, 0
    rendered = json.dumps(outputs, ensure_ascii=False)
    return len(rendered), rendered.count("\\n") + rendered.count("\n")


def _numeric_lines_without_units(text: str) -> Iterable[str]:
    for raw_line in text.splitlines():
        line = STABLE_ID_RE.sub("", raw_line.strip())
        if not line or DIMENSIONLESS_RE.search(line):
            continue
        for match in NUMBER_RE.finditer(line):
            value = match.group(0).replace(",", ".")
            if value.isdigit() and 1900 <= int(value) <= 2100:
                continue
            tail = line[match.end() : match.end() + 24]
            if UNIT_AFTER_NUMBER_RE.search(tail):
                continue
            yield line
            break


def lint_notebook(data: Any, *, path: str = "<memory>") -> dict[str, Any]:
    findings: list[dict[str, Any]] = []

    if not isinstance(data, dict):
        findings.append(_finding("NB-STRUCT-001", "error", "Notebook root must be an object."))
        return _report(path, findings, 0)

    cells = data.get("cells")
    if data.get("nbformat") != 4 or not isinstance(cells, list):
        findings.append(
            _finding(
                "NB-STRUCT-001",
                "error",
                "Expected nbformat 4 and a cells list.",
            )
        )
        return _report(path, findings, len(cells) if isinstance(cells, list) else 0)

    markdown_cells: list[tuple[int, dict[str, Any], str]] = []
    code_cells: list[tuple[int, dict[str, Any], str]] = []
    question_cells: set[int] = set()
    summary_cells: set[int] = set()
    observable_cells: set[int] = set()

    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            findings.append(
                _finding("NB-STRUCT-002", "error", "Cell must be an object.", cell_index=index)
            )
            continue
        cell_type = cell.get("cell_type")
        text = _source_text(cell)
        tags = _tags(cell)
        if cell_type == "markdown":
            markdown_cells.append((index, cell, text))
            if "research-question" in tags or QUESTION_RE.search(text):
                question_cells.add(index)
            if "report-summary" in tags or SUMMARY_RE.search(text):
                summary_cells.add(index)
            if "observable-output" in tags:
                observable_cells.add(index)
        elif cell_type == "code":
            code_cells.append((index, cell, text))
            outputs = cell.get("outputs", [])
            if not isinstance(outputs, list):
                findings.append(
                    _finding(
                        "NB-STRUCT-003",
                        "error",
                        "Code cell outputs must be a list.",
                        cell_index=index,
                    )
                )
                outputs = []
            if outputs and cell.get("execution_count") is None:
                findings.append(
                    _finding(
                        "NB-EXEC-001",
                        "error",
                        "Stored output has no execution count; output may be stale or detached.",
                        cell_index=index,
                    )
                )
            if any(
                isinstance(output, dict) and output.get("output_type") == "error"
                for output in outputs
            ):
                findings.append(
                    _finding(
                        "NB-EXEC-003",
                        "error",
                        "Notebook contains a stored error output.",
                        cell_index=index,
                    )
                )
            size, lines = _output_size(cell)
            if size > 100_000 or lines > 5_000:
                findings.append(
                    _finding(
                        "NB-OUTPUT-001",
                        "warning",
                        "Large stored output should be summarized or moved to an artifact.",
                        cell_index=index,
                    )
                )
        elif cell_type != "raw":
            findings.append(
                _finding(
                    "NB-STRUCT-004",
                    "error",
                    f"Unsupported cell_type {cell_type!r}.",
                    cell_index=index,
                )
            )

        if SECRET_RE.search(text):
            findings.append(
                _finding(
                    "NB-SEC-001",
                    "error",
                    "Possible embedded secret or password.",
                    cell_index=index,
                )
            )
        if ABSOLUTE_PATH_RE.search(text):
            findings.append(
                _finding(
                    "NB-PORT-001",
                    "warning",
                    "Absolute user-specific path should be replaced or declared as an external step.",
                    cell_index=index,
                )
            )

    markdown = "\n".join(text for _, _, text in markdown_cells)
    required_markers = (
        (question_cells, "NB-NARR-001", "Research question or task is not identifiable."),
        (SCOPE_RE.search(markdown), "NB-NARR-002", "Scope and excluded checks are not stated."),
        (
            COMPLETION_RE.search(markdown),
            "NB-NARR-003",
            "Completion criterion is not stated.",
        ),
        (INPUT_RE.search(markdown), "NB-NARR-004", "Material inputs are not identified."),
        (
            METHOD_RE.search(markdown),
            "NB-NARR-005",
            "Method or material assumptions are not stated before interpretation.",
        ),
        (summary_cells, "NB-NARR-006", "Bounded final summary is not identifiable."),
        (
            LIMIT_RE.search(markdown),
            "NB-NARR-007",
            "Limitations or what was not established are not stated.",
        ),
    )
    for observed, rule_id, message in required_markers:
        if not observed:
            findings.append(_finding(rule_id, "error", message))

    if len(question_cells) > 1:
        findings.append(
            _finding(
                "NB-SPLIT-001",
                "warning",
                "Multiple marked research questions or tasks were found; inspect whether they are independent before recommending a split.",
            )
        )

    execution_counts = [
        cell.get("execution_count")
        for _, cell, _ in code_cells
        if isinstance(cell.get("execution_count"), int)
    ]
    if any(later <= earlier for earlier, later in zip(execution_counts, execution_counts[1:])):
        findings.append(
            _finding(
                "NB-EXEC-002",
                "error",
                "Execution counts are duplicated or decrease in cell order; saved state is not a linear run.",
            )
        )

    all_code = "\n".join(text for _, _, text in code_cells)
    if RANDOM_RE.search(all_code) and not SEED_RE.search(all_code):
        findings.append(
            _finding(
                "NB-REPRO-003",
                "warning",
                "Pseudorandom operation found without a visible seed or random_state.",
            )
        )

    for index, cell, _ in code_cells:
        if not _has_plot_output(cell):
            continue
        following = cells[index + 1] if index + 1 < len(cells) else None
        if not isinstance(following, dict) or following.get("cell_type") != "markdown":
            has_account = False
        else:
            following_text = _source_text(following)
            has_account = "observable-output" in _tags(following) or bool(
                re.search(
                    r"(?i)\b(?:наблюден\w*|интерпретац\w*|ограничен\w*|"
                    r"observation|interpretation|limitation|figure|рисунок)\b",
                    following_text,
                )
            )
        if not has_account:
            findings.append(
                _finding(
                    "NB-OUTPUT-002",
                    "warning",
                    "Plot output is not followed by an observation or bounded interpretation.",
                    cell_index=index,
                )
            )

    for index, _, text in markdown_cells:
        if index not in summary_cells | observable_cells:
            continue
        lines = list(_numeric_lines_without_units(text))
        if lines:
            findings.append(
                _finding(
                    "NB-NUMBER-001",
                    "warning",
                    "A reported number lacks a nearby unit or dimensionless status: " + lines[0][:120],
                    cell_index=index,
                )
            )

    metadata = data.get("metadata", {})
    report_metadata = metadata.get("scientific_report") if isinstance(metadata, dict) else None
    if not isinstance(report_metadata, dict):
        findings.append(
            _finding(
                "NB-REPRO-001",
                "warning",
                "Notebook has no scientific_report metadata; working use is allowed but release state is unknown.",
            )
        )
    else:
        if report_metadata.get("schema_version") != "1.0":
            findings.append(
                _finding("NB-REPRO-002", "error", "scientific_report.schema_version must be '1.0'.")
            )
        artifact_status = report_metadata.get("artifact_status")
        execution_status = report_metadata.get("execution_status")
        if artifact_status not in VALID_ARTIFACT_STATUSES:
            findings.append(
                _finding(
                    "NB-REPRO-002",
                    "error",
                    f"Unknown artifact_status {artifact_status!r}.",
                )
            )
        if execution_status not in VALID_EXECUTION_STATUSES:
            findings.append(
                _finding(
                    "NB-REPRO-002",
                    "error",
                    f"Unknown execution_status {execution_status!r}.",
                )
            )
        if artifact_status == "frozen":
            for field in FROZEN_FIELDS:
                value = report_metadata.get(field)
                if not isinstance(value, str) or not value.strip():
                    findings.append(
                        _finding(
                            "NB-REPRO-002",
                            "error",
                            f"Frozen snapshot requires non-empty {field}.",
                        )
                    )
            outputs = report_metadata.get("significant_outputs")
            if not isinstance(outputs, list) or not outputs:
                findings.append(
                    _finding(
                        "NB-REPRO-002",
                        "error",
                        "Frozen snapshot requires a non-empty significant_outputs list.",
                    )
                )
            if execution_status != "clean_kernel_pass":
                findings.append(
                    _finding(
                        "NB-REPRO-002",
                        "error",
                        "Frozen snapshot requires execution_status 'clean_kernel_pass'.",
                    )
                )

    return _report(path, findings, len(cells))


def _report(path: str, findings: list[dict[str, Any]], cell_count: int) -> dict[str, Any]:
    counts = {
        severity: sum(1 for item in findings if item["severity"] == severity)
        for severity in ("error", "warning", "note")
    }
    status = "fail" if counts["error"] else "review" if counts["warning"] else "pass"
    return {
        "path": path,
        "status": status,
        "valid": counts["error"] == 0,
        "cell_count": cell_count,
        "counts": counts,
        "findings": findings,
        "not_assessed": [
            "actual_clean_kernel_execution",
            "scientific_method_validity",
            "scientific_interpretation_truth",
            "complete_hidden_state_detection",
        ],
    }


def lint_path(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as error:
        return _report(
            str(path),
            [_finding("NB-STRUCT-001", "error", f"Cannot read notebook JSON: {error}")],
            0,
        )
    return lint_notebook(data, path=str(path))


def _expand_paths(paths: list[Path]) -> list[Path]:
    found: set[Path] = set()
    for path in paths:
        if path.is_dir():
            found.update(item for item in path.rglob("*.ipynb") if ".ipynb_checkpoints" not in item.parts)
        elif path.suffix.lower() == ".ipynb":
            found.add(path)
    return sorted(found, key=lambda item: str(item).lower())


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path, help="Notebook file or directory")
    parser.add_argument("--json", action="store_true", help="Print one aggregate JSON report")
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    args = parser.parse_args()

    targets = _expand_paths(args.paths)
    if not targets:
        aggregate = {"status": "input_error", "reports": [], "error": "No .ipynb files found."}
        rendered = json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 2

    reports = [lint_path(path) for path in targets]
    aggregate_status = (
        "fail"
        if any(report["status"] == "fail" for report in reports)
        else "review"
        if any(report["status"] == "review" for report in reports)
        else "pass"
    )
    aggregate = {"status": aggregate_status, "reports": reports}
    rendered = json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if args.json:
        print(rendered, end="")
    else:
        for report in reports:
            counts = report["counts"]
            print(
                f"{report['status'].upper():6} {report['path']} "
                f"errors={counts['error']} warnings={counts['warning']}"
            )
            for item in report["findings"]:
                location = f" cell={item['cell_index']}" if "cell_index" in item else ""
                print(f"  {item['severity']} {item['rule_id']}{location}: {item['message']}")
    return 1 if aggregate_status == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
