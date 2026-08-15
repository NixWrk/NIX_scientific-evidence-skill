"""Invariants of reading somebody else's defended work.

A work shows what one council accepted; it establishes nothing. The normative
card relies on the author choosing `observed_practice`, which is discipline.
Here the schema simply has nowhere to put a rule, and these tests are what
keeps it that way.
"""

import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "scientific-evidence-workflow"
WORK_DIR = SKILL_DIR / "references" / "work-patterns"
ASSET_DIR = SKILL_DIR / "assets"

SPEC = importlib.util.spec_from_file_location(
    "scientific_evidence_validate_work", SKILL_DIR / "scripts" / "validate_work_card.py"
)
assert SPEC and SPEC.loader
WORK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(WORK)


def work_template() -> dict:
    return json.loads((ASSET_DIR / "work-pattern.template.json").read_text(encoding="utf-8"))


def sound_card() -> dict:
    """A card that passes, used as the base for breaking exactly one thing."""

    return {
        "schema_version": "1.0",
        "kind": "work",
        "work_id": "WORK-TEST-2012",
        "record_version": "v1",
        "document_kind": "dissertation",
        "bibliographic": {
            "author": "Иванов И. И.",
            "title": "Название",
            "year": "2012",
            "degree": "кандидат технических наук",
            "specialty_as_printed": "05.11.17",
            "council": "unknown",
            "organization": "МГТУ им. Н. Э. Баумана",
            "supervisor": "unknown",
        },
        "stratum": "specialty",
        "provenance": {
            "local_file": "Zotero storage/AAAA/x.pdf",
            "content_hash": "sha256:" + "0" * 64,
            "url": "zotero://select/library/items/AAAA",
            "analyzed_on": "2026-08-15",
            "analyzed_by": "тест",
        },
        "coverage": ["прочитано оглавление"],
        "structure": [{"part": "Введение", "locator": "с. 4"}],
        "volumes": {"pages": 144},
        "narrative": [
            {
                "chapter": "Глава 1",
                "locator": "с. 13–48",
                "role": "Обзор области.",
                "moves": ["от общего к частному", "выявление пробела"],
                "ends_with": "постановкой задачи",
                "leads_to": "выбору метода",
            }
        ],
        "spine": [
            {
                "link": "медицинская задача",
                "status": "observed",
                "where": "с. 47",
                "how": "сформулирована в конце обзора",
            }
        ],
        "formulations": [
            {
                "element": "положения на защиту",
                "locator": "с. 8",
                "count": 4,
                "shape": "перечень, каждый пункт с отглагольного существительного",
                "openers": ["Разработан"],
                "quote": "Разработан метод оценки ...",
            }
        ],
        "practice": [
            {
                "topic": "ссылки",
                "observation": "Отсылки приведены в квадратных скобках.",
                "locator": "с. 20",
            }
        ],
        "not_observed": ["приложения не просматривались"],
        "notes": [],
    }


def sound_aggregate() -> dict:
    return {
        "schema_version": "1.0",
        "kind": "aggregate",
        "aggregate_id": "PATTERN-TEST",
        "record_version": "v1",
        "scope": "council-24.2.331.09",
        "required_stratum": "council",
        "compiled_on": "2026-08-15",
        "compiled_by": "тест",
        "expected_arc": {
            "source": "автор работы, до чтения корпуса",
            "stated_on": "2026-08-15",
            "note": "гипотеза",
            "links": ["медицинская задача", "медико-техническая задача", "разработка"],
        },
        "works": ["WORK-TEST-2026"],
        "features": [
            {
                "feature_id": "F-001",
                "level": "стык",
                "question": "Есть ли выводы по главе.",
                "shown_by": [
                    {"work_id": "WORK-TEST-2026", "what": "выводы приведены", "locator": "с. 48"}
                ],
                "common": "выводы по главе приводятся",
                "variants": [],
                "norm_relation": "norm_silent",
                "norm_reference": None,
            }
        ],
        "not_observed": [],
        "notes": [],
    }


def council_cards() -> dict:
    council = sound_card()
    council.update({"work_id": "WORK-TEST-2026", "stratum": "council"})
    council["bibliographic"]["council"] = "24.2.331.09"
    return {"WORK-TEST-2012": sound_card(), "WORK-TEST-2026": council}


def test_the_shipped_template_is_a_usable_starting_point() -> None:
    """A template that starts invalid teaches the wrong shape.

    It carries real values rather than pipe-separated prompts, precisely so
    this check can be strict: the alternatives belong in the memory file, where
    prose can explain them, not in fields that then fail their own validator.
    """

    report = WORK.validate(work_template())

    assert report["valid"] is True, report["errors"]


