from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dissertation-formatting-and-apparatus" / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "bibliography_fail_closed", SCRIPTS / "audit_bibliography.py"
)
assert SPEC and SPEC.loader
BIB = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BIB)


def test_malformed_record_cannot_pass_with_only_record_id() -> None:
    findings = BIB.audit(
        {"profile": {"sorting_strategy": "unspecified"}, "records": [{"record_id": "R1"}], "in_text_citations": []}
    )

    assert "BIB-007" in {item["rule_id"] for item in findings}


def test_duplicate_record_ids_are_reported_before_resolution() -> None:
    record = {"record_id": "R1", "type": "article", "title": "Title"}
    findings = BIB.audit(
        {"profile": {"sorting_strategy": "unspecified"}, "records": [record, dict(record)], "in_text_citations": []}
    )

    assert "BIB-008" in {item["rule_id"] for item in findings}


def test_numeric_citation_display_must_match_record_number() -> None:
    findings = BIB.audit(
        {
            "profile": {"sorting_strategy": "unspecified", "sequential_numbering": True},
            "records": [{"record_id": "R1", "number": 1, "type": "article", "title": "Title"}],
            "in_text_citations": [{"record_id": "R1", "order": 1, "display": "[999]"}],
        }
    )

    assert "BIB-009" in {item["rule_id"] for item in findings}


def test_unknown_sorting_strategy_is_not_silently_ignored() -> None:
    findings = BIB.audit(
        {
            "profile": {"sorting_strategy": "magic"},
            "records": [{"record_id": "R1", "type": "article", "title": "Title"}],
            "in_text_citations": [],
        }
    )

    assert "BIB-010" in {item["rule_id"] for item in findings}
