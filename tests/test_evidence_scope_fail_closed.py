from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "scientific-evidence-workflow"
SPEC = importlib.util.spec_from_file_location(
    "evidence_scope_fail_closed", SKILL / "scripts" / "validate_bundle.py"
)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def bundle() -> dict:
    return json.loads(
        (SKILL / "assets" / "evidence-bundle.template.json").read_text(encoding="utf-8")
    )


def second_source() -> dict:
    return {
        "source_id": "SRC-OUTSIDE",
        "title": "Outside the declared corpus",
        "content_hash": None,
        "representation": "text",
        "local_ref": "local/outside.txt",
        "version": "v1",
    }


def test_input_scope_rejects_duplicate_source_identifiers() -> None:
    data = bundle()
    data["task"]["input_scope"].append("SRC-EXAMPLE-001")

    report = VALIDATOR.validate_bundle(data)

    assert "duplicate source identifiers" in "\n".join(report["errors"])


def test_evidence_cannot_escape_declared_input_scope() -> None:
    data = bundle()
    data["sources"].append(second_source())
    data["evidence"][0]["source_id"] = "SRC-OUTSIDE"

    report = VALIDATOR.validate_bundle(data)

    assert "evidence[EV-001].source_id: source 'SRC-OUTSIDE' is outside input_scope" in report[
        "errors"
    ]


def test_result_cannot_escape_declared_input_scope() -> None:
    data = bundle()
    data["sources"].append(second_source())
    data["results"] = [
        {
            "result_id": "RES-OUTSIDE",
            "source_id": "SRC-OUTSIDE",
            "locator": "row:1",
            "value": 1,
            "unit": "unit",
            "version": "v1",
            "analysis": "frozen result",
        }
    ]

    report = VALIDATOR.validate_bundle(data)

    assert "result[RES-OUTSIDE].source_id: source 'SRC-OUTSIDE' is outside input_scope" in report[
        "errors"
    ]


def test_unverified_extracted_evidence_cannot_support_a_released_claim() -> None:
    data = bundle()
    data["evidence"][0]["verification_status"] = "extracted"

    report = VALIDATOR.validate_bundle(data)

    assert "unverified extracted evidence cannot support a supported or bounded claim" in "\n".join(
        report["errors"]
    )


def test_organizational_source_is_rejected_when_genre_forbids_it() -> None:
    data = copy.deepcopy(bundle())
    data["task"]["genre"] = "article-annotation"
    data["sources"][0]["representation"] = "organizational"

    report = VALIDATOR.validate_bundle(data)

    assert "article-annotation' forbids organizational input" in "\n".join(report["errors"])
