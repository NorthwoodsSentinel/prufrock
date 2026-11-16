"""Tests for prufrock.companion. Every input is synthetic placeholder data."""

import json

from prufrock import companion


def _write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data) if not isinstance(data, str) else data)


def test_loaders_return_none_for_missing_files(tmp_path):
    assert companion.load_json(tmp_path / "x.json") is None
    assert companion.load_text(tmp_path / "x.md") is None


def test_full_companion(tmp_path):
    src = tmp_path / "src"
    po = src / "prufrock-output"
    _write(
        po / "voice" / "voice-profile.json",
        {
            "vocabulary_patterns": ["synthetic"],
            "anti_patterns": ["never"],
            "statistics": {"top_distinctive_words": [["gardens", 3], ["rivers", 2]]},
        },
    )
    _write(
        po / "faces" / "face-clusters.json",
        {
            "clusters": [
                {
                    "name": "Person A",
                    "relationship": "neighbour",
                    "notes": "Note.",
                    "face_count": 2,
                },
                {"name": "Person B", "face_count": 1},
                {"name": None, "face_count": 5},
            ]
        },
    )
    _write(po / "timeline.json", [{"date": "1980-05-06"}, {"date": "1990-07-08"}])
    _write(po / "deliverable" / "memoir-threads.md", "Synthetic thread text")
    out = tmp_path / "out"
    companion.run_companion(src, out, "Client")

    spec = (out / "companion-spec.md").read_text()
    assert spec.startswith("# Client — AI Writing Companion")
    assert "- **Person A** (neighbour) — appears in 2 photos. Note." in spec
    assert "- **Person B** (unknown relationship) — appears in 1 photos." in spec
    assert "The archive spans 1980-05-06 to 1990-07-08 (2 documented events)." in spec
    assert "Years covered: 1980, 1990" in spec
    assert "Synthetic thread text" in spec
    assert "### Vocabulary Patterns" in spec
    assert "### Anti Patterns" in spec
    assert "### Distinctive vocabulary\ngardens, rivers" in spec
    paste = (out / "companion-paste.md").read_text()
    assert "---\n" not in paste


def test_raw_analysis_profile_found_by_search(tmp_path):
    src = tmp_path / "src"
    po = src / "prufrock-output"
    _write(
        po / "elsewhere" / "voice-profile.json", {"raw_analysis": "Raw synthetic voice"}
    )
    _write(
        po / "elsewhere" / "face-clusters.json",
        {"clusters": [{"name": None, "face_count": 1}]},
    )
    out = tmp_path / "out"
    companion.run_companion(src, out, "Client")
    spec = (out / "companion-spec.md").read_text()
    assert "Raw synthetic voice" in spec
    assert "Complete face identification" in spec
    assert "Distinctive vocabulary" not in spec


def test_profile_with_statistics_but_no_words(tmp_path):
    src = tmp_path / "src"
    _write(
        src / "prufrock-output" / "voice" / "voice-profile.json",
        {"raw_analysis": "Raw", "statistics": {"total_words": 3}},
    )
    out = tmp_path / "out"
    companion.run_companion(src, out, "Client")
    assert "Distinctive vocabulary" not in (out / "companion-spec.md").read_text()


def test_empty_source_uses_every_placeholder(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    out = tmp_path / "out"
    companion.run_companion(src, out, "Client")
    spec = (out / "companion-spec.md").read_text()
    assert "Complete face identification" in spec
    assert "Run the timeline command" in spec
    assert "Run the assemble command" in spec
    assert "Run the voice command" in spec


def test_deliverable_dir_without_threads(tmp_path):
    src = tmp_path / "src"
    (src / "prufrock-output" / "deliverable").mkdir(parents=True)
    out = tmp_path / "out"
    companion.run_companion(src, out, "Client")
    assert "Run the assemble command" in (out / "companion-spec.md").read_text()
