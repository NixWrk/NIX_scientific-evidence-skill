"""Validate a work-pattern card or an aggregate, without external packages.

A defended work shows what one council accepted; it establishes nothing. Three
failures are worth stopping here, and each has its own check:

1. an obligation appearing in a record of somebody else's practice — in a key
   or in prose. A normative card relies on the author writing
   `observed_practice`; this schema simply has nowhere to put a rule, and the
   validator keeps it that way;
2. an observation without a locator, which cannot be checked back;
3. an aggregate resting on works too weak to bear its claim — a statement about
   one council's practice supported by a work defended elsewhere.
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

STRATA = ("council", "specialty", "outside")
# A claim about one council needs a work from that council. A claim about the
# specialty is content with either. Nothing supports a claim from `outside`.
STRATUM_RANK = {"council": 2, "specialty": 1, "outside": 0}
NORM_RELATIONS = ("confirms", "norm_silent", "diverges")
# The links of the through-line are deliberately not fixed here. An expected arc
# is a hypothesis somebody states before reading, and hard-coding it would let
# the frame confirm itself: read eight works looking for five links and eight
# will show them. The aggregate declares the arc together with who said so, and
# the check happens there.
SPINE_STATUSES = ("observed", "absent")
# A defended work is a model and not a standard, and a move seen in one of them
# is that author's. Roughly five works by different authors is where the store
# stops mistaking a habit for a practice of the field. Nothing makes this number
# exact; it is a stated threshold, and it warns rather than refuses so that an
# aggregate can be built up while it is still short of evidence.
AUTHORS_FOR_A_PATTERN = 5

# Keys that would let a rule be written down. Their absence is the point of
# this schema, so they are refused wherever they appear at any depth.
FORBIDDEN_KEYS = {"binding", "requirement", "requirements", "requirement_id", "mandatory", "applies_to"}

# Obligation in prose is the same leak by another route. Verbatim text from the
# work belongs in `quote`, which is exempt: a work may well say «должен».
#
# The stem is «долж», not «должн» — «должен» has no н before the ending, and an
# earlier version of this pattern silently missed the single most common form.
# Two words are deliberately absent. «следует» is ambiguous between obligation
# and inference («из главы 1 следует»), and «требования» is an ordinary noun a
# work card needs («глава 2 формулирует требования к системе»); only the verb
# «требуется» is refused.
OBLIGATION = re.compile(
    r"\b("
    r"долж(?:ен|на|но|ны|ного|ному|ным|ными|ных)"
    r"|обязан(?:а|о|ы)?"
    r"|обязательн\w*"
    r"|требуетс\w*|требуютс\w*"
    r"|необходим(?:о|а|ы|ый|ая|ое|ые|ого|ому)?"
    r"|надлежит"
    r"|не\s+допускаетс\w*"
    r")\b",
    re.IGNORECASE,
)
QUOTE_FIELDS = {"quote"}

WORK_FIELDS = {
    "schema_version", "kind", "work_id", "record_version", "document_kind", "bibliographic",
    "stratum", "provenance", "coverage", "structure", "volumes", "narrative", "spine",
    "formulations", "practice", "not_observed", "notes",
}
# One file, one hash, one card. A dissertation and its abstract are two
# documents of the same work, and their narrative is not comparable: the
# abstract compresses four chapters into a few pages. Carding them together
# would average two different objects into one description.
DOCUMENT_KINDS = ("dissertation", "autoreferat")
BIBLIOGRAPHIC_REQUIRED = (
    "author", "title", "year", "specialty_as_printed", "council", "organization", "supervisor",
)
PROVENANCE_REQUIRED = ("local_file", "content_hash", "analyzed_on")

AGGREGATE_FIELDS = {
    "schema_version", "kind", "aggregate_id", "record_version", "scope", "required_stratum",
    "compiled_on", "compiled_by", "expected_arc", "works", "features", "not_observed", "notes",
}
ARC_REQUIRED = ("source", "stated_on")


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _unexpected(record: dict[str, Any], allowed: set[str], path: str, errors: list[str]) -> None:
    for key in sorted(set(record) - allowed):
        errors.append(f"{path}: unexpected field {key!r}")


def _required(record: dict[str, Any], keys: tuple[str, ...], path: str, errors: list[str]) -> None:
    for key in keys:
        if not _nonempty(record.get(key)):
            errors.append(f"{path}.{key}: expected a non-empty string")


def _scan_for_obligation(node: Any, path: str, errors: list[str]) -> None:
    """Walk the whole record refusing rule-shaped keys and obligation prose."""

    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() in FORBIDDEN_KEYS:
                errors.append(
                    f"{path}.{key}: a work card has no field for an obligation; a defended "
                    "work shows practice and establishes nothing"
                )
            _scan_for_obligation(value, f"{path}.{key}" if key not in QUOTE_FIELDS else "", errors)
        return
    if isinstance(node, list):
        for index, item in enumerate(node):
            _scan_for_obligation(item, f"{path}[{index}]" if path else "", errors)
        return
    if isinstance(node, str) and path and OBLIGATION.search(node):
        found = OBLIGATION.search(node)
        assert found is not None
        errors.append(
            f"{path}: observation states an obligation ({found.group(0)!r}); describe what the "
            "work does, or put verbatim text in 'quote'"
        )


def _check_located(items: Any, path: str, fields: tuple[str, ...], errors: list[str]) -> None:
    if not isinstance(items, list):
        errors.append(f"{path}: expected a list")
        return
    for index, item in enumerate(items):
        here = f"{path}[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{here}: expected an object")
            continue
        _required(item, fields, here, errors)


def validate_work(data: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    _unexpected(data, WORK_FIELDS, "work", errors)
    _required(data, ("schema_version", "work_id", "record_version"), "work", errors)
    if data.get("schema_version") != "1.0":
        errors.append("work.schema_version: expected '1.0'")
    if _nonempty(data.get("work_id")) and not ID_PATTERN.fullmatch(data["work_id"]):
        errors.append("work.work_id: invalid identifier")
    if _nonempty(data.get("record_version")) and not VERSION_PATTERN.fullmatch(data["record_version"]):
        errors.append("work.record_version: expected 'v<number>'")
    if data.get("stratum") not in STRATA:
        errors.append(f"work.stratum: expected one of {list(STRATA)}")
    if data.get("document_kind") not in DOCUMENT_KINDS:
        errors.append(
            f"work.document_kind: expected one of {list(DOCUMENT_KINDS)}; a dissertation and "
            "its abstract argue at different lengths and are not comparable"
        )

    bibliographic = data.get("bibliographic")
    if not isinstance(bibliographic, dict):
        errors.append("work.bibliographic: expected an object")
    else:
        _required(bibliographic, BIBLIOGRAPHIC_REQUIRED, "work.bibliographic", errors)
        # A confounder left blank is indistinguishable from one nobody looked
        # for, so 'unknown' has to be written rather than omitted.
        for key in ("council", "supervisor"):
            if bibliographic.get(key) == "":
                errors.append(f"work.bibliographic.{key}: write 'unknown' rather than leaving it empty")

    provenance = data.get("provenance")
    if not isinstance(provenance, dict):
        errors.append("work.provenance: expected an object")
    else:
        _required(provenance, PROVENANCE_REQUIRED, "work.provenance", errors)
        if _nonempty(provenance.get("content_hash")) and not HASH_PATTERN.fullmatch(provenance["content_hash"]):
            errors.append("work.provenance.content_hash: expected 'sha256:<64 hex digits>'")
        if _nonempty(provenance.get("analyzed_on")) and not DATE_PATTERN.fullmatch(provenance["analyzed_on"]):
            errors.append("work.provenance.analyzed_on: expected YYYY-MM-DD")

    _check_located(data.get("structure", []), "work.structure", ("part", "locator"), errors)
    _check_located(
        data.get("narrative", []),
        "work.narrative",
        ("chapter", "locator", "role", "ends_with", "leads_to"),
        errors,
    )
    _check_located(data.get("spine", []), "work.spine", ("link", "how"), errors)
    _check_located(data.get("practice", []), "work.practice", ("topic", "observation", "locator"), errors)
    _check_located(
        data.get("formulations", []), "work.formulations", ("element", "locator", "shape"), errors
    )

    narrative = data.get("narrative", [])
    if isinstance(narrative, list):
        for index, chapter in enumerate(narrative):
            if not isinstance(chapter, dict):
                continue
            moves = chapter.get("moves")
            if not isinstance(moves, list) or not moves:
                errors.append(
                    f"work.narrative[{index}].moves: expected the ordered moves of the chapter; "
                    "a chapter recorded without its moves is a heading, not its argument"
                )

    spine = data.get("spine", [])
    if isinstance(spine, list):
        for index, link in enumerate(spine):
            if not isinstance(link, dict):
                continue
            here = f"work.spine[{index}]"
            status = link.get("status")
            if status not in SPINE_STATUSES:
                errors.append(f"{here}.status: expected one of {list(SPINE_STATUSES)}")
                continue
            # An observed link points at a page. An absent one cannot, but it
            # still owes an account of how the absence was established: a bare
            # «нет» is as unverifiable as an invented quotation.
            if status == "observed" and not _nonempty(link.get("where")):
                errors.append(f"{here}.where: an observed link points at where it sits")
            if status == "absent" and _nonempty(link.get("where")):
                errors.append(f"{here}.where: an absent link has nowhere to point")

    formulations = data.get("formulations", [])
    if isinstance(formulations, list):
        for index, item in enumerate(formulations):
            if not isinstance(item, dict):
                continue
            here = f"work.formulations[{index}]"
            count = item.get("count")
            if count is not None and (not isinstance(count, int) or count < 0):
                errors.append(f"{here}.count: expected a non-negative integer or null")
            openers = item.get("openers")
            if openers is not None and not isinstance(openers, list):
                errors.append(f"{here}.openers: expected a list of opening words or null")
            # Wording is the subject here, so a paraphrase loses the evidence.
            if not _nonempty(item.get("quote")):
                warnings.append(
                    f"{here}.quote: the wording is what is being observed; record it verbatim"
                )

    if not data.get("not_observed"):
        warnings.append("work.not_observed: nothing recorded as unexamined or absent")

    _scan_for_obligation(data, "work", errors)

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "structure": len(data.get("structure") or []),
            "chapters": len(narrative if isinstance(narrative, list) else []),
            "spine": len(spine if isinstance(spine, list) else []),
            "practice": len(data.get("practice") or []),
            "not_observed": len(data.get("not_observed") or []),
        },
    }


def validate_aggregate(data: dict[str, Any], cards: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    cards = cards or {}

    _unexpected(data, AGGREGATE_FIELDS, "aggregate", errors)
    _required(
        data,
        ("schema_version", "aggregate_id", "record_version", "scope", "compiled_on"),
        "aggregate",
        errors,
    )
    if data.get("schema_version") != "1.0":
        errors.append("aggregate.schema_version: expected '1.0'")
    required_stratum = data.get("required_stratum")
    if required_stratum not in ("council", "specialty"):
        errors.append("aggregate.required_stratum: expected 'council' or 'specialty'")

    works = data.get("works")
    if not isinstance(works, list) or not works:
        errors.append("aggregate.works: expected the list of work cards it rests on")
        works = []

    # An expected arc stated before reading can confirm itself. Recording who
    # stated it, and when, is what lets a later reader tell a frame brought to
    # the corpus from one the corpus produced.
    arc = data.get("expected_arc")
    arc_links: set[str] = set()
    if arc is not None:
        if not isinstance(arc, dict):
            errors.append("aggregate.expected_arc: expected an object")
        else:
            _required(arc, ARC_REQUIRED, "aggregate.expected_arc", errors)
            if _nonempty(arc.get("stated_on")) and not DATE_PATTERN.fullmatch(arc["stated_on"]):
                errors.append("aggregate.expected_arc.stated_on: expected YYYY-MM-DD")
            links = arc.get("links")
            if not isinstance(links, list) or not links:
                errors.append("aggregate.expected_arc.links: expected the anticipated links")
            else:
                arc_links = {link for link in links if isinstance(link, str)}

    if arc_links and cards:
        for work_id in works:
            card = cards.get(work_id)
            if not isinstance(card, dict):
                continue
            for index, link in enumerate(card.get("spine") or []):
                if not isinstance(link, dict):
                    continue
                name = link.get("link")
                if _nonempty(name) and name not in arc_links:
                    # Not an error. A work showing a link nobody anticipated is
                    # the corpus answering back, and that is the reason to read
                    # it; the arc is what gets updated, not the observation.
                    warnings.append(
                        f"aggregate.expected_arc: {work_id} spine[{index}] uses {name!r}, which "
                        "the declared arc does not anticipate; extend the arc if the corpus is right"
                    )

    features = data.get("features")
    if not isinstance(features, list):
        errors.append("aggregate.features: expected a list")
        features = []

    seen: set[str] = set()
    for index, feature in enumerate(features):
        path = f"aggregate.features[{index}]"
        if not isinstance(feature, dict):
            errors.append(f"{path}: expected an object")
            continue
        _required(feature, ("feature_id", "level", "question"), path, errors)
        identifier = feature.get("feature_id")
        if _nonempty(identifier):
            if identifier in seen:
                errors.append(f"{path}.feature_id: duplicate {identifier!r}")
            seen.add(identifier)
        if feature.get("norm_relation") not in NORM_RELATIONS:
            errors.append(f"{path}.norm_relation: expected one of {list(NORM_RELATIONS)}")
        if feature.get("norm_relation") in ("confirms", "diverges") and not _nonempty(feature.get("norm_reference")):
            errors.append(
                f"{path}.norm_reference: naming a relation to the norm requires naming which "
                "card and requirement"
            )

        shown_by = feature.get("shown_by")
        if not isinstance(shown_by, list) or not shown_by:
            errors.append(f"{path}.shown_by: a feature with no work behind it is an assertion")
            continue
        for offset, item in enumerate(shown_by):
            here = f"{path}.shown_by[{offset}]"
            if not isinstance(item, dict):
                errors.append(f"{here}: expected an object")
                continue
            _required(item, ("work_id", "what", "locator"), here, errors)
            work_id = item.get("work_id")
            if not _nonempty(work_id):
                continue
            if work_id not in works:
                errors.append(f"{here}.work_id: {work_id!r} is not listed in aggregate.works")
            card = cards.get(work_id)
            if card is None:
                if cards:
                    errors.append(f"{here}.work_id: no work card {work_id!r} exists")
                continue
            stratum = card.get("stratum")
            if STRATUM_RANK.get(stratum, -1) < STRATUM_RANK.get(required_stratum, 99):
                errors.append(
                    f"{here}.work_id: {work_id!r} is stratum {stratum!r}, too weak to support a "
                    f"claim about {data.get('scope')!r}"
                )

        variants = feature.get("variants") or []
        if not isinstance(variants, list):
            errors.append(f"{path}.variants: expected a list")
        elif len(shown_by) > 1 and not variants and not _nonempty(feature.get("common")):
            warnings.append(
                f"{path}: several works and neither a common pattern nor a variant recorded"
            )

        # A defended work is a model, not a standard, and one work is one work.
        # A `common` is a claim about how such works are written; a `variants`
        # entry is a claim about one of them, and needs no corpus behind it.
        cited = [cards[item["work_id"]] for item in shown_by
                 if isinstance(item, dict) and item.get("work_id") in cards]
        authors = {card.get("bibliographic", {}).get("author") for card in cited}
        authors.discard(None)
        if cited and _nonempty(feature.get("common")) and len(authors) < AUTHORS_FOR_A_PATTERN:
            warnings.append(
                f"{path}.common: a common pattern drawn from {len(authors)} author(s), fewer than "
                f"{AUTHORS_FOR_A_PATTERN}; below that a habit, a house style and a practice of the "
                "field are indistinguishable. Record it as a variant, or name the works and wait"
            )
        # The memory has said this since the store was built and nothing checked
        # it: a feature shared across one supervisor's students is that
        # supervisor's house style until somebody else's student shows it too.
        supervisors = {card.get("bibliographic", {}).get("supervisor") for card in cited}
        supervisors.discard(None)
        supervisors.discard("unknown")
        if len(cited) > 1 and len(supervisors) == 1 and len(authors) > 1:
            warnings.append(
                f"{path}: every work behind this feature was supervised by "
                f"{next(iter(supervisors))!r}; record it as that supervisor's practice until a "
                "work under another supervisor shows it"
            )

    if cards:
        for work_id in works:
            if work_id not in cards:
                errors.append(f"aggregate.works: no work card {work_id!r} exists")

    _scan_for_obligation(data, "aggregate", errors)

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {"works": len(works), "features": len(features)},
    }


def validate(data: Any, cards: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    if not isinstance(data, dict):
        return {"valid": False, "errors": ["record: expected an object"], "warnings": [], "counts": {}}
    kind = data.get("kind")
    if kind == "work":
        return validate_work(data)
    if kind == "aggregate":
        return validate_aggregate(data, cards)
    return {
        "valid": False,
        "errors": [f"record.kind: expected 'work' or 'aggregate', got {kind!r}"],
        "warnings": [],
        "counts": {},
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path, help="Path to a work card or an aggregate")
    parser.add_argument(
        "--cards",
        type=Path,
        help="Directory of work cards, so an aggregate can be checked against them",
    )
    parser.add_argument("--output", type=Path, help="Optional validation-report path")
    args = parser.parse_args()

    cards: dict[str, dict[str, Any]] = {}
    if args.cards and args.cards.is_dir():
        for path in sorted(args.cards.glob("*.json")):
            try:
                candidate = json.loads(path.read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict) and candidate.get("kind") == "work":
                cards[candidate.get("work_id", path.stem)] = candidate

    try:
        report = validate(json.loads(args.record.read_text(encoding="utf-8-sig")), cards)
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
