"""Audit manuscript terminology against an approved term ledger."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

from critic_common import finding, load_json, write_envelope


def _count(text: str, phrase: str) -> int:
    return len(re.findall(rf"(?<!\w){re.escape(phrase)}(?!\w)", text, flags=re.IGNORECASE))


def audit(text: str, ledger: dict) -> list[dict]:
    findings: list[dict] = []
    owners: dict[str, set[str]] = defaultdict(set)
    terms = ledger.get("terms", [])
    for item in terms:
        term_id = str(item.get("term_id", "")).strip() or "UNIDENTIFIED"
        canonical = str(item.get("canonical", "")).strip()
        definition = str(item.get("definition", "")).strip()
        if not canonical or not definition:
            findings.append(
                finding(
                    f"TERM-LEDGER-{len(findings)+1:03d}", "TERM-001", "terminology",
                    {"term_id": term_id, "canonical": canonical, "definition": definition},
                    "term_id, canonical form, and approved definition are present",
                    word_action="none", severity="major",
                    suggested_fix="Дополнить утверждённый терминологический реестр; определение не генерировать автоматически.",
                )
            )
        for form in [canonical, *item.get("aliases", []), *item.get("forbidden_variants", [])]:
            if str(form).strip():
                owners[str(form).strip().casefold()].add(term_id)
        if canonical and _count(text, canonical) == 0:
            findings.append(
                finding(
                    f"TERM-UNUSED-{len(findings)+1:03d}", "TERM-002", "terminology",
                    canonical, "canonical term occurs in the manuscript", word_action="none",
                    severity="note", suggested_fix="Проверить необходимость записи или употребить утверждённую форму.",
                )
            )
        for variant in item.get("forbidden_variants", []):
            matches = list(
                re.finditer(
                    rf"(?<!\w){re.escape(str(variant))}(?!\w)",
                    text,
                    flags=re.IGNORECASE,
                )
            )
            for occurrence, match in enumerate(matches, start=1):
                findings.append(
                    finding(
                        f"TERM-FORBIDDEN-{len(findings)+1:03d}", "TERM-003", "terminology",
                        match.group(0), canonical, exact_text=match.group(0), occurrence=occurrence,
                        severity="major",
                        suggested_fix={"old": match.group(0), "new": canonical, "rationale": "Утверждённая каноническая форма."},
                        autofix_safe=True, word_action="tracked_change",
                    )
                )
    for form, term_ids in owners.items():
        if len(term_ids) > 1:
            findings.append(
                finding(
                    f"TERM-COLLISION-{len(findings)+1:03d}", "TERM-004", "terminology",
                    {"form": form, "term_ids": sorted(term_ids)},
                    "each canonical or alias form belongs to one term", word_action="none",
                    severity="major", suggested_fix="Разрешить коллизию в утверждённом реестре терминов.",
                )
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", type=Path)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(write_envelope(audit(args.text.read_text(encoding="utf-8-sig"), load_json(args.ledger)), args.output), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
