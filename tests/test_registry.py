"""Keep the machine-readable registry synchronized with the tested artifacts.

A verdict is only reproducible while the recorded hash still identifies the
skill that was actually tested. These checks turn that promise into a failure
instead of a stale line in `registry/skills.yaml`.
"""

import hashlib
import importlib.util
import re
from pathlib import Path

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
        assert genre["bundle_mode"] in VALIDATOR.MODES, genre_id
        assert genre["source_count"]["min"] == rules["source_min"], genre_id
        assert genre["source_count"]["max"] == rules["source_max"], genre_id
        for dimension in GENRES["axes"]["evidence_dimensions"]:
            assert genre["evidence_regime"][dimension] == rules[dimension], (
                f"{genre_id}: {dimension} differs between registry and skill"
            )


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
