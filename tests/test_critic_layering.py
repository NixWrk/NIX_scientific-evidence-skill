from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCIENTIFIC = ROOT / "skills" / "scientific-evidence-workflow"


def test_critic_workflow_has_three_check_classes() -> None:
    workflow = (SCIENTIFIC / "references" / "critic-workflow.md").read_text(
        encoding="utf-8"
    )

    compact = " ".join(workflow.split())

    assert "### Technical" in workflow
    assert "### Editorial" in workflow
    assert "### Evidential" in workflow
    assert "verification record only for an evidential check" in compact


def test_evidence_verification_is_conditional() -> None:
    skill = (SCIENTIFIC / "SKILL.md").read_text(encoding="utf-8")
    protocol = (
        SCIENTIFIC / "references" / "critic-verification-protocol.md"
    ).read_text(encoding="utf-8")

    assert "only for an evidence-dependent finding" in skill
    assert "Use this protocol only when a finding depends" in protocol
    assert "critic-findings-v2" not in skill
    assert "validate_critic_findings_v2" not in skill


def test_delivery_is_format_neutral_and_word_is_optional() -> None:
    standard = (
        ROOT / "docs" / "dissertation-skill-evaluation-standard.md"
    ).read_text(encoding="utf-8")
    release = (
        ROOT
        / "skills"
        / "candidate-dissertation-workflow"
        / "references"
        / "release-gates.md"
    ).read_text(encoding="utf-8")

    compact_release = " ".join(release.split())

    assert "Каноническое содержание замечания не зависит от Word" in standard
    assert "Только этот класс проходит дополнительный протокол" in standard
    assert "Word comments or tracked changes are optional" in compact_release
