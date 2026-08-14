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

RESULT_FIELDS = {"result_id", "source_id", "locator", "value", "unit", "version", "analysis"}
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

    source_records = _as_list(data.get("sources"), "bundle.sources", errors)
    evidence_records = _as_list(data.get("evidence"), "bundle.evidence", errors)
    result_records = _as_list(data.get("results", []), "bundle.results", errors)
    structure_records = _as_list(data.get("structure", []), "bundle.structure", errors)
    claim_records = _as_list(data.get("claims"), "bundle.claims", errors)

    sources = _index_records(source_records, "source_id", "bundle.sources", errors)
    evidence = _index_records(evidence_records, "evidence_id", "bundle.evidence", errors)
    results = _index_records(result_records, "result_id", "bundle.results", errors)
    structure = _index_records(structure_records, "unit_id", "bundle.structure", errors)
    claims = _index_records(claim_records, "claim_id", "bundle.claims", errors)

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
        if "value" not in item or item.get("value") is None:
            errors.append(f"{path}.value: frozen result value is required")

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
                if structure.get(identifier, {}).get("status") == "planned":
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
            if rules["own_results"] == "forbidden" and results:
                errors.append(f"bundle.results: {genre!r} does not report own research results")
            if rules["internal_crossref"] == "forbidden":
                for claim_id, item in claims.items():
                    if item.get("structure_ids"):
                        errors.append(
                            f"claim[{claim_id}].structure_ids: {genre!r} carries no internal "
                            "references"
                        )

    counts = {
        "sources": len(sources),
        "evidence": len(evidence),
        "results": len(results),
        "structure": len(structure),
        "claims": len(claims),
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
