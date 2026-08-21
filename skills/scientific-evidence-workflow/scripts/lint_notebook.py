"""Lint `.ipynb` artifacts as self-contained scientific and technical reports.

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


ROLE_RE = re.compile(
    r"(?i)\b(?:прикладн\w+\s+роль|назначение\s+отч[её]та|report\s+role|applied\s+role)\b"
)
QUESTION_RE = re.compile(
    r"(?im)^\s*(?:#{1,4}\s*)?(?:\*\*)?"
    r"(?:исследовательский\s+вопрос|главный\s+вопрос|вопрос|задача|research\s+question|task)\b"
)
SCOPE_RE = re.compile(r"(?i)\b(?:границ\w*|scope|не\s+проверяется|out\s+of\s+scope)\b")
COMPLETION_RE = re.compile(
    r"(?i)\b(?:критерий\s+завершения|completion\s+criterion|готово,?\s+когда)\b"
)
INPUT_RE = re.compile(
    r"(?im)(?:^\s*(?:#{1,4}\s*)?(?:данные|inputs?)\b|"
    r"\b(?:входные\s+данные|исходные\s+данные|inputs?)\b)"
)
SEMANTIC_INPUT_RE = re.compile(
    r"(?i)\b(?:эксперимент\w*|измерен\w*|наблюден\w*|результат\w*|"
    r"сигнал\w*|выборк\w*|расч[её]т\w*|модел\w*|объект\w*|образц\w*|"
    r"протокол\w*|испытан\w*|регистрац\w*|measurement\w*|experiment\w*|"
    r"simulation\w*|model\w*|result\w*)\b"
)
PASSPORT_HEADING_RE = re.compile(r"(?im)^\s*#{1,4}\s*паспорт(?:\s|$)")
READER_METADATA_RE = re.compile(
    r"(?im)^\s*(?:#{1,4}\s*)?(?:\*\*)?(?:среда(?:\s+выполнения)?|"
    r"наследуемое\s+состояние|манифест\s+запуска)(?:\*\*)?\s*:?")
FORMULA_CATALOG_HEADING_RE = re.compile(
    r"(?im)^\s*#{1,4}\s*(?:формул\w*|уравнен\w*|математическ\w*\s+аппарат)\b"
)
TERM_GLOSSARY_HEADING_RE = re.compile(
    r"(?im)^\s*#{1,4}[^\n]*\bсловар[ья]\s+термин\w*\b"
)
MATERIAL_EQUATION_RE = re.compile(r"\\tag\{[^}]+\}")
DISPLAY_EQUATION_RE = re.compile(r"\$\$.*?\$\$|\\\[.*?\\\]", re.DOTALL)
FORMULA_TABLE_ROW_RE = re.compile(r"(?m)^\s*\|[^|\n]*\$[^|\n]*\$")
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
    r"мВ|В|кВ|мА|А|мОм|Ом(?:[·⋅]м)?|кОм|МОм|Па|кПа|МПа|мВт|Вт|кВт|"
    r"мДж|Дж|мг|г|кг|мкл|мл|л|"
    r"раз(?:а|ов)?|объект\w*|наблюден\w*|образц\w*|единиц\w*)\b",
    re.IGNORECASE,
)
DIMENSIONLESS_RE = re.compile(
    r"(?i)(?:\b[pnr]\s*=|R[²2]\s*=|безразмерн\w*|dimensionless)"
)

DYNAMIC_MARKDOWN_RE = re.compile(
    r"(?is)\b(?:Markdown|display_markdown|render_markdown)\s*\(\s*(?:f[\"']|[A-Za-z_]\w*)"
)
FROZEN_TEXT_FIELDS = ("run_id", "executed_at", "code_version", "environment")
RUSSIAN_RE = re.compile(r"[А-Яа-яЁё]")
VALID_ARTIFACT_STATUSES = {"working", "frozen"}
VALID_EXECUTION_STATUSES = {"not_run", "partial", "clean_kernel_pass", "failed"}
VALID_STUDY_TYPES = {"computational", "empirical", "mixed"}
VALID_LANGUAGE_AUDIT_STATUSES = {"not_run", "passed", "failed"}
VALID_GENRE_PROFILES = {
    "model-derivation",
    "computational-verification",
    "inverse-estimation",
    "empirical-analysis",
    "experiment-diagnostic",
    "synthesis-decision",
    "engineering-transfer",
}
PROFILE_TAG_REQUIREMENTS = {
    "model-derivation": {"equation-narrative", "verification-checks"},
    "computational-verification": {"verification-checks"},
    "inverse-estimation": {"identifiability-check", "verification-checks"},
    "empirical-analysis": {
        "experiment-context",
        "experiment-procedure",
        "experimental-observation",
        "experimental-analysis",
        "selection-policy",
    },
    "experiment-diagnostic": {
        "experiment-context",
        "experiment-procedure",
        "experimental-observation",
        "experimental-analysis",
        "verification-checks",
    },
    "synthesis-decision": {"decision-basis", "artifact-handoff"},
    "engineering-transfer": {"artifact-handoff", "acceptance-criterion"},
}
VALID_TECHNICAL_VALIDATION_STATUSES = {
    "not_checked", "passed", "failed", "blocked"
}
VALID_COMPUTATIONAL_VALIDATION_STATUSES = {
    "not_checked", "partial", "passed", "failed", "blocked"
}
VALID_SCIENTIFIC_VALIDATION_STATUSES = {
    "not_reviewed", "bounded", "approved", "rejected", "conflicted"
}
VALID_BIBLIOGRAPHY_STATUSES = {"not_applicable", "incomplete", "complete"}
VALID_SELECTION_POLICY_STATUSES = {"not_applicable", "clear", "conflicted", "resolved"}
VALID_AUTOMATION_STATUSES = {"blocked", "permitted"}
EXPERIMENT_TAG_REQUIREMENTS = {
    "experiment-context": (
        "NB-EXP-001",
        "Experiment source, purpose, object, conditions, and recorded variables are not identified.",
    ),
    "experiment-procedure": (
        "NB-EXP-002",
        "Planned and actually performed experimental procedure are not distinguished.",
    ),
    "experimental-observation": (
        "NB-EXP-003",
        "Actual experimental observation or result is not identified.",
    ),
    "experimental-analysis": (
        "NB-EXP-004",
        "Analysis and limits of the experimental result are not identified.",
    ),
}


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
    """Measure textual payloads while ignoring expected binary figure data."""
    outputs = cell.get("outputs", [])
    if not isinstance(outputs, list):
        return 0, 0
    parts: list[str] = []
    for output in outputs:
        if not isinstance(output, dict):
            continue
        if output.get("output_type") == "stream":
            parts.append(str(output.get("text", "")))
        if output.get("output_type") == "error":
            parts.extend(str(item) for item in output.get("traceback", []))
        data = output.get("data", {})
        if isinstance(data, dict):
            for mime, value in data.items():
                if mime.startswith("text/") or mime in {"application/json", "application/latex"}:
                    parts.append(json.dumps(value, ensure_ascii=False))
    rendered = "\n".join(parts)
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
    function_cells: dict[str, set[int]] = {
        "notebook-role": set(),
        "research-question": set(),
        "notebook-scope": set(),
        "completion-criterion": set(),
        "material-inputs": set(),
        "technical-background": set(),
        "method-and-assumptions": set(),
        "observable-output": set(),
        "calculation-chain": set(),
        "result-status": set(),
        "interpretation-and-limits": set(),
        "report-summary": set(),
        "computed-narrative": set(),
    }
    all_tags: set[str] = set()

    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            findings.append(
                _finding("NB-STRUCT-002", "error", "Cell must be an object.", cell_index=index)
            )
            continue
        cell_type = cell.get("cell_type")
        text = _source_text(cell)
        tags = _tags(cell)
        all_tags.update(tags)
        for tag, target in function_cells.items():
            if tag in tags:
                target.add(index)
        if cell_type == "markdown":
            markdown_cells.append((index, cell, text))
            if ROLE_RE.search(text):
                function_cells["notebook-role"].add(index)
            if QUESTION_RE.search(text):
                function_cells["research-question"].add(index)
            if SUMMARY_RE.search(text):
                function_cells["report-summary"].add(index)
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
    role_cells = function_cells["notebook-role"]
    question_cells = function_cells["research-question"]
    scope_cells = function_cells["notebook-scope"]
    completion_cells = function_cells["completion-criterion"]
    input_cells = function_cells["material-inputs"]
    background_cells = function_cells["technical-background"]
    method_cells = function_cells["method-and-assumptions"]
    observable_cells = function_cells["observable-output"]
    calculation_cells = function_cells["calculation-chain"]
    result_status_cells = function_cells["result-status"]
    limit_cells = function_cells["interpretation-and-limits"]
    summary_cells = function_cells["report-summary"]
    computed_narrative_cells = function_cells["computed-narrative"]

    required_markers = (
        (role_cells, "NB-NARR-008", "The notebook's applied role is not identifiable."),
        (question_cells, "NB-NARR-001", "Research question or task is not identifiable."),
        (
            scope_cells or SCOPE_RE.search(markdown),
            "NB-NARR-002",
            "Scope and excluded checks are not stated.",
        ),
        (
            completion_cells or COMPLETION_RE.search(markdown),
            "NB-NARR-003",
            "Completion criterion is not stated.",
        ),
        (
            input_cells or INPUT_RE.search(markdown),
            "NB-NARR-004",
            "Material inputs are not identified.",
        ),
        (
            background_cells,
            "NB-NARR-016",
            "Investigated object, model, terms, quantities, equations, conditions, or applicability limits are not identified.",
        ),
        (
            method_cells or METHOD_RE.search(markdown),
            "NB-NARR-005",
            "Method or material assumptions are not stated before interpretation.",
        ),
        (
            calculation_cells,
            "NB-NARR-011",
            "Traceable calculation-chain logic is not identified.",
        ),
        (
            result_status_cells,
            "NB-NARR-012",
            "No scientific status is attached to a material result.",
        ),
        (
            observable_cells,
            "NB-NARR-010",
            "No post-calculation observation or bounded result is identifiable.",
        ),
        (summary_cells, "NB-NARR-006", "Bounded final summary is not identifiable."),
        (
            limit_cells or LIMIT_RE.search(markdown),
            "NB-NARR-007",
            "Limitations or what was not established are not stated.",
        ),
        (
            computed_narrative_cells,
            "NB-NARR-009",
            "No computed-narrative cell renders result prose from current variables.",
        ),
    )
    for observed, rule_id, message in required_markers:
        if not observed:
            findings.append(_finding(rule_id, "error", message))

    for index, _, text in markdown_cells:
        equation_count = max(
            len(MATERIAL_EQUATION_RE.findall(text)),
            len(DISPLAY_EQUATION_RE.findall(text)),
            len(FORMULA_TABLE_ROW_RE.findall(text)),
        )
        formula_catalog = bool(FORMULA_CATALOG_HEADING_RE.search(text))
        glossary_bundle = bool(TERM_GLOSSARY_HEADING_RE.search(text)) and equation_count >= 2
        if (formula_catalog and equation_count >= 2) or glossary_bundle:
            findings.append(
                _finding(
                    "NB-NARR-018",
                    "error",
                    "Material equations are front-loaded as a catalogue or glossary. "
                    "Introduce each equation at the calculation stage where it first becomes necessary.",
                    cell_index=index,
                )
            )
        if PASSPORT_HEADING_RE.search(text):
            findings.append(
                _finding(
                    "NB-NARR-014",
                    "error",
                    "A reader-facing passport is a metadata form, not a scientific and technical report opening.",
                    cell_index=index,
                )
            )
        if READER_METADATA_RE.search(text):
            findings.append(
                _finding(
                    "NB-NARR-017",
                    "error",
                    "Environment, inherited state, or run-manifest metadata must not be a reader-facing report rubric.",
                    cell_index=index,
                )
            )

    if input_cells:
        input_text = "\n".join(_source_text(cells[index]) for index in input_cells)
        if not SEMANTIC_INPUT_RE.search(input_text):
            findings.append(
                _finding(
                    "NB-NARR-015",
                    "error",
                    "Material inputs are described only by technical locators; identify the experiment, observation, model, or calculation that produced them.",
                )
            )

    ordered_stage_sets = (
        input_cells,
        background_cells | method_cells | calculation_cells,
        observable_cells,
        summary_cells,
    )
    if all(ordered_stage_sets):
        positions = [min(stage) for stage in ordered_stage_sets]
        if not (positions[0] < positions[1] < positions[2] <= positions[3]):
            findings.append(
                _finding(
                    "NB-NARR-013",
                    "error",
                    "Calculation stages are not in traceable narrative order.",
                )
            )

    if len(question_cells) > 1:
        findings.append(
            _finding(
                "NB-SPLIT-001",
                "warning",
                "Multiple marked research questions or tasks were found; inspect whether they are independent before recommending a split.",
            )
        )

    for index in computed_narrative_cells:
        cell = cells[index]
        text = _source_text(cell)
        if cell.get("cell_type") != "code":
            findings.append(
                _finding(
                    "NB-NUMBER-003",
                    "error",
                    "The computed-narrative tag must be attached to a code cell.",
                    cell_index=index,
                )
            )
        elif not DYNAMIC_MARKDOWN_RE.search(text):
            findings.append(
                _finding(
                    "NB-NUMBER-003",
                    "error",
                    "A computed-narrative cell must render Markdown from a variable or formatted expression.",
                    cell_index=index,
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
        following_tags = _tags(following) if isinstance(following, dict) else set()
        following_text = _source_text(following) if isinstance(following, dict) else ""
        current_tags = _tags(cell)
        has_account = (
            "observable-output" in current_tags
            or "observable-output" in following_tags
            or bool(
                re.search(
                    r"(?i)\b(?:наблюден\w*|интерпретац\w*|ограничен\w*|"
                    r"observation|interpretation|limitation|figure|рисунок)\b",
                    following_text,
                )
            )
        )
        has_caption = (
            "figure-caption" in current_tags or "figure-caption" in following_tags
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
        if not has_caption:
            findings.append(
                _finding(
                    "NB-FIGURE-001",
                    "error",
                    "Plot output has no semantically marked figure caption.",
                    cell_index=index,
                )
            )

    for index, _, text in markdown_cells:
        if index not in summary_cells | observable_cells:
            continue
        if NUMBER_RE.search(text):
            findings.append(
                _finding(
                    "NB-NUMBER-002",
                    "error",
                    "A material result number is stored in static Markdown; render it from the result variable.",
                    cell_index=index,
                )
            )
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
    narrative_text = "\n".join(text for _, _, text in markdown_cells + code_cells)
    russian_narrative = bool(RUSSIAN_RE.search(narrative_text))

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
        study_type = report_metadata.get("study_type")
        if study_type is not None and study_type not in VALID_STUDY_TYPES:
            findings.append(
                _finding(
                    "NB-REPRO-002",
                    "error",
                    f"Unknown study_type {study_type!r}.",
                )
            )

        genre_profile = report_metadata.get("genre_profile")
        if genre_profile not in VALID_GENRE_PROFILES:
            findings.append(
                _finding(
                    "NB-GENRE-001",
                    "error",
                    f"Unknown or missing genre_profile {genre_profile!r}.",
                )
            )
        else:
            missing_profile_tags = sorted(
                PROFILE_TAG_REQUIREMENTS[genre_profile] - all_tags
            )
            if missing_profile_tags:
                findings.append(
                    _finding(
                        "NB-GENRE-002",
                        "error",
                        "Genre profile requires semantic tags: "
                        + ", ".join(missing_profile_tags)
                        + ".",
                    )
                )

        validation_fields = (
            (
                "technical_validation_status",
                VALID_TECHNICAL_VALIDATION_STATUSES,
            ),
            (
                "computational_validation_status",
                VALID_COMPUTATIONAL_VALIDATION_STATUSES,
            ),
            (
                "scientific_validation_status",
                VALID_SCIENTIFIC_VALIDATION_STATUSES,
            ),
        )
        for field, allowed in validation_fields:
            value = report_metadata.get(field)
            if value not in allowed:
                findings.append(
                    _finding(
                        "NB-VALID-001",
                        "error",
                        f"Unknown or missing {field} {value!r}.",
                    )
                )

        bibliography_status = report_metadata.get("bibliography_status")
        if bibliography_status not in VALID_BIBLIOGRAPHY_STATUSES:
            findings.append(
                _finding(
                    "NB-BIB-001",
                    "error",
                    f"Unknown or missing bibliography_status {bibliography_status!r}.",
                )
            )

        selection_status = report_metadata.get("selection_policy_status")
        resolution_ref = report_metadata.get("selection_resolution_ref")
        automation_status = report_metadata.get("automation_status")
        if selection_status not in VALID_SELECTION_POLICY_STATUSES:
            findings.append(
                _finding(
                    "NB-AUTO-001",
                    "error",
                    f"Unknown or missing selection_policy_status {selection_status!r}.",
                )
            )
        if automation_status not in VALID_AUTOMATION_STATUSES:
            findings.append(
                _finding(
                    "NB-AUTO-001",
                    "error",
                    f"Unknown or missing automation_status {automation_status!r}.",
                )
            )
        if (
            selection_status in {"not_applicable", "clear"}
            and resolution_ref is not None
        ):
            findings.append(
                _finding(
                    "NB-AUTO-002",
                    "error",
                    "A selection policy without a recorded conflict must use "
                    "selection_resolution_ref null.",
                )
            )
        if selection_status == "resolved" and (
            not isinstance(resolution_ref, str) or not resolution_ref.strip()
        ):
            findings.append(
                _finding(
                    "NB-AUTO-002",
                    "error",
                    "Resolved selection policy requires selection_resolution_ref.",
                )
            )
        if selection_status == "conflicted" and automation_status != "blocked":
            findings.append(
                _finding(
                    "NB-AUTO-002",
                    "error",
                    "Conflicting data-selection rules require automation_status 'blocked'.",
                )
            )
        if automation_status == "permitted":
            ready_for_automation = (
                report_metadata.get("technical_validation_status") == "passed"
                and report_metadata.get("computational_validation_status") == "passed"
                and report_metadata.get("scientific_validation_status")
                in {"bounded", "approved"}
                and selection_status != "conflicted"
            )
            if not ready_for_automation:
                findings.append(
                    _finding(
                        "NB-AUTO-003",
                        "error",
                        "Automation may be permitted only after all validation axes pass "
                        "and data-selection rules are not conflicted.",
                    )
                )

        empirical_tags = set(EXPERIMENT_TAG_REQUIREMENTS)
        if russian_narrative:
            narrative_language = report_metadata.get("narrative_language")
            language_profile = report_metadata.get("language_profile")
            language_audit_status = report_metadata.get("language_audit_status")
            if narrative_language != "ru":
                findings.append(
                    _finding(
                        "NB-LANG-001",
                        "error",
                        "Russian notebook narrative requires narrative_language 'ru'.",
                    )
                )
            if language_profile != "genre-notebook":
                findings.append(
                    _finding(
                        "NB-LANG-002",
                        "error",
                        "Russian notebook narrative requires language_profile 'genre-notebook'.",
                    )
                )
            if language_audit_status not in VALID_LANGUAGE_AUDIT_STATUSES:
                findings.append(
                    _finding(
                        "NB-LANG-003",
                        "error",
                        "Russian notebook narrative requires a valid language_audit_status.",
                    )
                )
            elif language_audit_status == "failed":
                findings.append(
                    _finding(
                        "NB-LANG-004",
                        "error",
                        "Russian language audit has unresolved errors.",
                    )
                )
            elif artifact_status == "frozen" and language_audit_status != "passed":
                findings.append(
                    _finding(
                        "NB-LANG-004",
                        "error",
                        "Frozen Russian notebook requires a passed language audit.",
                    )
                )

        empirical_account = study_type in {"empirical", "mixed"} or bool(
            empirical_tags & all_tags
        )
        if empirical_account:
            for tag, (rule_id, message) in EXPERIMENT_TAG_REQUIREMENTS.items():
                if tag not in all_tags:
                    findings.append(_finding(rule_id, "error", message))

        if artifact_status == "frozen":
            for field in FROZEN_TEXT_FIELDS:
                value = report_metadata.get(field)
                if not isinstance(value, str) or not value.strip():
                    findings.append(
                        _finding(
                            "NB-REPRO-002",
                            "error",
                            f"Frozen snapshot requires non-empty {field}.",
                        )
                    )
            inputs = report_metadata.get("significant_inputs")
            if not isinstance(inputs, list) or not inputs:
                findings.append(
                    _finding(
                        "NB-REPRO-002",
                        "error",
                        "Frozen snapshot requires a non-empty significant_inputs list.",
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
            if report_metadata.get("technical_validation_status") != "passed":
                findings.append(
                    _finding(
                        "NB-VALID-002",
                        "error",
                        "Frozen snapshot requires technical_validation_status 'passed'.",
                    )
                )
            if report_metadata.get("computational_validation_status") != "passed":
                findings.append(
                    _finding(
                        "NB-VALID-002",
                        "error",
                        "Frozen snapshot requires computational_validation_status 'passed'.",
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
            "current_upstream_resolution",
            "cross_notebook_chain_truth",
            "russian_language_quality_beyond_heuristics",
            "bibliographic_semantic_correctness",
            "selection_policy_truth",
            "validation_status_attestation",
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
