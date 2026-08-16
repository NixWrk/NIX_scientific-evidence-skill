"""Run the deterministic four-stage dissertation-critic benchmark.

This runner deliberately does not call a model, a subprocess, a network, or a
Word automation API.  It reads frozen fixture/gold/output records, validates
critic journals with :mod:`validate_critic_findings`, and computes transparent
matching metrics.  A real critic is run by a separate harness; its result is
placed in the ``skill`` output directory before this script is invoked.

The experiment directory accepts the following small, intentionally boring
layout::

    manifest.yaml
    fixtures/*.json
    gold/findings.json
    outputs/baseline/<case-id>.json
    outputs/skill/<case-id>.json

Each case record has ``case_id`` and ``stage``.  Gold/output records have a
``findings`` array.  The runner also accepts a bare findings array or a single
finding when an adapter is streaming records.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_critic_findings import (  # noqa: E402  (local portable script)
    TRACKED_ACTIONS,
    validate_finding,
    validate_findings,
)


STAGES = ("regression", "mutation", "clean_control", "holdout")
STAGE_SET = set(STAGES)
SHA256_RE = re.compile(r"^(?:sha256:)?[0-9a-f]{64}$", re.IGNORECASE)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_hash(value: Any) -> str:
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def read_data(path: Path) -> Any:
    """Read JSON/YAML data without executing anything from the experiment."""

    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() in {".json", ".jsonl"}:
        if path.suffix.lower() == ".jsonl":
            records: list[Any] = []
            for line_number, line in enumerate(text.splitlines(), start=1):
                if not line.strip():
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(f"{path}:{line_number}: {error}") from error
            return records
        return json.loads(text)
    try:
        import yaml  # type: ignore
    except ImportError as error:  # pragma: no cover - pyproject dev dependency supplies it
        raise RuntimeError("YAML manifest requires PyYAML; JSON manifests need no dependency") from error
    loaded = yaml.safe_load(text)
    return {} if loaded is None else loaded


def _as_records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [record for record in payload if isinstance(record, dict)]
    if isinstance(payload, dict):
        if isinstance(payload.get("cases"), list):
            return [record for record in payload["cases"] if isinstance(record, dict)]
        if isinstance(payload.get("case_id"), str):
            return [payload]
        # A convenient mapping form: {"CASE-001": {"stage": ..., ...}}.
        mapped: list[dict[str, Any]] = []
        for case_id, record in payload.items():
            if isinstance(record, dict):
                mapped.append({"case_id": case_id, **record})
        return mapped
    return []


def _findings_from_record(payload: Any) -> list[Any]:
    if isinstance(payload, dict) and "findings" in payload:
        return payload["findings"] if isinstance(payload["findings"], list) else []
    if isinstance(payload, list):
        # A list of finding objects is the bare journal form.  A list of case
        # records is handled by the caller before reaching this helper.
        return payload
    if isinstance(payload, dict) and "issue_id" in payload:
        return [payload]
    return []


def _manifest_value(manifest: Mapping[str, Any], *paths: tuple[str, ...], default: Any = None) -> Any:
    for path in paths:
        value: Any = manifest
        found = True
        for key in path:
            if not isinstance(value, Mapping) or key not in value:
                found = False
                break
            value = value[key]
        if found:
            return value
    return default


def _normalise_stages(manifest: Mapping[str, Any]) -> tuple[list[str], list[dict[str, str]]]:
    raw = manifest.get("stages", list(STAGES))
    stages: list[str] = []
    errors: list[dict[str, str]] = []
    if not isinstance(raw, list):
        return [], [{"code": "MANIFEST_STAGES", "detail": "stages must be an array"}]
    for item in raw:
        stage = item.get("id") if isinstance(item, Mapping) else item
        if not isinstance(stage, str) or stage not in STAGE_SET:
            errors.append({"code": "MANIFEST_STAGE", "detail": f"unknown stage {stage!r}"})
        elif stage not in stages:
            stages.append(stage)
    missing = sorted(STAGE_SET - set(stages))
    if missing:
        errors.append(
            {
                "code": "MANIFEST_STAGE_SET",
                "detail": f"manifest must declare all four stages; missing {missing}",
            }
        )
    return stages, errors


def _normalise_hashes(manifest: Mapping[str, Any]) -> dict[str, str]:
    raw = manifest.get("frozen_hashes", {})
    if isinstance(raw, Mapping) and isinstance(raw.get("files"), Mapping):
        raw = raw["files"]
    if isinstance(raw, list):
        result: dict[str, str] = {}
        for item in raw:
            if isinstance(item, Mapping) and isinstance(item.get("path"), str) and isinstance(item.get("sha256"), str):
                result[item["path"]] = item["sha256"]
        return result
    if not isinstance(raw, Mapping):
        return {}
    return {str(path): str(digest) for path, digest in raw.items()}


def _safe_experiment_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    root_resolved = root.resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ValueError(f"path escapes experiment directory: {relative!r}")
    return candidate


def verify_frozen_hashes(root: Path, manifest: Mapping[str, Any]) -> dict[str, Any]:
    expected = _normalise_hashes(manifest)
    checked: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, str]] = []
    for relative, recorded in sorted(expected.items()):
        try:
            path = _safe_experiment_path(root, relative)
        except ValueError as error:
            errors.append({"code": "FROZEN_HASH_PATH", "path": relative, "detail": str(error)})
            continue
        if not path.is_file():
            errors.append(
                {
                    "code": "FROZEN_HASH_MISSING",
                    "path": relative,
                    "detail": "frozen file does not exist",
                }
            )
            continue
        actual = sha256_file(path)
        expected_digest = recorded.lower().removeprefix("sha256:")
        valid_format = bool(SHA256_RE.fullmatch(recorded))
        checked[relative] = {
            "sha256": actual,
            "recorded": recorded,
            "match": valid_format and actual == expected_digest,
        }
        if not valid_format or actual != expected_digest:
            errors.append(
                {
                    "code": "FROZEN_HASH_MISMATCH",
                    "path": relative,
                    "detail": f"recorded {recorded!r}, actual sha256:{actual}",
                }
            )
    return {
        "required": bool(manifest.get("frozen_hashes")),
        "frozen": bool(expected) and not errors,
        "expected_files": len(expected),
        "checked": checked,
        "errors": errors,
    }


def load_cases(root: Path, manifest: Mapping[str, Any]) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    fixtures_dir = _manifest_value(
        manifest,
        ("fixtures_dir",),
        ("inputs", "fixtures_dir"),
        default="fixtures",
    )
    fixture_root = _safe_experiment_path(root, str(fixtures_dir))
    errors: list[dict[str, str]] = []
    cases: dict[str, dict[str, Any]] = {}
    if not fixture_root.is_dir():
        return {}, [{"code": "FIXTURES_MISSING", "detail": str(fixture_root)}]
    paths = sorted(path for path in fixture_root.iterdir() if path.suffix.lower() in {".json", ".jsonl"})
    for path in paths:
        try:
            records = _as_records(read_data(path))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            errors.append({"code": "FIXTURE_READ", "path": str(path), "detail": str(error)})
            continue
        for index, record in enumerate(records):
            case_id = record.get("case_id")
            stage = record.get("stage")
            case_path = f"{path.name}[{index}]"
            if not isinstance(case_id, str) or not case_id.strip():
                errors.append({"code": "CASE_ID", "path": case_path, "detail": "missing case_id"})
                continue
            if stage not in STAGE_SET:
                errors.append({"code": "CASE_STAGE", "path": case_path, "detail": f"unknown stage {stage!r}"})
                continue
            if case_id in cases:
                errors.append({"code": "DUPLICATE_CASE_ID", "path": case_path, "detail": case_id})
                continue
            declared_hash = record.get("input_sha256")
            actual_hash = sha256_file(path)
            if declared_hash is not None and str(declared_hash).lower().removeprefix("sha256:") != actual_hash:
                errors.append(
                    {
                        "code": "INPUT_HASH_MISMATCH",
                        "path": case_path,
                        "detail": f"recorded {declared_hash!r}, actual sha256:{actual_hash}",
                    }
                )
            cases[case_id] = {
                "case_id": case_id,
                "stage": stage,
                "fixture_path": str(path.relative_to(root)),
                "input_sha256": actual_hash,
                "record": record,
            }
    return cases, errors


def load_gold(root: Path, manifest: Mapping[str, Any], cases: Mapping[str, Any]) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, str]]]:
    gold_path_value = _manifest_value(
        manifest,
        ("gold",),
        ("inputs", "gold"),
        ("gold_path",),
        default="gold/findings.json",
    )
    if isinstance(gold_path_value, Mapping):
        gold_path_value = gold_path_value.get("path", "gold/findings.json")
    path = _safe_experiment_path(root, str(gold_path_value))
    errors: list[dict[str, str]] = []
    if not path.is_file():
        return {}, [{"code": "GOLD_MISSING", "path": str(path), "detail": "gold file does not exist"}]
    try:
        payload = read_data(path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return {}, [{"code": "GOLD_READ", "path": str(path), "detail": str(error)}]
    records = _as_records(payload)
    gold: dict[str, list[dict[str, Any]]] = {}
    for index, record in enumerate(records):
        case_id = record.get("case_id")
        if not isinstance(case_id, str) or case_id not in cases:
            errors.append(
                {
                    "code": "GOLD_CASE",
                    "path": f"{path.name}[{index}]",
                    "detail": f"unknown or missing case_id {case_id!r}",
                }
            )
            continue
        findings = _findings_from_record(record)
        validation = validate_findings({"findings": findings})
        if not validation["valid"]:
            errors.append(
                {
                    "code": "GOLD_SCHEMA_INVALID",
                    "path": f"{path.name}[{index}]",
                    "detail": json.dumps(validation["errors"], ensure_ascii=False),
                }
            )
        if case_id in gold:
            errors.append({"code": "GOLD_DUPLICATE_CASE", "path": path.name, "detail": case_id})
        gold[case_id] = [finding for finding in findings if isinstance(finding, dict)]
    for case_id in cases:
        if case_id not in gold:
            errors.append({"code": "GOLD_MISSING_CASE", "path": path.name, "detail": case_id})
            gold[case_id] = []
    return gold, errors


def _output_dirs(manifest: Mapping[str, Any]) -> dict[str, str]:
    configured = _manifest_value(manifest, ("outputs",), default={})
    if not isinstance(configured, Mapping):
        configured = {}
    return {
        "baseline": str(configured.get("baseline", "outputs/baseline")),
        "skill": str(configured.get("skill", "outputs/skill")),
    }


def load_outputs(
    root: Path,
    directory: str,
    profile: str,
    cases: Mapping[str, Any],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, str]], dict[str, dict[str, Any]]]:
    output_root = _safe_experiment_path(root, directory)
    errors: list[dict[str, str]] = []
    outputs: dict[str, list[dict[str, Any]]] = {}
    provenance: dict[str, dict[str, Any]] = {}
    if not output_root.is_dir():
        return {}, [{"code": "OUTPUT_DIR_MISSING", "profile": profile, "detail": str(output_root)}], {}
    paths = sorted(path for path in output_root.iterdir() if path.suffix.lower() in {".json", ".jsonl"})
    for path in paths:
        try:
            payload = read_data(path)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            errors.append({"code": "OUTPUT_READ", "profile": profile, "path": path.name, "detail": str(error)})
            continue
        records = _as_records(payload) if path.suffix.lower() == ".jsonl" else [payload]
        if not records and isinstance(payload, list):
            records = [{"case_id": path.stem, "findings": payload}]
        for index, record in enumerate(records):
            case_id = record.get("case_id") if isinstance(record, Mapping) else None
            if not isinstance(case_id, str):
                case_id = path.stem if len(records) == 1 else None
            if case_id not in cases:
                errors.append(
                    {
                        "code": "UNKNOWN_OUTPUT_CASE",
                        "profile": profile,
                        "path": f"{path.name}[{index}]",
                        "detail": f"unknown or missing case_id {case_id!r}",
                    }
                )
                continue
            findings = _findings_from_record(record)
            validation = validate_findings({"findings": findings})
            if not validation["valid"]:
                errors.append(
                    {
                        "code": "OUTPUT_SCHEMA_INVALID",
                        "profile": profile,
                        "path": f"{path.name}[{index}]",
                        "detail": json.dumps(validation["errors"], ensure_ascii=False),
                    }
                )
            if case_id in outputs:
                errors.append(
                    {
                        "code": "DUPLICATE_OUTPUT_CASE",
                        "profile": profile,
                        "path": path.name,
                        "detail": case_id,
                    }
                )
            outputs[case_id] = [finding for finding in findings if isinstance(finding, dict)]
            provenance[case_id] = {
                "path": str(path.relative_to(root)),
                "sha256": sha256_file(path),
            }
    for case_id in cases:
        if case_id not in outputs:
            errors.append(
                {
                    "code": "MISSING_OUTPUT",
                    "profile": profile,
                    "detail": case_id,
                }
            )
            outputs[case_id] = []
    return outputs, errors, provenance


def _locator_key(locator: Any) -> str:
    return json.dumps(locator, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _pair_findings(
    gold: list[dict[str, Any]], predicted: list[dict[str, Any]]
) -> tuple[list[tuple[dict[str, Any], dict[str, Any]]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Pair same-rule findings, preferring exact locator matches."""

    remaining_gold = list(range(len(gold)))
    remaining_pred = list(range(len(predicted)))
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for exact_locator in (True, False):
        for pred_index in list(remaining_pred):
            pred = predicted[pred_index]
            candidate: int | None = None
            for gold_index in remaining_gold:
                expected = gold[gold_index]
                if expected.get("rule_id") != pred.get("rule_id"):
                    continue
                if exact_locator and _locator_key(expected.get("locator")) != _locator_key(pred.get("locator")):
                    continue
                candidate = gold_index
                break
            if candidate is not None:
                pairs.append((gold[candidate], pred))
                remaining_gold.remove(candidate)
                remaining_pred.remove(pred_index)
    return pairs, [gold[index] for index in remaining_gold], [predicted[index] for index in remaining_pred]


