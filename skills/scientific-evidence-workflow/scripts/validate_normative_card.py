"""Validate a normative-pattern card without external packages.

A card is what turns a document into requirements the workflow may act on.
Everything here exists to stop three failures:

1. a requirement recorded without a locator, which cannot be checked back;
2. a card built from a catalogue entry rather than from the text, which would
   let a designation stand in for content nobody has read;
3. a silent overwrite of an earlier observation when a newer document differs.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
VERSION_PATTERN = re.compile(r"^v\d+$")

SOURCE_KINDS = {"document", "catalogue_card", "index_page"}
OBSERVATION = {"observed", "not_observed", "uncertain"}
BINDING = {"mandatory", "recommended", "conditional", "unclear"}

CARD_FIELDS = {
    "schema_version",
    "pattern_id",
    "record_version",
    "document_id",
    "title",
    "authority",
    "tier",
    "provenance",
    "coverage",
    "requirements",
    "not_observed",
    "conflicts",
    "application_notes",
}
CARD_REQUIRED = ("schema_version", "pattern_id", "record_version", "document_id", "title", "authority")

PROVENANCE_FIELDS = {"source_kind", "local_file", "content_hash", "url", "analyzed_on", "analyzed_by"}
PROVENANCE_REQUIRED = ("source_kind", "local_file", "content_hash", "analyzed_on")

REQUIREMENT_FIELDS = {
    "requirement_id",
    "topic",
    "statement",
    "locator",
    "observation",
    "binding",
    "applies_to",
    "verbatim_trigger",
    "note",
}
REQUIREMENT_REQUIRED = ("requirement_id", "topic", "statement", "locator", "observation", "binding")


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _unexpected(record: dict[str, Any], allowed: set[str], path: str, errors: list[str]) -> None:
    for key in sorted(set(record) - allowed):
        errors.append(f"{path}: unexpected field {key!r}")


def _required(record: dict[str, Any], keys: tuple[str, ...], path: str, errors: list[str]) -> None:
    for key in keys:
        if not _nonempty(record.get(key)):
            errors.append(f"{path}.{key}: expected a non-empty string")


def validate_card(data: Any) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(data, dict):
        return {"valid": False, "errors": ["card: expected an object"], "warnings": [], "counts": {}}

    _unexpected(data, CARD_FIELDS, "card", errors)
    _required(data, CARD_REQUIRED, "card", errors)
    if data.get("schema_version") != "1.0":
        errors.append("card.schema_version: expected '1.0'")
    if _nonempty(data.get("pattern_id")) and not ID_PATTERN.fullmatch(data["pattern_id"]):
        errors.append("card.pattern_id: invalid identifier")
    if _nonempty(data.get("record_version")) and not VERSION_PATTERN.fullmatch(data["record_version"]):
        errors.append("card.record_version: expected 'v<number>'")
    tier = data.get("tier")
    if not isinstance(tier, int) or not 1 <= tier <= 7:
        errors.append("card.tier: expected the priority tier as an integer between 1 and 7")

    provenance = data.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("card.provenance: expected an object")
        provenance = {}
    else:
        _unexpected(provenance, PROVENANCE_FIELDS, "card.provenance", errors)
        _required(provenance, PROVENANCE_REQUIRED, "card.provenance", errors)
        if provenance.get("source_kind") not in SOURCE_KINDS:
            errors.append(f"card.provenance.source_kind: expected one of {sorted(SOURCE_KINDS)}")
        if _nonempty(provenance.get("content_hash")) and not HASH_PATTERN.fullmatch(
            provenance["content_hash"]
        ):
            errors.append("card.provenance.content_hash: expected 'sha256:<64 hex digits>'")
        if _nonempty(provenance.get("analyzed_on")) and not DATE_PATTERN.fullmatch(
            provenance["analyzed_on"]
        ):
            errors.append("card.provenance.analyzed_on: expected YYYY-MM-DD")

    requirements = data.get("requirements", [])
    if not isinstance(requirements, list):
        errors.append("card.requirements: expected a list")
        requirements = []

    # The rule this validator exists for. A catalogue entry carries the
    # designation, the status and the dates of a document. It does not carry
    # what the document says, so a card built from one may record no
    # requirements at all.
    if provenance.get("source_kind") in {"catalogue_card", "index_page"} and requirements:
        errors.append(
            "card.requirements: a card built from a "
            f"{provenance['source_kind']} cannot carry requirements; it records identity "
            "and status only"
        )

    seen: set[str] = set()
    for index, item in enumerate(requirements):
        path = f"card.requirements[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{path}: expected an object")
            continue
        _unexpected(item, REQUIREMENT_FIELDS, path, errors)
        _required(item, REQUIREMENT_REQUIRED, path, errors)
        identifier = item.get("requirement_id")
        if _nonempty(identifier):
            if not ID_PATTERN.fullmatch(identifier):
                errors.append(f"{path}.requirement_id: invalid identifier")
            elif identifier in seen:
                errors.append(f"{path}.requirement_id: duplicate {identifier!r}")
            seen.add(identifier)
        if item.get("observation") not in OBSERVATION:
            errors.append(f"{path}.observation: expected one of {sorted(OBSERVATION)}")
        if item.get("binding") not in BINDING:
            errors.append(f"{path}.binding: expected one of {sorted(BINDING)}")
        if item.get("observation") == "uncertain" and not _nonempty(item.get("note")):
            errors.append(f"{path}.note: required when the observation is uncertain")
        if item.get("binding") == "conditional" and not _nonempty(item.get("applies_to")):
            errors.append(f"{path}.applies_to: required for a conditional requirement")

    not_observed = data.get("not_observed", [])
    if not isinstance(not_observed, list):
        errors.append("card.not_observed: expected a list")
        not_observed = []
    if provenance.get("source_kind") == "document" and not not_observed:
        # Silence about what was missing reads as completeness later.
        warnings.append(
            "card.not_observed: no absent feature is recorded; state what the document does "
            "not settle"
        )

    conflicts = data.get("conflicts", [])
    if not isinstance(conflicts, list):
        errors.append("card.conflicts: expected a list")
        conflicts = []
    if _nonempty(data.get("record_version")) and data["record_version"] != "v1" and not conflicts:
        warnings.append(
            "card.conflicts: a superseding version records no difference from the version "
            "it replaces"
        )

    counts = {
        "requirements": len(requirements),
        "observed": sum(1 for item in requirements if isinstance(item, dict) and item.get("observation") == "observed"),
        "uncertain": sum(1 for item in requirements if isinstance(item, dict) and item.get("observation") == "uncertain"),
        "mandatory": sum(1 for item in requirements if isinstance(item, dict) and item.get("binding") == "mandatory"),
        "not_observed": len(not_observed),
        "conflicts": len(conflicts),
    }
    return {"valid": not errors, "errors": errors, "warnings": warnings, "counts": counts}


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("card", type=Path, help="Path to a normative-pattern card")
    parser.add_argument("--output", type=Path, help="Optional validation-report path")
    args = parser.parse_args()

    try:
        report = validate_card(json.loads(args.card.read_text(encoding="utf-8-sig")))
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
