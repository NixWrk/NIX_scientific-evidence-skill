"""Audit abbreviation definitions and list/text closure in Russian prose."""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

from critic_common import finding, load_json, write_envelope


TOKEN_RE = re.compile(r"(?<![A-Za-zА-ЯЁа-яё])(?:[A-ZА-ЯЁ]{2,}[A-ZА-ЯЁ0-9-]{0,10})(?![A-Za-zА-ЯЁа-яё])")
DEF_RE = re.compile(
    r"(?P<expansion>[A-ZА-ЯЁa-zа-яё][A-ZА-ЯЁa-zа-яё0-9 ,\-]{2,100}?)\s*"
    r"\((?P<abbr>[A-ZА-ЯЁ]{2,}[A-ZА-ЯЁ0-9-]{0,10})\)"
)
DEFAULT_ALLOW = {"ГОСТ", "РФ", "СССР", "ООН", "DOI", "URL", "ISBN", "ISSN"}
ROMAN_RE = re.compile(r"^[IVXLCDMХІ]+$")


def audit(text: str, declared: dict | None = None, allow: set[str] | None = None) -> list[dict]:
    allowed = DEFAULT_ALLOW | (allow or set())
    definitions: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for match in DEF_RE.finditer(text):
        definitions[match.group("abbr")].append((match.group("expansion").strip(), match.start("abbr")))

    declared_map: dict[str, str] = {}
    declared_values: dict[str, set[str]] = defaultdict(set)
    for item in (declared or {}).get("abbreviations", []):
        abbreviation = str(item.get("abbreviation", "")).strip()
        expansion = str(item.get("expansion", "")).strip()
        if abbreviation:
            declared_map.setdefault(abbreviation, expansion)
            if expansion:
                declared_values[abbreviation].add(expansion.casefold())

    findings: list[dict] = []
    occurrences: dict[str, int] = defaultdict(int)
    uses: dict[str, list[int]] = defaultdict(list)
    reported_undefined: set[str] = set()
    for match in TOKEN_RE.finditer(text):
        token = match.group(0)
        occurrences[token] += 1
        uses[token].append(match.start())
        if token in allowed or ROMAN_RE.fullmatch(token) or any(character.isdigit() for character in token):
            continue
        known = token in definitions or token in declared_map
        if not known and token not in reported_undefined:
            reported_undefined.add(token)
            findings.append(
                finding(
                    f"ABBR-UNDEFINED-{len(findings)+1:03d}", "ABBR-001", "abbreviations",
                    token, "first use is expanded or the abbreviation is declared",
                    exact_text=token, occurrence=occurrences[token], severity="major",
                    suggested_fix="Расшифровать при первом употреблении или добавить в утверждённый перечень.",
                )
            )
        elif token in definitions and match.start() < min(position for _, position in definitions[token]):
            findings.append(
                finding(
                    f"ABBR-BEFORE-DEFINITION-{len(findings)+1:03d}", "ABBR-002", "abbreviations",
                    token, "definition precedes the first abbreviated use", exact_text=token,
                    occurrence=occurrences[token], severity="major",
                    suggested_fix="Перенести расшифровку к первому употреблению.",
                )
            )

    # Parenthesized prose is not a safe deterministic source for semantic
    # conflict detection: grammatical context is easily captured as part of an
    # expansion. Treat the approved list as the authoritative conflict surface.
    for abbreviation, expansions in declared_values.items():
        if len(expansions) > 1:
            findings.append(
                finding(
                    f"ABBR-CONFLICT-{len(findings)+1:03d}", "ABBR-003", "abbreviations",
                    sorted(expansions), "one abbreviation has one approved meaning",
                    exact_text=abbreviation, occurrence=1, severity="major",
                    suggested_fix="Согласовать единственную расшифровку с терминологическим реестром.",
                )
            )

    for abbreviation in sorted(set(declared_map) - set(uses)):
        findings.append(
            finding(
                f"ABBR-UNUSED-{len(findings)+1:03d}", "ABBR-004", "abbreviations",
                abbreviation, "each listed abbreviation occurs in the manuscript",
                word_action="none", severity="note", suggested_fix="Удалить неиспользуемую запись после проверки.",
            )
        )

    skeletons: dict[str, set[str]] = defaultdict(set)
    translation = str.maketrans({"А": "A", "В": "B", "С": "C", "Е": "E", "Н": "H", "К": "K", "М": "M", "О": "O", "Р": "P", "Т": "T", "Х": "X"})
    for token in uses:
        skeletons[token.translate(translation)].add(token)
    for variants in skeletons.values():
        if len(variants) > 1:
            observed = sorted(variants)
            findings.append(
                finding(
                    f"ABBR-SCRIPT-{len(findings)+1:03d}", "ABBR-005", "abbreviations",
                    observed, "one script is used for visually identical abbreviations",
                    exact_text=observed[0], occurrence=1, severity="major",
                    suggested_fix="Проверить алфавит символов и выбрать утверждённое написание.",
                )
            )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", type=Path)
    parser.add_argument("--declared", type=Path)
    parser.add_argument("--allow", action="append", default=[])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    declared = load_json(args.declared) if args.declared else None
    print(write_envelope(audit(args.text.read_text(encoding="utf-8-sig"), declared, set(args.allow)), args.output), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
