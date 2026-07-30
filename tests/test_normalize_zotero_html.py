from pathlib import Path

from tools.normalize_zotero_html import normalize_html


FIXTURE = Path(__file__).parent / "fixtures" / "sample_article.html"


def test_normalize_html_preserves_traceable_blocks() -> None:
    document = normalize_html(
        FIXTURE.read_bytes(),
        source_id="SRC-TEST-001",
        zotero_item_key="ITEM1234",
        attachment_key="ATTACH01",
    )

    assert document["content_sha256"]
    assert document["statistics"] == {
        "bytes": FIXTURE.stat().st_size,
        "blocks": 6,
        "headings": 2,
        "tables": 1,
        "characters": 134,
        "words": 25,
    }
    assert [block["block_id"] for block in document["blocks"]] == [
        f"SRC-TEST-001-B{number:04d}" for number in range(1, 7)
    ]
    assert document["blocks"][3]["section_path"] == ["Fixture study", "Results"]
    assert document["blocks"][4]["rows"][1] == ["A", "7.5"]
    assert document["blocks"][1]["locator"]["selector"].startswith("main#marker-doc")
