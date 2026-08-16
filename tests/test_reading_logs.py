"""Invariants of the reading log — the record of reading a work page by page.

Pass A measures a work without reading it and pass B reads every page. The log
is what pass B leaves behind, and it is written in chunks across sessions, so
it has to be checkable at any moment and it has to survive being appended to.

What these tests protect is the discovery property. A reader confined to a list
of kinds finds only what the list already knows, so the log admits `unnamed`;
but an unnamed observation without a proposed name is a shapeless remark, and a
proposed name promoted on its first appearance is a pattern invented out of one
event. Three locators is the price of a kind.
"""

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "scientific-evidence-workflow"
LOG_DIR = SKILL_DIR / "references" / "reading-logs"

SPEC = importlib.util.spec_from_file_location(
    "scientific_evidence_validate_reading_log",
    SKILL_DIR / "scripts" / "validate_reading_log.py",
)
assert SPEC and SPEC.loader
LOG = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LOG)


def line(**overrides) -> str:
    record = {
        "section": "1.2",
        "page": 17,
        "kind": "опора",
        "observation": "Отсылка стоит при величине, а не при утверждении.",
    }
    record.update(overrides)
    return json.dumps(record, ensure_ascii=False)


def test_an_observation_without_a_page_cannot_be_checked_back() -> None:
    """A log full of unlocatable claims is worse than no log at all."""

    report = LOG.validate_log([line(page=None)])

    assert report["valid"] is False
    assert "нельзя проверить по источнику" in "\n".join(report["errors"])


def test_an_unnamed_observation_must_propose_a_name() -> None:
    """`unnamed` is what makes discovery possible; it is not a dumping ground."""

    report = LOG.validate_log([line(kind="unnamed", proposed_name="")])

    assert report["valid"] is False
    assert "обязано получить имя" in "\n".join(report["errors"])


def test_a_name_is_proposed_only_for_unnamed() -> None:
    """A kind already in the list is not up for renaming."""

    report = LOG.validate_log([line(proposed_name="что-то-своё")])

    assert report["valid"] is False
    assert "только для вида 'unnamed'" in "\n".join(report["errors"])


def test_two_locators_are_a_coincidence_and_three_are_a_kind() -> None:
    """The threshold is the whole defence against inventing patterns."""

    twice = [
        line(kind="unnamed", proposed_name="новое", page=page, quote="x")
        for page in (11, 12)
    ]
    thrice = twice + [line(kind="unnamed", proposed_name="новое", page=13, quote="x")]

    assert LOG.validate_log(twice)["ждут доказательств"] == {"новое": ["с. 11", "с. 12"]}
    assert LOG.validate_log(twice)["готовы стать видом"] == {}
    assert LOG.validate_log(thrice)["готовы стать видом"] == {
        "новое": ["с. 11", "с. 12", "с. 13"]
    }


def test_a_promoted_name_is_not_proposed_again() -> None:
    """The records that earned a kind keep `unnamed`: they are its evidence.

    Rewriting them into the new kind would delete the only record of where it
    came from, so the report has to tell a finished promotion from an open one.
    """

    promoted = LOG.KINDS[-2]
    lines = [
        line(kind="unnamed", proposed_name=promoted, page=page, quote="x")
        for page in (11, 12, 13)
    ]

    report = LOG.validate_log(lines)

    assert report["уже стало видом"] == {promoted: ["с. 11", "с. 12", "с. 13"]}
    assert report["готовы стать видом"] == {}
    assert report["ждут доказательств"] == {}


def test_an_observation_may_not_state_an_obligation_but_a_quote_may() -> None:
    """The work can say «должен»; an observation about the work cannot."""

    smuggled = LOG.validate_log([line(observation="Раздел должен открываться целью.")])
    quoted = LOG.validate_log(
        [line(kind="оговорка", observation="Ограничение выражено модально.", quote="должен быть оправдан")]
    )

    assert smuggled["valid"] is False
    assert "долженствование" in "\n".join(smuggled["errors"])
    assert quoted["valid"] is True


def test_an_observation_about_wording_carries_the_words() -> None:
    """Paraphrase destroys the evidence of a kind that is about wording."""

    for kind in sorted(LOG.QUOTE_REQUIRED):
        report = LOG.validate_log([line(kind=kind, quote=None)])
        assert report["valid"] is False, kind
        assert "приводит слова, а не пересказ" in "\n".join(report["errors"]), kind


def test_coverage_reports_the_pages_nobody_looked_at() -> None:
    """Reading every page is the point; an unread page has to be visible."""

    report = LOG.validate_log([line(page=2)], pages=4)

    assert report["counts"]["покрытие"]["страницы без наблюдений"] == [1, 3, 4]


def test_stored_reading_logs_validate() -> None:
    """Whatever the store holds must pass its own validator."""

    logs = sorted(LOG_DIR.glob("*.jsonl"))
    assert logs, "reading logs are the record of pass B; an empty directory is a regression"

    for path in logs:
        report = LOG.validate_log(path.read_text(encoding="utf-8-sig").splitlines())
        assert report["valid"] is True, f"{path.name}: {report['errors']}"


def test_the_tikhomirov_log_covers_every_page_of_the_work() -> None:
    """Pass B on Tikhomirov was a full read, and the log is where that is checked.

    The work has 102 pages in the PDF. A gap here means either a page was
    skipped or a page with nothing on it was left unrecorded, and the log
    cannot tell those apart after the fact.
    """

    path = LOG_DIR / "WORK-TIKHOMIROV-2021-DISS.jsonl"
    report = LOG.validate_log(path.read_text(encoding="utf-8-sig").splitlines(), pages=102)

    assert report["counts"]["покрытие"]["страницы без наблюдений"] == []