def test_a_work_card_cannot_state_an_obligation() -> None:
    """The guarantee this schema exists for, closed on both routes.

    A key that would carry a binding, and prose that would smuggle one. The
    second matters more: nobody writes `mandatory` by accident, but «должен»
    slips into a summary of somebody else's work very easily.
    """

    by_key = sound_card()
    by_key["practice"][0]["binding"] = "mandatory"
    report = WORK.validate(by_key)
    assert report["valid"] is False
    assert "no field for an obligation" in "\n".join(report["errors"])

    by_prose = sound_card()
    by_prose["practice"][0]["observation"] = "Список литературы должен идти в порядке упоминания."
    report = WORK.validate(by_prose)
    assert report["valid"] is False
    assert "states an obligation" in "\n".join(report["errors"])


def test_verbatim_text_from_the_work_may_carry_obligation() -> None:
    """Quoting is not asserting.

    A dissertation says «должен» all the time. Refusing the word everywhere
    would push the analyst to paraphrase the source, which is worse: the
    paraphrase is unverifiable while the quotation is not.
    """

    card = sound_card()
    card["practice"][0]["quote"] = "прибор должен обеспечивать погрешность не более 5 %"

    assert WORK.validate(card)["valid"] is True


def test_a_chapter_without_its_moves_is_only_a_heading() -> None:
    """The narrative level is the reason for reading the works at all.

    A chapter recorded as a title and a page range repeats the table of
    contents. How the chapter argues is what no normative document supplies.
    """

    card = sound_card()
    card["narrative"][0]["moves"] = []

    report = WORK.validate(card)

    assert report["valid"] is False
    assert "not its argument" in "\n".join(report["errors"])


def test_a_confounder_is_written_as_unknown_rather_than_left_blank() -> None:
    """An empty supervisor is indistinguishable from one nobody looked for.

    This is what separates a shared pattern of the council from the habit of
    one supervisor's students.
    """

    card = sound_card()
    card["bibliographic"]["supervisor"] = ""

    report = WORK.validate(card)

    assert report["valid"] is False
    assert "supervisor" in "\n".join(report["errors"])


def test_an_aggregate_may_not_rest_on_a_work_too_weak_to_bear_it() -> None:
    """A claim about one council needs a work defended in that council."""

    cards = council_cards()
    assert WORK.validate(sound_aggregate(), cards)["valid"] is True

    weakened = sound_aggregate()
    weakened["works"].append("WORK-TEST-2012")
    weakened["features"][0]["shown_by"].append(
        {"work_id": "WORK-TEST-2012", "what": "выводы приведены", "locator": "с. 60"}
    )
    report = WORK.validate(weakened, cards)

    assert report["valid"] is False
    assert "too weak to support a claim" in "\n".join(report["errors"])


def test_a_specialty_claim_accepts_both_strata() -> None:
    """The weaker scope is the point of having two of them.

    A work of the council is also a work of the specialty, so it counts for
    both; the refusal only runs one way.
    """

    cards = council_cards()
    aggregate = sound_aggregate()
    aggregate.update({"scope": "specialty-2.2.12", "required_stratum": "specialty"})
    aggregate["works"].append("WORK-TEST-2012")
    aggregate["features"][0]["shown_by"].append(
        {"work_id": "WORK-TEST-2012", "what": "выводы приведены", "locator": "с. 60"}
    )

    assert WORK.validate(aggregate, cards)["valid"] is True


def test_a_relation_to_the_norm_names_the_card_it_relates_to() -> None:
    """`confirms` and `diverges` are claims about a card, so the card is named.

    `norm_silent` is the opposite: there is nothing to point at, and it is the
    only relation under which practice supplies a default.
    """

    cards = council_cards()
    unnamed = sound_aggregate()
    unnamed["features"][0]["norm_relation"] = "confirms"

    report = WORK.validate(unnamed, cards)
    assert report["valid"] is False
    assert "naming which" in "\n".join(report["errors"])

    named = copy.deepcopy(unnamed)
    named["features"][0]["norm_reference"] = "NORM-GOST-R-7.0.11-2011-001 REQ-022"
    assert WORK.validate(named, cards)["valid"] is True


