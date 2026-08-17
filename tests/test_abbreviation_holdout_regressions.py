from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dissertation-formatting-and-apparatus" / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "abbreviation_holdout_regressions", SCRIPTS / "audit_abbreviations.py"
)
assert SPEC and SPEC.loader
ABBR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ABBR)


def test_repeated_undefined_abbreviation_produces_one_finding() -> None:
    findings = ABBR.audit("КПРЭГ рассчитан. КПРЭГ сравнен. КПРЭГ повторен.")

    undefined = [item for item in findings if item["rule_id"] == "ABBR-001"]
    assert [item["observed"] for item in undefined] == ["КПРЭГ"]


def test_parenthesized_channel_descriptions_do_not_create_false_conflict() -> None:
    text = (
        "В клинической практике основными являются фронто-мастоидальные (FM) отведения. "
        "Далее использованы фронто-мастоидальные отведения (FM)."
    )

    findings = ABBR.audit(text)

    assert "ABBR-003" not in {item["rule_id"] for item in findings}


def test_roman_numerals_and_digit_channel_identifiers_are_not_abbreviations() -> None:
    findings = ABBR.audit("В разделе VIII исследованы каналы TT1 и FF1.")

    assert "ABBR-001" not in {item["rule_id"] for item in findings}
