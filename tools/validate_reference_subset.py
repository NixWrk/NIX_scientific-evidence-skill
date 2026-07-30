"""Check that every block identifier in an output occurs in its frozen input."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


BLOCK_ID = re.compile(r"\bSRC-[A-Z0-9-]+-B\d{4}\b")


def validate_subset(artifact: Path, source_artifact: Path) -> dict[str, Any]:
    cited = BLOCK_ID.findall(artifact.read_text(encoding="utf-8"))
    available = set(BLOCK_ID.findall(source_artifact.read_text(encoding="utf-8")))
    unique_cited = sorted(set(cited))
    missing = sorted(set(unique_cited) - available)
    return {
        "artifact": str(artifact),
        "source_artifact": str(source_artifact),
        "references": len(cited),
        "unique_references": len(unique_cited),
        "source_references": len(available),
        "missing": missing,
        "valid": bool(cited) and not missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--source-artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    report = validate_subset(args.artifact, args.source_artifact)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
