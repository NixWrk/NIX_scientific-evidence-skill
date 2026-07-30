"""Validate committed corpus/gold references against local normalized runs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as error:
            raise ValueError(f"{path}:{line_number}: {error}") from error
    return records


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    repeated: set[str] = set()
    for value in values:
        if value in seen:
            repeated.add(value)
        seen.add(value)
    return repeated


def validate(experiment_dir: Path, normalized_dir: Path) -> dict[str, Any]:
    errors: list[str] = []
    corpus = read_jsonl(experiment_dir / "corpus.jsonl")
    gold = read_jsonl(experiment_dir / "gold.jsonl")

    source_ids = [record["source_id"] for record in corpus]
    question_ids = [record["question_id"] for record in gold]
    for value in sorted(duplicates(source_ids)):
        errors.append(f"duplicate source_id: {value}")
    for value in sorted(duplicates(question_ids)):
        errors.append(f"duplicate question_id: {value}")

    blocks: dict[str, set[str]] = {}
    for record in corpus:
        source_id = record["source_id"]
        path = normalized_dir / f"{source_id}.json"
        if not path.exists():
            errors.append(f"missing normalized document: {source_id}")
            continue
        document = json.loads(path.read_text(encoding="utf-8"))
        if document["content_sha256"] != record["source_html_sha256"]:
            errors.append(f"content hash mismatch: {source_id}")
        blocks[source_id] = {block["block_id"] for block in document["blocks"]}

    evidence_count = 0
    for question in gold:
        if question["answerable"] and not question["evidence"]:
            errors.append(f"answerable question without evidence: {question['question_id']}")
        if not question["answerable"] and (question["evidence"] or question["expected_facts"]):
            errors.append(f"unanswerable question has gold facts: {question['question_id']}")
        for block_id in question["evidence"]:
            evidence_count += 1
            source_id = block_id.rsplit("-B", maxsplit=1)[0]
            if source_id not in blocks:
                errors.append(f"unknown source in evidence: {block_id}")
            elif block_id not in blocks[source_id]:
                errors.append(f"unknown block in evidence: {block_id}")

    return {
        "experiment_id": experiment_dir.name,
        "corpus_records": len(corpus),
        "gold_questions": len(gold),
        "evidence_references": evidence_count,
        "corpus_jsonl_sha256": file_sha256(experiment_dir / "corpus.jsonl"),
        "gold_jsonl_sha256": file_sha256(experiment_dir / "gold.jsonl"),
        "valid": not errors,
        "errors": errors,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", type=Path, required=True)
    parser.add_argument("--normalized-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = validate(args.experiment_dir, args.normalized_dir)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    if not report["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
