from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path

from lxml import etree


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/dissertation-formatting-and-apparatus/scripts"
sys.path.insert(0, str(SCRIPTS))


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


illustrations = _load("audit_illustration_register")
validator = _load("validate_critic_findings")
W = illustrations.W_NS


def _w(local: str) -> str:
    return f"{{{W}}}{local}"


def _docx(path: Path, paragraphs: list[list[tuple[str, str]]]) -> None:
    root = etree.Element(_w("document"), nsmap={"w": W})
    body = etree.SubElement(root, _w("body"))
    for parts in paragraphs:
        paragraph = etree.SubElement(body, _w("p"))
        for kind, value in parts:
            run = etree.SubElement(paragraph, _w("r"))
            node = etree.SubElement(run, _w(kind))
            if kind == "br" and value:
                node.set(_w("type"), value)
            elif kind == "tab":
                pass
            else:
                node.text = value
    etree.SubElement(body, _w("sectPr"))
    raw = etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", raw)


def _registry(**extra) -> dict:
    value = {
        "items": [
            {"item_id": "FIG-1", "kind": "figure", "number": "1", "caption": "Схема отбора"},
            {"item_id": "TAB-1", "kind": "table", "number": "1", "caption": "Характеристика групп"},
        ]
    }
    value.update(extra)
    return value


def _clean_docx(path: Path) -> None:
    _docx(
        path,
        [
            [("t", "Как показано на рис"), ("t", "унке 1, группы различались.")],
            [("t", "Рисунок 1"), ("tab", ""), ("t", "— Схема"), ("br", ""), ("t", "отбора")],
            [("t", "Результаты приведены в таблице 1.")],
            [("t", "Таблица 1 — Характеристика групп")],
        ],
    )


def _assert_valid(findings: list[dict]) -> None:
    report = validator.validate_findings({"schema_version": "PSES-DISS-001/v1", "findings": findings})
    assert report["valid"], report["errors"]


def test_clean_docx_handles_runs_tabs_breaks_and_preserves_source(tmp_path: Path) -> None:
    source = tmp_path / "clean.docx"
    _clean_docx(source)
    before = source.read_bytes()

    assert illustrations.audit(source, _registry()) == []
    assert source.read_bytes() == before


def test_missing_caption_and_reference_are_non_normative_with_word_anchor(tmp_path: Path) -> None:
    source = tmp_path / "missing.docx"
    _docx(source, [[("t", "В тексте есть рисунок 1, но нет подписи.")], [("t", "Основной текст")]])
    registry = {"items": [{"item_id": "FIG-1", "kind": "figure", "number": "1", "caption": "Схема"}]}

    findings = illustrations.audit(source, registry)

    assert {item["rule_id"] for item in findings} == {"ILLUSTRATION-CAPTION-001"}
    item = findings[0]
    assert item["issue_class"] == "internal_inconsistency"
    assert item["authority_ids"] == []
    assert item["locator"] == {
        "kind": "text",
        "exact_text": "В тексте есть рисунок 1, но нет подписи.",
        "occurrence": 1,
    }
    assert item["word_action"] == "comment"
    _assert_valid(findings)


def test_caption_is_not_counted_as_separate_reference(tmp_path: Path) -> None:
    source = tmp_path / "caption-only.txt"
    source.write_text("Рисунок 1 — Схема отбора\n", encoding="utf-8")
    registry = {"items": [{"item_id": "FIG-1", "kind": "figure", "number": "1", "caption": "Схема отбора"}]}

    findings = illustrations.audit(source, registry)

    assert len(findings) == 1
    assert findings[0]["rule_id"] == "ILLUSTRATION-REFERENCE-001"
    assert findings[0]["locator"]["exact_text"] == "Рисунок 1 — Схема отбора"


def test_registry_and_source_duplicates_are_reported(tmp_path: Path) -> None:
    source = tmp_path / "duplicates.txt"
    source.write_text(
        "См. рисунок 1.\nРисунок 1 — Схема\nРисунок 1 — Повтор\n",
        encoding="utf-8",
    )
    registry = {
        "items": [
            {"item_id": "A", "kind": "figure", "number": "1", "caption": "Схема"},
            {"item_id": "B", "kind": "figure", "number": "1", "caption": "Повтор"},
        ]
    }

    findings = illustrations.audit(source, registry)
    rules = [item["rule_id"] for item in findings]
    assert rules.count("ILLUSTRATION-NUMBER-001") == 2
    assert all(item["issue_class"] == "internal_inconsistency" for item in findings)
    _assert_valid(findings)


def test_explicit_versioned_authority_promotes_defect_to_normative(tmp_path: Path) -> None:
    source = tmp_path / "authority.txt"
    source.write_text("Рисунок 1 — Схема\n", encoding="utf-8")
    authority = "NORM-LOCAL-ILLUSTRATIONS-001:REQ-004"
    registry = {
        "authority_ids": [authority, "UNVERSIONED"],
        "items": [{"item_id": "FIG-1", "kind": "figure", "number": "1", "caption": "Схема"}],
    }

    findings = illustrations.audit(source, registry)

    assert len(findings) == 1
    assert findings[0]["issue_class"] == "normative_violation"
    assert findings[0]["rule_id"] == authority
    assert findings[0]["authority_ids"] == [authority]
    _assert_valid(findings)


def test_cli_writes_canonical_envelope_and_bad_input_exits_2(tmp_path: Path, capsys) -> None:
    source = tmp_path / "clean.docx"
    registry = tmp_path / "registry.json"
    output = tmp_path / "findings.json"
    _clean_docx(source)
    registry.write_text(json.dumps(_registry(), ensure_ascii=False), encoding="utf-8")

    assert illustrations.main([str(source), str(registry), "--out", str(output)]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed == json.loads(output.read_text(encoding="utf-8"))
    assert printed == {"schema_version": "PSES-DISS-001/v1", "findings": []}

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{}", encoding="utf-8")
    assert illustrations.main([str(source), str(invalid)]) == 2
    assert "registry.items" in capsys.readouterr().err
