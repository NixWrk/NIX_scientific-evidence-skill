"""Measure distributions over the whole text of a dissertation.

This is the discovery pass. It deliberately does not search for a list of known
things: it reports distributions whose anomalies point at patterns nobody has
named yet. A targeted search can only confirm what its author already suspected;
a distribution can surprise.

Everything here is measurement, not interpretation. Naming what a number means
is the reader's job, and it happens after the text has been read.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any

# Paragraph reconstruction: layout blocks, not blank-line splitting. Blank lines
# are unreliable in extracted PDFs, and in some documents every line arrives as
# its own block. A block is treated as data rather than prose when digits
# dominate it.
DIGIT_SHARE_OF_A_TABLE = 0.18
SHORTEST_PARAGRAPH = 40

HEDGE = r"\b(мож(?:ет|но|ут)|возможно|предположительно|по-видимому|вероятно|как правило|обычно|практически|порядка|около|приблизительно)\b"
CERTAIN = r"\b(установлено|показано|доказано|подтвержд\w+|определено|обоснован\w*)\b"
PERSONAL = r"\b(мы|нами|нам|автором работы|в нашей|наш\w+)\b"
IMPERSONAL = r"\b(проведен\w*|выполнен\w*|рассмотрен\w*|получен\w*|разработан\w*|предложен\w*|использован\w*)\b"
NEGATIVE = r"(не удалось|не позволя\w+|не обеспечива\w+|превышает допустим\w+|оказал\w+ недостаточн\w+|не в полной мере)"
COMPARISON = r"\b(по сравнению с|в отличие от|согласуется с|расходится с|лучше, чем|хуже, чем|относительно известн\w+)\b"
BOUNDARY = r"\b(при условии|в диапазоне|не более|не менее|ограничен\w*|в пределах|для случая)\b"
CITATION = r"\[(\d{1,3}(?:\s*[,–-]\s*\d{1,3})*)\]"
FIGURE_REF = r"\b(?:Рисунок|Рис\.?|рисунк\w+)\s*(\d+(?:\.\d+)?)"
TABLE_REF = r"\b(?:Таблиц\w+|Табл\.?)\s*(\d+(?:\.\d+)?)"
NUMBER = r"\b\d+(?:[.,]\d+)?\b"
# Written without a space in this corpus — «36±6» — so a pattern demanding one
# reports zero and looks like a finding. It did, until the count was checked
# against the text by hand.
UNCERTAINTY = r"\d\s*±\s*\d|±\s*\d+(?:[.,]\d+)?\s*%"
SAMPLE = r"\b(n\s*=\s*\d+|\d+\s+(?:добровольц\w+|доброволец|пациент\w+|испытуем\w+|измерени\w+|наблюдени\w+))"


CONTINUES = re.compile(r"[^.!?:;»)]\s*$")
RESUMES = re.compile(r"^[а-яёa-z(]")
HEADING = re.compile(r"^(?:Глава\s*\d|\d+(?:\.\d+)*\s+[А-ЯЁ])")
CAPTION = re.compile(r"^(?:Рисунок|Таблица|Рис\.|Табл\.)\s*\d")


def paragraphs(path: Path) -> list[dict[str, Any]]:
    """Rebuild paragraphs from layout blocks, keeping the page of each.

    A block is not a paragraph. Text wraps across blocks and across pages, and
    taking blocks as they come leaves nearly half of them as fragments — which
    was measured before this merging step was added, not assumed. A block that
    does not end a sentence is joined to the next one when that next one resumes
    in lower case.
    """

    import fitz

    document = fitz.open(path)
    raw: list[dict[str, Any]] = []
    for index, page in enumerate(document, start=1):
        for block in page.get_text("blocks"):
            if block[6] != 0:
                continue
            text = " ".join(block[4].split())
            if not text:
                continue
            digits = sum(character.isdigit() for character in text) / len(text)
            raw.append({
                "page": index,
                "text": text,
                "kind": "data" if digits > DIGIT_SHARE_OF_A_TABLE else "prose",
            })

    merged: list[dict[str, Any]] = []
    for block in raw:
        # A heading or a caption interrupts a paragraph without ending it; the
        # continuation may sit after it, or on the next page. Look back past
        # such interruptions for the prose block that is still open.
        target = None
        for candidate in reversed(merged[-3:]):
            if candidate["kind"] != "prose":
                continue
            if HEADING.match(candidate["text"]) or CAPTION.match(candidate["text"]):
                continue
            target = candidate
            break

        joinable = (
            target is not None
            and block["kind"] == "prose"
            and not HEADING.match(block["text"])
            and not CAPTION.match(block["text"])
            and CONTINUES.search(target["text"])
            and RESUMES.match(block["text"])
            and block["page"] - target["page"] <= 1
        )
        if joinable:
            # Line-break hyphenation survives extraction; drop it when joining.
            target["text"] = re.sub(r"[-‑]\s*$", "", target["text"]) + " " + block["text"]
            target["text"] = " ".join(target["text"].split())
            continue
        merged.append(dict(block))

    return [b for b in merged if len(b["text"]) >= SHORTEST_PARAGRAPH]


def reconstruction_quality(prose: list[str]) -> dict[str, Any]:
    """How well the rebuilt paragraphs behave like paragraphs.

    A reconstruction that nobody measured is an assumption. Two cheap signals:
    a paragraph should start with a capital and end where a sentence ends.
    """

    if not prose:
        return {"paragraphs": 0}
    starts = sum(1 for p in prose if p[:1].isupper() or p[:1].isdigit())
    ends = sum(1 for p in prose if p.rstrip()[-1:] in ".!?:;")
    return {
        "paragraphs": len(prose),
        "starts_with_capital": round(starts / len(prose), 3),
        "ends_with_sentence_punctuation": round(ends / len(prose), 3),
    }


def chapter_of(page: int, bounds: dict[str, list[int]]) -> str:
    for name, (first, last) in bounds.items():
        if first <= page <= last:
            return name
    return "вне глав"


def count(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text, re.IGNORECASE))


def measure(path: Path, bounds: dict[str, list[int]]) -> dict[str, Any]:
    blocks = paragraphs(path)
    prose = [b for b in blocks if b["kind"] == "prose"]
    data = [b for b in blocks if b["kind"] == "data"]
    whole = " ".join(b["text"] for b in prose)

    per_chapter: dict[str, dict[str, Any]] = {}
    for name in list(bounds) + ["вне глав"]:
        chunk = " ".join(b["text"] for b in prose if chapter_of(b["page"], bounds) == name)
        if not chunk:
            continue
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", chunk) if len(s) > 20]
        per_chapter[name] = {
            "paragraphs": sum(1 for b in prose if chapter_of(b["page"], bounds) == name),
            "characters": len(chunk),
            "hedging": count(HEDGE, chunk),
            "certainty": count(CERTAIN, chunk),
            "personal": count(PERSONAL, chunk),
            "impersonal": count(IMPERSONAL, chunk),
            "negative_result": count(NEGATIVE, chunk),
            "comparison_with_others": count(COMPARISON, chunk),
            "boundary_of_applicability": count(BOUNDARY, chunk),
            "citations": count(CITATION, chunk),
            "citations_per_1000_chars": round(count(CITATION, chunk) / len(chunk) * 1000, 2),
            "median_sentence_length": int(statistics.median(len(s) for s in sentences)) if sentences else None,
        }

    # Distance between a figure being named in prose and the caption block that
    # carries it. A negative distance means the prose points forward.
    caption_page: dict[str, int] = {}
    for block in blocks:
        m = re.match(r"(?:Рисунок|Таблица)\s*(\d+(?:\.\d+)?)", block["text"])
        if m:
            caption_page.setdefault(m.group(1), block["page"])
    distances = []
    for block in prose:
        for m in re.finditer(FIGURE_REF, block["text"]):
            page = caption_page.get(m.group(1))
            if page is not None:
                distances.append(page - block["page"])

    decimals = Counter(len(m.split(",")[1]) for m in re.findall(r"\d+,\d+", whole))
    numbers = re.findall(NUMBER, whole)

    return {
        "reconstruction": reconstruction_quality([b["text"] for b in prose]),
        "blocks": {"prose": len(prose), "data": len(data)},
        "pages": max((b["page"] for b in blocks), default=0),
        "per_chapter": per_chapter,
        "whole_text": {
            "characters": len(whole),
            "hedging": count(HEDGE, whole),
            "certainty": count(CERTAIN, whole),
            "personal": count(PERSONAL, whole),
            "impersonal": count(IMPERSONAL, whole),
            "negative_result": count(NEGATIVE, whole),
            "comparison_with_others": count(COMPARISON, whole),
            "boundary_of_applicability": count(BOUNDARY, whole),
            "citations": count(CITATION, whole),
            "numbers": len(numbers),
            "numbers_with_uncertainty": count(UNCERTAINTY, whole),
            "sample_size_mentions": count(SAMPLE, whole),
            "decimal_places": dict(sorted(decimals.items())),
            "figure_reference_distance_pages": {
                "n": len(distances),
                "forward": sum(1 for d in distances if d > 0),
                "same_page": sum(1 for d in distances if d == 0),
                "backward": sum(1 for d in distances if d < 0),
            },
        },
    }


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--bounds", type=Path, required=True, help="JSON: {chapter: [first_page, last_page]}")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    bounds = json.loads(args.bounds.read_text(encoding="utf-8"))
    report = measure(args.pdf, bounds)
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