def _ratio(numerator: int, denominator: int) -> float | None:
    return None if denominator == 0 else round(numerator / denominator, 6)


def _new_rule_metrics() -> dict[str, Any]:
    return {
        "tp": 0,
        "fp": 0,
        "fn": 0,
        "TP": 0,
        "FP": 0,
        "FN": 0,
        "locator": {"evaluated": 0, "exact": 0, "accuracy": None},
        "authority": {"applicable": 0, "resolved": 0, "exact": 0, "resolution_rate": None, "accuracy": None},
        "classification": {"evaluated": 0, "exact": 0, "class_exact": 0, "severity_exact": 0, "accuracy": None},
    }


def _finalise_rule_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    metrics["TP"] = metrics["tp"]
    metrics["FP"] = metrics["fp"]
    metrics["FN"] = metrics["fn"]
    metrics["precision"] = _ratio(metrics["tp"], metrics["tp"] + metrics["fp"])
    metrics["recall"] = _ratio(metrics["tp"], metrics["tp"] + metrics["fn"])
    if metrics["precision"] is not None and metrics["recall"] is not None and metrics["precision"] + metrics["recall"]:
        metrics["f1"] = round(2 * metrics["precision"] * metrics["recall"] / (metrics["precision"] + metrics["recall"]), 6)
    else:
        metrics["f1"] = None
    locator = metrics["locator"]
    locator["accuracy"] = _ratio(locator["exact"], locator["evaluated"])
    authority = metrics["authority"]
    authority["resolution_rate"] = _ratio(authority["resolved"], authority["applicable"])
    authority["accuracy"] = _ratio(authority["exact"], authority["applicable"])
    classification = metrics["classification"]
    classification["accuracy"] = _ratio(classification["exact"], classification["evaluated"])
    return metrics


