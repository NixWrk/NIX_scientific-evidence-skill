from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dissertation-formatting-and-apparatus" / "scripts"
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location(
    "abbreviation_lowercase_definition", SCRIPTS / "audit_abbreviations.py"
)
assert SPEC and SPEC.loader
ABBR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ABBR)


def test_lowercase_in_sentence_definition_closes_abbreviation() -> None:
    findings = ABBR.audit(
        "В исследовании использован метод спектрального анализа (МСА). Затем МСА применён повторно."
    )

    assert not [
        item
        for item in findings
        if item["rule_id"] == "ABBR-001" and item["observed"] == "МСА"
    ]
