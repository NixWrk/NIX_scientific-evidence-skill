"""Validate a PSES-DISS-001 critic journal without external services.

The JSON schema is useful to hosts that only perform structural validation.  This
module is the semantic gate used by the benchmark and by Word adapters.  It
keeps the two safety rules that are easiest to lose in a generic JSON schema:

* a normative violation must name an applicable, versioned authority; and
* a tracked change must carry an exact old/new replacement and an exact Word
  anchor (including the occurrence of repeated text).

The validator accepts the canonical ``{"findings": [...]}`` envelope, a bare
array, or one finding.  The latter two forms make it possible to validate a
streaming adapter while the envelope remains the interchange format.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
SEVERITIES = {"critical", "major", "minor", "note"}
ISSUE_CLASSES = {
    "normative_violation",
    "internal_inconsistency",
    "evidence_gap",
    "observed_practice_difference",
    "recommendation",
}
WORD_ACTIONS = {"none", "comment", "tracked_change", "tracked_change_with_comment"}
FINDING_FIELDS = {
    "issue_id",
    "rule_id",
    "module",
    "severity",
    "issue_class",
    "locator",
    "observed",
    "expected",
    "authority_ids",
    "evidence_ids",
    "suggested_fix",
    "confidence",
    "autofix_safe",
    "word_action",
}
LOCATOR_FIELDS = {
    "kind",
    "document",
    "section",
    "page",
    "paragraph",
    "char_start",
    "char_end",
    "exact_text",
    "occurrence",
}
FIX_FIELDS = {"old", "new", "rationale"}
WORD_ACTIONS_WITH_ANCHOR = {"comment", "tracked_change", "tracked_change_with_comment"}
TRACKED_ACTIONS = {"tracked_change", "tracked_change_with_comment"}


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_identifier(value: Any) -> bool:
    return isinstance(value, str) and bool(ID_PATTERN.fullmatch(value))


def _error(code: str, path: str, detail: str) -> dict[str, str]:
    return {"code": code, "path": path, "detail": detail}


def _warning(code: str, path: str, detail: str) -> dict[str, str]:
    return {"code": code, "path": path, "detail": detail}


def _validate_ids(value: Any, path: str, errors: list[dict[str, str]]) -> None:
    if not isinstance(value, list):
        errors.append(_error("TYPE", path, "expected an array of identifiers"))
        return
    seen: set[str] = set()
    for index, identifier in enumerate(value):
        item_path = f"{path}[{index}]"
        if not _is_identifier(identifier):
            errors.append(_error("IDENTIFIER", item_path, "expected a non-empty identifier"))
        elif identifier in seen:
            errors.append(_error("DUPLICATE_ID", item_path, f"duplicate identifier {identifier!r}"))
        seen.add(identifier)


def _validate_locator(locator: Any, path: str, errors: list[dict[str, str]]) -> None:
    if locator is None:
        return
    if isinstance(locator, str):
        if not locator.strip():
            errors.append(_error("LOCATOR", path, "a string locator must not be empty"))
        return
    if not isinstance(locator, dict):
        errors.append(_error("TYPE", path, "expected null, a string, or a locator object"))
        return

    for key in sorted(set(locator) - LOCATOR_FIELDS):
        errors.append(_error("UNEXPECTED_FIELD", f"{path}.{key}", "unknown locator field"))

    if "exact_text" in locator and not _nonempty_string(locator["exact_text"]):
        errors.append(_error("LOCATOR_EXACT_TEXT", f"{path}.exact_text", "must be a non-empty string"))
    if "occurrence" in locator:
        occurrence = locator["occurrence"]
        if isinstance(occurrence, bool) or not isinstance(occurrence, int) or occurrence < 1:
            errors.append(_error("LOCATOR_OCCURRENCE", f"{path}.occurrence", "must be an integer >= 1"))
    if ("exact_text" in locator) != ("occurrence" in locator):
        errors.append(
            _error(
                "LOCATOR_PAIR",
                path,
                "exact_text and occurrence must be supplied together",
            )
        )

    for key in ("document", "section", "kind"):
        if key in locator and not _nonempty_string(locator[key]):
            errors.append(_error("LOCATOR_FIELD", f"{path}.{key}", "must be a non-empty string"))
    for key in ("page", "paragraph", "char_start", "char_end"):
        if key in locator:
            value = locator[key]
            minimum = 1 if key in {"page", "paragraph"} else 0
            if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
                errors.append(
                    _error(
                        "LOCATOR_FIELD",
                        f"{path}.{key}",
                        f"must be an integer >= {minimum}",
                    )
                )
    if (
        isinstance(locator.get("char_start"), int)
        and isinstance(locator.get("char_end"), int)
        and locator["char_end"] < locator["char_start"]
    ):
        errors.append(_error("LOCATOR_RANGE", path, "char_end must not precede char_start"))


def _validate_fix(fix: Any, path: str, errors: list[dict[str, str]]) -> None:
    if fix is None:
        return
    if isinstance(fix, str):
        if not fix.strip():
            errors.append(_error("FIX", path, "a string suggestion must not be empty"))
        return
    if not isinstance(fix, dict):
        errors.append(_error("TYPE", path, "expected null, a string, or an old/new object"))
        return
    for key in sorted(set(fix) - FIX_FIELDS):
        errors.append(_error("UNEXPECTED_FIELD", f"{path}.{key}", "unknown suggested_fix field"))
    for key in ("old", "new"):
        if key in fix and not _nonempty_string(fix[key]):
            errors.append(_error("FIX_TEXT", f"{path}.{key}", "must be a non-empty string"))
    if "rationale" in fix and not _nonempty_string(fix["rationale"]):
        errors.append(_error("FIX_RATIONALE", f"{path}.rationale", "must be a non-empty string"))


def validate_finding(finding: Any, *, path: str = "finding") -> dict[str, Any]:
    """Validate one finding and return structured errors/warnings.

    ``valid`` is false for both structural errors and the PSES semantic safety
    rules.  Keeping codes alongside human-readable details lets the benchmark
    report stop-errors without scraping prose.
    """

    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    if not isinstance(finding, dict):
        return {
            "valid": False,
            "errors": [_error("TYPE", path, "expected an object")],
            "warnings": [],
        }

    for key in sorted(set(finding) - FINDING_FIELDS):
        errors.append(_error("UNEXPECTED_FIELD", f"{path}.{key}", "unknown finding field"))
    for key in ("issue_id", "rule_id", "module"):
        if not _nonempty_string(finding.get(key)):
            errors.append(_error("REQUIRED", f"{path}.{key}", "must be a non-empty string"))
    for key in ("issue_id", "rule_id"):
        if _nonempty_string(finding.get(key)) and not _is_identifier(finding[key]):
            errors.append(_error("IDENTIFIER", f"{path}.{key}", "invalid identifier"))

    if finding.get("severity") not in SEVERITIES:
        errors.append(_error("ENUM", f"{path}.severity", f"expected one of {sorted(SEVERITIES)}"))
    if finding.get("issue_class") not in ISSUE_CLASSES:
        errors.append(
            _error(
                "ENUM",
                f"{path}.issue_class",
                f"expected one of {sorted(ISSUE_CLASSES)}",
            )
        )
    if finding.get("word_action") not in WORD_ACTIONS:
        errors.append(
            _error(
                "ENUM",
                f"{path}.word_action",
                f"expected one of {sorted(WORD_ACTIONS)}",
            )
        )

    _validate_locator(finding.get("locator"), f"{path}.locator", errors)
    _validate_ids(finding.get("authority_ids"), f"{path}.authority_ids", errors)
    _validate_ids(finding.get("evidence_ids"), f"{path}.evidence_ids", errors)
    _validate_fix(finding.get("suggested_fix"), f"{path}.suggested_fix", errors)

    confidence = finding.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        errors.append(_error("CONFIDENCE", f"{path}.confidence", "must be a number between 0 and 1"))
    if not isinstance(finding.get("autofix_safe"), bool):
        errors.append(_error("TYPE", f"{path}.autofix_safe", "must be boolean"))

    word_action = finding.get("word_action")
    locator = finding.get("locator")
    if word_action in WORD_ACTIONS_WITH_ANCHOR:
        if not isinstance(locator, dict):
            errors.append(
                _error(
                    "WORD_ANCHOR_REQUIRED",
                    f"{path}.locator",
                    "Word comments and changes require an object anchor with exact_text and occurrence",
                )
            )
        else:
            if not _nonempty_string(locator.get("exact_text")):
                errors.append(
                    _error(
                        "WORD_EXACT_TEXT_REQUIRED",
                        f"{path}.locator.exact_text",
                        "Word actions require the exact anchor text",
                    )
                )
            occurrence = locator.get("occurrence")
            if isinstance(occurrence, bool) or not isinstance(occurrence, int) or occurrence < 1:
                errors.append(
                    _error(
                        "WORD_OCCURRENCE_REQUIRED",
                        f"{path}.locator.occurrence",
                        "Word actions require a positive occurrence number",
                    )
                )

    if word_action in TRACKED_ACTIONS:
        fix = finding.get("suggested_fix")
        if not isinstance(fix, dict) or not _nonempty_string(fix.get("old")) or not _nonempty_string(fix.get("new")):
            errors.append(
                _error(
                    "TRACKED_CHANGE_EXACT_REPLACEMENT_REQUIRED",
                    f"{path}.suggested_fix",
                    "tracked changes require non-empty exact old and new strings",
                )
            )

    if finding.get("issue_class") == "normative_violation":
        authorities = finding.get("authority_ids")
        if not isinstance(authorities, list) or not authorities:
            errors.append(
                _error(
                    "NORMATIVE_AUTHORITY_REQUIRED",
                    f"{path}.authority_ids",
                    "normative_violation requires at least one authority_id",
                )
            )

    if finding.get("autofix_safe") is True and finding.get("suggested_fix") is None:
        warnings.append(
            _warning(
                "AUTOFIX_WITHOUT_SUGGESTION",
                f"{path}.suggested_fix",
                "autofix_safe is true but no suggested_fix was recorded",
            )
        )

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def _extract_findings(payload: Any) -> tuple[list[Any], list[dict[str, str]]]:
    if isinstance(payload, list):
        return payload, []
    if isinstance(payload, dict) and "findings" in payload:
        findings = payload["findings"]
        if not isinstance(findings, list):
            return [], [_error("TYPE", "findings", "expected an array")]
        return findings, []
    if isinstance(payload, dict) and "issue_id" in payload:
        return [payload], []
    return [], [_error("CONTAINER", "root", "expected a findings envelope, array, or finding")]


def validate_findings(payload: Any) -> dict[str, Any]:
    """Validate a findings payload, including journal-level ID uniqueness."""

    findings, container_errors = _extract_findings(payload)
    errors: list[dict[str, str]] = list(container_errors)
    warnings: list[dict[str, str]] = []
    seen: set[str] = set()
    valid_findings = 0
    for index, finding in enumerate(findings):
        result = validate_finding(finding, path=f"findings[{index}]")
        errors.extend(result["errors"])
        warnings.extend(result["warnings"])
        if result["valid"]:
            valid_findings += 1
        if isinstance(finding, dict) and _nonempty_string(finding.get("issue_id")):
            issue_id = finding["issue_id"]
            if issue_id in seen:
                errors.append(
                    _error(
                        "DUPLICATE_ISSUE_ID",
                        f"findings[{index}].issue_id",
                        f"issue_id {issue_id!r} is not unique within this journal",
                    )
                )
            seen.add(issue_id)

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "findings": len(findings),
            "valid_findings": valid_findings,
            "errors": len(errors),
            "warnings": len(warnings),
        },
    }


def read_payload(path: Path) -> Any:
    """Read JSON or JSONL (one envelope/finding per line) using UTF-8/BOM."""

    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".jsonl":
        records: list[Any] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: {error}") from error
        return records
    return json.loads(text)


def render_report(report: dict[str, Any]) -> str:
    return json.dumps(report, ensure_ascii=False, indent=2) + "\n"


def main(argv: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("findings", type=Path, help="JSON or JSONL findings journal")
    parser.add_argument("--output", type=Path, help="Optional validation report path")
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        report = validate_findings(read_payload(args.findings))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        report = {
            "valid": False,
            "errors": [_error("READ", str(args.findings), str(error))],
            "warnings": [],
            "counts": {"findings": 0, "valid_findings": 0, "errors": 1, "warnings": 0},
        }

    rendered = render_report(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
