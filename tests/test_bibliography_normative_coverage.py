"""Regression tests for the deliberately partial bibliography norm matrix."""

from __future__ import annotations

import json
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD_DIR = ROOT / "skills/scientific-evidence-workflow/references/normative-patterns"
MATRIX = ROOT / "docs/bibliography-normative-coverage.md"

CARD_SPEC = importlib.util.spec_from_file_location(
    "bibliography_normative_card_validator",
    ROOT / "skills/scientific-evidence-workflow/scripts/validate_normative_card.py",
)
assert CARD_SPEC and CARD_SPEC.loader
CARD_VALIDATOR = importlib.util.module_from_spec(CARD_SPEC)
CARD_SPEC.loader.exec_module(CARD_VALIDATOR)


def load_card(name: str) -> dict:
    return json.loads((CARD_DIR / name).read_text(encoding="utf-8"))


def test_matrix_exists_and_keeps_the_two_layers_separate() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    assert "библиографическая **ссылка**" in text
    assert "библиографическое **описание**" in text
    assert "ссылка и описание остаются двумя слоями" in text
    assert "Порядок списка литературы" in text
    assert "не вводит порядок" in text


def test_cards_remain_structurally_valid() -> None:
    for name in (
        "NORM-GOST-R-7.0.5-2008-001.json",
        "NORM-GOST-R-7.0.100-2018-001.json",
        "NORM-BMSTU-DISS-REQ-001.json",
    ):
        report = CARD_VALIDATOR.validate_card(load_card(name))
        assert report["valid"], (name, report["errors"])


def test_existing_requirement_ids_are_preserved() -> None:
    expected = {
        "NORM-GOST-R-7.0.5-2008-001.json": {f"REQ-{i:03d}" for i in range(1, 10)},
        "NORM-GOST-R-7.0.100-2018-001.json": {f"REQ-{i:03d}" for i in range(1, 25)},
        "NORM-BMSTU-DISS-REQ-001.json": {f"REQ-{i:03d}" for i in range(1, 18)},
    }
    for name, requirement_ids in expected.items():
        card = load_card(name)
        assert {item["requirement_id"] for item in card["requirements"]} == requirement_ids


def test_gost_7_0_5_unread_link_sections_are_not_assessed() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    for section in range(5, 11):
        assert f"| Раздел {section} | `not_assessed`" in text
    card = load_card("NORM-GOST-R-7.0.5-2008-001.json")
    assert any("разделов 5–10 заблокировано" in item for item in card["not_observed"])


def test_gost_7_0_100_unread_description_branches_are_not_assessed() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    assert "| 5.2–5.7 (кроме явно названных подпунктов) | `partial`" in text
    assert "| Раздел 6 | `not_assessed`" in text
    card = load_card("NORM-GOST-R-7.0.100-2018-001.json")
    assert any("подразделов 5.2–5.7 и раздела 6 заблокировано" in item for item in card["not_observed"])


def test_local_bmstu_rules_are_explicit_and_do_not_create_sorting() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    for requirement_id in ("REQ-010", "REQ-011", "REQ-012", "REQ-013", "REQ-014"):
        assert f"| {requirement_id} | `local_override`" in text
    assert "это не задаёт сортировку" in text
    assert "не превращается в обязательную сортировку" in text


def test_matrix_records_source_blocker_without_reconstructing_norms() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    assert "JC6BQAN9" in text
    assert "7ZH84CLI" in text
    assert "новые" in text and "нормативные REQ не добавляются" in text
    assert "не реконструируется" in text
