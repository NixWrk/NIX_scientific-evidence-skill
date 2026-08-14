#!/usr/bin/env python3
"""Heuristic audit for recurrent problems in Russian scientific prose.

Rules are data, not code. `russian/core.json` always applies; genre and domain
profiles layer on top of it. Genre and subject area are independent axes: a
review written about ultrasound needs `genre-review` and a domain profile, and
neither one implies the other. Keeping them apart is what lets the audit move
to another topic without carrying someone else's vocabulary along.
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
        raise FileNotFoundError(f"unknown profile {profile_id!r}; available: {available}")
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
            raise ValueError(f"{profile_id}: profile_id field does not match the file name")
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


def audit_text(text: str, profile_ids: Sequence[str] = (), directory: Path = PROFILE_DIR) -> dict:
    ruleset = build_ruleset(profile_ids, directory)
    issues = []
    for line_number, line in visible_lines(text):
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
                            "Translate the word or verify that it is a necessary "
                            "introduced term or identifier."
                        ),
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
            "Surface-pattern audit only; it does not verify facts, terminology, "
            "syntax, cohesion, or scientific quality."
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="UTF-8 Markdown or text file")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--profile",
        action="append",
        default=[],
        metavar="PROFILE_ID",
        help="additional profile, repeatable; genre-* and domain-* ids are resolved "
        "under scripts/russian/ (the core profile always applies)",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="list available profiles and exit",
    )
    parser.add_argument(
        "--fail-on",
        choices=("never", "error", "warning"),
        default="never",
        help="select findings that produce exit status 1 (default: never)",
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
