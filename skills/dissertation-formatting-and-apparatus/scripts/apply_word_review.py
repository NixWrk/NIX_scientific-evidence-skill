#!/usr/bin/env python3
"""Apply a dissertation critic journal to a copy of a Word document.

The critic journal is the canonical review result.  This script only creates a
derived Word representation of that journal:

* ``comments`` adds true Word comments and leaves the text unchanged;
* ``track-changes`` adds OOXML insertions/deletions for safe replacements and
  comments for findings which cannot be represented as a replacement;
* ``hybrid`` uses both representations when ``word_action`` requests them.

Locators are deliberately strict.  ``locator.exact_text`` must occur exactly
once unless a positive, one-based ``locator.occurrence`` is supplied.  A
missing or ambiguous locator is an error; the script never chooses a nearby
match as a guess.

The implementation uses only the ZIP/XML layers of a DOCX.  That keeps the
source file byte-for-byte untouched and preserves existing comments and tracked
changes, including parts which are not understood by python-docx.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import importlib.util
import json
import os
import re
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from lxml import etree


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
REVIEW_NS = "urn:science-skills:dissertation-review"
XML_NS = "http://www.w3.org/XML/1998/namespace"

NS = {
    "w": W_NS,
    "r": R_NS,
    "pr": PKG_REL_NS,
    "ct": CT_NS,
    "review": REVIEW_NS,
}

COMMENTS_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
)
COMMENTS_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"
)
SETTINGS_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings"
)
SETTINGS_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"
)

WORD_ACTIONS = {
    "none",
    "comment",
    "tracked_change",
    "tracked_change_with_comment",
}
PROFILES = {"comments", "track-changes", "hybrid"}


_VALIDATOR_SPEC = importlib.util.spec_from_file_location(
    "dissertation_critic_findings_validator",
    Path(__file__).resolve().with_name("validate_critic_findings.py"),
)
assert _VALIDATOR_SPEC and _VALIDATOR_SPEC.loader
_VALIDATOR = importlib.util.module_from_spec(_VALIDATOR_SPEC)
_VALIDATOR_SPEC.loader.exec_module(_VALIDATOR)


def qn(namespace: str, local: str) -> str:
    return f"{{{namespace}}}{local}"


def w(local: str) -> str:
    return qn(W_NS, local)


def xml_bytes(root: etree._Element) -> bytes:
    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        standalone=True,
    )


def utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


class ReviewError(ValueError):
    """A journal or locator cannot be applied without guessing."""


class TextSegment:
    __slots__ = ("node", "run", "parent", "start", "end", "text")

    def __init__(
        self,
        node: etree._Element,
        run: etree._Element,
        parent: etree._Element,
        start: int,
        end: int,
        text: str,
    ) -> None:
        self.node = node
        self.run = run
        self.parent = parent
        self.start = start
        self.end = end
        self.text = text


class Match:
    __slots__ = ("paragraph", "segments", "start", "end", "text")

    def __init__(
        self,
        paragraph: etree._Element,
        segments: tuple[TextSegment, ...],
        start: int,
        end: int,
        text: str,
    ) -> None:
        self.paragraph = paragraph
        self.segments = segments
        self.start = start
        self.end = end
        self.text = text


def _json_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def load_journal(path: str | os.PathLike[str] | None) -> list[dict[str, Any]]:
    """Load the JSON journal accepted by the preliminary standard.

    The canonical shape is either a JSON list of findings or an object with an
    ``issues`` key.  ``findings`` and ``entries`` are accepted as harmless
    aliases because review exports in the repository use both terms.
    """

    if path is None:
        return []
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ReviewError(f"cannot read journal {source}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ReviewError(f"journal is not valid JSON: {source}: {exc}") from exc

    if isinstance(value, list):
        issues = value
    elif isinstance(value, Mapping):
        issues = None
        for key in ("issues", "findings", "entries"):
            if key in value:
                issues = value[key]
                break
        if issues is None:
            raise ReviewError("journal object must contain an 'issues' array")
    else:
        raise ReviewError("journal must be a JSON array or an object with 'issues'")

    if not isinstance(issues, list):
        raise ReviewError("journal issues must be an array")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, issue in enumerate(issues, start=1):
        if not isinstance(issue, Mapping):
            raise ReviewError(f"issue {index} must be an object")
        item = dict(issue)
        issue_id = item.get("issue_id")
        if not isinstance(issue_id, str) or not issue_id.strip():
            raise ReviewError(f"issue {index} has no non-empty issue_id")
        if issue_id in seen:
            raise ReviewError(f"duplicate issue_id: {issue_id}")
        seen.add(issue_id)

        action = item.get("word_action")
        if action not in WORD_ACTIONS:
            raise ReviewError(
                f"{issue_id}: word_action must be explicitly set to one of {sorted(WORD_ACTIONS)}"
            )
        result.append(item)
    return result


def _paragraphs(doc_root: etree._Element) -> list[etree._Element]:
    # document.xml can contain paragraphs in body, tables, SDTs, and other
    # normal Word containers.  Comments are in another part and are excluded.
    return list(doc_root.xpath(".//w:p", namespaces=NS))


def _is_descendant(element: etree._Element, tag: str) -> bool:
    parent = element.getparent()
    while parent is not None:
        if parent.tag == tag:
            return True
        parent = parent.getparent()
    return False


def _text_nodes(
    paragraph: etree._Element,
    *,
    include_deleted: bool = False,
) -> list[tuple[etree._Element, etree._Element]]:
    nodes: list[tuple[etree._Element, etree._Element]] = []
    for node in paragraph.xpath(".//w:t | .//w:delText", namespaces=NS):
        if node.tag == w("delText") and not include_deleted:
            continue
        if node.getparent() is None or node.getparent().tag != w("r"):
            continue
        if node.tag == w("delText"):
            # Deleted text is not current text.  It is available to audit and
            # comments only when include_deleted=True.
            if not include_deleted:
                continue
        nodes.append((node, node.getparent()))
    return nodes


def _segments(
    paragraph: etree._Element,
    *,
    include_deleted: bool = False,
) -> list[TextSegment]:
    result: list[TextSegment] = []
    offset = 0
    for node, run in _text_nodes(paragraph, include_deleted=include_deleted):
        text = node.text or ""
        segment = TextSegment(
            node=node,
            run=run,
            parent=run.getparent(),
            start=offset,
            end=offset + len(text),
            text=text,
        )
        result.append(segment)
        offset += len(text)
    return result


def _find_occurrences(text: str, needle: str) -> list[tuple[int, int]]:
    occurrences: list[tuple[int, int]] = []
    cursor = 0
    while True:
        hit = text.find(needle, cursor)
        if hit < 0:
            return occurrences
        occurrences.append((hit, hit + len(needle)))
        # Advancing by one also gives deterministic behavior for overlapping
        # matches, while ordinary phrases remain naturally non-overlapping.
        cursor = hit + 1


def _locator(issue: Mapping[str, Any]) -> Mapping[str, Any]:
    locator = issue.get("locator")
    if not isinstance(locator, Mapping):
        raise ReviewError(f"{issue['issue_id']}: locator must contain exact_text")
    exact_text = locator.get("exact_text")
    if not isinstance(exact_text, str) or exact_text == "":
        raise ReviewError(f"{issue['issue_id']}: locator.exact_text must be non-empty")
    occurrence = locator.get("occurrence")
    if occurrence is not None and (
        isinstance(occurrence, bool)
        or not isinstance(occurrence, int)
        or occurrence < 1
    ):
        raise ReviewError(
            f"{issue['issue_id']}: locator.occurrence must be a positive one-based integer"
        )
    return locator


def _resolve_match(
    doc_root: etree._Element,
    issue: Mapping[str, Any],
    *,
    include_deleted: bool = False,
) -> Match:
    locator = _locator(issue)
    needle = str(locator["exact_text"])
    occurrence = locator.get("occurrence")
    hits: list[Match] = []
    for paragraph in _paragraphs(doc_root):
        segments = _segments(paragraph, include_deleted=include_deleted)
        if not segments:
            continue
        paragraph_text = "".join(segment.text for segment in segments)
        for start, end in _find_occurrences(paragraph_text, needle):
            affected = tuple(
                segment
                for segment in segments
                if segment.start < end and segment.end > start
            )
            if affected:
                hits.append(
                    Match(
                        paragraph=paragraph,
                        segments=affected,
                        start=start,
                        end=end,
                        text=needle,
                    )
                )

    if occurrence is None:
        if len(hits) != 1:
            if not hits:
                raise ReviewError(
                    f"{issue['issue_id']}: exact_text not found: {needle!r}"
                )
            raise ReviewError(
                f"{issue['issue_id']}: exact_text is ambiguous ({len(hits)} matches); "
                "set locator.occurrence"
            )
        return hits[0]
    if occurrence > len(hits):
        raise ReviewError(
            f"{issue['issue_id']}: occurrence {occurrence} is out of range "
            f"for {len(hits)} matches of {needle!r}"
        )
    return hits[occurrence - 1]


def _clone_run_with_text(
    run: etree._Element,
    text: str,
    *,
    text_tag: str = "t",
) -> etree._Element | None:
    if not text:
        return None
    new_run = etree.Element(w("r"))
    rpr = run.find("w:rPr", namespaces=NS)
    if rpr is not None:
        new_run.append(etree.fromstring(etree.tostring(rpr)))
    text_node = etree.SubElement(new_run, w(text_tag))
    text_node.text = text
    if text[:1].isspace() or text[-1:].isspace():
        text_node.set(qn(XML_NS, "space"), "preserve")
    return new_run


def _ensure_single_text_run(segment: TextSegment, issue_id: str) -> None:
    run = segment.run
    text_children = run.xpath("./w:t | ./w:delText", namespaces=NS)
    if len(text_children) != 1 or text_children[0] is not segment.node:
        raise ReviewError(
            f"{issue_id}: locator touches a complex Word run; exact run-level "
            "editing is required"
        )
    if _is_descendant(run, w("ins")) or _is_descendant(run, w("del")):
        raise ReviewError(
            f"{issue_id}: locator touches an existing tracked change; refusing "
            "to nest a new redline"
        )


def _replace_match(
    match: Match,
    replacement: str,
    *,
    issue_id: str,
    change_id: int,
    author: str,
    when: str,
) -> tuple[int, etree._Element, etree._Element | None]:
    segments = list(match.segments)
    for segment in segments:
        _ensure_single_text_run(segment, issue_id)
    parents = {id(segment.parent): segment.parent for segment in segments}
    if len(parents) != 1:
        raise ReviewError(
            f"{issue_id}: locator spans incompatible Word containers; refusing to guess"
        )
    parent = segments[0].parent
    runs = [segment.run for segment in segments]
    if any(run.getparent() is not parent for run in runs):
        raise ReviewError(f"{issue_id}: locator does not form one editable run range")

    first = segments[0]
    last = segments[-1]
    first_local_start = match.start - first.start
    last_local_end = match.end - last.start
    before = first.text[:first_local_start]
    after = last.text[last_local_end:]
    old_text = "".join(
        segment.text[
            max(match.start, segment.start) - segment.start : min(match.end, segment.end)
        ]
        for segment in segments
    )

    deleted = etree.Element(w("del"))
    deleted.set(w("id"), str(change_id))
    deleted.set(w("author"), author)
    deleted.set(w("date"), when)
    deleted.set(qn(REVIEW_NS, "issue_id"), issue_id)
    deleted_run = _clone_run_with_text(runs[0], old_text, text_tag="delText")
    if deleted_run is None:  # pragma: no cover - old_text cannot be empty here
        raise ReviewError(f"{issue_id}: matched text is empty")
    deleted.append(deleted_run)

    inserted: etree._Element | None = None
    if replacement != "":
        inserted = etree.Element(w("ins"))
        inserted.set(w("id"), str(change_id + 1))
        inserted.set(w("author"), author)
        inserted.set(w("date"), when)
        inserted.set(qn(REVIEW_NS, "issue_id"), issue_id)
        inserted_run = _clone_run_with_text(runs[0], replacement, text_tag="t")
        if inserted_run is None:  # pragma: no cover - guarded by replacement check
            raise ReviewError(f"{issue_id}: replacement is empty")
        inserted.append(inserted_run)

    first_index = parent.index(runs[0])
    replacements: list[etree._Element] = []
    prefix_run = _clone_run_with_text(runs[0], before)
    if prefix_run is not None:
        replacements.append(prefix_run)
    replacements.append(deleted)
    if inserted is not None:
        replacements.append(inserted)
    suffix_run = _clone_run_with_text(runs[-1], after)
    if suffix_run is not None:
        replacements.append(suffix_run)

    for run in runs:
        parent.remove(run)
    for node in reversed(replacements):
        parent.insert(first_index, node)
    return change_id + (2 if inserted is not None else 1), deleted, inserted


def _comment_text(issue: Mapping[str, Any]) -> str:
    issue_id = str(issue["issue_id"])
    chunks = [f"[{issue_id}]"]
    for label in ("observed", "expected", "suggested_fix"):
        value = issue.get(label)
        if value is not None:
            chunks.append(f"{label}: {_json_value(value)}")
    if len(chunks) == 1:
        chunks.append("Review finding from the critic journal.")
    return "\n".join(chunks)


def _ensure_comments_root(existing: bytes | None) -> etree._Element:
    if existing is not None:
        return etree.fromstring(existing)
    return etree.Element(w("comments"), nsmap={"w": W_NS})


def _existing_comment_ids(comments_root: etree._Element) -> set[int]:
    values: set[int] = set()
    for element in comments_root.xpath(".//w:comment", namespaces=NS):
        value = element.get(w("id"))
        if value is not None:
            try:
                values.add(int(value))
            except ValueError:
                continue
    return values


def _existing_xml_ids(*roots: etree._Element | None) -> set[int]:
    values: set[int] = set()
    for root in roots:
        if root is None:
            continue
        for element in root.xpath(".//*[@w:id]", namespaces=NS):
            value = element.get(w("id"))
            if value is not None:
                try:
                    values.add(int(value))
                except ValueError:
                    continue
    return values


def _append_comment(
    comments_root: etree._Element,
    comment_id: int,
    text: str,
    *,
    author: str,
    when: str,
) -> None:
    comment = etree.SubElement(comments_root, w("comment"))
    comment.set(w("id"), str(comment_id))
    comment.set(w("author"), author)
    comment.set(w("date"), when)
    paragraph = etree.SubElement(comment, w("p"))
    run = etree.SubElement(paragraph, w("r"))
    text_node = etree.SubElement(run, w("t"))
    text_node.text = text
    if text[:1].isspace() or text[-1:].isspace():
        text_node.set(qn(XML_NS, "space"), "preserve")


def _anchor_elements(
    paragraph: etree._Element,
    start_element: etree._Element,
    end_element: etree._Element,
    comment_id: int,
) -> None:
    if start_element.getparent() is not paragraph or end_element.getparent() is not paragraph:
        raise ReviewError("comment anchor must stay within one paragraph")
    start_index = paragraph.index(start_element)
    paragraph.insert(start_index, etree.Element(w("commentRangeStart"), {w("id"): str(comment_id)}))
    # The inserted start shifts the end index by one only when it precedes the
    # end element; looking it up again avoids index arithmetic mistakes.
    end_index = paragraph.index(end_element) + 1
    paragraph.insert(end_index, etree.Element(w("commentRangeEnd"), {w("id"): str(comment_id)}))
    reference_run = etree.Element(w("r"))
    reference = etree.SubElement(reference_run, w("commentReference"))
    reference.set(w("id"), str(comment_id))
    paragraph.insert(end_index + 1, reference_run)


def _anchor_match(
    match: Match,
    *,
    comment_id: int,
    issue_id: str,
) -> tuple[etree._Element, etree._Element]:
    """Split ordinary runs so a comment range covers exactly exact_text."""

    segments = list(match.segments)
    for segment in segments:
        _ensure_single_text_run(segment, issue_id)
    parents = {id(segment.parent): segment.parent for segment in segments}
    if len(parents) != 1:
        raise ReviewError(
            f"{issue_id}: exact_text spans incompatible Word containers; refusing to guess"
        )
    parent = segments[0].parent
    runs = [segment.run for segment in segments]
    if any(run.getparent() is not parent for run in runs):
        raise ReviewError(f"{issue_id}: exact_text does not form one comment range")

    first = segments[0]
    last = segments[-1]
    before = first.text[: match.start - first.start]
    after = last.text[match.end - last.start :]
    inside_runs: list[etree._Element] = []
    replacements: list[etree._Element] = []
    prefix_run = _clone_run_with_text(runs[0], before)
    if prefix_run is not None:
        replacements.append(prefix_run)

    for index, segment in enumerate(segments):
        local_start = max(match.start, segment.start) - segment.start
        local_end = min(match.end, segment.end) - segment.start
        inside = segment.text[local_start:local_end]
        inside_run = _clone_run_with_text(segment.run, inside, text_tag="t")
        if inside_run is None:
            raise ReviewError(f"{issue_id}: locator resolved to empty text")
        inside_runs.append(inside_run)
        replacements.append(inside_run)
        # Only the final segment contributes a suffix; all intermediate text is
        # wholly covered by the locator.
        if index == len(segments) - 1:
            suffix_run = _clone_run_with_text(segment.run, after)
            if suffix_run is not None:
                replacements.append(suffix_run)

    first_index = parent.index(runs[0])
    for run in runs:
        parent.remove(run)
    for node in reversed(replacements):
        parent.insert(first_index, node)
    # Inside runs are now siblings in the paragraph.  Comment anchors belong
    # to the paragraph, not to the comment part.
    _anchor_elements(parent, inside_runs[0], inside_runs[-1], comment_id)
    return inside_runs[0], inside_runs[-1]


def _anchor_change(
    deleted: etree._Element,
    inserted: etree._Element | None,
    *,
    comment_id: int,
) -> None:
    parent = deleted.getparent()
    if parent is None:
        raise ReviewError("tracked change is detached before comment anchoring")
    end = inserted if inserted is not None else deleted
    _anchor_elements(parent, deleted, end, comment_id)


def _ensure_content_types(root: etree._Element) -> None:
    exists = root.xpath(
        ".//ct:Override[@PartName='/word/comments.xml']", namespaces=NS
    )
    if exists:
        return
    override = etree.SubElement(root, qn(CT_NS, "Override"))
    override.set("PartName", "/word/comments.xml")
    override.set("ContentType", COMMENTS_CONTENT_TYPE)


def _ensure_settings_content_type(root: etree._Element) -> None:
    if root.xpath(
        ".//ct:Override[@PartName='/word/settings.xml']", namespaces=NS
    ):
        return
    override = etree.SubElement(root, qn(CT_NS, "Override"))
    override.set("PartName", "/word/settings.xml")
    override.set("ContentType", SETTINGS_CONTENT_TYPE)


def _ensure_settings_relationship(root: etree._Element) -> None:
    for rel in root.xpath(".//pr:Relationship", namespaces=NS):
        if rel.get("Type") == SETTINGS_REL_TYPE and rel.get("Target") in {
            "settings.xml",
            "/word/settings.xml",
        }:
            return
    ids: list[int] = []
    for rel in root.xpath(".//pr:Relationship", namespaces=NS):
        match = re.fullmatch(r"rId(\d+)", rel.get("Id", ""))
        if match:
            ids.append(int(match.group(1)))
    rel = etree.SubElement(root, qn(PKG_REL_NS, "Relationship"))
    rel.set("Id", f"rId{max(ids, default=0) + 1}")
    rel.set("Type", SETTINGS_REL_TYPE)
    rel.set("Target", "settings.xml")


def _ensure_comments_relationship(root: etree._Element) -> None:
    for rel in root.xpath(".//pr:Relationship", namespaces=NS):
        if rel.get("Type") == COMMENTS_REL_TYPE:
            target = rel.get("Target", "")
            if target in {"comments.xml", "/word/comments.xml"}:
                return
    ids: list[int] = []
    for rel in root.xpath(".//pr:Relationship", namespaces=NS):
        match = re.fullmatch(r"rId(\d+)", rel.get("Id", ""))
        if match:
            ids.append(int(match.group(1)))
    rel = etree.SubElement(root, qn(PKG_REL_NS, "Relationship"))
    rel.set("Id", f"rId{max(ids, default=0) + 1}")
    rel.set("Type", COMMENTS_REL_TYPE)
    rel.set("Target", "comments.xml")


def _ensure_track_revisions(settings_root: etree._Element) -> None:
    if settings_root.find("w:trackRevisions", namespaces=NS) is None:
        settings_root.insert(0, etree.Element(w("trackRevisions")))


def _issue_has_replacement(issue: Mapping[str, Any]) -> bool:
    value = issue.get("suggested_fix")
    if value is None:
        return False
    if isinstance(value, str):
        return True
    if isinstance(value, Mapping):
        return any(
            key in value and isinstance(value[key], str)
            for key in ("new", "replacement", "replace_with", "new_text", "text", "value")
        )
    return False


def _replacement_text(issue: Mapping[str, Any]) -> str:
    value = issue.get("suggested_fix")
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        for key in ("new", "replacement", "replace_with", "new_text", "text", "value"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                return candidate
    raise ReviewError(
        f"{issue['issue_id']}: tracked change requires suggested_fix as text or "
        "an object with canonical old/new or a replacement alias"
    )


def _should_comment(issue: Mapping[str, Any], profile: str, has_replacement: bool) -> bool:
    action = issue.get("word_action", "none")
    if action == "none":
        return False
    if profile == "comments":
        return True
    if action == "comment":
        return True
    if action == "tracked_change_with_comment":
        return True
    if action == "tracked_change" and not has_replacement:
        return True
    return False


def _should_track(issue: Mapping[str, Any], profile: str, has_replacement: bool) -> bool:
    if profile == "comments":
        return False
    return issue.get("word_action") in {
        "tracked_change",
        "tracked_change_with_comment",
    } and has_replacement


def _write_derived_docx(
    source: Path,
    output: Path,
    *,
    journal: Sequence[Mapping[str, Any]],
    profile: str,
    author: str,
) -> dict[str, Any]:
    if profile not in PROFILES:
        raise ReviewError(f"profile must be one of {sorted(PROFILES)}")
    source_resolved = source.resolve()
    output_resolved = output.resolve()
    if source_resolved == output_resolved:
        raise ReviewError("output must be a separate reviewed copy, not the source DOCX")
    if not source.is_file():
        raise ReviewError(f"source DOCX does not exist: {source}")

    with zipfile.ZipFile(source, "r") as zin:
        names = set(zin.namelist())
        for required in ("word/document.xml", "[Content_Types].xml"):
            if required not in names:
                raise ReviewError(f"source DOCX is missing {required}")
        doc_root = etree.fromstring(zin.read("word/document.xml"))
        ct_root = etree.fromstring(zin.read("[Content_Types].xml"))
        rels_name = "word/_rels/document.xml.rels"
        rels_root = (
            etree.fromstring(zin.read(rels_name)) if rels_name in names else None
        )
        comments_name = "word/comments.xml"
        comments_root = _ensure_comments_root(
            zin.read(comments_name) if comments_name in names else None
        )
        settings_name = "word/settings.xml"
        settings_root = (
            etree.fromstring(zin.read(settings_name)) if settings_name in names else None
        )

        all_ids = _existing_xml_ids(doc_root, comments_root)
        next_id = max(all_ids, default=-1) + 1
        comment_ids = _existing_comment_ids(comments_root)
        when = utc_now()
        changed = False
        comments_added = 0
        changes_added = 0
        applied: list[dict[str, Any]] = []

        for issue in journal:
            issue_id = str(issue["issue_id"])
            action = issue.get("word_action", "none")
            if action == "none":
                continue
            has_replacement = _issue_has_replacement(issue)
            do_track = _should_track(issue, profile, has_replacement)
            do_comment = _should_comment(issue, profile, has_replacement)
            match: Match | None = None
            if do_track:
                match = _resolve_match(doc_root, issue, include_deleted=False)
                new_text = _replacement_text(issue)
                suggested_fix = issue.get("suggested_fix")
                if isinstance(suggested_fix, Mapping) and "old" in suggested_fix:
                    old_text = suggested_fix.get("old")
                    if old_text != match.text:
                        raise ReviewError(
                            f"{issue_id}: suggested_fix.old must equal the exact "
                            "located text"
                        )
                next_id, deleted, inserted = _replace_match(
                    match,
                    new_text,
                    issue_id=issue_id,
                    change_id=next_id,
                    author=author,
                    when=when,
                )
                changes_added += 1
                changed = True
                if do_comment:
                    comment_id = next_id
                    next_id += 1
                    comment_ids.add(comment_id)
                    _anchor_change(deleted, inserted, comment_id=comment_id)
                    _append_comment(
                        comments_root,
                        comment_id,
                        _comment_text(issue),
                        author=author,
                        when=when,
                    )
                    comments_added += 1
                    changed = True
            elif do_comment:
                match = _resolve_match(doc_root, issue, include_deleted=False)
                comment_id = next_id
                next_id += 1
                comment_ids.add(comment_id)
                _anchor_match(
                    match,
                    comment_id=comment_id,
                    issue_id=issue_id,
                )
                _append_comment(
                    comments_root,
                    comment_id,
                    _comment_text(issue),
                    author=author,
                    when=when,
                )
                comments_added += 1
                changed = True
            applied.append(
                {
                    "issue_id": issue_id,
                    "comment": bool(do_comment),
                    "tracked_change": bool(do_track),
                }
            )

        if changes_added:
            if settings_root is None:
                settings_root = etree.Element(w("settings"), nsmap={"w": W_NS})
            _ensure_track_revisions(settings_root)

        overrides: dict[str, bytes] = {}
        if changed:
            overrides["word/document.xml"] = xml_bytes(doc_root)
        if comments_added:
            if rels_root is None:
                rels_root = etree.Element(qn(PKG_REL_NS, "Relationships"), nsmap={"pr": PKG_REL_NS})
            _ensure_comments_relationship(rels_root)
            _ensure_content_types(ct_root)
            overrides["word/comments.xml"] = xml_bytes(comments_root)
            overrides["word/_rels/document.xml.rels"] = xml_bytes(rels_root)
            overrides["[Content_Types].xml"] = xml_bytes(ct_root)
        if changes_added:
            if rels_root is None:
                rels_root = etree.Element(
                    qn(PKG_REL_NS, "Relationships"), nsmap={"pr": PKG_REL_NS}
                )
            _ensure_settings_relationship(rels_root)
            _ensure_settings_content_type(ct_root)
            overrides[settings_name] = xml_bytes(settings_root)  # type: ignore[arg-type]
            overrides["word/_rels/document.xml.rels"] = xml_bytes(rels_root)
            overrides["[Content_Types].xml"] = xml_bytes(ct_root)

        output.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(
            prefix=f".{output.name}.", suffix=".tmp", dir=str(output.parent)
        )
        os.close(fd)
        temporary = Path(temporary_name)
        try:
            with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as zout:
                for info in zin.infolist():
                    name = info.filename
                    if name in overrides:
                        zout.writestr(info, overrides[name])
                    else:
                        zout.writestr(info, zin.read(name))
                if comments_added and comments_name not in names:
                    zout.writestr(comments_name, overrides[comments_name])
                if settings_root is not None and settings_name not in names and changes_added:
                    zout.writestr(settings_name, overrides[settings_name])
            os.replace(temporary, output)
        except Exception:
            try:
                temporary.unlink()
            except OSError:
                pass
            raise

    return {
        "output": str(output),
        "profile": profile,
        "issues": applied,
        "comments_added": comments_added,
        "tracked_changes_added": changes_added,
    }


def apply_review(
    source_docx: str | os.PathLike[str],
    journal: str | os.PathLike[str] | Sequence[Mapping[str, Any]],
    output_docx: str | os.PathLike[str],
    *,
    profile: str = "hybrid",
    author: str = "Dissertation critic",
) -> dict[str, Any]:
    """Create a reviewed copy and return a compact application report."""

    if isinstance(journal, (str, os.PathLike)):
        issues = load_journal(journal)
    else:
        issues = []
        for index, issue in enumerate(journal, start=1):
            if not isinstance(issue, Mapping):
                raise ReviewError(f"issue {index} must be an object")
            issues.append(dict(issue))
    # Validate sequence input through the same checks used by JSON files.
    if not isinstance(journal, (str, os.PathLike)):
        normalized = []
        seen: set[str] = set()
        for index, issue in enumerate(issues, start=1):
            item = dict(issue)
            issue_id = item.get("issue_id")
            if not isinstance(issue_id, str) or not issue_id.strip() or issue_id in seen:
                raise ReviewError(f"invalid or duplicate issue_id at issue {index}")
            seen.add(issue_id)
            action = item.get("word_action")
            if action not in WORD_ACTIONS:
                raise ReviewError(
                    f"{issue_id}: word_action must be explicitly set to one of {sorted(WORD_ACTIONS)}"
                )
            normalized.append(item)
        issues = normalized
    validation_report = _VALIDATOR.validate_findings({"findings": issues})
    if not validation_report["valid"]:
        details = "; ".join(
            f"{error['code']} at {error['path']}: {error['detail']}"
            for error in validation_report["errors"]
        )
        raise ReviewError(f"PSES journal validation failed: {details}")

    return _write_derived_docx(
        Path(source_docx),
        Path(output_docx),
        journal=issues,
        profile=profile,
        author=author,
    )


def _comment_anchor_ids(doc_root: etree._Element) -> tuple[set[str], set[str], set[str]]:
    starts = {
        element.get(w("id"), "")
        for element in doc_root.xpath(".//w:commentRangeStart", namespaces=NS)
    }
    ends = {
        element.get(w("id"), "")
        for element in doc_root.xpath(".//w:commentRangeEnd", namespaces=NS)
    }
    refs = {
        element.get(w("id"), "")
        for element in doc_root.xpath(".//w:commentReference", namespaces=NS)
    }
    return starts, ends, refs


def _issue_markers(doc_root: etree._Element, comments_root: etree._Element | None) -> set[str]:
    result: set[str] = set()
    for element in doc_root.xpath(".//*[@review:issue_id]", namespaces=NS):
        value = element.get(qn(REVIEW_NS, "issue_id"))
        if value:
            result.add(value)
    if comments_root is not None:
        for text in comments_root.xpath(".//w:comment//w:t/text()", namespaces=NS):
            match = re.match(r"\[([^\]]+)\]", text)
            if match:
                result.add(match.group(1))
    return result


def audit_document(
    docx_path: str | os.PathLike[str],
    journal: str | os.PathLike[str] | Sequence[Mapping[str, Any]] | None = None,
    *,
    source_docx: str | os.PathLike[str] | None = None,
    profile: str | None = None,
) -> dict[str, Any]:
    """Audit the OOXML review plumbing without changing the DOCX."""

    issues = []
    if journal is not None:
        if isinstance(journal, (str, os.PathLike)):
            issues = load_journal(journal)
        else:
            for index, issue in enumerate(journal, start=1):
                if not isinstance(issue, Mapping):
                    raise ReviewError(f"issue {index} must be an object")
                issues.append(dict(issue))
    errors: list[str] = []
    with zipfile.ZipFile(docx_path, "r") as zin:
        names = set(zin.namelist())
        if "word/document.xml" not in names:
            errors.append("missing word/document.xml")
            return {"valid": False, "errors": errors}
        doc_root = etree.fromstring(zin.read("word/document.xml"))
        comments_root = (
            etree.fromstring(zin.read("word/comments.xml"))
            if "word/comments.xml" in names
            else None
        )
        ct_root = (
            etree.fromstring(zin.read("[Content_Types].xml"))
            if "[Content_Types].xml" in names
            else None
        )
        rels_root = (
            etree.fromstring(zin.read("word/_rels/document.xml.rels"))
            if "word/_rels/document.xml.rels" in names
            else None
        )
        settings_root = (
            etree.fromstring(zin.read("word/settings.xml"))
            if "word/settings.xml" in names
            else None
        )

        starts, ends, refs = _comment_anchor_ids(doc_root)
        start_values = [
            element.get(w("id"), "")
            for element in doc_root.xpath(".//w:commentRangeStart", namespaces=NS)
        ]
        end_values = [
            element.get(w("id"), "")
            for element in doc_root.xpath(".//w:commentRangeEnd", namespaces=NS)
        ]
        ref_values = [
            element.get(w("id"), "")
            for element in doc_root.xpath(".//w:commentReference", namespaces=NS)
        ]
        if (
            len(start_values) != len(starts)
            or len(end_values) != len(ends)
            or len(ref_values) != len(refs)
            or "" in starts
            or "" in ends
            or "" in refs
        ):
            errors.append("comment anchors have duplicate or missing ids")
        comment_elements = (
            comments_root.xpath(".//w:comment", namespaces=NS)
            if comments_root is not None
            else []
        )
        comment_ids = {element.get(w("id"), "") for element in comment_elements}
        if len(comment_ids) != len(comment_elements):
            errors.append("duplicate or missing comment ids")
        if starts != ends or starts != refs:
            errors.append("comment range starts, ends, and references are not balanced")
        if starts != comment_ids:
            errors.append("comment ids do not match document anchors")

        if comments_root is not None:
            if ct_root is None or not ct_root.xpath(
                ".//ct:Override[@PartName='/word/comments.xml' and @ContentType=$type]",
                namespaces=NS,
                type=COMMENTS_CONTENT_TYPE,
            ):
                errors.append("comments.xml lacks its content-type override")
            if rels_root is None or not rels_root.xpath(
                ".//pr:Relationship[@Type=$type and (@Target='comments.xml' or @Target='/word/comments.xml')]",
                namespaces=NS,
                type=COMMENTS_REL_TYPE,
            ):
                errors.append("comments.xml lacks its document relationship")
        elif starts or ends or refs:
            errors.append("document has comment anchors but comments.xml is missing")

        changes = doc_root.xpath(".//w:ins | .//w:del", namespaces=NS)
        change_ids = [element.get(w("id")) for element in changes]
        if any(value is None for value in change_ids):
            errors.append("tracked change lacks w:id")
        if len([value for value in change_ids if value is not None]) != len(
            {value for value in change_ids if value is not None}
        ):
            errors.append("tracked change ids are not unique")
        if {value for value in change_ids if value is not None} & comment_ids:
            errors.append("tracked change and comment ids must be globally unique")
        for element in changes:
            if not element.get(w("author")):
                errors.append("tracked change lacks w:author")
            if not element.get(w("date")):
                errors.append("tracked change lacks w:date")
            if element.tag == w("del") and not element.xpath(
                ".//w:delText", namespaces=NS
            ):
                errors.append("w:del does not contain w:delText")
            if element.tag == w("ins") and not element.xpath(
                ".//w:t", namespaces=NS
            ):
                errors.append("w:ins does not contain w:t")
        if changes and (settings_root is None or settings_root.find("w:trackRevisions", namespaces=NS) is None):
            errors.append("tracked changes exist but w:trackRevisions is not enabled")

        found_issue_ids = _issue_markers(doc_root, comments_root)
        expected_issue_ids = {
            str(issue["issue_id"])
            for issue in issues
            if issue.get("word_action", "none") != "none"
        }
        if profile not in {None, *PROFILES}:
            errors.append(f"unknown audit profile: {profile}")
        marked_change_issue_ids = {
            element.get(qn(REVIEW_NS, "issue_id"))
            for element in changes
            if element.get(qn(REVIEW_NS, "issue_id"))
        }
        expected_change_issue_ids = {
            str(issue["issue_id"])
            for issue in issues
            if issue.get("word_action")
            in {"tracked_change", "tracked_change_with_comment"}
            and _issue_has_replacement(issue)
        }
        # A comments-only rendering intentionally has no w:ins/w:del.  For
        # profiles that may contain redlines, every expected changed finding
        # must be marked on at least one generated change element.
        if profile != "comments" and changes and expected_change_issue_ids:
            missing_change_markers = sorted(
                expected_change_issue_ids - marked_change_issue_ids
            )
            if missing_change_markers:
                errors.append(
                    "tracked changes missing issue_id markers: "
                    f"{missing_change_markers}"
                )
        missing = sorted(expected_issue_ids - found_issue_ids)
        if missing:
            errors.append(f"journal issue_id not represented in Word: {missing}")
        if source_docx is not None:
            with zipfile.ZipFile(source_docx, "r") as source_zip:
                source_doc = etree.fromstring(source_zip.read("word/document.xml"))
                source_comments = (
                    etree.fromstring(source_zip.read("word/comments.xml"))
                    if "word/comments.xml" in source_zip.namelist()
                    else None
                )
                source_change_ids = {
                    element.get(w("id"))
                    for element in source_doc.xpath(".//w:ins | .//w:del", namespaces=NS)
                }
                current_change_ids = {
                    value for value in change_ids if value is not None
                }
                if not source_change_ids <= current_change_ids:
                    errors.append("reviewed copy removed existing tracked changes")
                source_comment_ids = (
                    {
                        element.get(w("id"))
                        for element in source_comments.xpath(".//w:comment", namespaces=NS)
                    }
                    if source_comments is not None
                    else set()
                )
                if not source_comment_ids <= comment_ids:
                    errors.append("reviewed copy removed existing comments")

    return {
        "valid": not errors,
        "errors": errors,
        "comments": len(comment_ids),
        "comment_anchors": len(starts),
        "tracked_changes": len(changes),
        "issue_ids": sorted(found_issue_ids),
    }


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_docx", help="source DOCX, or reviewed DOCX with --audit")
    parser.add_argument(
        "journal_positional",
        nargs="?",
        help="JSON journal (normal mode or audit mode)",
    )
    parser.add_argument("--journal", dest="journal_option", help="JSON journal")
    parser.add_argument(
        "--out",
        "--output",
        dest="out",
        help="separate reviewed DOCX output path",
    )
    parser.add_argument("--profile", choices=sorted(PROFILES), default="hybrid")
    parser.add_argument("--author", default="Dissertation critic")
    parser.add_argument(
        "--audit",
        action="store_true",
        help="audit comments, anchors, relationships, content types, redlines, and issue_id markers",
    )
    parser.add_argument(
        "--source",
        help="original DOCX for an optional preservation check in --audit mode",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    journal_path = args.journal_option or args.journal_positional
    try:
        if args.audit:
            report = audit_document(
                args.input_docx,
                journal_path,
                source_docx=args.source,
                profile=args.profile,
            )
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0 if report["valid"] else 1
        if not journal_path:
            raise ReviewError("normal mode requires a JSON journal")
        if not args.out:
            raise ReviewError("normal mode requires --out reviewed.docx")
        report = apply_review(
            args.input_docx,
            journal_path,
            args.out,
            profile=args.profile,
            author=args.author,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (ReviewError, OSError, zipfile.BadZipFile, etree.XMLSyntaxError) as exc:
        print(f"apply_word_review: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover - exercised through CLI smoke tests
    raise SystemExit(main())
