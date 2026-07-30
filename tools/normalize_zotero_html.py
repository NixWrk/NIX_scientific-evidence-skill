"""Normalize a Zotero HTML attachment into traceable text blocks.

The normalized document may contain copyrighted full text and therefore should
be written under the ignored ``runs/`` directory. Only hashes and aggregate
statistics belong in committed experiment manifests.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag


TEXT_KINDS = {
    "p": "paragraph",
    "li": "list_item",
    "figcaption": "figure_caption",
    "blockquote": "quote",
}
BLOCK_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", *TEXT_KINDS, "table"}
SPACE_RE = re.compile(r"\s+")


def clean_text(value: str) -> str:
    """Collapse layout whitespace without changing punctuation or wording."""

    return SPACE_RE.sub(" ", value).strip()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def choose_root(soup: BeautifulSoup) -> Tag:
    """Choose the narrowest likely article container."""

    for selector in ("main#marker-doc", "article", "main", "body"):
        candidate = soup.select_one(selector)
        if isinstance(candidate, Tag):
            return candidate
    return soup


def css_selector(element: Tag, root: Tag) -> str:
    """Build a deterministic structural selector relative to the article root."""

    segments: list[str] = []
    current: Tag | None = element
    while current is not None and current is not root:
        parent = current.parent
        if not isinstance(parent, Tag):
            break
        siblings = [child for child in parent.children if isinstance(child, Tag) and child.name == current.name]
        position = siblings.index(current) + 1
        segments.append(f"{current.name}:nth-of-type({position})")
        current = parent

    root_name = root.name or "document"
    root_selector = f"{root_name}#{root['id']}" if root.get("id") else root_name
    return " > ".join([root_selector, *reversed(segments)])


def table_value(table: Tag) -> list[list[str]]:
    rows: list[list[str]] = []
    for row in table.find_all("tr"):
        cells = [clean_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"], recursive=False)]
        if cells:
            rows.append(cells)
    return rows


def normalize_html(
    raw_html: bytes,
    *,
    source_id: str,
    zotero_item_key: str,
    attachment_key: str,
) -> dict[str, Any]:
    """Return a JSON-serializable normalized representation."""

    soup = BeautifulSoup(raw_html, "lxml")
    root = choose_root(soup)

    for unwanted in root.select("script, style, nav, aside, footer, noscript"):
        unwanted.decompose()

    blocks: list[dict[str, Any]] = []
    section_stack: list[str] = []

    for element in root.find_all(BLOCK_TAGS):
        if element.name != "table" and element.find_parent("table") is not None:
            continue
        if element.name == "li" and element.find_parent("li") is not None:
            continue

        locator = {
            "representation": "html",
            "selector": css_selector(element, root),
        }

        if element.name and re.fullmatch(r"h[1-6]", element.name):
            text = clean_text(element.get_text(" ", strip=True))
            if not text:
                continue
            level = int(element.name[1])
            section_stack = section_stack[: level - 1]
            section_stack.append(text)
            block = {
                "kind": "heading",
                "level": level,
                "text": text,
                "section_path": list(section_stack),
                "locator": locator,
            }
        elif element.name == "table":
            rows = table_value(element)
            if not rows:
                continue
            block = {
                "kind": "table",
                "rows": rows,
                "text": " | ".join(" | ".join(row) for row in rows),
                "section_path": list(section_stack),
                "locator": locator,
            }
        else:
            text = clean_text(element.get_text(" ", strip=True))
            if not text:
                continue
            block = {
                "kind": TEXT_KINDS[element.name],
                "text": text,
                "section_path": list(section_stack),
                "locator": locator,
            }

        block["block_id"] = f"{source_id}-B{len(blocks) + 1:04d}"
        blocks.append(block)

    title = clean_text(soup.title.get_text(" ", strip=True)) if soup.title else None
    joined_text = "\n".join(block["text"] for block in blocks)
    return {
        "schema_version": 1,
        "source_id": source_id,
        "zotero_item_key": zotero_item_key,
        "attachment_key": attachment_key,
        "representation": "html",
        "content_sha256": sha256_bytes(raw_html),
        "title": title,
        "statistics": {
            "bytes": len(raw_html),
            "blocks": len(blocks),
            "headings": sum(block["kind"] == "heading" for block in blocks),
            "tables": sum(block["kind"] == "table" for block in blocks),
            "characters": len(joined_text),
            "words": len(joined_text.split()),
        },
        "blocks": blocks,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stats-output", type=Path)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--zotero-item-key", required=True)
    parser.add_argument("--attachment-key", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw_html = args.input.read_bytes()
    document = normalize_html(
        raw_html,
        source_id=args.source_id,
        zotero_item_key=args.zotero_item_key,
        attachment_key=args.attachment_key,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.stats_output:
        stats = {key: value for key, value in document.items() if key != "blocks"}
        args.stats_output.parent.mkdir(parents=True, exist_ok=True)
        args.stats_output.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
