"""The study results exist twice on purpose: readable in docs/, bundled for the installed app.

If one copy changes without the other, the page would show different numbers than the report.
"""

from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs" / "reports"
BUNDLED = ROOT / "src" / "receipttrace" / "webdata"


def test_bundled_reports_are_byte_identical_to_the_published_ones() -> None:
    names = [
        "cord-inspection.manifest.json",
        "gemini-development-20.json",
        "ocr-baseline.json",
        "ocr-vs-gemini-development-20.json",
    ]
    for name in names:
        assert (DOCS / name).read_bytes() == (BUNDLED / "reports" / name).read_bytes(), name


def test_bundled_extractions_are_byte_identical_to_the_preserved_evidence() -> None:
    for method, folder in (("gemini", "gemini-development-20"), ("ocr", "ocr-baseline")):
        evidence = sorted((DOCS / "evidence" / folder).glob("cord-*.json"))
        assert len(evidence) == 20
        for path in evidence:
            bundled = BUNDLED / "extractions" / method / path.name
            assert path.read_bytes() == bundled.read_bytes(), f"{method}/{path.name}"
