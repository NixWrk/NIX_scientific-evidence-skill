"""Export executed notebooks to code-free reader HTML and validate the result."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _load_runtime():
    try:
        import nbformat
        from nbconvert import HTMLExporter
        from traitlets.config import Config
    except ImportError as error:
        raise RuntimeError(
            "Reader HTML export requires nbformat, nbconvert, and traitlets in the host environment."
        ) from error
    return nbformat, HTMLExporter, Config


def _load_local_validators():
    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    from validate_reader_html import lint_path as validate_html

    return validate_html


def export_notebook(path: Path, output_path: Path) -> dict[str, Any]:
    nbformat, HTMLExporter, Config = _load_runtime()
    validate_html = _load_local_validators()

    notebook = nbformat.read(path, as_version=4)
    config = Config()
    config.TemplateExporter.exclude_input = True
    config.TemplateExporter.exclude_input_prompt = True
    config.TemplateExporter.exclude_output_prompt = True
    config.HTMLExporter.embed_images = True
    exporter = HTMLExporter(config=config)
    exporter.template_name = "lab"
    body, _ = exporter.from_notebook_node(
        notebook,
        resources={"metadata": {"name": path.stem, "path": str(path.parent)}},
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(body, encoding="utf-8")
    report = validate_html(output_path)
    return {
        "source": str(path),
        "output": str(output_path),
        "status": report["status"],
        "validation": report,
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebooks", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    targets: list[Path] = []
    for path in args.notebooks:
        if path.is_dir():
            targets.extend(
                item
                for item in path.rglob("*.ipynb")
                if ".ipynb_checkpoints" not in item.parts
            )
        elif path.suffix.lower() == ".ipynb":
            targets.append(path)
    targets = sorted(set(targets))
    if not targets:
        print(json.dumps({"status": "input_error", "reports": []}, indent=2))
        return 2

    reports: list[dict[str, Any]] = []
    try:
        for path in targets:
            if args.output_dir:
                output = args.output_dir / f"{path.stem}.html"
            else:
                output = path.with_suffix(".html")
            reports.append(export_notebook(path, output))
    except (OSError, RuntimeError, ValueError) as error:
        print(json.dumps({"status": "fail", "error": str(error), "reports": reports}, ensure_ascii=False, indent=2))
        return 1

    aggregate = {
        "status": "fail" if any(report["status"] != "pass" for report in reports) else "pass",
        "reports": reports,
    }
    if args.json:
        print(json.dumps(aggregate, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            print(f"{report['status'].upper():4} {report['output']}")
    return 1 if aggregate["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
