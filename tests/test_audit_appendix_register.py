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


appendices = _load("audit_appendix_register")
validator = _load("validate_critic_findings")
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


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
            if kind not in {"tab", "br"}:
                node.text = value
    etree.SubElement(body, _w("sectPr"))
    raw = etree.tostring(root, encoding="UTF-8", xml_declaration=True, standalone=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("word/document.xml", raw)


def _registry(**extra) -> dict:
    value = {"items": [{"appendix_id": "APP-A", "designation": "А", "title": "Первичные данные"}]}
    value.update(extra)
    return value


def _assert_valid(findings: list[dict]) -> None:
    report = validator.validate_findings({"schema_version": "PSES-DISS-001/v1", "findings": findings})
    assert report["valid"], report["errors"]


def test_clean_docx_handles_split_runs_and_preserves_source(tmp_path: Path) -> None:
    source = tmp_path / "clean.docx"
    _docx(
        source,
        [
            [("t", "Дополнительные данные приведены в прилож"), ("t", "ении А.")],
            [("t", "ПРИЛОЖЕНИЕ"), ("tab", ""), ("t", "А")],
            [("t", "обязательное")],
            [("t", "Первичные"), ("br", ""), ("t", "данные")],
        ],
    )
    before = source.read_bytes()

    assert appendices.audit(source, _registry()) == []
    assert source.read_bytes() == before


def test_missing_heading_is_internal_and_reference_scope_not_assessed(tmp_path: Path) -> None:
    source = tmp_path / "missing.txt"
    source.write_text("Основной текст без приложения.\n", encoding="utf-8")

    findings = appendices.audit(source, _registry())

    heading = next(item for item in findings if item["rule_id"] == "APPENDIX-HEADING-001")
    scope = next(item for item in findings if item["rule_id"] == "APPENDIX-REFERENCE-SCOPE-001")
    assert heading["issue_class"] == "internal_inconsistency"
    assert heading["authority_ids"] == []
    assert heading["locator"]["exact_text"] == "Основной текст без приложения."
    assert scope["issue_class"] == "recommendation"
    assert scope["observed"]["status"] == "not_assessed"
    assert scope["locator"] is None
    _assert_valid(findings)


def test_reference_after_first_appendix_does_not_count_as_main_text_reference(tmp_path: Path) -> None:
    source = tmp_path / "late-reference.txt"
    source.write_text(
        "Основной текст.\nПРИЛОЖЕНИЕ А\nПервичные данные\nСм. приложение А.\n",
        encoding="utf-8",
    )

    findings = appendices.audit(source, _registry())

    assert len(findings) == 1
    assert findings[0]["rule_id"] == "APPENDIX-REFERENCE-001"
    assert findings[0]["locator"] == {"kind": "text", "exact_text": "ПРИЛОЖЕНИЕ А", "occurrence": 1}


def test_registry_and_source_duplicate_designations_are_reported(tmp_path: Path) -> None:
    source = tmp_path / "duplicates.txt"
    source.write_text(
        "См. приложение А.\nПРИЛОЖЕНИЕ А\nПервичные данные\nПРИЛОЖЕНИЕ А\nПовтор\n",
        encoding="utf-8",
    )
    registry = {
        "items": [
            {"appendix_id": "APP-A1", "designation": "А", "title": "Первичные данные"},
            {"appendix_id": "APP-A2", "designation": "А", "title": "Повтор"},
        ]
    }

    findings = appendices.audit(source, registry)

    assert [item["rule_id"] for item in findings].count("APPENDIX-DESIGNATION-001") == 2
    assert all(item["issue_class"] == "internal_inconsistency" for item in findings)
    _assert_valid(findings)


def test_declared_page_is_explicitly_not_assessed_without_violation(tmp_path: Path) -> None:
    source = tmp_path / "page.txt"
    source.write_text("См. приложение А.\nПРИЛОЖЕНИЕ А\nПервичные данные\n", encoding="utf-8")
    registry = {"items": [{"appendix_id": "APP-A", "designation": "А", "title": "Первичные данные", "page": 99}]}

    findings = appendices.audit(source, registry)

    assert len(findings) == 1
    assert findings[0]["rule_id"] == "APPENDIX-PAGE-001"
    assert findings[0]["observed"]["status"] == "not_assessed"
    assert findings[0]["issue_class"] == "recommendation"
    assert findings[0]["authority_ids"] == []
    assert findings[0]["word_action"] == "none"
    _assert_valid(findings)


def test_versioned_authority_promotes_missing_reference_only(tmp_path: Path) -> None:
    source = tmp_path / "authority.txt"
    source.write_text("Основной текст.\nПРИЛОЖЕНИЕ А\nПервичные данные\n", encoding="utf-8")
    authority = "LOCAL-DISSERTATION-PROFILE-002:REQ-APP-3"
    registry = _registry(authority_ids=[authority, "LOCAL-UNVERSIONED"])

    findings = appendices.audit(source, registry)

    assert len(findings) == 1
    assert findings[0]["issue_class"] == "normative_violation"
    assert findings[0]["authority_ids"] == [authority]
    assert findings[0]["rule_id"] == authority
    _assert_valid(findings)


def test_cli_writes_canonical_envelope_and_invalid_utf8_exits_2(tmp_path: Path, capsys) -> None:
    source = tmp_path / "clean.txt"
    registry = tmp_path / "registry.json"
    output = tmp_path / "findings.json"
    source.write_text("См. приложение А.\nПРИЛОЖЕНИЕ А\nПервичные данные\n", encoding="utf-8")
    registry.write_text(json.dumps(_registry(), ensure_ascii=False), encoding="utf-8")

    assert appendices.main([str(source), str(registry), "--out", str(output)]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed == json.loads(output.read_text(encoding="utf-8"))
    assert printed == {"schema_version": "PSES-DISS-001/v1", "findings": []}

    bad = tmp_path / "bad.txt"
    bad.write_bytes(b"\xff\xfe")
    assert appendices.main([str(bad), str(registry)]) == 2
    assert "UTF-8" in capsys.readouterr().err