def test_a_feature_cites_a_work_that_exists_and_is_declared() -> None:
    """A pointer into nothing reads exactly like evidence."""

    cards = council_cards()

    undeclared = sound_aggregate()
    undeclared["features"][0]["shown_by"][0]["work_id"] = "WORK-TEST-2012"
    report = WORK.validate(undeclared, cards)
    assert report["valid"] is False
    assert "not listed in aggregate.works" in "\n".join(report["errors"])

    absent = sound_aggregate()
    absent["works"] = ["WORK-NOBODY-1999"]
    absent["features"][0]["shown_by"][0]["work_id"] = "WORK-NOBODY-1999"
    report = WORK.validate(absent, cards)
    assert report["valid"] is False
    assert "no work card" in "\n".join(report["errors"])


def test_the_shipped_aggregate_template_is_a_usable_starting_point() -> None:
    report = WORK.validate(
        json.loads((ASSET_DIR / "work-aggregate.template.json").read_text(encoding="utf-8"))
    )

    assert report["valid"] is True, report["errors"]


def test_an_absent_link_is_a_finding_and_still_owes_its_evidence() -> None:
    """The point of recording absence at all.

    A work that never forms the medical problem before reviewing technical
    solutions has told us something. But «нет» with nothing behind it is as
    unverifiable as an invented quotation, so an absent link still says how the
    absence was established — and cannot point at a page, because there is none.
    """

    absent = sound_card()
    absent["spine"] = [
        {
            "link": "медико-техническая задача",
            "status": "absent",
            "where": None,
            "how": "главы 1 и 2 прочитаны целиком; постановка сразу техническая",
        }
    ]
    assert WORK.validate(absent)["valid"] is True

    pointing = copy.deepcopy(absent)
    pointing["spine"][0]["where"] = "с. 40"
    report = WORK.validate(pointing)
    assert report["valid"] is False
    assert "nowhere to point" in "\n".join(report["errors"])

    unaccounted = copy.deepcopy(absent)
    unaccounted["spine"][0]["how"] = ""
    report = WORK.validate(unaccounted)
    assert report["valid"] is False
    assert "how" in "\n".join(report["errors"])


def test_an_observed_link_points_at_where_it_sits() -> None:
    card = sound_card()
    card["spine"][0]["where"] = ""

    report = WORK.validate(card)

    assert report["valid"] is False
    assert "points at where it sits" in "\n".join(report["errors"])


def test_the_expected_arc_records_who_stated_it() -> None:
    """A frame brought to the corpus must be distinguishable from one it produced.

    Read eight works looking for five links and eight will show them. Naming
    the source and the date is what lets a later reader see that the arc was a
    hypothesis stated in advance rather than a finding.
    """

    cards = council_cards()
    anonymous = sound_aggregate()
    del anonymous["expected_arc"]["source"]

    report = WORK.validate(anonymous, cards)

    assert report["valid"] is False
    assert "expected_arc.source" in "\n".join(report["errors"])


def test_a_link_the_arc_did_not_anticipate_is_reported_but_not_refused() -> None:
    """The corpus is allowed to answer back.

    An unanticipated link means the hypothesis was incomplete, not that the
    reading was wrong. Refusing it would make the frame unfalsifiable — which
    is the whole failure this design is avoiding — so it warns instead.
    """

    cards = council_cards()
    cards["WORK-TEST-2026"]["spine"] = [
        {
            "link": "клиническая апробация",
            "status": "observed",
            "where": "с. 120",
            "how": "отдельная глава",
        }
    ]

    report = WORK.validate(sound_aggregate(), cards)

    assert report["valid"] is True
    assert any("does not anticipate" in warning for warning in report["warnings"])


def test_a_formulation_without_its_verbatim_wording_is_flagged() -> None:
    """Wording is the observation here, so a paraphrase discards the evidence."""

    card = sound_card()
    card["formulations"][0]["quote"] = None

    report = WORK.validate(card)

    assert report["valid"] is True
    assert any("verbatim" in warning for warning in report["warnings"])


def test_a_card_says_whether_it_reads_a_dissertation_or_an_abstract() -> None:
    """The two are not comparable at the level this store exists for.

    An abstract compresses four chapters into a few pages, so its chapter moves
    and its seams are a different object from the dissertation's. Carding them
    without saying which is which would average two shapes into one.
    """

    card = sound_card()
    del card["document_kind"]

    report = WORK.validate(card)

    assert report["valid"] is False
    assert "not comparable" in "\n".join(report["errors"])


def test_stored_work_records_validate_against_each_other() -> None:
    """Whatever the store holds must pass, and aggregates must resolve."""

    records = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(WORK_DIR.glob("*.json"))
    ]
    cards = {record["work_id"]: record for record in records if record.get("kind") == "work"}

    for record in records:
        report = WORK.validate(record, cards)
        identifier = record.get("work_id") or record.get("aggregate_id")
        assert report["valid"] is True, f"{identifier}: {report['errors']}"
