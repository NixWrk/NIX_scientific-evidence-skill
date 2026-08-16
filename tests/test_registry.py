"""Keep the machine-readable registry synchronized with the tested artifacts.

A verdict is only reproducible while the recorded hash still identifies the
skill that was actually tested. These checks turn that promise into a failure
instead of a stale line in `registry/skills.yaml`.
"""

import hashlib
import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[1]
_VALIDATOR_PATH = ROOT / "skills/scientific-evidence-workflow/scripts/validate_bundle.py"
_SPEC = importlib.util.spec_from_file_location("registry_validate_bundle", _VALIDATOR_PATH)
assert _SPEC and _SPEC.loader
VALIDATOR = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(VALIDATOR)
REGISTRY = yaml.safe_load((ROOT / "registry" / "skills.yaml").read_text(encoding="utf-8"))
QUEUE = yaml.safe_load((ROOT / "registry" / "skill-test-queue.yaml").read_text(encoding="utf-8"))
GENRES = yaml.safe_load((ROOT / "registry" / "genres.yaml").read_text(encoding="utf-8"))
NORMATIVE = yaml.safe_load((ROOT / "registry" / "normative-base.yaml").read_text(encoding="utf-8"))
TOOLS = yaml.safe_load((ROOT / "registry" / "tools.yaml").read_text(encoding="utf-8"))
EXPERIMENT_IDS = {
    path.name.split("-", maxsplit=2)[0] + "-" + path.name.split("-", maxsplit=2)[1]
    for path in (ROOT / "experiments").iterdir()
    if path.is_dir() and path.name.startswith("EXP-")
}

LOCAL_PREFIX = "local:"


def local_entries() -> list[dict]:
    return [
        entry
        for entry in REGISTRY["verdicts"]
        if str(entry.get("source", "")).startswith(LOCAL_PREFIX)
    ]


def referenced_experiments(entry: dict) -> set[str]:
    referenced: set[str] = set()
    for field in ("experiment", "prior_static_experiment"):
        if entry.get(field):
            referenced.add(entry[field])
    referenced.update(entry.get("experiments", []))
    return referenced


def test_local_skill_hash_matches_the_committed_skill() -> None:
    entries = local_entries()

    assert entries, "registry records no locally maintained skill"
    for entry in entries:
        skill_dir = ROOT / entry["source"][len(LOCAL_PREFIX) :]
        recorded = entry["skill_sha256"]
        actual = hashlib.sha256((skill_dir / "SKILL.md").read_bytes()).hexdigest()

        assert actual == recorded, (
            f"{entry['id']}: registry records {recorded} but SKILL.md hashes to {actual}; "
            "update registry/skills.yaml together with the skill"
        )
        assert re.fullmatch(r"\d+\.\d+", str(entry["version"])), entry["id"]


def test_every_registry_experiment_reference_exists() -> None:
    for entry in REGISTRY["verdicts"]:
        for experiment in referenced_experiments(entry):
            assert experiment in EXPERIMENT_IDS, f"{entry['id']} references missing {experiment}"


def test_every_queue_experiment_reference_exists() -> None:
    for repository in QUEUE["repositories"]:
        for candidate in repository["candidates"]:
            for field in ("experiment", "static_experiment"):
                if candidate.get(field):
                    assert candidate[field] in EXPERIMENT_IDS, candidate["id"]


def test_genre_identifiers_families_and_parents_resolve() -> None:
    genres = GENRES["genres"]
    ids = [genre["id"] for genre in genres]

    assert len(ids) == len(set(ids))
    for genre in genres:
        assert genre["family"] in GENRES["families"], genre["id"]
        if genre.get("parent"):
            assert genre["parent"] in ids, genre["id"]
            assert genre["parent"] != genre["id"]


def test_genre_fields_use_declared_axis_values() -> None:
    axes = GENRES["axes"]

    for genre in GENRES["genres"]:
        assert genre["normativity"] in axes["normativity"], genre["id"]
        assert genre["depth"] in axes["depth"], genre["id"]
        assert genre["purpose"] in axes["purpose"], genre["id"]
        assert genre["status"] in axes["status"], genre["id"]
        assert set(genre["audience"]) <= set(axes["audience"]), genre["id"]
        assert set(genre["render_targets"]) <= set(axes["render_target"]), genre["id"]
        assert set(genre["evidence_regime"]) == set(axes["evidence_dimensions"]), genre["id"]
        assert set(genre["evidence_regime"].values()) <= set(axes["evidence_permission"]), genre["id"]
        assert genre["required_components"], genre["id"]


