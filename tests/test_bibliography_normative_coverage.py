"""Regression tests for bibliography normative coverage v3."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD_DIR = ROOT / "skills/scientific-evidence-workflow/references/normative-patterns"
MATRIX = ROOT / "docs/bibliography-normative-coverage.md"
SPEC = importlib.util.spec_from_file_location(
    "normative_validator",
    ROOT / "skills/scientific-evidence-workflow/scripts/validate_normative_card.py",
)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def load_card(name: str) -> dict:
    return json.loads((CARD_DIR / name).read_text(encoding="utf-8"))


def test_layers_and_sorting_boundary_are_explicit() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    assert "библиографическая **ссылка**" in text
    assert "библиографическое **описание**" in text
    assert "ссылка и описание остаются двумя слоями" in text.casefold()
    assert "Порядок списка литературы" in text
    assert "не вводит" in text


def test_cards_v3_are_valid_and_preserve_requirement_prefixes() -> None:
    expected = {
        "NORM-GOST-R-7.0.5-2008-001.json": 33,
        "NORM-GOST-R-7.0.100-2018-001.json": 42,
        "NORM-BMSTU-DISS-REQ-001.json": 17,
    }
    for name, count in expected.items():
        card = load_card(name)
        report = VALIDATOR.validate_card(card)
        assert report["valid"], (name, report["errors"])
        assert {item["requirement_id"] for item in card["requirements"]} == {
            f"REQ-{i:03d}" for i in range(1, count + 1)
        }
    assert load_card("NORM-GOST-R-7.0.5-2008-001.json")["record_version"] == "v3"
    assert load_card("NORM-GOST-R-7.0.100-2018-001.json")["record_version"] == "v3"


def test_gost_7_0_5_sections_5_to_10_are_covered_with_defective_copy_recorded() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    for section in range(5, 11):
        assert f"| Раздел {section} | `covered`" in text
    card = load_card("NORM-GOST-R-7.0.5-2008-001.json")
    assert any("физически дефектна" in item for item in card["coverage"])
    assert card["provenance"]["content_hash"].endswith("09e7b08")


def test_gost_7_0_100_target_sections_are_covered() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    for section in ("5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "Раздел 6"):
        assert f"| {section} | `covered`" in text
    card = load_card("NORM-GOST-R-7.0.100-2018-001.json")
    assert not any("заблокирован" in item for item in card["not_observed"])


def test_local_rules_do_not_create_sorting() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    for requirement_id in ("REQ-010", "REQ-011", "REQ-012", "REQ-013", "REQ-014"):
        assert f"| {requirement_id} | `local_override`" in text
    assert "не превращается в обязательную сортировку" in text.replace("\n", " ")
