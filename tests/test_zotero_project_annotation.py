from __future__ import annotations

from copy import deepcopy
import json
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "zotero-project-annotation" / "scripts" / "validate_project_annotation.py"
RP_MANIFEST_TEMPLATE = ROOT / "skills" / "research-project-workflow" / "assets" / "project-manifest.template.json"
SPEC = spec_from_file_location("zotero_project_annotation_validator", SCRIPT)
assert SPEC and SPEC.loader
VALIDATOR = module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


SOURCE_HASH = "sha256:" + "0" * 64
PROJECT_HASH = "sha256:" + "1" * 64


def valid_record() -> dict:
    return {
        "schema_version": "ZPA-001/v1",
        "annotation_id": "ANN-001",
        "record_type": "derived_project_annotation",
        "status": "current",
        "remake_required": False,
        "stale_reason": None,
        "block_reason": None,
        "metadata_only": False,
        "source_content_hash": SOURCE_HASH,
        "project_context_hash": PROJECT_HASH,
        "source": {
            "zotero_item_key": "ABCD1234",
            "title": "A publication",
            "content_hash": SOURCE_HASH,
            "read_scope": "full_text",
            "locators_read": ["Abstract", "Methods", "Results"],
        },
        "project": {
            "project_id": "PRJ-001",
            "title": "A project",
            "goal": "Understand the research problem.",
            "objectives": [{"id": "OBJ-001", "text": "Measure the target."}],
            "research_questions": [{"id": "RQ-001", "text": "What is the target?"}],
        },
        "relevance_target_ids": ["RQ-001", "OBJ-001"],
        "annotation": {
            "summary": "A neutral summary.",
            "source_voice": {
                "what_work_did": "The source describes a study and its design.",
                "reported_outcomes": [
                    {
                        "claim_id": "CL-001",
                        "statement": "The source reports an outcome.",
                        "value": "10 units (95% CI 8-12)",
                        "locator": "zotero:ABCD1234#Results",
                    }
                ],
                "stated_boundaries": ["The authors state a boundary."],
            },
            "author_conclusion": "The authors conclude that the method is feasible.",
            "project_judgement": {
                "why_useful_here": "It informs RQ-001 and OBJ-001.",
                "what_it_does_not_settle": "It does not settle external validity.",
            },
        },
        "evidence_role": "derived_annotation_not_evidence",
        "provenance": {
            "created_at": "2026-08-17",
            "machine_record_path": "derived/annotations/ANN-001.json",
        },
    }


def report(record: dict, **kwargs):
    return VALIDATOR.validate_annotation(record, **kwargs)


def annotation_from_rp_manifest(manifest: dict) -> dict:
    record = valid_record()
    context = manifest["context"]
    record["project_context_hash"] = manifest["context_hash"]
    record["project"]["project_id"] = manifest["project_id"]
    record["project"]["title"] = manifest["title"]
    record["project"]["goal"] = context["goal"]
    record["project"]["objectives"] = [
        {"id": objective["objective_id"], "text": objective["text"]}
        for objective in context["objectives"]
    ]
    record["project"]["research_questions"] = [
        {"id": question["question_id"], "text": question["text"]}
        for question in context["research_questions"]
    ]
    record["relevance_target_ids"] = [
        context["research_questions"][0]["question_id"],
        context["objectives"][0]["objective_id"],
    ]
    return record


def test_valid_annotation_separates_voices_and_targets():
    result = report(valid_record())
    assert result["valid"], result["errors"]


def test_relevance_targets_must_be_declared_project_rq_or_objective():
    record = valid_record()
    record["relevance_target_ids"] = ["RQ-999"]
    result = report(record)
    assert not result["valid"]
    assert any("not declared" in error for error in result["errors"])


def test_project_manifest_is_used_for_target_validation():
    manifest = {
        "project_id": "PRJ-001",
        "project_context_hash": PROJECT_HASH,
        "objectives": [{"id": "OBJ-001", "text": "Measure the target."}],
        "research_questions": [{"id": "RQ-001", "text": "What is the target?"}],
    }
    result = report(valid_record(), project_manifest=manifest)
    assert result["valid"], result["errors"]

    manifest["research_questions"] = [{"id": "RQ-002", "text": "A different question."}]
    result = report(valid_record(), project_manifest=manifest)
    assert not result["valid"]
    assert any("absent from project manifest" in error for error in result["errors"])


def test_annotation_derived_from_rp_template_matches_canonical_context_hash():
    manifest = json.loads(RP_MANIFEST_TEMPLATE.read_text(encoding="utf-8"))
    record = annotation_from_rp_manifest(manifest)

    result = report(record, project_manifest=manifest)
    assert result["valid"], result["errors"]

    mismatched = deepcopy(record)
    mismatched["project_context_hash"] = SOURCE_HASH
    result = report(mismatched, project_manifest=manifest)
    assert not result["valid"]
    assert any(
        "project_manifest.context_hash" in error
        and "annotation.project_context_hash" in error
        for error in result["errors"]
    )


def test_nested_legacy_project_context_hash_is_checked_against_rp_manifest():
    manifest = json.loads(RP_MANIFEST_TEMPLATE.read_text(encoding="utf-8"))
    record = annotation_from_rp_manifest(manifest)
    record.pop("project_context_hash")
    record["project"]["project_context_hash"] = SOURCE_HASH

    result = report(record, project_manifest=manifest)

    assert not result["valid"]
    assert any("project_manifest.context_hash" in error for error in result["errors"])

def test_changed_source_hash_requires_stale_status_and_remake():
    record = valid_record()
    changed = "sha256:" + "2" * 64
    result = report(record, source_content_hash=changed)
    assert not result["valid"]
    assert any("must be status 'stale'" in error for error in result["errors"])

    record["status"] = "stale"
    record["remake_required"] = True
    record["stale_reason"] = "Source content hash changed."
    result = report(record, source_content_hash=changed)
    assert result["valid"], result["errors"]


def test_changed_project_context_hash_requires_stale_status():
    record = valid_record()
    changed = "sha256:" + "3" * 64
    result = report(record, project_context_hash=changed)
    assert not result["valid"]
    assert any("project_context_hash" in error and "must be status 'stale'" in error for error in result["errors"])


def test_all_three_voice_fields_are_required():
    record = valid_record()
    del record["annotation"]["author_conclusion"]
    result = report(record)
    assert not result["valid"]
    assert any("author_conclusion" in error for error in result["errors"])


def test_metadata_only_is_explicitly_blocked():
    record = valid_record()
    record["source"]["read_scope"] = "metadata_only"
    record["metadata_only"] = True
    result = report(record)
    assert not result["valid"]
    assert any("metadata-only source must be blocked" in error for error in result["errors"])

    blocked = deepcopy(record)
    blocked["status"] = "blocked_metadata_only"
    blocked["remake_required"] = True
    blocked["block_reason"] = "Full text was unavailable; metadata only."
    blocked["annotation"]["source_voice"]["reported_outcomes"] = []
    result = report(blocked)
    assert result["valid"], result["errors"]


def test_annotation_is_never_evidence():
    record = valid_record()
    record["evidence_role"] = "evidence"
    result = report(record)
    assert not result["valid"]
    assert any("cannot stand in for the publication" in error for error in result["errors"])