def test_every_referenced_invariant_is_defined_and_every_definition_is_used() -> None:
    defined = set(GENRES["invariants"])
    referenced = {name for genre in GENRES["genres"] for name in genre.get("invariants", [])}

    assert referenced <= defined, f"undefined invariants: {sorted(referenced - defined)}"
    assert defined <= referenced, f"unused invariants: {sorted(defined - referenced)}"


def test_genre_registry_and_design_document_agree() -> None:
    document = (ROOT / GENRES["design_document"]).read_text(encoding="utf-8")

    for genre in GENRES["genres"]:
        assert f"`{genre['id']}`" in document, f"{genre['id']} is absent from the design document"
    for name in GENRES["invariants"]:
        assert f"`{name}`" in document, f"{name} is absent from the design document"


def test_implemented_genres_match_the_skill() -> None:
    """The skill carries its own genre table so it stays portable.

    That copy is only trustworthy while it agrees with the registry, so compare
    them in both directions.
    """

    declared = {
        genre["id"]: genre
        for genre in GENRES["genres"]
        if genre.get("implemented_in") == "scientific-evidence-workflow"
    }

    assert set(declared) == set(VALIDATOR.GENRES), (
        f"registry declares {sorted(declared)} as implemented, "
        f"the skill implements {sorted(VALIDATOR.GENRES)}"
    )
    for genre_id, genre in declared.items():
        rules = VALIDATOR.GENRES[genre_id]
        assert genre["status"] == "existing", genre_id
        assert genre["bundle_mode"] == rules["bundle_mode"], genre_id
        if genre["bundle_mode"] is not None:
            assert genre["bundle_mode"] in VALIDATOR.MODES, genre_id
        assert genre["source_count"]["min"] == rules["source_min"], genre_id
        assert genre["source_count"]["max"] == rules["source_max"], genre_id
        assert genre.get("source_representations") == rules["source_representations"], genre_id
        assert genre.get("figure_control", False) == rules.get("figure_control", False), genre_id
        for dimension in GENRES["axes"]["evidence_dimensions"]:
            assert genre["evidence_regime"][dimension] == rules[dimension], (
                f"{genre_id}: {dimension} differs between registry and skill"
            )


def test_methods_chapter_is_a_convention_not_a_fabricated_norm() -> None:
    methods = next(
        genre for genre in GENRES["genres"] if genre["id"] == "dissertation-methods-chapter"
    )

    assert methods["normativity"] == "conventional"
    assert methods["source_representations"] == ["data", "protocol"]
    assert methods["evidence_regime"]["own_results"] == "allowed"
    assert "не отдельную главу методов" in methods["notes"]


def test_actual_local_model_run_records_failure_and_release_gate() -> None:
    candidate = next(
        item for item in TOOLS["candidates"] if item["id"] == "evidence-first-agent"
    )
    evaluation = json.loads(
        (
            ROOT
            / "experiments"
            / "EXP-0026-local-model-portability"
            / "evaluation.json"
        ).read_text(encoding="utf-8")
    )

    assert "EXP-0026" in candidate["experiments"]
    assert candidate["local_model_execution"] == (
        "partial_pass_two_pass_and_host_gate_required"
    )
    assert evaluation["run_01"]["verdict"] == "fail"
    assert evaluation["run_02"]["verdict"] == "partial_pass_requires_host_gate"
    assert evaluation["overall"]["local_model_output_safe_for_unreviewed_release"] is False

def test_implemented_genres_have_their_language_profile() -> None:
    """A genre is only closed when its language layer exists too."""

    skill = ROOT / "skills" / "scientific-evidence-workflow"

    for genre in GENRES["genres"]:
        if genre.get("implemented_in") != "scientific-evidence-workflow":
            continue
        profile_id = genre["language_profile"]
        genre_id = genre["id"]

        assert (skill / "references" / "russian" / f"{profile_id}.md").is_file(), genre_id
        assert (skill / "scripts" / "russian" / f"{profile_id}.json").is_file(), genre_id
        reference = (skill / "references" / "genres" / f"{genre_id}.md").read_text(encoding="utf-8")
        assert profile_id in reference, f"{genre_id} does not name its language profile"


