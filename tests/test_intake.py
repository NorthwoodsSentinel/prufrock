"""Tests for prufrock.intake. Every file is generated here: solid-colour
images and placeholder text."""

import json

from PIL import Image

from prufrock import intake


def test_classify_file(tmp_path):
    assert intake.classify_file(tmp_path / "a.JPG") == "photo"
    assert intake.classify_file(tmp_path / "a.pdf") == "document"
    assert intake.classify_file(tmp_path / "a.mov") == "video"
    assert intake.classify_file(tmp_path / "a.flac") == "audio"
    assert intake.classify_file(tmp_path / "a.zzz") == "unknown"


def test_resize_image_shrinks_large_images(tmp_path):
    src = tmp_path / "big.png"
    Image.new("RGB", (40, 20), (10, 20, 30)).save(src)
    meta = intake.resize_image(src, tmp_path / "out" / "big.png", max_dim=10)
    assert meta == {
        "original_size": [40, 20],
        "processed_size": [10, 5],
        "resized": True,
    }


def test_resize_image_keeps_small_images(tmp_path):
    src = tmp_path / "small.png"
    Image.new("RGB", (8, 6)).save(src)
    meta = intake.resize_image(src, tmp_path / "small-out.png", max_dim=10)
    assert meta["resized"] is False
    assert meta["processed_size"] == [8, 6]


def test_run_intake(tmp_path):
    src = tmp_path / "src"
    (src / "sub").mkdir(parents=True)
    Image.new("RGB", (8, 6)).save(src / "sub" / "photo.png")
    (src / "broken.jpg").write_bytes(b"not an image")
    (src / "letter.txt").write_text("Synthetic placeholder text.")
    (src / "clip.mp4").write_bytes(b"synthetic")
    out = src / "prufrock-output"
    out.mkdir()
    (out / "old.txt").write_text("earlier output, must be skipped")

    intake.run_intake(src, out)

    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["summary"] == {
        "photo": 2,
        "document": 1,
        "video": 1,
        "audio": 0,
        "unknown": 0,
    }
    items = {i["source_path"]: i for i in manifest["items"]}
    assert set(items) == {"broken.jpg", "clip.mp4", "letter.txt", "sub/photo.png"}
    assert items["sub/photo.png"]["processed_path"] == "processed/sub/photo.png"
    assert items["sub/photo.png"]["resized"] is False
    assert "error" in items["broken.jpg"]
    assert (
        out / "processed" / "letter.txt"
    ).read_text() == "Synthetic placeholder text."
    assert (out / "processed" / "sub" / "photo.png").is_file()
