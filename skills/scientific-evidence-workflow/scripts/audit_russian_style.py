#!/usr/bin/env python3
"""Эвристическая проверка типичных недостатков русского научного текста.

Правила хранятся в данных. Профиль `russian/core.json` применяется всегда;
жанровые и предметные профили дополняют его независимо друг от друга.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable, NamedTuple, Sequence


PROFILE_DIR = Path(__file__).resolve().parent / "russian"
CORE_PROFILE = "core"

LATIN_WORD = re.compile(r"(?<![\w-])[A-Za-z][A-Za-z/-]*(?![\w-])")
WORD = re.compile(r"[A-Za-zА-Яа-яЁё]+")
CONTRASTIVE_SCAFFOLD = re.compile(
    r"(?i)(?:\bне\b[^.!?\n]{0,120},?\s+\bа\b|\bа\s+не\b|"
    r"\bно\s+не\b|\bне\s+только\b[^.!?\n]{0,120}\bно\s+и\b)"
)
FOCUS_PARTICLE = re.compile(r"(?i)(?<![а-яё])(?:именно|как раз)(?![а-яё])")
SEVERITIES = {"error", "warning"}


class Rule(NamedTuple):
    code: str
    severity: str
    pattern: re.Pattern[str]
    message: str
    profile: str


class Ruleset(NamedTuple):
    profiles: list[str]
    rules: list[Rule]
    latin_allow: frozenset[str]


def load_profile(profile_id: str, directory: Path = PROFILE_DIR) -> dict:
    path = directory / f"{profile_id}.json"
    if not path.is_file():
        available = sorted(item.stem for item in directory.glob("*.json"))
        raise FileNotFoundError(f"неизвестный профиль {profile_id!r}; доступны: {available}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_ruleset(profile_ids: Sequence[str] = (), directory: Path = PROFILE_DIR) -> Ruleset:
    """Compile the core profile plus any requested genre or domain profiles."""

    applied: list[str] = [CORE_PROFILE]
    for profile_id in profile_ids:
        if profile_id not in applied:
            applied.append(profile_id)

    rules: list[Rule] = []
    latin_allow: set[str] = set()
    for profile_id in applied:
        profile = load_profile(profile_id, directory)
        if profile.get("profile_id") != profile_id:
            raise ValueError(f"{profile_id}: поле profile_id не совпадает с именем файла")
        latin_allow.update(profile.get("latin_allow", []))
        for entry in profile["rules"]:
            if entry["severity"] not in SEVERITIES:
                raise ValueError(f"{profile_id}/{entry['code']}: unknown severity")
            rules.append(
                Rule(
                    code=entry["code"],
                    severity=entry["severity"],
                    pattern=re.compile(entry["pattern"]),
                    message=entry["message"],
                    profile=profile_id,
                )
            )
    return Ruleset(profiles=applied, rules=rules, latin_allow=frozenset(latin_allow))


def visible_lines(text: str) -> Iterable[tuple[int, str]]:
    """Yield prose lines with fenced code, inline code, and URLs masked."""
    in_fence = False
    for number, original in enumerate(text.splitlines(), start=1):
        if re.match(r"^\s*```", original):
            in_fence = not in_fence
            yield number, ""
            continue
        if in_fence:
            yield number, ""
            continue
        line = re.sub(r"`[^`]*`", "", original)
        line = re.sub(r"https?://\S+", "", line)
        line = re.sub(r"\]\([^)]*\)", "]", line)
        yield number, line


def find_occurrences(
    lines: Sequence[tuple[int, str]], pattern: re.Pattern[str]
) -> list[tuple[int, str]]:
    return [
        (line_number, match.group(0))
        for line_number, line in lines
        for match in pattern.finditer(line)
    ]


def audit_text(text: str, profile_ids: Sequence[str] = (), directory: Path = PROFILE_DIR) -> dict:
    ruleset = build_ruleset(profile_ids, directory)
    visible = list(visible_lines(text))
    issues = []
    for line_number, line in visible:
        covered_spans = []
        for rule in ruleset.rules:
            for match in rule.pattern.finditer(line):
                covered_spans.append(match.span())
                issues.append(
                    {
                        "code": rule.code,
                        "severity": rule.severity,
                        "profile": rule.profile,
                        "line": line_number,
                        "match": match.group(0),
                        "message": rule.message,
                    }
                )

        if re.search(r"[А-Яа-яЁё]", line):
            for match in LATIN_WORD.finditer(line):
                token = match.group(0)
                if any(start <= match.start() < end for start, end in covered_spans):
                    continue
                if token.lower() in ruleset.latin_allow or token[0].isupper():
                    continue
                issues.append(
                    {
                        "code": "latin_prose",
                        "severity": "warning",
                        "profile": CORE_PROFILE,
                        "line": line_number,
                        "match": token,
                        "message": (
                            "Переведи слово или проверь, что это необходимый и ранее "
                            "введённый термин либо идентификатор."
                        ),
                    }
                )

    word_count = sum(len(WORD.findall(line)) for _, line in visible)
    aggregate_rules = (
        (
            "contrastive_scaffolding",
            CONTRASTIVE_SCAFFOLD,
            4,
            250,
            "Слишком много фраз построено через отрицательное противопоставление. "
            "Сохрани необходимые контрасты, остальные утверждения сформулируй прямо.",
        ),
        (
            "focus_particle_density",
            FOCUS_PARTICLE,
            2,
            300,
            "Частицы фокуса повторяются слишком часто. Оставь их только для выбора "
            "одного объекта из нескольких явно названных.",
        ),
    )
    for code, pattern, minimum, words_per_hit, message in aggregate_rules:
        occurrences = find_occurrences(visible, pattern)
        if len(occurrences) < minimum:
            continue
        if len(occurrences) * words_per_hit < max(word_count, 1):
            continue
        issues.append(
            {
                "code": code,
                "severity": "warning",
                "profile": CORE_PROFILE,
                "line": occurrences[0][0],
                "match": f"{len(occurrences)} случаев на {word_count} слов",
                "message": message,
            }
        )

    errors = sum(issue["severity"] == "error" for issue in issues)
    warnings = sum(issue["severity"] == "warning" for issue in issues)
    return {
        "valid": errors == 0,
        "profiles": ruleset.profiles,
        "counts": {"errors": errors, "warnings": warnings, "issues": len(issues)},
        "issues": issues,
        "limitations": (
            "Эвристическая проверка распознаёт только часть поверхностных признаков; "
            "она не подтверждает факты, терминологию, синтаксис, связность или "
            "научное качество текста."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="текстовый файл или Markdown в UTF-8")
    parser.add_argument("--json", action="store_true", help="вывести отчёт JSON")
    parser.add_argument(
        "--profile",
        action="append",
        default=[],
        metavar="PROFILE_ID",
        help="дополнительный профиль; параметр можно повторять. Профили genre-* "
        "и domain-* загружаются из scripts/russian/, профиль core действует всегда",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="показать доступные профили и завершить работу",
    )
    parser.add_argument(
        "--fail-on",
        choices=("never", "error", "warning"),
        default="never",
        help="выбрать находки, при которых программа завершается с кодом 1",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.list_profiles:
        for path in sorted(PROFILE_DIR.glob("*.json")):
            profile = json.loads(path.read_text(encoding="utf-8"))
            print(f"{profile['profile_id']}: {profile['description']}")
        return 0

    report = audit_text(args.path.read_text(encoding="utf-8"), args.profile)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        for issue in report["issues"]:
            print(
                f"{args.path}:{issue['line']}: {issue['severity']} "
                f"{issue['code']}: {issue['match']}"
            )
        counts = report["counts"]
        print(
            f"profiles={','.join(report['profiles'])} errors={counts['errors']} "
            f"warnings={counts['warnings']} issues={counts['issues']}"
        )

    if args.fail_on == "error" and report["counts"]["errors"]:
        return 1
    if args.fail_on == "warning" and report["counts"]["issues"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