def test_declared_bundle_modes_are_known() -> None:
    for genre in GENRES["genres"]:
        if "bundle_mode" in genre:
            assert genre["bundle_mode"] in GENRES["axes"]["bundle_mode"], genre["id"]


def test_normative_documents_are_uniquely_identified_and_tiered() -> None:
    tiers = NORMATIVE["priority_tiers"]
    ids = [document["id"] for document in NORMATIVE["documents"]]

    assert len(ids) == len(set(ids))
    assert sorted(tiers) == list(range(1, len(tiers) + 1))
    for document in NORMATIVE["documents"]:
        assert document["tier"] in tiers, document["id"]
        assert document["acquisition"] in NORMATIVE["acquisition_states"], document["id"]
        assert document["scope"], document["id"]
        assert document["rules_to_extract"], document["id"]


def test_deferred_work_names_real_documents_and_a_trigger() -> None:
    """Deferred is not forgotten and not done.

    Every entry must point at a real document and say what would make it
    needed; a deferral without a trigger is indistinguishable from an item
    that fell out of sight.
    """

    known = {document["id"] for document in NORMATIVE["documents"]}
    deferred = NORMATIVE["deferred"]

    assert deferred
    seen = set()
    for entry in deferred:
        document_id = entry["id"]
        assert document_id in known, f"deferred entry {document_id} is not a known document"
        assert document_id not in seen, f"{document_id} deferred twice"
        seen.add(document_id)
        assert entry.get("trigger", "").strip(), f"{document_id}: deferral without a trigger"


def test_a_document_held_for_lookup_is_not_queued_for_a_card() -> None:
    """Not every held document is a document awaiting a card.

    A council roster is a list of people; a library page is a submission
    procedure. Neither states a rule about the text, and everything they touch
    in it is already established by a higher tier. Leaving them in `deferred`
    read as pending normative work and quietly promised requirements that would
    never arrive.

    So each entry must say when it is consulted, what it gives, and why a card
    would add nothing — and must be in exactly one of the two lists.
    """

    consulted = NORMATIVE["consulted_not_carded"]
    known = {document["id"] for document in NORMATIVE["documents"]}
    deferred = {entry["id"] for entry in NORMATIVE["deferred"]}
    carded = {
        document["id"]
        for document in NORMATIVE["documents"]
        if document["acquisition"] == "carded"
    }

    assert consulted
    seen = set()
    for entry in consulted:
        document_id = entry["id"]
        assert document_id in known, f"{document_id} is not a known document"
        assert document_id not in seen, f"{document_id} listed twice"
        seen.add(document_id)
        for field in ("consulted_at", "gives", "why_no_card"):
            assert entry.get(field, "").strip(), f"{document_id}: {field} is empty"
        assert document_id not in deferred, (
            f"{document_id}: both deferred and held for lookup; the two states say "
            "opposite things about whether a card is coming"
        )
        assert document_id not in carded, (
            f"{document_id}: carded although it was judged to establish no rule"
        )


def test_a_deferral_the_repository_cannot_settle_names_who_decides() -> None:
    """Some conditions depend on the subject of the work, which only the author knows.

    GOST ISO 14971 and GOST IEC 60601-1 unfold by kind of device. Carding them
    before the device is named would not be early work, it would be a guess
    written down as a requirement, and it would tie a skill meant to be
    subject-independent to one subject. So these entries are a finished state,
    not a queue item, and the flag says whose call it is.

    Two things are checked because both can rot: that such an entry explains
    itself, and that nobody quietly cards it anyway.
    """

    deciders = {"author"}
    carded = {
        document["id"]
        for document in NORMATIVE["documents"]
        if document["acquisition"] == "carded"
    }

    flagged = [entry for entry in NORMATIVE["deferred"] if "decided_by" in entry]
    assert flagged, "the deferrals that only the author can settle have disappeared"

    for entry in flagged:
        document_id = entry["id"]
        assert entry["decided_by"] in deciders, f"{document_id}: unknown decider"
        assert entry.get("note", "").strip(), (
            f"{document_id}: deferred to the author without saying why the repository cannot decide"
        )
        assert document_id not in carded, (
            f"{document_id}: carded although its condition depends on facts only the author has"
        )


