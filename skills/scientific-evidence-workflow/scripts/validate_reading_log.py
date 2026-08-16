"""Validate a reading log: one observation per line, JSON Lines.

The log is written in chunks across sessions, so it has to survive being
appended to and it has to be checkable at any moment, not only when finished.

Three rules matter here beyond the shape:

1. an observation without a locator cannot be checked back, and a reading log
   full of unlocatable claims is worse than no log;
2. `kind: "unnamed"` is what makes discovery possible — the reader is not
   confined to the kinds someone thought of in advance — but even the unnamed
   must be given a proposed name, or the log fills with shapeless remarks;
3. a proposed name becomes a kind only on three or more separate locators. One
   occurrence is an event. Two is a coincidence.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# The obligation scanner lives with the work-card validator. Importing it keeps
# one definition of what counts as smuggling a rule into an observation.
_SPEC = importlib.util.spec_from_file_location(
    "_work_card", Path(__file__).with_name("validate_work_card.py")
)
assert _SPEC and _SPEC.loader
_WORK_CARD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_WORK_CARD)

KINDS = (
    "открытие-раздела",
    "ход-довода",
    "опора",
    "своё-чужое",
    "число",
    "иллюстрация",
    "термин",
    "переход",
    "оговорка",
    "закрытие-раздела",
    "unnamed",
)
# Observations about how something is worded lose their evidence when
# paraphrased, so they carry the words themselves.
QUOTE_REQUIRED = {"термин", "оговорка", "своё-чужое"}
PROMOTION_THRESHOLD = 3

LINE_FIELDS = {"section", "page", "kind", "observation", "quote", "proposed_name", "note"}
LINE_REQUIRED = ("section", "kind", "observation")


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_line(record: Any, index: int, errors: list[str], warnings: list[str]) -> None:
    path = f"строка {index}"
    if not isinstance(record, dict):
        errors.append(f"{path}: ожидается объект")
        return

    for key in sorted(set(record) - LINE_FIELDS):
        errors.append(f"{path}: неизвестное поле {key!r}")
    for key in LINE_REQUIRED:
        if not _nonempty(record.get(key)):
            errors.append(f"{path}.{key}: ожидается непустая строка")

    page = record.get("page")
    if not isinstance(page, int) or page < 1:
        errors.append(f"{path}.page: наблюдение без страницы нельзя проверить по источнику")

    kind = record.get("kind")
    if kind not in KINDS:
        errors.append(f"{path}.kind: ожидается одно из {list(KINDS)}")
        return

    if kind == "unnamed" and not _nonempty(record.get("proposed_name")):
        errors.append(
            f"{path}.proposed_name: наблюдение вне перечня обязано получить имя, "
            "иначе журнал наполняется бесформенными замечаниями"
        )
    if kind != "unnamed" and _nonempty(record.get("proposed_name")):
        errors.append(f"{path}.proposed_name: имя предлагается только для вида 'unnamed'")

    if kind in QUOTE_REQUIRED and not _nonempty(record.get("quote")):
        errors.append(f"{path}.quote: наблюдение о формулировке приводит слова, а не пересказ")

    # `quote` is verbatim from the work and may say «должен»; the observation
    # about it may not.
    for field in ("observation", "note"):
        value = record.get(field)
        if _nonempty(value) and _WORK_CARD.OBLIGATION.search(value):
            found = _WORK_CARD.OBLIGATION.search(value)
            assert found is not None
            errors.append(
                f"{path}.{field}: наблюдение выражает долженствование ({found.group(0)!r}); "
                "опиши, что работа делает, или перенеси слова в 'quote'"
            )


def validate_log(lines: list[str], pages: int | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    records: list[dict[str, Any]] = []

    for index, raw in enumerate(lines, start=1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as error:
            errors.append(f"строка {index}: не разбирается как JSON — {error}")
            continue
        validate_line(record, index, errors, warnings)
        if isinstance(record, dict):
            records.append(record)

    proposed: dict[str, list[str]] = defaultdict(list)
    for record in records:
        if record.get("kind") == "unnamed" and _nonempty(record.get("proposed_name")):
            proposed[record["proposed_name"]].append(f"с. {record.get('page')}")

    ready = {name: places for name, places in proposed.items() if len(places) >= PROMOTION_THRESHOLD}
    waiting = {name: places for name, places in proposed.items() if len(places) < PROMOTION_THRESHOLD}

    touched = sorted({r["page"] for r in records if isinstance(r.get("page"), int)})
    coverage: dict[str, Any] = {"страниц с наблюдениями": len(touched)}
    if pages:
        missing = [p for p in range(1, pages + 1) if p not in set(touched)]
        coverage["всего страниц"] = pages
        coverage["доля покрытия"] = round(len(touched) / pages, 3)
        coverage["страницы без наблюдений"] = missing
        if missing:
            warnings.append(
                f"без наблюдений остались страницы: {missing[:20]}"
                f"{' и ещё ' + str(len(missing) - 20) if len(missing) > 20 else ''}"
            )

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "наблюдений": len(records),
            "по видам": dict(Counter(r.get("kind") for r in records)),
            "покрытие": coverage,
        },
        "готовы стать видом": ready,
        "ждут доказательств": waiting,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    parser.add_argument("--pages", type=int, help="сколько страниц в источнике, для расчёта покрытия")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    try:
        lines = args.log.read_text(encoding="utf-8-sig").splitlines()
    except OSError as error:
        report = {"valid": False, "errors": [str(error)], "warnings": [], "counts": {}}
    else:
        report = validate_log(lines, args.pages)

    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
