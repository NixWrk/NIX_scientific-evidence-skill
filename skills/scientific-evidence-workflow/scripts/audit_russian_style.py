#!/usr/bin/env python3
"""Heuristic audit for recurrent problems in Russian scientific prose."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


RULES = (
    (
        "mixed_english",
        "error",
        re.compile(
            r"(?i)(?<![\w-])(?:narrative review|journal articles?|full texts?|"
            r"evidence|endpoints?|respiratory effort|pressure support|"
            r"ventilatory settings?|prospective substudies?|derivation cohorts?|"
            r"accessory muscles?|load/capacity balance|diaphragm dysfunction|"
            r"skin-to-(?:pleura|liver|rhomboid)(?: distance| depth)?|"
            r"mid-axillary(?: line)?|breathing phase|respiratory phase|"
            r"procedural acoustic window|treatment decisions?|consensus guidelines?|"
            r"meta-analysis|cut-?offs?|thresholds?|reproducibility|"
            r"workflow|fallback|retries|production-ready|performance|"
            r"claims?|sites?|tasks?|populations?|eligible|supported|bounded|"
            r"unsupported)(?![\w-])"
        ),
        "Use a precise Russian equivalent or introduce the foreign term once.",
    ),
    (
        "hybrid_verb",
        "error",
        re.compile(
            r"(?i)(?<![а-яё])(?:ретра(?:ить|ится|ил[аи]?|ено)|"
            r"фетч(?:ить|ится|ил[аи]?|ено)|кэшировать|"
            r"мерж(?:ить|ится|ил[аи]?|ено)|пуш(?:ить|ится|ил[аи]?|ено)|"
            r"парс(?:ить|ится|ил[аи]?|ено)|логировать|"
            r"депло(?:ить|ится|ил[аи]?|ено))(?![а-яё])"
        ),
        "Replace the hybrid verb with a Russian description of the action.",
    ),
    (
        "mixed_script_word",
        "error",
        re.compile(
            r"(?<![A-Za-zА-Яа-яЁё])(?:"
            r"(?:[A-Z][a-z]+|[a-z]+)-[А-Яа-яЁё]+|"
            r"[А-Яа-яЁё]+-(?:[A-Z][a-z]+|[a-z]+)"
            r")(?![A-Za-zА-Яа-яЁё])"
        ),
        "Replace mixed-script word formation with a normative Russian phrase.",
    ),
    (
        "empty_metaphrase",
        "warning",
        re.compile(
            r"(?i)(?<![а-яё])(?:важно отметить|следует отметить|"
            r"нельзя не отметить|очевидно|в целом)(?![а-яё])"
        ),
        "Remove the metaphrase if the sentence keeps its meaning.",
    ),
    (
        "unsupported_booster",
        "warning",
        re.compile(
            r"(?i)(?<![а-яё])(?:критически важно|ключев(?:ая роль|ую роль)|"
            r"значительно улучшает|оптимальн(?:ый|ая|ое|ые)|"
            r"высокоэффективн(?:ый|ая|ое|ые))(?![а-яё])"
        ),
        "Give a criterion or replace the evaluation with an exact observation.",
    ),
    (
        "vague_calque",
        "warning",
        re.compile(
            r"(?i)(?<![а-яё])(?:это про|в части|на уровне|в рамках)(?![а-яё])"
        ),
        "Name the exact action, object, relation, or condition.",
    ),
)

LATIN_WORD = re.compile(r"(?<![\w-])[A-Za-z][A-Za-z/-]*(?![\w-])")
LATIN_PROSE_ALLOW = {"p", "r", "rho"}


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


def audit_text(text: str) -> dict:
    issues = []
    for line_number, line in visible_lines(text):
        covered_spans = []
        for code, severity, pattern, message in RULES:
            for match in pattern.finditer(line):
                covered_spans.append(match.span())
                issues.append(
                    {
                        "code": code,
                        "severity": severity,
                        "line": line_number,
                        "match": match.group(0),
                        "message": message,
                    }
                )

        if re.search(r"[А-Яа-яЁё]", line):
            for match in LATIN_WORD.finditer(line):
                token = match.group(0)
                if any(start <= match.start() < end for start, end in covered_spans):
                    continue
                if token in LATIN_PROSE_ALLOW or token[0].isupper():
                    continue
                issues.append(
                    {
                        "code": "latin_prose",
                        "severity": "warning",
                        "line": line_number,
                        "match": token,
                        "message": (
                            "Translate the word or verify that it is a necessary "
                            "introduced term or identifier."
                        ),
                    }
                )

    errors = sum(issue["severity"] == "error" for issue in issues)
    warnings = sum(issue["severity"] == "warning" for issue in issues)
    return {
        "valid": errors == 0,
        "counts": {"errors": errors, "warnings": warnings, "issues": len(issues)},
        "issues": issues,
        "limitations": (
            "Surface-pattern audit only; it does not verify facts, terminology, "
            "syntax, cohesion, or scientific quality."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="UTF-8 Markdown or text file")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--fail-on",
        choices=("never", "error", "warning"),
        default="never",
        help="select findings that produce exit status 1 (default: never)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = audit_text(args.path.read_text(encoding="utf-8"))
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
            f"errors={counts['errors']} warnings={counts['warnings']} "
            f"issues={counts['issues']}"
        )

    if args.fail_on == "error" and report["counts"]["errors"]:
        return 1
    if args.fail_on == "warning" and report["counts"]["issues"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
