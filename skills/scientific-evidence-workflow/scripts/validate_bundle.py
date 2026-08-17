"""Validate a scientific-evidence-workflow bundle without external packages."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
MODES = {"qa", "literature_review", "manuscript", "record"}
FIGURE_MODES = {"with_figures", "without_figures"}
FORMATTING_MODES = {"journal_example", "section_only"}
REPRESENTATIONS = {
    "html",
    "pdf",
    "markdown",
    "text",
    "table",
    "figure",
    "data",
    "protocol",
    "note",
    "organizational",
}
SUPPORT_TYPES = {"direct", "inferential", "method", "context", "limitation", "contrary"}
VERIFICATION_STATUSES = {"extracted", "verified", "rejected"}
CLAIM_TYPES = {
    "factual",
    "numeric",
    "causal",
    "interpretive",
    "synthesis",
    "method",
    "limitation",
    "structural",
    "hypothesis",
}
UNIT_TYPES = {
    "part",
    "chapter",
    "section",
    "paragraph",
    "equation",
    "table",
    "figure",
    "appendix",
    "task",
    "conclusion",
    "proposition",
}
UNIT_STATUSES = {"planned", "drafted", "final"}
REVISION_CATEGORIES = {
    "scientific_precision",
    "evidence_boundary",
    "terminology",
    "logic",
    "grammar",
    "structure",
}
REVISION_STATUSES = {"proposed", "accepted", "rejected"}

# Genres implemented by this skill. The repository keeps this table identical to
# registry/genres.yaml with a drift test; the skill itself stays self-contained
# and never reads that file.
GENRES: dict[str, dict[str, Any]] = {
    "article-annotation": {
        "bundle_mode": "qa",
        "literature": "required",
        "own_results": "forbidden",
        "internal_crossref": "forbidden",
        "organizational": "forbidden",
        "source_min": 1,
        "source_max": 1,
        "source_representations": None,
    },
    "stage-report": {
        "bundle_mode": "record",
        "literature": "allowed",
        "own_results": "required",
        "internal_crossref": "allowed",
        "organizational": "allowed",
        "source_min": 1,
        "source_max": None,
        "source_representations": None,
    },
    "micro-review": {
        "bundle_mode": "literature_review",
        "literature": "required",
        "own_results": "forbidden",
        "internal_crossref": "allowed",
        "organizational": "forbidden",
        "source_min": 2,
        "source_max": 5,
        "source_representations": None,
    },
    "experiment-description": {
        "bundle_mode": "record",
        "literature": "allowed",
        "own_results": "allowed",
        "internal_crossref": "allowed",
        "organizational": "allowed",
        "source_min": 1,
        "source_max": None,
        "source_representations": ["protocol", "data"],
    },
    "procedure-record": {
        "bundle_mode": "record",
        "literature": "forbidden",
        "own_results": "allowed",
        "internal_crossref": "allowed",
        "organizational": "forbidden",
        "source_min": 1,
        "source_max": None,
        "source_representations": ["protocol", "data", "note"],
    },
    "decision-log": {
        "bundle_mode": "record",
        "literature": "allowed",
        "own_results": "allowed",
        "internal_crossref": "allowed",
        "organizational": "forbidden",
        "source_min": 1,
        "source_max": None,
        "source_representations": None,
    },
    "stage-presentation": {
        "bundle_mode": "record",
        "literature": "allowed",
        "own_results": "required",
        "internal_crossref": "allowed",
        "organizational": "allowed",
        "source_min": 1,
        "source_max": None,
        "source_representations": None,
        "figure_control": True,
    },
    "dissertation-outline": {
        "bundle_mode": "record",
        "literature": "allowed",
        "own_results": "allowed",
        "internal_crossref": "required",
        "organizational": "required",
        "source_min": 1,
        "source_max": None,
        "source_representations": ["organizational"],
        "required_structure_types": {"chapter", "section"},
    },
    "dissertation-introduction": {
        "bundle_mode": "manuscript",
        "literature": "required",
        "own_results": "allowed",
        "internal_crossref": "required",
        "organizational": "required",
        "source_min": 2,
        "source_max": None,
        "source_representations": ["organizational"],
        "required_output_sections": {
            "relevance",
            "state_of_art",
            "aim",
            "tasks",
            "novelty",
            "significance",
            "methods",
            "propositions",
            "validity_and_approbation",
        },
    },
    "dissertation-literature-review-chapter": {
        "bundle_mode": "manuscript",
        "literature": "required",
        "own_results": "forbidden",
        "internal_crossref": "required",
        "organizational": "forbidden",
        "source_min": 3,
        "source_max": None,
        "source_representations": None,
        "required_structure_types": {"chapter", "section"},
        "required_output_sections": {
            "review_scope",
            "conceptual_framework",
            "thematic_synthesis",
            "conflicts_and_limits",
            "research_gap",
            "chapter_conclusions",
        },
    },
    "dissertation-methods-chapter": {
        "bundle_mode": "manuscript",
        "literature": "allowed",
        "own_results": "allowed",
        "internal_crossref": "required",
        "organizational": "allowed",
        "source_min": 1,
        "source_max": None,
        "source_representations": ["data", "protocol"],
        "required_structure_types": {"chapter", "section"},
        "required_output_sections": {
            "method_scope",
            "procedure",
            "data_processing",
            "quality_control",
            "chapter_conclusions",
        },
    },
    "dissertation-results-chapter": {
        "bundle_mode": "manuscript",
        "literature": "forbidden",
        "own_results": "required",
        "internal_crossref": "required",
        "organizational": "forbidden",
        "source_min": 1,
        "source_max": None,
        "source_representations": None,
        "required_structure_types": {"chapter", "section"},
        "required_output_sections": {
            "result_scope",
            "reported_results",
            "negative_results",
            "result_traceability",
            "chapter_conclusions",
        },
        "allowed_output_sections": {
            "result_scope",
            "reported_results",
            "negative_results",
            "result_traceability",
            "chapter_conclusions",
        },
    },
    "dissertation-synthesis-chapter": {
        "bundle_mode": "manuscript",
        "literature": "required",
        "own_results": "required",
        "internal_crossref": "required",
        "organizational": "forbidden",
        "source_min": 1,
        "source_max": None,
        "source_representations": None,
        "required_structure_types": {"chapter", "section"},
        "required_output_sections": {
            "synthesis_scope",
            "result_interpretation",
            "literature_comparison",
            "conflicts_and_explanations",
            "limitations",
            "chapter_conclusions",
        },
        "allowed_output_sections": {
            "synthesis_scope",
            "result_interpretation",
            "literature_comparison",
            "conflicts_and_explanations",
            "limitations",
            "chapter_conclusions",
        },
    },
    "dissertation-conclusion": {
        "bundle_mode": "manuscript",
        "literature": "forbidden",
        "own_results": "required",
        "internal_crossref": "required",
        "organizational": "forbidden",
        "source_min": 1,
        "source_max": None,
        "source_representations": None,
        "required_structure_types": {"task", "conclusion"},
        "required_output_sections": {
            "conclusion_scope",
            "task_conclusions",
            "practical_recommendations",
            "future_work",
            "aim_closure",
        },
        "allowed_output_sections": {
            "conclusion_scope",
            "task_conclusions",
            "practical_recommendations",
            "future_work",
            "aim_closure",
        },
    },
    "defense-propositions": {
        "bundle_mode": "manuscript",
        "literature": "forbidden",
        "own_results": "required",
        "internal_crossref": "required",
        "organizational": "forbidden",
        "source_min": 1,
        "source_max": None,
        "source_representations": None,
        "required_structure_types": {"proposition"},
        "required_output_sections": {
            "proposition_statement",
            "proposition_boundary",
            "proposition_result_anchor",
            "proposition_section_anchor",
        },
        "allowed_output_sections": {
            "proposition_statement",
            "proposition_boundary",
            "proposition_result_anchor",
            "proposition_section_anchor",
        },
    },
    "novelty-statement": {
        "bundle_mode": "manuscript",
        "literature": "required",
        "own_results": "required",
        "internal_crossref": "required",
        "organizational": "forbidden",
        "source_min": 1,
        "source_max": None,
        "source_representations": None,
        "required_output_sections": {
            "novelty_boundary",
            "novelty_claim",
            "theoretical_significance",
            "practical_significance",
            "novelty_traceability",
        },
        "allowed_output_sections": {
            "novelty_boundary",
            "novelty_claim",
            "theoretical_significance",
            "practical_significance",
            "novelty_traceability",
        },
    },
    "thesis-synopsis": {
        "bundle_mode": "manuscript",
        "literature": "allowed",
        "own_results": "required",
        "internal_crossref": "required",
        "organizational": "required",
        "source_min": 1,
        "source_max": None,
        "source_representations": ["organizational"],
        "required_output_sections": {
            "synopsis_scope",
            "general_characteristics",
            "main_content",
            "synopsis_conclusion",
            "author_publications",
            "synopsis_traceability",
        },
        "allowed_output_sections": {
            "synopsis_scope",
            "general_characteristics",
            "main_content",
            "synopsis_conclusion",
            "author_publications",
            "synopsis_traceability",
        },
    },
    "approbation-record": {
        "bundle_mode": "record",
        "literature": "forbidden",
        "own_results": "forbidden",
        "internal_crossref": "allowed",
        "organizational": "required",
        "source_min": 1,
        "source_max": None,
        "source_representations": ["organizational"],
        "required_output_sections": {
            "conference_reports",
            "publication_records",
            "registration_records",
            "implementation_records",
            "approbation_crossrefs",
        },
        "allowed_output_sections": {
            "conference_reports",
            "publication_records",
            "registration_records",
            "implementation_records",
            "approbation_crossrefs",
        },
    },
    # Produces a normative card, not an evidence bundle. Validated by
    # scripts/validate_normative_card.py.
    "normative-pattern-analysis": {
        "bundle_mode": None,
        "literature": "forbidden",
        "own_results": "forbidden",
        "internal_crossref": "forbidden",
        "organizational": "required",
        "source_min": 1,
        "source_max": 1,
        "source_representations": None,
    },
}
CERTAINTIES = {"direct", "inferred", "uncertain", "conflicted"}
CLAIM_STATUSES = {"supported", "bounded", "unsupported", "conflicted"}
DISPOSITIONS = {"keep", "hedge", "keep_with_boundary", "drop", "request_input", "disclose_conflict"}

# Field names and required sets are module constants so that
# assets/evidence-bundle.schema.json can be checked against this validator
# instead of drifting away from it. See the schema drift test.
TOP_LEVEL_FIELDS = {
    "schema_version",
    "bundle_id",
    "task",
    "sources",
    "evidence",
    "results",
    "structure",
    "claims",
    "revisions",
}
TOP_LEVEL_REQUIRED_STRINGS = ("schema_version", "bundle_id")
TOP_LEVEL_REQUIRED = TOP_LEVEL_REQUIRED_STRINGS + ("task", "sources", "evidence", "claims")

TASK_FIELDS = {
    "mode",
    "genre",
    "request",
    "input_scope",
    "language",
    "audience",
    "figure_mode",
    "figure_source_ids",
    "formatting_mode",
    "journal_pattern_id",
    "journal_example_source_id",
}
TASK_REQUIRED = ("mode", "request")

SOURCE_FIELDS = {"source_id", "title", "content_hash", "representation", "local_ref", "version"}
SOURCE_REQUIRED = ("source_id", "title", "representation", "local_ref")

EVIDENCE_FIELDS = {
    "evidence_id",
    "source_id",
    "locator",
    "claim",
    "support_type",
    "fragment",
    "value",
    "unit",
    "study_context",
    "limitations",
    "verification_status",
}
EVIDENCE_REQUIRED = (
    "evidence_id",
    "source_id",
    "locator",
    "claim",
    "support_type",
    "verification_status",
)

RESULT_FIELDS = {"result_id", "source_id", "locator", "value", "unit", "version", "analysis", "approved"}
RESULT_REQUIRED_STRINGS = ("result_id", "source_id", "locator", "version")
RESULT_REQUIRED = RESULT_REQUIRED_STRINGS + ("value",)

STRUCTURE_FIELDS = {"unit_id", "unit_type", "label", "title", "parent_id", "document", "status"}
STRUCTURE_REQUIRED = ("unit_id", "unit_type", "label", "status")

CLAIM_FIELDS = {
    "claim_id",
    "text",
    "output_section",
    "claim_type",
    "certainty",
    "evidence_ids",
    "result_ids",
    "structure_ids",
    "status",
    "disposition",
    "boundary",
    "causal_basis",
    "attribution",
}
CLAIM_REQUIRED = (
    "claim_id",
    "text",
    "output_section",
    "claim_type",
    "certainty",
    "status",
    "disposition",
)

REVISION_FIELDS = {
    "revision_id",
    "locator",
    "structure_ids",
    "claim_ids",
    "original",
    "corrected",
    "reason",
    "category",
    "evidence_ids",
    "result_ids",
    "status",
}
REVISION_REQUIRED = (
    "revision_id",
    "locator",
    "original",
    "corrected",
    "reason",
    "category",
    "status",
)


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _as_list(value: Any, path: str, errors: list[str]) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{path}: expected a list")
        return []
    return value


def _check_allowed_keys(record: dict[str, Any], allowed: set[str], path: str, errors: list[str]) -> None:
    for key in sorted(set(record) - allowed):
        errors.append(f"{path}: unexpected field {key!r}")


def _check_required_strings(
    record: dict[str, Any], required: Iterable[str], path: str, errors: list[str]
) -> None:
    for key in required:
        if not _nonempty_string(record.get(key)):
            errors.append(f"{path}.{key}: expected a non-empty string")


def _cyclic_units(structure: dict[str, dict[str, Any]]) -> set[str]:
    """Return units whose parent chain closes on itself."""

    cyclic: set[str] = set()
    for unit_id in structure:
        walked: list[str] = []
        current: Any = unit_id
        while isinstance(current, str) and current in structure:
            if current in walked:
                cyclic.update(walked[walked.index(current) :])
                break
            walked.append(current)
            current = structure[current].get("parent_id")
    return cyclic


def _index_records(
    records: list[Any], id_field: str, path: str, errors: list[str]
) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for index, value in enumerate(records):
        item_path = f"{path}[{index}]"
        if not isinstance(value, dict):
            errors.append(f"{item_path}: expected an object")
            continue
        identifier = value.get(id_field)
        if not _nonempty_string(identifier) or not ID_PATTERN.fullmatch(identifier):
            errors.append(f"{item_path}.{id_field}: invalid identifier")
            continue
        if identifier in indexed:
            errors.append(f"{item_path}.{id_field}: duplicate identifier {identifier!r}")
            continue
        indexed[identifier] = value
    return indexed


def validate_bundle(data: Any) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(data, dict):
        return {"valid": False, "errors": ["bundle: expected an object"], "warnings": [], "counts": {}}

    _check_allowed_keys(data, TOP_LEVEL_FIELDS, "bundle", errors)
    _check_required_strings(data, TOP_LEVEL_REQUIRED_STRINGS, "bundle", errors)
    if data.get("schema_version") != "1.0":
        errors.append("bundle.schema_version: expected '1.0'")

    task = data.get("task")
    if not isinstance(task, dict):
        errors.append("bundle.task: expected an object")
        task = {}
    else:
        _check_allowed_keys(task, TASK_FIELDS, "bundle.task", errors)
        _check_required_strings(task, TASK_REQUIRED, "bundle.task", errors)
    mode = task.get("mode")
    if mode not in MODES:
        errors.append(f"bundle.task.mode: expected one of {sorted(MODES)}")

    genre = task.get("genre")
    genre_rules = GENRES.get(genre) if _nonempty_string(genre) else None

    # Figures need the same discipline wherever they appear, not only in a
    # manuscript: a chart shown at a meeting is as capable of inventing data as
    # a figure in a paper. Journal formatting stays manuscript-only.
    figure_controlled = mode == "manuscript" or bool(
        genre_rules and genre_rules.get("figure_control")
    )
    if figure_controlled:
        figure_mode = task.get("figure_mode")
        if figure_mode not in FIGURE_MODES:
            errors.append(
                f"bundle.task.figure_mode: {genre or mode} requires one of {sorted(FIGURE_MODES)}"
            )
    if mode == "manuscript":
        formatting_mode = task.get("formatting_mode")
        if formatting_mode not in FORMATTING_MODES:
            errors.append(
                "bundle.task.formatting_mode: manuscript requires one of "
                f"{sorted(FORMATTING_MODES)}"
            )
        if formatting_mode == "journal_example":
            _check_required_strings(
                task,
                ["journal_pattern_id", "journal_example_source_id"],
                "bundle.task",
                errors,
            )
    if figure_controlled:
        figure_mode = task.get("figure_mode")
        figure_source_ids = task.get("figure_source_ids")
        if figure_mode == "with_figures":
            if (
                not isinstance(figure_source_ids, list)
                or not figure_source_ids
                or not all(_nonempty_string(value) for value in figure_source_ids)
            ):
                errors.append(
                    "bundle.task.figure_source_ids: with_figures requires a non-empty "
                    "list of source identifiers"
                )
        elif figure_mode == "without_figures" and "figure_source_ids" in task:
            errors.append(
                "bundle.task.figure_source_ids: must be omitted when figure_mode is "
                "'without_figures'"
            )
    input_scope = task.get("input_scope", [])
    if not isinstance(input_scope, list) or not all(_nonempty_string(item) for item in input_scope):
        errors.append("bundle.task.input_scope: expected a list of source identifiers")
        input_scope = []
    elif len(set(input_scope)) != len(input_scope):
        errors.append("bundle.task.input_scope: duplicate source identifiers are forbidden")

    source_records = _as_list(data.get("sources"), "bundle.sources", errors)
    evidence_records = _as_list(data.get("evidence"), "bundle.evidence", errors)
    result_records = _as_list(data.get("results", []), "bundle.results", errors)
    structure_records = _as_list(data.get("structure", []), "bundle.structure", errors)
    claim_records = _as_list(data.get("claims"), "bundle.claims", errors)
    revision_records = _as_list(data.get("revisions", []), "bundle.revisions", errors)

    sources = _index_records(source_records, "source_id", "bundle.sources", errors)
    evidence = _index_records(evidence_records, "evidence_id", "bundle.evidence", errors)
    results = _index_records(result_records, "result_id", "bundle.results", errors)
    structure = _index_records(structure_records, "unit_id", "bundle.structure", errors)
    claims = _index_records(claim_records, "claim_id", "bundle.claims", errors)
    revisions = _index_records(revision_records, "revision_id", "bundle.revisions", errors)

    for source_id, source in sources.items():
        path = f"source[{source_id}]"
        _check_allowed_keys(source, SOURCE_FIELDS, path, errors)
        _check_required_strings(source, SOURCE_REQUIRED, path, errors)
        if source.get("representation") not in REPRESENTATIONS:
            errors.append(f"{path}.representation: unsupported representation")
        content_hash = source.get("content_hash")
        if content_hash is not None and not _nonempty_string(content_hash):
            errors.append(f"{path}.content_hash: expected a string or null")
        if content_hash is None and not _nonempty_string(source.get("version")):
            warnings.append(f"{path}: source has neither content_hash nor version")

    for source_id in input_scope:
        if source_id not in sources:
            errors.append(f"bundle.task.input_scope: unknown source {source_id!r}")
    if figure_controlled and task.get("figure_mode") == "with_figures":
        for source_id in task.get("figure_source_ids", []):
            if source_id not in sources:
                errors.append(f"bundle.task.figure_source_ids: unknown source {source_id!r}")
            elif source_id not in input_scope:
                errors.append(
                    f"bundle.task.figure_source_ids: source {source_id!r} is outside input_scope"
                )
    journal_example_source_id = task.get("journal_example_source_id")
    if mode == "manuscript" and task.get("formatting_mode") == "journal_example":
        if _nonempty_string(journal_example_source_id) and journal_example_source_id not in sources:
            errors.append(
                "bundle.task.journal_example_source_id: unknown source "
                f"{journal_example_source_id!r}"
            )
        elif _nonempty_string(journal_example_source_id) and journal_example_source_id not in input_scope:
            errors.append(
                "bundle.task.journal_example_source_id: source "
                f"{journal_example_source_id!r} is outside input_scope"
            )

    for evidence_id, item in evidence.items():
        path = f"evidence[{evidence_id}]"
        _check_allowed_keys(item, EVIDENCE_FIELDS, path, errors)
        _check_required_strings(item, EVIDENCE_REQUIRED, path, errors)
        if item.get("source_id") not in sources:
            errors.append(f"{path}.source_id: unknown source {item.get('source_id')!r}")
        elif item.get("source_id") not in input_scope:
            errors.append(
                f"{path}.source_id: source {item.get('source_id')!r} is outside input_scope"
            )
        if item.get("support_type") not in SUPPORT_TYPES:
            errors.append(f"{path}.support_type: expected one of {sorted(SUPPORT_TYPES)}")
        if item.get("verification_status") not in VERIFICATION_STATUSES:
            errors.append(
                f"{path}.verification_status: expected one of {sorted(VERIFICATION_STATUSES)}"
            )
        fragment = item.get("fragment")
        if fragment is not None and not isinstance(fragment, str):
            errors.append(f"{path}.fragment: expected a string or null")

    for result_id, item in results.items():
        path = f"result[{result_id}]"
        _check_allowed_keys(item, RESULT_FIELDS, path, errors)
        _check_required_strings(item, RESULT_REQUIRED_STRINGS, path, errors)
        if item.get("source_id") not in sources:
            errors.append(f"{path}.source_id: unknown source {item.get('source_id')!r}")
        elif item.get("source_id") not in input_scope:
            errors.append(
                f"{path}.source_id: source {item.get('source_id')!r} is outside input_scope"
            )
        if "value" not in item or item.get("value") is None:
            errors.append(f"{path}.value: frozen result value is required")
        if "approved" in item and not isinstance(item.get("approved"), bool):
            errors.append(f"{path}.approved: expected boolean")

    for unit_id, item in structure.items():
        path = f"structure[{unit_id}]"
        _check_allowed_keys(item, STRUCTURE_FIELDS, path, errors)
        _check_required_strings(item, STRUCTURE_REQUIRED, path, errors)
        if item.get("unit_type") not in UNIT_TYPES:
            errors.append(f"{path}.unit_type: expected one of {sorted(UNIT_TYPES)}")
        if item.get("status") not in UNIT_STATUSES:
            errors.append(f"{path}.status: expected one of {sorted(UNIT_STATUSES)}")
        parent_id = item.get("parent_id")
        if parent_id is not None:
            if not _nonempty_string(parent_id):
                errors.append(f"{path}.parent_id: expected a string or null")
            elif parent_id == unit_id:
                errors.append(f"{path}.parent_id: a unit cannot contain itself")
            elif parent_id not in structure:
                errors.append(f"{path}.parent_id: unknown unit {parent_id!r}")

    for unit_id in sorted(_cyclic_units(structure)):
        errors.append(f"structure[{unit_id}]: parent chain closes on itself")

    for revision_id, item in revisions.items():
        path = f"revision[{revision_id}]"
        _check_allowed_keys(item, REVISION_FIELDS, path, errors)
        _check_required_strings(item, REVISION_REQUIRED, path, errors)
        if item.get("category") not in REVISION_CATEGORIES:
            errors.append(f"{path}.category: expected one of {sorted(REVISION_CATEGORIES)}")
        if item.get("status") not in REVISION_STATUSES:
            errors.append(f"{path}.status: expected one of {sorted(REVISION_STATUSES)}")
        if item.get("original") == item.get("corrected"):
            errors.append(f"{path}: original and corrected wording must differ")

        revision_refs: dict[str, tuple[list[str], dict[str, dict[str, Any]]]] = {
            "structure_ids": (item.get("structure_ids", []), structure),
            "claim_ids": (item.get("claim_ids", []), claims),
            "evidence_ids": (item.get("evidence_ids", []), evidence),
            "result_ids": (item.get("result_ids", []), results),
        }
        clean_refs: dict[str, list[str]] = {}
        for field, (values, known) in revision_refs.items():
            if not isinstance(values, list) or not all(
                _nonempty_string(value) for value in values
            ):
                errors.append(f"{path}.{field}: expected a list of identifiers")
                clean_refs[field] = []
                continue
            clean_refs[field] = values
            for identifier in sorted(set(values) - set(known)):
                errors.append(f"{path}.{field}: unknown identifier {identifier!r}")

        semantic = item.get("category") in {
            "scientific_precision",
            "evidence_boundary",
            "terminology",
            "logic",
        }
        if item.get("status") == "accepted" and semantic:
            if not clean_refs["claim_ids"]:
                errors.append(f"{path}.claim_ids: accepted semantic correction requires a claim")
            if not (clean_refs["evidence_ids"] or clean_refs["result_ids"]):
                errors.append(
                    f"{path}: accepted semantic correction requires evidence_ids or result_ids"
                )
        if (
            item.get("status") == "accepted"
            and item.get("category") == "structure"
            and not clean_refs["structure_ids"]
        ):
            errors.append(
                f"{path}.structure_ids: accepted structural correction requires a unit"
            )

    for claim_id, item in claims.items():
        path = f"claim[{claim_id}]"
        _check_allowed_keys(item, CLAIM_FIELDS, path, errors)
        _check_required_strings(item, CLAIM_REQUIRED, path, errors)
        if item.get("claim_type") not in CLAIM_TYPES:
            errors.append(f"{path}.claim_type: expected one of {sorted(CLAIM_TYPES)}")
        if item.get("certainty") not in CERTAINTIES:
            errors.append(f"{path}.certainty: expected one of {sorted(CERTAINTIES)}")
        if item.get("status") not in CLAIM_STATUSES:
            errors.append(f"{path}.status: expected one of {sorted(CLAIM_STATUSES)}")
        if item.get("disposition") not in DISPOSITIONS:
            errors.append(f"{path}.disposition: expected one of {sorted(DISPOSITIONS)}")

        evidence_ids = item.get("evidence_ids", [])
        result_ids = item.get("result_ids", [])
        structure_ids = item.get("structure_ids", [])
        if not isinstance(evidence_ids, list) or not all(_nonempty_string(value) for value in evidence_ids):
            errors.append(f"{path}.evidence_ids: expected a list of identifiers")
            evidence_ids = []
        if not isinstance(result_ids, list) or not all(_nonempty_string(value) for value in result_ids):
            errors.append(f"{path}.result_ids: expected a list of identifiers")
            result_ids = []
        if not isinstance(structure_ids, list) or not all(_nonempty_string(value) for value in structure_ids):
            errors.append(f"{path}.structure_ids: expected a list of identifiers")
            structure_ids = []

        unknown_evidence = sorted(set(evidence_ids) - set(evidence))
        unknown_results = sorted(set(result_ids) - set(results))
        unknown_units = sorted(set(structure_ids) - set(structure))
        for identifier in unknown_evidence:
            errors.append(f"{path}.evidence_ids: unknown evidence {identifier!r}")
        for identifier in unknown_results:
            errors.append(f"{path}.result_ids: unknown result {identifier!r}")
        for identifier in unknown_units:
            errors.append(f"{path}.structure_ids: unknown unit {identifier!r}")

        status = item.get("status")
        disposition = item.get("disposition")

        # An internal reference points; it does not support. Only a structural
        # claim, which is a statement about the organization of the work, is
        # established by the units it names.
        references = evidence_ids + result_ids
        if item.get("claim_type") == "structural":
            if not structure_ids:
                errors.append(f"{path}.structure_ids: required for a structural claim")
            references = references + structure_ids
            for identifier in sorted(set(structure_ids)):
                if (
                    status in {"supported", "bounded"}
                    and structure.get(identifier, {}).get("status") == "planned"
                ):
                    errors.append(
                        f"{path}: structural claim cannot rest on planned unit {identifier!r}"
                    )
        if status == "supported":
            if not references:
                errors.append(f"{path}: supported claim requires evidence or result references")
            if disposition != "keep":
                errors.append(f"{path}: supported claim must use disposition 'keep'")
        elif status == "bounded":
            if not references:
                errors.append(f"{path}: bounded claim requires evidence or result references")
            if disposition not in {"hedge", "keep_with_boundary"}:
                errors.append(f"{path}: bounded claim must use 'hedge' or 'keep_with_boundary'")
            if not _nonempty_string(item.get("boundary")):
                errors.append(f"{path}.boundary: required for bounded claim")
        elif status == "unsupported":
            if disposition not in {"drop", "request_input"}:
                errors.append(f"{path}: unsupported claim must use 'drop' or 'request_input'")
        elif status == "conflicted":
            if len(set(references)) < 2:
                errors.append(f"{path}: conflicted claim requires at least two distinct references")
            if disposition != "disclose_conflict":
                errors.append(f"{path}: conflicted claim must use 'disclose_conflict'")

        cited_evidence = [evidence[value] for value in evidence_ids if value in evidence]
        if any(record.get("verification_status") == "rejected" for record in cited_evidence):
            errors.append(f"{path}: rejected evidence cannot support a claim")
        if status == "supported" and item.get("claim_type") != "limitation" and cited_evidence and all(
            record.get("support_type") in {"contrary", "limitation"} for record in cited_evidence
        ) and not result_ids:
            errors.append(f"{path}: supported claim cannot rely only on contrary or limitation evidence")
        if any(record.get("verification_status") == "extracted" for record in cited_evidence):
            if status in {"supported", "bounded"}:
                errors.append(
                    f"{path}: unverified extracted evidence cannot support a supported or bounded claim"
                )
            else:
                warnings.append(f"{path}: claim uses evidence that has not been verified")

        if item.get("claim_type") == "numeric":
            has_evidence_value = any(record.get("value") is not None for record in cited_evidence)
            if not result_ids and not has_evidence_value:
                errors.append(f"{path}: numeric claim requires a result or evidence record with value")
            if mode == "manuscript" and str(item.get("output_section", "")).lower() == "results" and not result_ids:
                errors.append(f"{path}: manuscript Results numeric claim requires result_ids")

        if (
            item.get("claim_type") == "causal"
            and item.get("certainty") == "direct"
            and status == "supported"
            and not _nonempty_string(item.get("causal_basis"))
        ):
            errors.append(f"{path}.causal_basis: required for direct supported causal claim")

        # A hypothesis is a recorded conjecture, never an assertion of the
        # current analysis. Keeping it unsupported blocks the path by which a
        # working guess becomes a reported result.
        if item.get("claim_type") == "hypothesis":
            if not _nonempty_string(item.get("attribution")):
                errors.append(f"{path}.attribution: required for a hypothesis")
            if status != "unsupported":
                errors.append(f"{path}: a hypothesis must keep status 'unsupported'")
            if disposition != "request_input":
                errors.append(f"{path}: a hypothesis must use disposition 'request_input'")

    if genre is not None:
        if not _nonempty_string(genre) or genre not in GENRES:
            errors.append(f"bundle.task.genre: unknown or unimplemented genre {genre!r}")
        elif GENRES[genre]["bundle_mode"] is None:
            errors.append(
                f"bundle.task.genre: {genre!r} produces a record of its own kind, not an "
                "evidence bundle; validate it with its own validator"
            )
        else:
            rules = GENRES[genre]
            if mode != rules["bundle_mode"]:
                errors.append(
                    f"bundle.task.genre: {genre!r} runs in mode {rules['bundle_mode']!r}, "
                    f"not {mode!r}"
                )
            if len(input_scope) < rules["source_min"]:
                errors.append(
                    f"bundle.task.input_scope: {genre!r} requires at least "
                    f"{rules['source_min']} source(s)"
                )
            if rules["source_max"] is not None and len(input_scope) > rules["source_max"]:
                warnings.append(
                    f"bundle.task.input_scope: {genre!r} is defined for at most "
                    f"{rules['source_max']} source(s); consider a wider genre"
                )
            organizational_inputs = {
                source_id
                for source_id in input_scope
                if sources.get(source_id, {}).get("representation") == "organizational"
            }
            if rules["organizational"] == "forbidden" and organizational_inputs:
                errors.append(
                    f"bundle.task.input_scope: {genre!r} forbids organizational input"
                )
            if rules["organizational"] == "required" and not organizational_inputs:
                errors.append(
                    f"bundle.task.input_scope: {genre!r} requires organizational input"
                )

            required_reps = rules["source_representations"]
            if required_reps:
                present = {
                    sources[source_id].get("representation")
                    for source_id in input_scope
                    if source_id in sources
                }
                if not present & set(required_reps):
                    errors.append(
                        f"bundle.task.input_scope: {genre!r} requires a source with "
                        f"representation {sorted(required_reps)}; without a record of what "
                        "was performed the account would be reconstructed"
                    )
            if rules["literature"] == "required" and not evidence:
                errors.append(f"bundle.evidence: {genre!r} requires literature evidence")
            if rules["literature"] == "forbidden":
                # `context` is the literature-context support type. A record of
                # what was done does not argue from the field's opinion.
                for evidence_id, item in evidence.items():
                    if item.get("support_type") == "context":
                        errors.append(
                            f"evidence[{evidence_id}].support_type: {genre!r} carries no "
                            "literature context"
                        )
            if rules["own_results"] == "required" and not results:
                errors.append(f"bundle.results: {genre!r} requires own research results")
            if results and genre in {
                "dissertation-outline",
                "dissertation-introduction",
                "dissertation-methods-chapter",
                "dissertation-results-chapter",
                "dissertation-synthesis-chapter",
                "dissertation-conclusion",
                "defense-propositions",
                "novelty-statement",
                "thesis-synopsis",
            }:
                for result_id, result in results.items():
                    if result.get("approved") is not True:
                        errors.append(
                            f"result[{result_id}].approved: {genre!r} requires approved=true "
                            "for every own result"
                        )
            if rules["own_results"] == "forbidden" and results:
                errors.append(f"bundle.results: {genre!r} does not report own research results")
            if rules["internal_crossref"] == "forbidden":
                for claim_id, item in claims.items():
                    if item.get("structure_ids"):
                        errors.append(
                            f"claim[{claim_id}].structure_ids: {genre!r} carries no internal "
                            "references"
                        )
            elif rules["internal_crossref"] == "required":
                if not structure:
                    errors.append(f"bundle.structure: {genre!r} requires addressable units")
                for claim_id, item in claims.items():
                    if not item.get("structure_ids"):
                        errors.append(
                            f"claim[{claim_id}].structure_ids: {genre!r} requires an "
                            "addressable output unit"
                        )

            required_structure_types = rules.get("required_structure_types", set())
            present_structure_types = {item.get("unit_type") for item in structure.values()}
            for unit_type in sorted(required_structure_types - present_structure_types):
                errors.append(f"bundle.structure: {genre!r} requires a {unit_type!r} unit")

            required_sections = rules.get("required_output_sections", set())
            present_sections = {item.get("output_section") for item in claims.values()}
            for section in sorted(required_sections - present_sections):
                errors.append(
                    f"bundle.claims: {genre!r} requires output_section {section!r}"
                )

            allowed_sections = rules.get("allowed_output_sections")
            if allowed_sections is not None:
                for claim_id, item in claims.items():
                    section = item.get("output_section")
                    if section not in allowed_sections:
                        errors.append(
                            f"claim[{claim_id}].output_section: {genre!r} does not define "
                            f"section {section!r}; expected one of {sorted(allowed_sections)}"
                        )

            # These dissertation genres exclude administrative records from
            # their scientific input. This is checked only where the source
            # representation makes the exclusion directly observable.
            if genre in {
                "dissertation-results-chapter",
                "dissertation-synthesis-chapter",
                "dissertation-conclusion",
                "defense-propositions",
                "novelty-statement",
            }:
                for source_id in input_scope:
                    if sources.get(source_id, {}).get("representation") == "organizational":
                        errors.append(
                            f"source[{source_id}].representation: {genre!r} forbids "
                            "organizational input"
                        )
                for evidence_id, item in evidence.items():
                    source = sources.get(item.get("source_id"), {})
                    if source.get("representation") == "organizational":
                        errors.append(
                            f"evidence[{evidence_id}].source_id: {genre!r} forbids "
                            "organizational evidence"
                        )

            if genre == "dissertation-results-chapter":
                for claim_id, item in claims.items():
                    if (
                        item.get("status") in {"supported", "bounded"}
                        and item.get("claim_type") != "structural"
                        and not item.get("result_ids")
                    ):
                        errors.append(
                            f"claim[{claim_id}]: dissertation-results-chapter requires "
                            "result_ids for every supported or bounded result statement"
                        )

            if genre == "dissertation-synthesis-chapter":
                scoped_literature_ids = {
                    evidence_id
                    for evidence_id, record in evidence.items()
                    if record.get("source_id") in input_scope
                    and sources.get(record.get("source_id"), {}).get("representation")
                    in {"html", "pdf", "markdown", "text"}
                }
                if not scoped_literature_ids:
                    errors.append(
                        "bundle.evidence: dissertation-synthesis-chapter requires "
                        "in-scope literature evidence"
                    )
                for claim_id, item in claims.items():
                    if item.get("status") not in {"supported", "bounded"}:
                        continue
                    if item.get("claim_type") == "structural":
                        continue
                    section = item.get("output_section")
                    if section in {"result_interpretation", "chapter_conclusions"} and not item.get(
                        "result_ids"
                    ):
                        errors.append(
                            f"claim[{claim_id}]: synthesis section {section!r} requires "
                            "result_ids"
                        )
                    if section == "literature_comparison" and (
                        not (set(item.get("evidence_ids", [])) & scoped_literature_ids)
                        or not item.get("result_ids")
                    ):
                        errors.append(
                            f"claim[{claim_id}]: synthesis literature_comparison requires "
                            "in-scope literature evidence_ids and result_ids"
                        )

            if genre == "dissertation-conclusion":
                for claim_id, item in claims.items():
                    if item.get("status") == "unsupported":
                        errors.append(
                            f"claim[{claim_id}]: dissertation-conclusion cannot introduce "
                            "an unsupported claim"
                        )
                    if (
                        item.get("status") in {"supported", "bounded"}
                        and item.get("claim_type") != "structural"
                        and not item.get("result_ids")
                    ):
                        errors.append(
                            f"claim[{claim_id}]: dissertation-conclusion requires result_ids "
                            "for every supported or bounded conclusion statement"
                        )

                task_conclusion_claims = [
                    item
                    for item in claims.values()
                    if item.get("output_section") == "task_conclusions"
                ]
                covered_units = {
                    identifier
                    for item in task_conclusion_claims
                    for identifier in item.get("structure_ids", [])
                }
                for claim in task_conclusion_claims:
                    anchored_types = {
                        structure.get(identifier, {}).get("unit_type")
                        for identifier in claim.get("structure_ids", [])
                    }
                    if not {"task", "conclusion"}.issubset(anchored_types):
                        errors.append(
                            f"claim[{claim.get('claim_id')}]: task_conclusions requires both "
                            "task and conclusion structure_ids"
                        )
                for unit_id, unit in structure.items():
                    if unit.get("unit_type") in {"task", "conclusion"} and unit_id not in covered_units:
                        errors.append(
                            f"structure[{unit_id}]: dissertation-conclusion requires coverage "
                            "by a task_conclusions claim"
                        )

            if genre == "defense-propositions":
                covered_propositions: set[str] = set()
                for claim_id, item in claims.items():
                    if item.get("status") not in {"supported", "bounded"}:
                        continue
                    if item.get("claim_type") == "structural":
                        continue
                    proposition_units = {
                        identifier
                        for identifier in item.get("structure_ids", [])
                        if structure.get(identifier, {}).get("unit_type") == "proposition"
                    }
                    covered_propositions.update(proposition_units)
                    if not item.get("result_ids") or not proposition_units:
                        errors.append(
                            f"claim[{claim_id}]: defense proposition requires result_ids and "
                            "a proposition structure_id"
                        )
                for unit_id, unit in structure.items():
                    if unit.get("unit_type") == "proposition" and unit_id not in covered_propositions:
                        errors.append(
                            f"structure[{unit_id}]: defense-propositions requires coverage by "
                            "a supported or bounded proposition claim"
                        )

            if genre == "novelty-statement":
                scoped_literature_ids = {
                    evidence_id
                    for evidence_id, record in evidence.items()
                    if record.get("source_id") in input_scope
                    and sources.get(record.get("source_id"), {}).get("representation")
                    in {"html", "pdf", "markdown", "text"}
                }
                for claim_id, item in claims.items():
                    if item.get("status") in {"supported", "bounded"} and item.get(
                        "claim_type"
                    ) != "structural":
                        if not (
                            set(item.get("evidence_ids", [])) & scoped_literature_ids
                        ) or not item.get("result_ids"):
                            errors.append(
                                f"claim[{claim_id}]: novelty-statement requires in-scope "
                                "literature evidence_ids and result_ids"
                            )
                    if (
                        item.get("status") == "bounded"
                        or item.get("output_section") in {"novelty_boundary", "novelty_claim"}
                    ) and not _nonempty_string(item.get("boundary")):
                        errors.append(
                            f"claim[{claim_id}].boundary: novelty or bounded claim requires "
                            "an explicit comparison boundary"
                        )

            if genre == "thesis-synopsis":
                for claim_id, item in claims.items():
                    if item.get("status") == "unsupported":
                        errors.append(
                            f"claim[{claim_id}]: thesis-synopsis cannot introduce an "
                            "unsupported claim"
                        )

            if genre == "approbation-record":
                for source_id in input_scope:
                    if sources.get(source_id, {}).get("representation") != "organizational":
                        errors.append(
                            f"source[{source_id}].representation: approbation-record accepts "
                            "only organizational inputs"
                        )
                for evidence_id, item in evidence.items():
                    source = sources.get(item.get("source_id"), {})
                    if source.get("representation") != "organizational":
                        errors.append(
                            f"evidence[{evidence_id}].source_id: approbation-record evidence "
                            "must come from an organizational source"
                        )
                for claim_id, item in claims.items():
                    if item.get("result_ids"):
                        errors.append(
                            f"claim[{claim_id}].result_ids: approbation-record does not use "
                            "scientific results as organizational evidence"
                        )
                    if item.get("claim_type") in {"causal", "synthesis", "method"}:
                        errors.append(
                            f"claim[{claim_id}].claim_type: approbation-record records an "
                            "organizational fact, not a scientific result claim"
                        )

            if genre == "dissertation-introduction":
                aims = [
                    item
                    for item in claims.values()
                    if item.get("output_section") == "aim"
                    and item.get("status") in {"supported", "bounded"}
                ]
                if len(aims) != 1:
                    errors.append(
                        "bundle.claims: dissertation-introduction requires exactly one "
                        "supported or bounded aim"
                    )

                novelty = [
                    item for item in claims.values() if item.get("output_section") == "novelty"
                ]
                for item in novelty:
                    if item.get("status") != "bounded" or not _nonempty_string(
                        item.get("boundary")
                    ):
                        errors.append(
                            f"claim[{item.get('claim_id')}]: dissertation novelty must be "
                            "bounded and name its comparison boundary"
                        )

                propositions = [
                    item
                    for item in claims.values()
                    if item.get("output_section") == "propositions"
                ]
                for item in propositions:
                    anchored_units = [
                        structure.get(identifier, {})
                        for identifier in item.get("structure_ids", [])
                        if identifier in structure
                    ]
                    if not item.get("result_ids") or not any(
                        unit.get("unit_type") in {"proposition", "section"}
                        for unit in anchored_units
                    ):
                        errors.append(
                            f"claim[{item.get('claim_id')}]: dissertation proposition "
                            "requires result_ids and a proposition or section unit"
                        )

            if genre == "dissertation-literature-review-chapter":
                for claim_id, item in claims.items():
                    if item.get("output_section") == "research_gap":
                        if item.get("status") != "bounded" or not _nonempty_string(
                            item.get("boundary")
                        ):
                            errors.append(
                                f"claim[{claim_id}]: dissertation literature-review gap "
                                "must be bounded and name its corpus boundary"
                            )

                    if item.get("status") not in {"supported", "bounded"}:
                        continue
                    if item.get("claim_type") == "structural":
                        continue
                    scoped_literature = [
                        evidence.get(identifier, {})
                        for identifier in item.get("evidence_ids", [])
                        if identifier in evidence
                        and evidence[identifier].get("source_id") in input_scope
                        and sources.get(evidence[identifier].get("source_id"), {}).get(
                            "representation"
                        )
                        in {"html", "pdf", "markdown", "text"}
                    ]
                    if not scoped_literature:
                        errors.append(
                            f"claim[{claim_id}]: dissertation literature-review requires "
                            "in-scope literature evidence for every supported synthesis"
                        )

            if genre == "dissertation-methods-chapter":
                for claim_id, item in claims.items():
                    if item.get("status") not in {"supported", "bounded"}:
                        continue
                    if item.get("claim_type") == "structural":
                        continue
                    recorded_method_evidence = [
                        evidence.get(identifier, {})
                        for identifier in item.get("evidence_ids", [])
                        if identifier in evidence
                        and evidence[identifier].get("source_id") in input_scope
                        and sources.get(evidence[identifier].get("source_id"), {}).get(
                            "representation"
                        )
                        in {"protocol", "data"}
                    ]
                    if not recorded_method_evidence and not item.get("result_ids"):
                        errors.append(
                            f"claim[{claim_id}]: dissertation-methods-chapter requires "
                            "protocol/data evidence or an approved result for every "
                            "supported method statement"
                        )

    counts = {
        "sources": len(sources),
        "evidence": len(evidence),
        "results": len(results),
        "structure": len(structure),
        "claims": len(claims),
        "revisions": len(revisions),
        "supported_claims": sum(1 for item in claims.values() if item.get("status") == "supported"),
        "bounded_claims": sum(1 for item in claims.values() if item.get("status") == "bounded"),
        "unsupported_claims": sum(1 for item in claims.values() if item.get("status") == "unsupported"),
        "conflicted_claims": sum(1 for item in claims.values() if item.get("status") == "conflicted"),
    }
    return {"valid": not errors, "errors": errors, "warnings": warnings, "counts": counts}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bundle", type=Path, help="Path to evidence-bundle JSON")
    parser.add_argument("--output", type=Path, help="Optional validation-report path")
    args = parser.parse_args()

    try:
        data = json.loads(args.bundle.read_text(encoding="utf-8-sig"))
        report = validate_bundle(data)
    except (OSError, json.JSONDecodeError) as error:
        report = {"valid": False, "errors": [str(error)], "warnings": [], "counts": {}}

    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
