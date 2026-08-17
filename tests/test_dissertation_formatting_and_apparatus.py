import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "dissertation-formatting-and-apparatus"
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ABBR = load("audit_abbreviations")
TERMS = load("audit_terminology")
BIB = load("audit_bibliography")
VALIDATOR = load("validate_critic_findings")


def assert_valid(findings: list[dict]) -> None:
    report = VALIDATOR.validate_findings({"schema_version": "PSES-DISS-001/v1", "findings": findings})
    assert report["valid"], report["errors"]


def test_abbreviation_audit_detects_undefined_and_conflicting_meaning() -> None:
    text = "МСА применён. НЛО отмечено."
    declared = {"abbreviations": [
        {"abbreviation": "МСА", "expansion": "метод спектрального анализа"},
        {"abbreviation": "МСА", "expansion": "малая система анализа"},
    ]}
    findings = ABBR.audit(text, declared)
    assert {item["rule_id"] for item in findings} >= {"ABBR-001", "ABBR-003"}
    assert_valid(findings)


def test_abbreviation_audit_reports_unused_declared_item() -> None:
    findings = ABBR.audit("Текст без сокращений.", {"abbreviations": [{"abbreviation": "АБВ", "expansion": "алфавитная запись"}]})
    assert [item["rule_id"] for item in findings] == ["ABBR-004"]
    assert_valid(findings)


def test_terminology_audit_uses_exact_safe_replacement() -> None:
    ledger = {"terms": [{"term_id": "TERM-1", "canonical": "погрешность", "definition": "Отклонение результата.", "aliases": [], "forbidden_variants": ["ошибка измерения"]}]}
    findings = TERMS.audit("Ошибка измерения определена экспериментально.", ledger)
    forbidden = next(item for item in findings if item["rule_id"] == "TERM-003")
    assert forbidden["word_action"] == "tracked_change"
    assert forbidden["suggested_fix"]["new"] == "погрешность"
    assert_valid(findings)


def test_bibliography_unspecified_order_is_not_enforced_and_unknown_type_is_not_assessed() -> None:
    ledger = {
        "profile": {"sorting_strategy": "unspecified", "sequential_numbering": True, "supported_record_types": ["article"], "numbering_authority_ids": ["NORM-GOST-REQ-1"]},
        "in_text_citations": [{"record_id": "R2", "order": 1, "display": "[2]"}],
        "records": [
            {"record_id": "R1", "number": 1, "type": "dataset", "title": "Данные", "year": 2024},
            {"record_id": "R2", "number": 2, "type": "article", "title": "Статья", "year": 2023},
        ],
    }
    findings = BIB.audit(ledger)
    rules = {item["rule_id"] for item in findings}
    assert "BIB-006" not in rules
    assert "BIB-004" in rules
    assert_valid(findings)


def test_bibliography_reports_resolution_duplicates_and_explicit_order() -> None:
    ledger = {
        "profile": {"sorting_strategy": "citation_order", "sequential_numbering": False, "supported_record_types": ["article"], "citation_authority_ids": ["NORM-CITE-REQ-1"], "sorting_authority_ids": ["LOCAL-ORDER-REQ-1"]},
        "in_text_citations": [{"record_id": "MISSING", "order": 1, "display": "[9]"}, {"record_id": "R2", "order": 2, "display": "[2]"}],
        "records": [
            {"record_id": "R1", "number": 1, "type": "article", "title": "Одна", "year": 2024, "doi": "10.x/a"},
            {"record_id": "R2", "number": 2, "type": "article", "title": "Одна", "year": 2024, "doi": "10.x/a"},
        ],
    }
    findings = BIB.audit(ledger)
    rules = {item["rule_id"] for item in findings}
    assert {"BIB-001", "BIB-003", "BIB-006"} <= rules
    assert_valid(findings)


def test_bibliography_missing_rule_authority_is_an_evidence_gap_not_invalid_normativity() -> None:
    ledger = {
        "profile": {"sorting_strategy": "alphabetical", "sequential_numbering": True},
        "in_text_citations": [],
        "records": [
            {"record_id": "R2", "number": 2, "type": "article", "authors": "Б", "title": "Б"},
            {"record_id": "R1", "number": 1, "type": "article", "authors": "А", "title": "А"},
        ],
    }
    findings = BIB.audit(ledger)
    relevant = [item for item in findings if item["rule_id"] in {"BIB-005", "BIB-006"}]
    assert relevant and all(item["issue_class"] == "evidence_gap" for item in relevant)
    assert_valid(findings)
