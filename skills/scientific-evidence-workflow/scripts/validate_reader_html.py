"""Validate a reader-facing HTML export of a scientific notebook.

The validator checks release mechanics only. It does not assess scientific
truth, visual quality, or whether a citation supports the surrounding claim.
"""

from __future__ import annotations

import argparse
import json
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


CODE_INPUT_CLASSES = {
    "input",
    "input_area",
    "input_prompt",
    "jp-inputprompt",
    "jp-codecell-inputwrapper",
}
EXTERNAL_SCHEMES = {"http", "https", "mailto"}


class ReaderHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.links: list[tuple[str | None, int]] = []
        self.empty_anchors: list[int] = []
        self.images: list[tuple[str | None, int]] = []
        self.code_inputs: list[tuple[str, int]] = []
        self.class_stack: list[set[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {name.lower(): value for name, value in attrs}
        for key in ("id", "name"):
            value = values.get(key)
            if value:
                self.ids.add(unquote(value))

        if tag.lower() == "a":
            href = values.get("href")
            if href is not None:
                self.links.append((href, self.getpos()[0]))
            elif not values.get("id") and not values.get("name"):
                self.empty_anchors.append(self.getpos()[0])
        if tag.lower() == "img":
            self.images.append((values.get("src"), self.getpos()[0]))

        classes = {
            item.lower()
            for item in (values.get("class") or "").split()
            if item
        }
        inside_code_cell = "jp-codecell" in classes or any(
            "jp-codecell" in ancestor for ancestor in self.class_stack
        )
        mime = (values.get("data-mime-type") or "").lower()
        script_type = (values.get("type") or "").lower()
        if classes & CODE_INPUT_CLASSES or (
            "jp-inputarea" in classes and inside_code_cell
        ):
            self.code_inputs.append(("class=" + " ".join(sorted(classes)), self.getpos()[0]))
        elif mime.startswith("text/x-"):
            self.code_inputs.append((f"mime={mime or script_type}", self.getpos()[0]))
        self.class_stack.append(classes)

    def handle_endtag(self, tag: str) -> None:
        if self.class_stack:
            self.class_stack.pop()

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)


def _finding(rule_id: str, message: str, *, line: int | None = None) -> dict[str, Any]:
    finding: dict[str, Any] = {"rule_id": rule_id, "severity": "error", "message": message}
    if line is not None:
        finding["line_number"] = line
    return finding


def _local_target_exists(target: str, html_path: Path) -> bool:
    clean = unquote(target.split("#", 1)[0]).strip()
    if not clean:
        return True
    path = Path(clean)
    if not path.is_absolute():
        path = html_path.parent / path
    return path.exists()


def validate_reader_html(text: str, *, path: str | Path = "<memory>") -> dict[str, Any]:
    parser = ReaderHTMLParser()
    findings: list[dict[str, Any]] = []
    try:
        parser.feed(text)
        parser.close()
    except Exception as error:  # HTMLParser exposes several ValueError subclasses.
        findings.append(_finding("HTML-STRUCT-001", f"HTML cannot be parsed: {error}"))

    html_path = Path(path)
    for description, line in parser.code_inputs:
        findings.append(
            _finding(
                "HTML-CODE-001",
                f"Reader HTML contains a visible or embedded notebook input area ({description}).",
                line=line,
            )
        )

    for line in parser.empty_anchors:
        findings.append(_finding("HTML-LINK-001", "Anchor has no href, id, or name.", line=line))

    for href, line in parser.links:
        if not href or not href.strip():
            findings.append(_finding("HTML-LINK-001", "Anchor has no href.", line=line))
            continue
        target = href.strip()
        lowered = target.lower()
        if lowered.startswith("javascript:"):
            findings.append(_finding("HTML-LINK-002", "javascript: links are forbidden.", line=line))
            continue
        if target.startswith("#"):
            fragment = unquote(target[1:])
            if not fragment or fragment not in parser.ids:
                findings.append(
                    _finding(
                        "HTML-LINK-003",
                        f"Internal link does not resolve: {target!r}.",
                        line=line,
                    )
                )
            continue
        parsed = urlparse(target)
        if parsed.scheme:
            if parsed.scheme.lower() not in EXTERNAL_SCHEMES and parsed.scheme.lower() != "data":
                findings.append(
                    _finding(
                        "HTML-LINK-004",
                        f"Unsupported link scheme: {parsed.scheme!r}.",
                        line=line,
                    )
                )
            continue
        if str(path) != "<memory>" and not _local_target_exists(target, html_path):
            findings.append(
                _finding(
                    "HTML-LINK-005",
                    f"Local link target does not exist: {target!r}.",
                    line=line,
                )
            )

    for src, line in parser.images:
        if not src or not src.strip():
            findings.append(_finding("HTML-IMAGE-001", "Image has no src.", line=line))
            continue
        target = src.strip()
        parsed = urlparse(target)
        if parsed.scheme in {"data", "http", "https"}:
            continue
        if parsed.scheme:
            findings.append(
                _finding(
                    "HTML-IMAGE-002",
                    f"Unsupported image scheme: {parsed.scheme!r}.",
                    line=line,
                )
            )
        elif str(path) != "<memory>" and not _local_target_exists(target, html_path):
            findings.append(
                _finding(
                    "HTML-IMAGE-003",
                    f"Image target does not exist: {target!r}.",
                    line=line,
                )
            )

    counts = {"error": len(findings), "warning": 0, "note": 0}
    return {
        "path": str(path),
        "status": "fail" if findings else "pass",
        "valid": not findings,
        "counts": counts,
        "findings": findings,
        "metrics": {
            "anchors": len(parser.ids),
            "links": len(parser.links),
            "images": len(parser.images),
            "code_input_areas": len(parser.code_inputs),
        },
        "not_assessed": [
            "scientific_validity",
            "citation_support",
            "visual_layout",
            "remote_url_availability",
        ],
    }


def lint_path(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as error:
        return {
            "path": str(path),
            "status": "fail",
            "valid": False,
            "counts": {"error": 1, "warning": 0, "note": 0},
            "findings": [_finding("HTML-STRUCT-002", f"Cannot read HTML: {error}")],
            "metrics": {},
            "not_assessed": [],
        }
    return validate_reader_html(text, path=path)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    targets: list[Path] = []
    for path in args.paths:
        if path.is_dir():
            targets.extend(sorted(path.rglob("*.html")))
        elif path.suffix.lower() in {".html", ".htm"}:
            targets.append(path)
    reports = [lint_path(path) for path in sorted(set(targets))]
    if not reports:
        print(json.dumps({"status": "input_error", "reports": []}, indent=2))
        return 2
    aggregate = {
        "status": "fail" if any(not report["valid"] for report in reports) else "pass",
        "reports": reports,
    }
    if args.json:
        print(json.dumps(aggregate, ensure_ascii=False, indent=2))
    else:
        for report in reports:
            print(f"{report['status'].upper():4} {report['path']}")
            for finding in report["findings"]:
                print(f"  {finding['rule_id']}: {finding['message']}")
    return 1 if aggregate["status"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