def test_nothing_is_both_carded_and_deferred() -> None:
    """A carded document is done; leaving it deferred would misstate the state."""

    deferred = {entry["id"] for entry in NORMATIVE["deferred"]}
    carded = {
        document["id"]
        for document in NORMATIVE["documents"]
        if document["acquisition"] == "carded"
    }

    # GOST-8.417-2024 used to be allowed here: carded from the registry entry
    # with the text still unread. Once the text was carded the exception had no
    # subject left, so it is gone rather than kept as a dormant loophole.
    assert not deferred & carded, f"carded but still listed as deferred: {sorted(deferred & carded)}"


def test_every_card_hashes_a_file_the_registry_actually_holds() -> None:
    """A card's provenance hash must match a file recorded in the registry.

    Without this the hash is just a string in a JSON file, and a wrong one
    looks exactly like a right one. This check caught a fabricated hash once
    already.
    """

    card_dir = ROOT / "skills/scientific-evidence-workflow/references/normative-patterns"
    holdings = NORMATIVE["holdings"]

    for path in sorted(card_dir.glob("*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        document_id = card["document_id"]
        recorded = card["provenance"]["content_hash"].removeprefix("sha256:")
        holding = holdings.get(document_id)

        assert isinstance(holding, dict), f"{path.name}: {document_id} is not in holdings"
        known = {entry["sha256"] for entry in holding.get("files", [])}
        assert recorded in known, (
            f"{path.name}: content_hash {recorded[:16]}… matches no file recorded for "
            f"{document_id}; the card hashes something the registry does not hold"
        )


def test_every_work_card_hashes_a_file_the_registry_actually_holds() -> None:
    """The same guard as for normative cards, for the same reason.

    A hash nobody checks is a string, and a wrong one looks exactly like a
    right one. Work cards read files held in Zotero, so the registry holdings
    are the only place the hash can be checked against.
    """

    work_dir = ROOT / "skills/scientific-evidence-workflow/references/work-patterns"
    known = {
        entry["sha256"]
        for holding in NORMATIVE["holdings"].values()
        if isinstance(holding, dict)
        for entry in holding.get("files", [])
    }

    checked = 0
    for path in sorted(work_dir.glob("*.json")):
        card = json.loads(path.read_text(encoding="utf-8"))
        if card.get("kind") != "work":
            continue
        recorded = card["provenance"]["content_hash"].removeprefix("sha256:")
        assert recorded in known, (
            f"{path.name}: content_hash {recorded[:16]}… matches no file the registry records"
        )
        checked += 1

    if not checked:
        pytest.skip("no work cards yet")


def test_carding_state_matches_the_cards_that_exist() -> None:
    """A requirement counts as established only through a card.

    The registry may not claim more extraction than there are cards, and a
    document may not be marked carded without one. Both directions are checked
    so the flag cannot be flipped ahead of the work.
    """

    card_dir = ROOT / "skills/scientific-evidence-workflow/references/normative-patterns"
    carded_by_file = {
        json.loads(path.read_text(encoding="utf-8"))["document_id"]
        for path in card_dir.glob("*.json")
    }
    states = {document["id"]: document["acquisition"] for document in NORMATIVE["documents"]}
    carded_by_registry = {doc_id for doc_id, state in states.items() if state == "carded"}

    assert carded_by_registry == carded_by_file, "cards and registry disagree on what is carded"

    if not carded_by_file:
        expected = "none"
    elif carded_by_file == set(states):
        expected = "complete"
    else:
        expected = "partial"
    assert NORMATIVE["provenance"]["requirements_extracted"] == expected
    assert NORMATIVE["provenance"]["designations_verified_by"] == "user"


def test_holdings_and_acquisition_states_agree() -> None:
    """Holding a file and saying so must not drift apart."""

    holdings = {
        key: value
        for key, value in NORMATIVE["holdings"].items()
        if isinstance(value, dict)
    }
    states = {document["id"]: document["acquisition"] for document in NORMATIVE["documents"]}

    for document_id, holding in holdings.items():
        if document_id not in states:
            continue
        assert states[document_id] in {"obtained", "carded"}, document_id
        assert holding["kind"] in {"document", "catalogue_card", "index_page"}, document_id
    for document_id, state in states.items():
        if state in {"obtained", "carded"}:
            assert document_id in holdings, f"{document_id} claims a file it does not record"


def test_a_catalogue_card_is_not_recorded_as_the_standard() -> None:
    """A registry entry carries designation and status, never the requirements.

    The invariant is about the kind, not about which documents happen to be
    cards today: any holding declared a catalogue entry must say plainly that
    the text was not obtained, so nobody reads a designation as content.
    """

    for document_id, holding in NORMATIVE["holdings"].items():
        if not isinstance(holding, dict):
            continue
        if holding["kind"] == "catalogue_card":
            assert "не получен" in holding.get("note", ""), document_id
            assert not any(
                name.lower().endswith(".pdf") for name in
                (entry["name"] for entry in holding.get("files", []))
            ), f"{document_id}: помечено карточкой, но держит документ"


def test_recorded_hashes_match_the_local_files() -> None:
    """Verifies the store when it is present; skips where it is not.

    The files are deliberately outside the repository, so this check only runs
    on a machine that holds them.
    """

    store = ROOT / NORMATIVE["local_store"]["path"]
    if not store.is_dir():
        pytest.skip("normative store is not present on this machine")

    checked, absent, external = 0, [], 0
    for holding in NORMATIVE["holdings"].values():
        if not isinstance(holding, dict):
            continue
        for entry in holding.get("files", []):
            # Files held inside a Zotero library live outside this store and
            # their path is not portable; count them rather than going blind.
            if str(entry.get("url", "")).startswith("zotero://"):
                external += 1
                continue
            path = store / entry["name"]
            if not path.is_file():
                absent.append(entry["name"])
                continue
            assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"], entry["name"]
            assert path.stat().st_size == entry["bytes"], entry["name"]
            checked += 1

    if not checked and absent:
        pytest.skip(f"none of the {len(absent)} store files are present on this machine")
    assert checked, "holdings record no verifiable file"
    assert not absent, f"recorded but missing from the store: {sorted(absent)}"


def test_the_normative_store_is_not_committed() -> None:
    """Standards carry their own terms of use; only hashes belong in git."""

    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    store = NORMATIVE["local_store"]

    assert store["committed"] is False
    assert store["gitignored_by"].rstrip("/") + "/" in ignore
    assert store["path"].startswith(store["gitignored_by"].rstrip("/"))


def test_a_defended_example_never_outranks_a_normative_document() -> None:
    tiers = NORMATIVE["priority_tiers"]
    example_tier = next(tier for tier, name in tiers.items() if name == "defended_example")

    assert example_tier == max(tiers)
    for document in NORMATIVE["documents"]:
        if document.get("status") == "defended_example":
            assert document["tier"] == example_tier, document["id"]


def test_corpus_acquisition_stays_outside_processing() -> None:
    """The network policy is the repository's core invariant; keep it explicit."""

    acquisition = [genre for genre in GENRES["genres"] if genre["family"] == "acquisition"]

    assert acquisition
    for genre in acquisition:
        assert genre["policy"]["runs_inside_processing_task"] == "forbidden", genre["id"]
    for genre in GENRES["genres"]:
        if genre["family"] != "acquisition":
            assert "policy" not in genre or genre["policy"].get("network") is None, genre["id"]


def test_local_skill_records_the_experiments_that_name_it() -> None:
    """Lower bound only.

    An experiment that names the skill path in its own artifacts must appear in
    the verdict. The reverse does not hold: an experiment can exercise the skill
    without naming the path, so a pass here is not proof of a complete list.
    """

    for entry in local_entries():
        relative = entry["source"][len(LOCAL_PREFIX) :]
        recorded = referenced_experiments(entry)
        naming = {
            experiment
            for experiment in EXPERIMENT_IDS
            for path in (ROOT / "experiments").glob(f"{experiment}-*/*")
            if path.is_file() and relative in path.read_text(encoding="utf-8", errors="ignore")
        }

        assert naming <= recorded, (
            f"{entry['id']}: experiments {sorted(naming - recorded)} name the skill but are "
            "absent from its registry verdict"
        )
