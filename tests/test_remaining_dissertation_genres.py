"""Semantic gates for the remaining dissertation evidence-bundle genres."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT / "skills" / "scientific-evidence-workflow" / "scripts" / "validate_bundle.py"
)
SPEC = importlib.util.spec_from_file_location("remaining_genre_validator", VALIDATOR_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


CANONICAL_SECTIONS = {
    "dissertation-results-chapter": {
        "result_scope",
        "reported_results",
        "negative_results",
        "result_traceability",
        "chapter_conclusions",
    },
    "dissertation-synthesis-chapter": {
        "synthesis_scope",
        "result_interpretation",
        "literature_comparison",
        "conflicts_and_explanations",
        "limitations",
        "chapter_conclusions",
    },
    "dissertation-conclusion": {
        "conclusion_scope",
        "task_conclusions",
        "practical_recommendations",
        "future_work",
        "aim_closure",
    },
    "defense-propositions": {
        "proposition_statement",
        "proposition_boundary",
        "proposition_result_anchor",
        "proposition_section_anchor",
    },
    "novelty-statement": {
        "novelty_boundary",
        "novelty_claim",
        "theoretical_significance",
        "practical_significance",
        "novelty_traceability",
    },
    "thesis-synopsis": {
        "synopsis_scope",
        "general_characteristics",
        "main_content",
        "synopsis_conclusion",
        "author_publications",
        "synopsis_traceability",
    },
    "approbation-record": {
        "conference_reports",
        "publication_records",
        "registration_records",
        "implementation_records",
        "approbation_crossrefs",
    },
}


def source(source_id: str, representation: str) -> dict:
    return {
        "source_id": source_id,
        "title": source_id,
        "content_hash": None,
        "representation": representation,
        "local_ref": f"local:{source_id}",
        "version": "v1",
    }


def evidence(evidence_id: str, source_id: str, support_type: str = "direct") -> dict:
    return {
        "evidence_id": evidence_id,
        "source_id": source_id,
        "locator": "section:1/paragraph:1",
        "claim": "Проверенная запись.",
        "support_type": support_type,
        "fragment": None,
        "value": None,
        "unit": None,
        "study_context": None,
        "limitations": None,
        "verification_status": "verified",
    }


def result(result_id: str = "RES-1") -> dict:
    return {
        "result_id": result_id,
        "source_id": "SRC-DATA",
        "locator": "table:1/row:1",
        "value": 1,
        "unit": "a.u.",
        "version": "v1",
        "analysis": "frozen-analysis-v1",
        "approved": True,
    }


def unit(unit_id: str, unit_type: str, parent_id: str | None = None) -> dict:
    return {
        "unit_id": unit_id,
        "unit_type": unit_type,
        "label": unit_id,
        "title": unit_id,
        "parent_id": parent_id,
        "document": "dissertation",
        "status": "final",
    }


def claim(
    claim_id: str,
    section: str,
    *,
    evidence_ids: list[str] | None = None,
    result_ids: list[str] | None = None,
    structure_ids: list[str] | None = None,
    status: str = "supported",
    claim_type: str = "factual",
    boundary: str | None = None,
) -> dict:
    dispositions = {
        "supported": "keep",
        "bounded": "keep_with_boundary",
        "unsupported": "request_input",
    }
    return {
        "claim_id": claim_id,
        "text": f"Проверяемое утверждение {claim_id}.",
        "output_section": section,
        "claim_type": claim_type,
        "certainty": "direct" if status == "supported" else "uncertain",
        "evidence_ids": evidence_ids or [],
        "result_ids": result_ids or [],
        "structure_ids": structure_ids or [],
        "status": status,
        "disposition": dispositions[status],
        "boundary": boundary,
        "causal_basis": None,
    }


def bundle(genre: str) -> dict:
    mode = "record" if genre == "approbation-record" else "manuscript"
    task = {
        "mode": mode,
        "genre": genre,
        "request": "Подготовить проверяемый фрагмент.",
        "input_scope": [],
        "language": "ru",
        "audience": "dissertation_council",
    }
    if mode == "manuscript":
        task.update({"figure_mode": "without_figures", "formatting_mode": "section_only"})

    data = {
        "schema_version": "1.0",
        "bundle_id": f"BUNDLE-{genre}",
        "task": task,
        "sources": [],
        "evidence": [],
        "results": [],
        "structure": [],
        "claims": [],
        "revisions": [],
    }

    if genre == "dissertation-results-chapter":
        data["sources"] = [source("SRC-DATA", "data")]
        data["task"]["input_scope"] = ["SRC-DATA"]
        data["results"] = [result()]
        data["structure"] = [unit("CH-RESULTS", "chapter"), unit("SEC-RESULTS", "section", "CH-RESULTS")]
        data["claims"] = [
            claim(f"CL-{index}", section, result_ids=["RES-1"], structure_ids=["SEC-RESULTS"])
            for index, section in enumerate(sorted(CANONICAL_SECTIONS[genre]), 1)
        ]
    elif genre == "dissertation-synthesis-chapter":
        data["sources"] = [source("SRC-DATA", "data"), source("SRC-LIT", "pdf")]
        data["task"]["input_scope"] = ["SRC-DATA", "SRC-LIT"]
        data["evidence"] = [evidence("EV-LIT", "SRC-LIT", "context")]
        data["results"] = [result()]
        data["structure"] = [unit("CH-SYN", "chapter"), unit("SEC-SYN", "section", "CH-SYN")]
        data["claims"] = [
            claim("CL-S", "synthesis_scope", result_ids=["RES-1"], structure_ids=["SEC-SYN"]),
            claim("CL-I", "result_interpretation", result_ids=["RES-1"], structure_ids=["SEC-SYN"]),
            claim("CL-C", "literature_comparison", evidence_ids=["EV-LIT"], result_ids=["RES-1"], structure_ids=["SEC-SYN"]),
            claim("CL-X", "conflicts_and_explanations", evidence_ids=["EV-LIT"], structure_ids=["SEC-SYN"]),
            claim("CL-L", "limitations", result_ids=["RES-1"], claim_type="limitation", structure_ids=["SEC-SYN"]),
            claim("CL-CC", "chapter_conclusions", result_ids=["RES-1"], structure_ids=["SEC-SYN"]),
        ]
    elif genre == "dissertation-conclusion":
        data["sources"] = [source("SRC-DATA", "data")]
        data["task"]["input_scope"] = ["SRC-DATA"]
        data["results"] = [result()]
        data["structure"] = [unit("TASK-1", "task"), unit("CONCLUSION-1", "conclusion")]
        data["claims"] = [
            claim("CL-S", "conclusion_scope", result_ids=["RES-1"], structure_ids=["CONCLUSION-1"]),
            claim("CL-T", "task_conclusions", result_ids=["RES-1"], structure_ids=["TASK-1", "CONCLUSION-1"]),
            claim("CL-P", "practical_recommendations", result_ids=["RES-1"], structure_ids=["CONCLUSION-1"]),
            claim("CL-F", "future_work", result_ids=["RES-1"], structure_ids=["CONCLUSION-1"]),
            claim("CL-A", "aim_closure", result_ids=["RES-1"], structure_ids=["CONCLUSION-1"]),
        ]
    elif genre == "defense-propositions":
        data["sources"] = [source("SRC-DATA", "data")]
        data["task"]["input_scope"] = ["SRC-DATA"]
        data["results"] = [result()]
        data["structure"] = [unit("PROP-1", "proposition")]
        data["claims"] = [
            claim(f"CL-PROP-{index}", section, result_ids=["RES-1"], structure_ids=["PROP-1"])
            for index, section in enumerate(sorted(CANONICAL_SECTIONS[genre]), 1)
        ]
    elif genre == "novelty-statement":
        data["sources"] = [source("SRC-DATA", "data"), source("SRC-LIT", "text")]
        data["task"]["input_scope"] = ["SRC-DATA", "SRC-LIT"]
        data["evidence"] = [evidence("EV-LIT", "SRC-LIT", "context")]
        data["results"] = [result()]
        data["structure"] = [unit("SEC-NOV", "section")]
        data["claims"] = [
            claim("CL-B", "novelty_boundary", evidence_ids=["EV-LIT"], result_ids=["RES-1"], structure_ids=["SEC-NOV"], boundary="Корпус публикаций 2020–2025 гг."),
            claim("CL-N", "novelty_claim", evidence_ids=["EV-LIT"], result_ids=["RES-1"], structure_ids=["SEC-NOV"], boundary="Корпус публикаций 2020–2025 гг."),
            claim("CL-T", "theoretical_significance", evidence_ids=["EV-LIT"], result_ids=["RES-1"], structure_ids=["SEC-NOV"]),
            claim("CL-P", "practical_significance", evidence_ids=["EV-LIT"], result_ids=["RES-1"], structure_ids=["SEC-NOV"]),
            claim("CL-X", "novelty_traceability", evidence_ids=["EV-LIT"], result_ids=["RES-1"], structure_ids=["SEC-NOV"]),
        ]
    elif genre == "thesis-synopsis":
        data["sources"] = [source("SRC-DATA", "data"), source("SRC-ORG", "organizational")]
        data["task"]["input_scope"] = ["SRC-DATA", "SRC-ORG"]
        data["evidence"] = [evidence("EV-ORG", "SRC-ORG")]
        data["results"] = [result()]
        data["structure"] = [unit("SEC-SYNOPSIS", "section")]
        data["claims"] = [
            claim("CL-S", "synopsis_scope", evidence_ids=["EV-ORG"], structure_ids=["SEC-SYNOPSIS"]),
            claim("CL-G", "general_characteristics", evidence_ids=["EV-ORG"], structure_ids=["SEC-SYNOPSIS"]),
            claim("CL-M", "main_content", result_ids=["RES-1"], structure_ids=["SEC-SYNOPSIS"]),
            claim("CL-C", "synopsis_conclusion", result_ids=["RES-1"], structure_ids=["SEC-SYNOPSIS"]),
            claim("CL-A", "author_publications", evidence_ids=["EV-ORG"], structure_ids=["SEC-SYNOPSIS"]),
            claim("CL-X", "synopsis_traceability", result_ids=["RES-1"], structure_ids=["SEC-SYNOPSIS"]),
        ]
    elif genre == "approbation-record":
        data["sources"] = [source("SRC-ORG", "organizational")]
        data["task"]["input_scope"] = ["SRC-ORG"]
        data["evidence"] = [evidence("EV-ORG", "SRC-ORG")]
        data["claims"] = [
            claim(f"CL-{index}", section, evidence_ids=["EV-ORG"])
            for index, section in enumerate(sorted(CANONICAL_SECTIONS[genre]), 1)
        ]
    else:  # pragma: no cover - test helper guard
        raise AssertionError(genre)
    return data


def errors(report: dict) -> str:
    return "\n".join(report["errors"])


@pytest.mark.parametrize("genre", sorted(CANONICAL_SECTIONS))
def test_remaining_genres_accept_their_minimal_provable_bundle(genre: str) -> None:
    report = VALIDATOR.validate_bundle(bundle(genre))
    assert report["valid"] is True, report["errors"]


@pytest.mark.parametrize("genre, sections", sorted(CANONICAL_SECTIONS.items()))
def test_canonical_output_sections_are_closed(genre: str, sections: set[str]) -> None:
    rules = VALIDATOR.GENRES[genre]
    assert rules["required_output_sections"] == sections
    assert rules["allowed_output_sections"] == sections

    changed = bundle(genre)
    changed["claims"][0]["output_section"] = "invented_section"
    report = VALIDATOR.validate_bundle(changed)
    assert report["valid"] is False
    assert "does not define section 'invented_section'" in errors(report)


def test_results_requires_result_ids_and_rejects_observable_forbidden_inputs() -> None:
    changed = bundle("dissertation-results-chapter")
    changed["claims"][0]["result_ids"] = []
    changed["sources"].append(source("SRC-ORG", "organizational"))
    changed["task"]["input_scope"].append("SRC-ORG")
    changed["evidence"] = [evidence("EV-CONTEXT", "SRC-DATA", "context")]

    report = VALIDATOR.validate_bundle(changed)
    text = errors(report)
    assert "requires result_ids for every supported or bounded result statement" in text
    assert "carries no literature context" in text
    assert "forbids organizational input" in text


def test_synthesis_routes_interpretation_to_results_and_comparison_to_literature() -> None:
    changed = bundle("dissertation-synthesis-chapter")
    next(item for item in changed["claims"] if item["output_section"] == "result_interpretation")["result_ids"] = []
    comparison = next(item for item in changed["claims"] if item["output_section"] == "literature_comparison")
    comparison["evidence_ids"] = []
    comparison["result_ids"] = []

    report = VALIDATOR.validate_bundle(changed)
    text = errors(report)
    assert "synthesis section 'result_interpretation' requires result_ids" in text
    assert "literature_comparison requires in-scope literature evidence_ids and result_ids" in text


def test_conclusion_forbids_new_unsupported_claims_and_requires_task_mapping() -> None:
    changed = bundle("dissertation-conclusion")
    task_claim = next(item for item in changed["claims"] if item["output_section"] == "task_conclusions")
    task_claim["structure_ids"] = ["CONCLUSION-1"]
    changed["claims"].append(
        claim("CL-NEW", "future_work", status="unsupported", structure_ids=["CONCLUSION-1"])
    )

    report = VALIDATOR.validate_bundle(changed)
    text = errors(report)
    assert "cannot introduce an unsupported claim" in text
    assert "requires both task and conclusion structure_ids" in text
    assert "requires coverage by a task_conclusions claim" in text


def test_defense_proposition_requires_a_result_and_proposition_unit() -> None:
    changed = bundle("defense-propositions")
    for item in changed["claims"]:
        item["result_ids"] = []
        item["structure_ids"] = []

    report = VALIDATOR.validate_bundle(changed)
    text = errors(report)
    assert "requires result_ids and a proposition structure_id" in text
    assert "requires coverage by a supported or bounded proposition claim" in text


def test_novelty_requires_literature_results_and_explicit_boundary() -> None:
    changed = bundle("novelty-statement")
    novelty = next(item for item in changed["claims"] if item["output_section"] == "novelty_claim")
    novelty["evidence_ids"] = []
    novelty["result_ids"] = []
    novelty["boundary"] = None

    report = VALIDATOR.validate_bundle(changed)
    text = errors(report)
    assert "requires in-scope literature evidence_ids and result_ids" in text
    assert "requires an explicit comparison boundary" in text


def test_synopsis_requires_organizational_source_and_rejects_unsupported_claim() -> None:
    changed = bundle("thesis-synopsis")
    changed["sources"][1]["representation"] = "text"
    changed["claims"].append(
        claim("CL-NEW", "main_content", status="unsupported", structure_ids=["SEC-SYNOPSIS"])
    )

    report = VALIDATOR.validate_bundle(changed)
    text = errors(report)
    assert "requires a source with representation ['organizational']" in text
    assert "cannot introduce an unsupported claim" in text


def test_approbation_uses_only_organizational_evidence_not_scientific_results() -> None:
    changed = bundle("approbation-record")
    changed["sources"][0]["representation"] = "text"
    changed["claims"][0]["claim_type"] = "causal"
    changed["claims"][0]["causal_basis"] = "randomized experiment"

    report = VALIDATOR.validate_bundle(changed)
    text = errors(report)
    assert "accepts only organizational inputs" in text
    assert "evidence must come from an organizational source" in text
    assert "not a scientific result claim" in text


def test_bundle_builders_are_independent() -> None:
    first = bundle("novelty-statement")
    second = bundle("novelty-statement")
    first["claims"][0]["evidence_ids"].clear()
    assert second != first
