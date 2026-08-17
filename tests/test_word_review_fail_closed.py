from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dissertation-formatting-and-apparatus" / "scripts"


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = load("word_fail_closed_validator", "validate_critic_findings.py")
REVIEW = load("apply_word_review", "apply_word_review.py")


def canonical_change(*, old: str, new: str, exact_text: str) -> dict:
    return {
        "issue_id": "ISSUE-1",
        "rule_id": "RULE-1",
        "module": "word-review",
        "severity": "major",
        "issue_class": "internal_inconsistency",
        "locator": {"kind": "text", "exact_text": exact_text, "occurrence": 1},
        "observed": old,
        "expected": new,
        "authority_ids": [],
        "evidence_ids": [],
        "suggested_fix": {"old": old, "new": new, "rationale": "Exact replacement"},
        "confidence": 1.0,
        "autofix_safe": True,
        "word_action": "tracked_change",
    }


def test_tracked_change_rejects_noop_and_locator_mismatch() -> None:
    noop = VALIDATOR.validate_finding(canonical_change(old="text", new="text", exact_text="text"))
    mismatch = VALIDATOR.validate_finding(
        canonical_change(old="other", new="replacement", exact_text="text")
    )

    assert {item["code"] for item in noop["errors"]} >= {"TRACKED_CHANGE_NOOP"}
    assert {item["code"] for item in mismatch["errors"]} >= {"TRACKED_CHANGE_LOCATOR_MISMATCH"}


def test_direct_word_adapter_rejects_noncanonical_tracked_change_before_reading_docx(
    tmp_path: Path,
) -> None:
    malformed = {
        "issue_id": "ISSUE-1",
        "word_action": "tracked_change",
        "locator": {"exact_text": "text", "occurrence": 1},
        "suggested_fix": "replace it",
    }

    with pytest.raises(REVIEW.ReviewError, match="PSES journal validation failed"):
        REVIEW.apply_review(
            tmp_path / "missing-source.docx",
            [malformed],
            tmp_path / "must-not-exist.docx",
        )

    assert not (tmp_path / "must-not-exist.docx").exists()


def test_direct_word_adapter_rejects_missing_word_action_before_reading_docx(
    tmp_path: Path,
) -> None:
    malformed = canonical_change(old="text", new="replacement", exact_text="text")
    malformed.pop("word_action")

    with pytest.raises(REVIEW.ReviewError, match="word_action must be explicitly set"):
        REVIEW.apply_review(
            tmp_path / "missing-source.docx",
            [malformed],
            tmp_path / "must-not-exist.docx",
        )

    assert not (tmp_path / "must-not-exist.docx").exists()
