"""Small helpers shared by deterministic dissertation apparatus auditors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def finding(
    issue_id: str,
    rule_id: str,
    module: str,
    observed: Any,
    expected: Any,
    *,
    exact_text: str | None = None,
    occurrence: int = 1,
    severity: str = "minor",
    issue_class: str = "internal_inconsistency",
    authority_ids: list[str] | None = None,
    evidence_ids: list[str] | None = None,
    suggested_fix: Any = None,
    autofix_safe: bool = False,
    word_action: str = "comment",
) -> dict[str, Any]:
    locator = None
    if exact_text:
        locator = {"kind": "text", "exact_text": exact_text, "occurrence": occurrence}
    elif word_action != "none":
        word_action = "none"
    return {
        "issue_id": issue_id,
        "rule_id": rule_id,
        "module": module,
        "severity": severity,
        "issue_class": issue_class,
        "locator": locator,
        "observed": observed,
        "expected": expected,
        "authority_ids": authority_ids or [],
        "evidence_ids": evidence_ids or [],
        "suggested_fix": suggested_fix,
        "confidence": 1.0,
        "autofix_safe": autofix_safe,
        "word_action": word_action,
    }


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_envelope(findings: list[dict[str, Any]], output: Path | None = None) -> str:
    rendered = json.dumps(
        {"schema_version": "PSES-DISS-001/v1", "findings": findings},
        ensure_ascii=False,
        indent=2,
    ) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    return rendered
