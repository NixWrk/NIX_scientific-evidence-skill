"""Audit citation/list reconciliation without inventing an unspecified order."""

from __future__ import annotations

import argparse
import re
from collections import Counter
from pathlib import Path

from critic_common import finding, load_json, write_envelope


def _key(record: dict) -> tuple[str, str]:
    return (str(record.get("title", "")).strip().casefold(), str(record.get("year", "")).strip())


def audit(ledger: dict) -> list[dict]:
    findings: list[dict] = []
    profile = ledger.get("profile", {})
    records = ledger.get("records", [])
    citations = ledger.get("in_text_citations", [])
    record_ids = [record.get("record_id") for record in records if record.get("record_id")]
    by_id = {record.get("record_id"): record for record in records if record.get("record_id")}
    for index, record in enumerate(records):
        missing = [field for field in ("record_id", "type", "title") if not str(record.get(field, "")).strip()]
        if missing:
            findings.append(
                finding(
                    f"BIB-MALFORMED-{len(findings)+1:03d}", "BIB-007", "bibliography",
                    {"index": index, "record_id": record.get("record_id"), "missing": missing},
                    "ledger record has record_id, type, and title", word_action="none",
                    severity="major", issue_class="internal_inconsistency",
                    suggested_fix="Дополнить структурные поля записи до нормативной проверки.",
                )
            )
    for record_id, count in Counter(record_ids).items():
        if count > 1:
            findings.append(
                finding(
                    f"BIB-DUPLICATE-ID-{len(findings)+1:03d}", "BIB-008", "bibliography",
                    {"record_id": record_id, "count": count}, "record_id is unique",
                    word_action="none", severity="critical", issue_class="internal_inconsistency",
                    suggested_fix="Назначить уникальные record_id до сверки ссылок.",
                )
            )
    cited_order: list[str] = []
    for citation in sorted(citations, key=lambda item: item.get("order", 0)):
        record_id = citation.get("record_id")
        if record_id not in by_id:
            findings.append(
                finding(
                    f"BIB-UNRESOLVED-{len(findings)+1:03d}", "BIB-001", "bibliography",
                    record_id, "every in-text citation resolves to one bibliography record",
                    exact_text=str(citation.get("display") or record_id), occurrence=int(citation.get("occurrence", 1)),
                    severity="critical", issue_class="internal_inconsistency",
                    authority_ids=list(profile.get("citation_authority_ids", [])),
                    suggested_fix="Связать ссылку с существующей записью или добавить проверенное описание.",
                )
            )
        else:
            display = str(citation.get("display", "")).strip()
            numeric_display = re.fullmatch(r"\[(\d+)\]", display)
            record_number = by_id[record_id].get("number")
            if numeric_display and record_number is not None and int(numeric_display.group(1)) != record_number:
                findings.append(
                    finding(
                        f"BIB-DISPLAY-{len(findings)+1:03d}", "BIB-009", "bibliography",
                        display, f"[{record_number}]", exact_text=display,
                        occurrence=int(citation.get("occurrence", 1)), severity="critical",
                        issue_class="internal_inconsistency",
                        suggested_fix="Синхронизировать отображаемый номер со связанной записью.",
                    )
                )
            if record_id not in cited_order:
                cited_order.append(record_id)

    if profile.get("uncited_record_policy", "report") == "report":
        for record_id in sorted(set(by_id) - set(cited_order)):
            findings.append(
                finding(
                    f"BIB-UNCITED-{len(findings)+1:03d}", "BIB-002", "bibliography",
                    record_id, "record is cited or explicitly retained by policy", word_action="none",
                    severity="note", issue_class="recommendation",
                    suggested_fix="Проверить необходимость записи; не удалять автоматически.",
                )
            )

    doi_counts = Counter(str(record.get("doi", "")).strip().casefold() for record in records if record.get("doi"))
    key_counts = Counter(_key(record) for record in records if any(_key(record)))
    for record in records:
        duplicate = (record.get("doi") and doi_counts[str(record["doi"]).strip().casefold()] > 1) or key_counts[_key(record)] > 1
        if duplicate:
            findings.append(
                finding(
                    f"BIB-DUPLICATE-{len(findings)+1:03d}", "BIB-003", "bibliography",
                    record.get("record_id"), "one record per work", word_action="none",
                    severity="major", suggested_fix="Сверить DOI, заглавие и год; объединить только после ручной проверки.",
                )
            )

    supported = set(profile.get("supported_record_types", []))
    for record in records:
        if supported and record.get("type") not in supported:
            findings.append(
                finding(
                    f"BIB-NOT-ASSESSED-{len(findings)+1:03d}", "BIB-004", "bibliography",
                    {"record_id": record.get("record_id"), "type": record.get("type")},
                    "record type is covered by the resolved normative card", word_action="none",
                    severity="note", issue_class="evidence_gap",
                    suggested_fix="Пометить запись not_assessed и дополнить нормативное покрытие до проверки.",
                )
            )

    if profile.get("sequential_numbering") is True:
        numbers = [record.get("number") for record in records]
        if numbers != list(range(1, len(records) + 1)):
            authorities = list(profile.get("numbering_authority_ids", []))
            findings.append(
                finding(
                    f"BIB-NUMBERING-{len(findings)+1:03d}", "BIB-005", "bibliography",
                    numbers, list(range(1, len(records) + 1)), word_action="none",
                    severity="major",
                    issue_class="normative_violation" if authorities else "evidence_gap",
                    authority_ids=authorities,
                    suggested_fix="Перенумеровать только после фиксации выбранного порядка списка.",
                )
            )

    strategy = profile.get("sorting_strategy", "unspecified")
    if strategy not in {"unspecified", "citation_order", "alphabetical"}:
        findings.append(
            finding(
                f"BIB-STRATEGY-{len(findings)+1:03d}", "BIB-010", "bibliography",
                strategy, "unspecified, citation_order, or alphabetical", word_action="none",
                severity="major", issue_class="evidence_gap",
                suggested_fix="Выбрать поддерживаемую стратегию и зафиксировать применимое основание.",
            )
        )
    actual_ids = [record.get("record_id") for record in records]
    expected_ids: list[str] | None = None
    if strategy == "citation_order":
        expected_ids = cited_order + [record_id for record_id in actual_ids if record_id not in cited_order]
    elif strategy == "alphabetical":
        expected_ids = [record.get("record_id") for record in sorted(records, key=lambda item: (str(item.get("authors", "")).casefold(), str(item.get("title", "")).casefold()))]
    if expected_ids is not None and actual_ids != expected_ids:
        authorities = list(profile.get("sorting_authority_ids", []))
        findings.append(
            finding(
                f"BIB-ORDER-{len(findings)+1:03d}", "BIB-006", "bibliography",
                actual_ids, expected_ids, word_action="none", severity="major",
                issue_class="normative_violation" if authorities else "evidence_gap",
                authority_ids=authorities,
                suggested_fix=f"Привести список к явно выбранному порядку: {strategy}.",
            )
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    print(write_envelope(audit(load_json(args.ledger)), args.output), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
