"""Static audit for portable Agent Skills used in this repository.

The audit has two deliberately separate layers:

1. a dependency-free check of the required Agent Skills frontmatter subset;
2. policy signals that require a human verdict before a corpus run.

Policy signals are evidence, not an automatic accusation: a URL in a reference
list and a mandatory network call are not the same thing.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
from typing import Any


TOP_LEVEL_FIELD = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s*(.*))?$")

POLICY_PATTERNS: dict[str, re.Pattern[str]] = {
    "external_model": re.compile(
        r"\b(?:openai|anthropic|claude|gemini|perplexity|cross[- ]model|llm cli)\b",
        re.IGNORECASE,
    ),
    "network_access": re.compile(
        r"\b(?:web search|websearch|web_fetch|doi lookup|curl|wget|network access)\b|https?://",
        re.IGNORECASE,
    ),
    "corpus_expansion": re.compile(
        r"\b(?:discover literature|literature search|search strategy|search before|additional literature|external sources?|new papers?)\b",
        re.IGNORECASE,
    ),
    "state_mutation": re.compile(
        r"\b(?:write|writes|append|rewrite|delete|update|apply|modify)\b.{0,80}"
        r"(?:zotero|manuscript|\.research|\.paper)",
        re.IGNORECASE,
    ),
}


def _decode_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        try:
            decoded = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return value[1:-1]
        return str(decoded)
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse the top-level scalar subset needed by the Agent Skills spec."""

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")

    try:
        closing = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as exc:
        raise ValueError("SKILL.md frontmatter has no closing delimiter") from exc

    metadata: dict[str, str] = {}
    index = 1
    while index < closing:
        line = lines[index]
        match = TOP_LEVEL_FIELD.match(line)
        if not match:
            index += 1
            continue

        key, raw_value = match.groups()
        raw_value = raw_value or ""
        if raw_value in {"|", ">"}:
            folded: list[str] = []
            index += 1
            while index < closing and (not lines[index] or lines[index][0].isspace()):
                folded.append(lines[index].strip())
                index += 1
            metadata[key] = " ".join(part for part in folded if part)
            continue

        metadata[key] = _decode_scalar(raw_value)
        index += 1

    return metadata, "\n".join(lines[closing + 1 :]).strip()


def _valid_name(name: str) -> bool:
    if not 1 <= len(name) <= 64:
        return False
    if name != name.lower() or name.startswith("-") or name.endswith("-") or "--" in name:
        return False
    return all(character.isalnum() or character == "-" for character in name)


def audit_skill(skill_dir: Path) -> dict[str, Any]:
    skill_dir = skill_dir.resolve()
    skill_file = skill_dir / "SKILL.md"
    errors: list[str] = []
    warnings: list[str] = []

    if not skill_file.is_file():
        return {
            "skill_dir": str(skill_dir),
            "spec_subset_valid": False,
            "spec_errors": ["Missing required file: SKILL.md"],
            "warnings": [],
            "policy_signals": {},
        }

    raw = skill_file.read_bytes()
    text = raw.decode("utf-8-sig")
    try:
        metadata, body = parse_frontmatter(text)
    except ValueError as exc:
        metadata = {}
        body = ""
        errors.append(str(exc))

    name = metadata.get("name", "")
    description = metadata.get("description", "")
    compatibility = metadata.get("compatibility", "")

    if not name:
        errors.append("Missing required field in frontmatter: name")
    elif not _valid_name(name):
        errors.append("Invalid skill name")
    elif name != skill_dir.name:
        errors.append("Skill name must match the parent directory name")

    if not description:
        errors.append("Missing required field in frontmatter: description")
    elif len(description) > 1024:
        errors.append("Description exceeds 1024 characters")

    if compatibility and len(compatibility) > 500:
        errors.append("Compatibility exceeds 500 characters")
    if not body:
        errors.append("SKILL.md has no instruction body")

    line_count = len(text.splitlines())
    if line_count > 500:
        warnings.append("SKILL.md exceeds the recommended 500 lines")

    signals: dict[str, list[dict[str, Any]]] = {}
    for kind, pattern in POLICY_PATTERNS.items():
        matches: list[dict[str, Any]] = []
        for line_number, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                matches.append({"line": line_number, "text": line.strip()[:240]})
        if matches:
            signals[kind] = matches

    return {
        "skill_dir": str(skill_dir),
        "skill_file": str(skill_file),
        "name": name or None,
        "description_length": len(description),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "line_count": line_count,
        "spec_subset_valid": not errors,
        "spec_errors": errors,
        "warnings": warnings,
        "policy_signals": signals,
        "manual_policy_review_required": bool(signals),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_dir", type=Path, help="Directory containing SKILL.md")
    parser.add_argument(
        "--fail-on-policy-signals",
        action="store_true",
        help="Return a non-zero status when any policy signal is detected",
    )
    args = parser.parse_args()

    report = audit_skill(args.skill_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if not report["spec_subset_valid"]:
        return 1
    if args.fail_on_policy_signals and report["manual_policy_review_required"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
