"""Build an isolated Q&A runner directory without exposing gold answers."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from validate_experiment import read_jsonl


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", type=Path, required=True)
    parser.add_argument("--normalized-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output_dir
    corpus_output = output / "corpus"
    corpus_output.mkdir(parents=True, exist_ok=True)

    questions = [
        {"question_id": record["question_id"], "question": record["question"]}
        for record in read_jsonl(args.experiment_dir / "gold.jsonl")
    ]
    (output / "questions.jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in questions),
        encoding="utf-8",
    )

    shutil.copy2(args.experiment_dir / "prompt.md", output / "instructions.md")
    shutil.copy2(args.experiment_dir / "response.schema.json", output / "response.schema.json")

    documents: list[dict[str, str]] = []
    for source in read_jsonl(args.experiment_dir / "corpus.jsonl"):
        source_id = source["source_id"]
        source_path = args.normalized_dir / f"{source_id}.json"
        target_path = corpus_output / source_path.name
        shutil.copy2(source_path, target_path)
        documents.append({"source_id": source_id, "sha256": sha256(target_path)})

    manifest = {
        "experiment_id": "EXP-0001",
        "questions": len(questions),
        "documents": documents,
        "instructions_sha256": sha256(output / "instructions.md"),
        "response_schema_sha256": sha256(output / "response.schema.json"),
        "contains_gold_answers": False,
    }
    (output / "runner-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    forbidden = [path for path in output.rglob("*") if "gold" in path.name.lower()]
    if forbidden:
        raise RuntimeError(f"Gold leakage detected: {forbidden}")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