def evaluate_cases(
    case_ids: Iterable[str],
    gold_by_case: Mapping[str, list[dict[str, Any]]],
    predicted_by_case: Mapping[str, list[dict[str, Any]]],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    per_rule: dict[str, dict[str, Any]] = defaultdict(_new_rule_metrics)
    totals = {"tp": 0, "fp": 0, "fn": 0}
    all_pairs: list[dict[str, Any]] = []
    for case_id in case_ids:
        gold = gold_by_case.get(case_id, [])
        predicted = predicted_by_case.get(case_id, [])
        pairs, unmatched_gold, unmatched_predicted = _pair_findings(gold, predicted)
        for expected, actual in pairs:
            rule_id = str(expected.get("rule_id", actual.get("rule_id", "<missing>")))
            record = per_rule[rule_id]
            record["tp"] += 1
            totals["tp"] += 1
            record["locator"]["evaluated"] += 1
            locator_exact = _locator_key(expected.get("locator")) == _locator_key(actual.get("locator"))
            record["locator"]["exact"] += int(locator_exact)
            authority_applicable = expected.get("issue_class") == "normative_violation" or actual.get("issue_class") == "normative_violation"
            if authority_applicable:
                authority = record["authority"]
                authority["applicable"] += 1
                authority["resolved"] += int(bool(actual.get("authority_ids")))
                authority["exact"] += int(set(expected.get("authority_ids", [])) == set(actual.get("authority_ids", [])))
            classification = record["classification"]
            classification["evaluated"] += 1
            class_exact = expected.get("issue_class") == actual.get("issue_class")
            severity_exact = expected.get("severity") == actual.get("severity")
            classification["class_exact"] += int(class_exact)
            classification["severity_exact"] += int(severity_exact)
            classification["exact"] += int(class_exact and severity_exact)
            all_pairs.append({"case_id": case_id, "expected": expected, "actual": actual})
        for finding in unmatched_gold:
            rule_id = str(finding.get("rule_id", "<missing>"))
            per_rule[rule_id]["fn"] += 1
            totals["fn"] += 1
        for finding in unmatched_predicted:
            rule_id = str(finding.get("rule_id", "<missing>"))
            per_rule[rule_id]["fp"] += 1
            totals["fp"] += 1

    overall: dict[str, Any] = {
        **totals,
        "TP": totals["tp"],
        "FP": totals["fp"],
        "FN": totals["fn"],
        "cases": len(list(case_ids)) if not isinstance(case_ids, list) else len(case_ids),
        "gold_findings": sum(len(gold_by_case.get(case_id, [])) for case_id in case_ids),
        "predicted_findings": sum(len(predicted_by_case.get(case_id, [])) for case_id in case_ids),
        "per_rule": {rule_id: _finalise_rule_metrics(metrics) for rule_id, metrics in sorted(per_rule.items())},
    }
    overall["precision"] = _ratio(overall["tp"], overall["tp"] + overall["fp"])
    overall["recall"] = _ratio(overall["tp"], overall["tp"] + overall["fn"])
    if overall["precision"] is not None and overall["recall"] is not None and overall["precision"] + overall["recall"]:
        overall["f1"] = round(2 * overall["precision"] * overall["recall"] / (overall["precision"] + overall["recall"]), 6)
    else:
        overall["f1"] = None

    # Aggregate the secondary metrics over matched finding pairs.
    locator_exact = sum(int(_locator_key(item["expected"].get("locator")) == _locator_key(item["actual"].get("locator"))) for item in all_pairs)
    authority_pairs = [item for item in all_pairs if item["expected"].get("issue_class") == "normative_violation" or item["actual"].get("issue_class") == "normative_violation"]
    class_exact = sum(int(item["expected"].get("issue_class") == item["actual"].get("issue_class") and item["expected"].get("severity") == item["actual"].get("severity")) for item in all_pairs)
    overall["locator"] = {"evaluated": len(all_pairs), "exact": locator_exact, "accuracy": _ratio(locator_exact, len(all_pairs))}
    overall["authority"] = {
        "applicable": len(authority_pairs),
        "resolved": sum(int(bool(item["actual"].get("authority_ids"))) for item in authority_pairs),
        "exact": sum(int(set(item["expected"].get("authority_ids", [])) == set(item["actual"].get("authority_ids", []))) for item in authority_pairs),
        "resolution_rate": _ratio(sum(int(bool(item["actual"].get("authority_ids"))) for item in authority_pairs), len(authority_pairs)),
        "accuracy": _ratio(sum(int(set(item["expected"].get("authority_ids", [])) == set(item["actual"].get("authority_ids", []))) for item in authority_pairs), len(authority_pairs)),
    }
    overall["classification"] = {
        "evaluated": len(all_pairs),
        "exact": class_exact,
        "class_exact": sum(int(item["expected"].get("issue_class") == item["actual"].get("issue_class")) for item in all_pairs),
        "severity_exact": sum(int(item["expected"].get("severity") == item["actual"].get("severity")) for item in all_pairs),
        "accuracy": _ratio(class_exact, len(all_pairs)),
    }
    return overall, all_pairs


def _finding_stop_errors(profile: str, case_id: str, finding: Mapping[str, Any]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    issue_id = str(finding.get("issue_id", "<missing>"))
    if finding.get("issue_class") == "normative_violation" and not finding.get("authority_ids"):
        errors.append(
            {
                "code": "NORMATIVE_WITHOUT_AUTHORITY",
                "profile": profile,
                "case_id": case_id,
                "issue_id": issue_id,
                "detail": "normative_violation has no authority_ids",
            }
        )
    if finding.get("word_action") in TRACKED_ACTIONS:
        fix = finding.get("suggested_fix")
        if not isinstance(fix, Mapping) or not isinstance(fix.get("old"), str) or not fix.get("old", "").strip() or not isinstance(fix.get("new"), str) or not fix.get("new", "").strip():
            errors.append(
                {
                    "code": "TRACKED_CHANGE_WITHOUT_EXACT_OLD_NEW",
                    "profile": profile,
                    "case_id": case_id,
                    "issue_id": issue_id,
                    "detail": "tracked change has no exact old/new suggestion",
                }
            )
    return errors


def _unmatched_normative_errors(
    profile: str,
    pairs_by_case: Mapping[str, tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]],
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    for case_id, (_pairs, _unmatched_gold, unmatched_predicted) in pairs_by_case.items():
        for finding in unmatched_predicted:
            if finding.get("issue_class") == "normative_violation":
                errors.append(
                    {
                        "code": "FALSE_NORMATIVE_ASSERTION",
                        "profile": profile,
                        "case_id": case_id,
                        "issue_id": str(finding.get("issue_id", "<missing>")),
                        "detail": "unmatched normative violation on the benchmark gold",
                    }
                )
    return errors


def _matching_details(
    case_ids: Iterable[str],
    gold_by_case: Mapping[str, list[dict[str, Any]]],
    predicted_by_case: Mapping[str, list[dict[str, Any]]],
) -> dict[str, tuple[list[tuple[dict[str, Any], dict[str, Any]]], list[dict[str, Any]], list[dict[str, Any]]]]:
    details: dict[str, tuple[list[tuple[dict[str, Any], dict[str, Any]]], list[dict[str, Any]], list[dict[str, Any]]]] = {}
    for case_id in case_ids:
        details[case_id] = _pair_findings(gold_by_case.get(case_id, []), predicted_by_case.get(case_id, []))
    return details


def _profile_metrics(
    profile: str,
    cases: Mapping[str, dict[str, Any]],
    gold_by_case: Mapping[str, list[dict[str, Any]]],
    predicted_by_case: Mapping[str, list[dict[str, Any]]],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    stop_errors: list[dict[str, str]] = []
    stage_metrics: dict[str, Any] = {}
    for stage in STAGES:
        case_ids = [case_id for case_id, case in cases.items() if case["stage"] == stage]
        metrics, _pairs = evaluate_cases(case_ids, gold_by_case, predicted_by_case)
        metrics["stage"] = stage
        stage_metrics[stage] = metrics

    all_case_ids = list(cases)
    overall, _pairs = evaluate_cases(all_case_ids, gold_by_case, predicted_by_case)
    overall["per_stage"] = stage_metrics
    overall["profile"] = profile

    for case_id, findings in predicted_by_case.items():
        for finding in findings:
            stop_errors.extend(_finding_stop_errors(profile, case_id, finding))
    details = _matching_details(all_case_ids, gold_by_case, predicted_by_case)
    errors_for_unmatched: dict[str, tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]] = {}
    for case_id, (pairs, unmatched_gold, unmatched_predicted) in details.items():
        errors_for_unmatched[case_id] = ([], unmatched_gold, unmatched_predicted)
    stop_errors.extend(_unmatched_normative_errors(profile, errors_for_unmatched))
    return overall, stop_errors


def run_benchmark(
    experiment_dir: Path,
    *,
    output: Path | None = None,
    baseline_dir: str | None = None,
    skill_dir: str | None = None,
) -> dict[str, Any]:
    """Run one immutable experiment and return a JSON-serialisable report."""

    root = experiment_dir.resolve()
    errors: list[dict[str, str]] = []
    manifest_path = root / "manifest.yaml"
    if not manifest_path.is_file():
        manifest_path = root / "manifest.yml"
    if not manifest_path.is_file():
        report = {
            "status": "blocked",
            "release_decision": "stop",
            "stop_errors": [{"code": "MANIFEST_MISSING", "detail": str(root)}],
        }
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return report

    try:
        manifest = read_data(manifest_path)
    except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as error:
        report = {
            "status": "blocked",
            "release_decision": "stop",
            "stop_errors": [{"code": "MANIFEST_READ", "detail": str(error)}],
        }
        if output:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return report
    if not isinstance(manifest, Mapping):
        manifest = {}
        errors.append({"code": "MANIFEST_TYPE", "detail": "manifest must be an object"})

    stages, stage_errors = _normalise_stages(manifest)
    errors.extend(stage_errors)
    hashes = verify_frozen_hashes(root, manifest)
    errors.extend(hashes["errors"])
    if hashes["required"] and not hashes["frozen"] and not hashes["errors"]:
        errors.append({"code": "FROZEN_HASHES_EMPTY", "detail": "manifest requires frozen hashes but declares none"})

    cases, case_errors = load_cases(root, manifest)
    errors.extend(case_errors)
    gold_by_case, gold_errors = load_gold(root, manifest, cases)
    errors.extend(gold_errors)

    configured_dirs = _output_dirs(manifest)
    if baseline_dir:
        configured_dirs["baseline"] = baseline_dir
    if skill_dir:
        configured_dirs["skill"] = skill_dir
    outputs: dict[str, dict[str, list[dict[str, Any]]]] = {}
    output_provenance: dict[str, dict[str, dict[str, Any]]] = {}
    profile_errors: list[dict[str, str]] = []
    for profile in ("baseline", "skill"):
        loaded, loaded_errors, provenance = load_outputs(root, configured_dirs[profile], profile, cases)
        outputs[profile] = loaded
        output_provenance[profile] = provenance
        profile_errors.extend(loaded_errors)
    errors.extend(profile_errors)

    metrics: dict[str, Any] = {}
    stop_errors: list[dict[str, str]] = []
    for profile in ("baseline", "skill"):
        profile_metrics, profile_stop_errors = _profile_metrics(profile, cases, gold_by_case, outputs[profile])
        metrics[profile] = profile_metrics
        stop_errors.extend(profile_stop_errors)

    # Frozen/configuration/read errors prevent a release.  Keep them separate
    # from model-quality stop errors so an experiment report says what failed.
    stop_errors.extend(errors)
    status = "passed" if not stop_errors else "blocked"
    report: dict[str, Any] = {
        "experiment_id": str(manifest.get("experiment_id", root.name)),
        "standard_id": str(manifest.get("standard_id", "PSES-DISS-001")),
        "status": status,
        "release_decision": "pass" if status == "passed" else "stop",
        "stages": stages,
        "cases": {
            "count": len(cases),
            "by_stage": {stage: sum(1 for case in cases.values() if case["stage"] == stage) for stage in STAGES},
            "input_sha256": {case_id: case["input_sha256"] for case_id, case in sorted(cases.items())},
        },
        "gold_protection": {
            "hidden_from_runner_output": True,
            "path": str(_manifest_value(manifest, ("gold",), ("inputs", "gold"), ("gold_path",), default="gold/findings.json")),
            "sha256": sha256_file(_safe_experiment_path(root, str(_manifest_value(manifest, ("gold",), ("inputs", "gold"), ("gold_path",), default="gold/findings.json")))) if _safe_experiment_path(root, str(_manifest_value(manifest, ("gold",), ("inputs", "gold"), ("gold_path",), default="gold/findings.json"))).is_file() else None,
        },
        "frozen_hashes": hashes,
        "outputs": output_provenance,
        "execution_policy": {
            "external_llm_called": False,
            "network_used": False,
            "gold_exposed_to_critic": False,
        },
        "metrics": metrics,
        "stop_errors": stop_errors,
    }
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: Iterable[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--baseline-dir")
    parser.add_argument("--skill-dir")
    args = parser.parse_args(list(argv) if argv is not None else None)
    output = args.output or (args.experiment_dir / "report" / "status.json")
    report = run_benchmark(
        args.experiment_dir,
        output=output,
        baseline_dir=args.baseline_dir,
        skill_dir=args.skill_dir,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
