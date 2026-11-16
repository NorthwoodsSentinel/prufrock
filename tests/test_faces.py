"""Tests for prufrock.faces. Images are generated solid colours or noise; the
face_recognition library is replaced by a fake that returns scripted faces,
so no real photograph or face is ever involved."""

import json
import random
import sys
import types

from PIL import Image

from prufrock import faces


def _photo(path, size=(40, 30)):
    rng = random.Random(7)
    img = Image.new("L", size)
    img.putdata([rng.randrange(256) for _ in range(size[0] * size[1])])
    img.convert("RGB").save(path)
    return path


def _page(path, size=(40, 30)):
    Image.new("RGB", size, (250, 250, 250)).save(path)
    return path


def test_tall_image_is_a_page(tmp_path):
    assert faces.is_likely_photo(_photo(tmp_path / "tall.png", (10, 30))) is False


def test_bright_uniform_image_is_a_page(tmp_path):
    assert faces.is_likely_photo(_page(tmp_path / "page.png")) is False


def test_noisy_image_is_a_photo(tmp_path):
    assert faces.is_likely_photo(_photo(tmp_path / "photo.png")) is True


def test_bright_but_varied_image_is_a_photo(tmp_path):
    img = Image.new("L", (20, 20), 255)
    img.putdata([255 if i % 2 else 0 for i in range(400)])
    img.save(tmp_path / "checker.png")
    assert faces.is_likely_photo(tmp_path / "checker.png") is True


def test_tiny_image_has_no_sample_and_counts_as_photo(tmp_path):
    Image.new("RGB", (4, 1), (0, 0, 0)).save(tmp_path / "tiny.png")
    assert faces.is_likely_photo(tmp_path / "tiny.png") is True


def test_unreadable_image_counts_as_photo(tmp_path):
    bad = tmp_path / "bad.jpg"
    bad.write_bytes(b"not an image")
    assert faces.is_likely_photo(bad) is True


def _fake_face_recognition(monkeypatch, faces_by_file, broken=()):
    """faces_by_file maps a file name to a list of (location, encoding) pairs.
    An encoding is a float; the distance between two faces is their difference."""
    module = types.ModuleType("face_recognition")

    def load_image_file(path):
        name = path.rsplit("/", 1)[-1]
        if name in broken:
            raise OSError("synthetic load failure")
        return name

    def face_locations(image, model):
        assert model == "hog"
        return [loc for loc, _ in faces_by_file.get(image, [])]

    def face_encodings(image, locations):
        return [enc for _, enc in faces_by_file.get(image, [])]

    def face_distance(known, candidate):
        return [abs(known[0] - candidate)]

    module.load_image_file = load_image_file  # type: ignore[attr-defined]  # stand-in module built at runtime
    module.face_locations = face_locations  # type: ignore[attr-defined]  # stand-in module built at runtime
    module.face_encodings = face_encodings  # type: ignore[attr-defined]  # stand-in module built at runtime
    module.face_distance = face_distance  # type: ignore[attr-defined]  # stand-in module built at runtime
    monkeypatch.setitem(sys.modules, "face_recognition", module)


def test_missing_library_returns_quietly(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "face_recognition", None)
    out = tmp_path / "out"
    faces.run_faces(tmp_path, out, 0.6)
    assert not out.exists()


def test_no_images(monkeypatch, tmp_path):
    _fake_face_recognition(monkeypatch, {})
    src = tmp_path / "src"
    src.mkdir()
    faces.run_faces(src, tmp_path / "out", 0.6)
    assert list((tmp_path / "out").iterdir()) == []


def test_only_pages(monkeypatch, tmp_path):
    _fake_face_recognition(monkeypatch, {})
    src = tmp_path / "src"
    src.mkdir()
    _page(src / "page.png")
    faces.run_faces(src, tmp_path / "out", 0.6)
    assert list((tmp_path / "out").iterdir()) == []


def test_no_faces_found(monkeypatch, tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    _photo(src / "a.png")
    _photo(src / "b.png")
    _fake_face_recognition(monkeypatch, {}, broken={"b.png"})
    faces.run_faces(src, tmp_path / "out", 0.6)
    assert not (tmp_path / "out" / "face-clusters.json").exists()


def test_clusters_and_worksheet(monkeypatch, tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    names = [f"p{i}.png" for i in range(7)]
    for n in names:
        _photo(src / n)
    _page(src / "page.png")
    loc = (0, 1, 1, 0)
    scripted = {n: [(loc, 1.0)] for n in names}
    # p0 also holds someone else, early, so a later cluster meets faces that
    # are already assigned; p1 holds two faces of the same person, so its
    # copy into the cluster folder already exists the second time.
    scripted["p0.png"].append((loc, 5.0))
    scripted["p1.png"].append((loc, 1.1))
    _fake_face_recognition(monkeypatch, scripted)

    out = tmp_path / "out"
    faces.run_faces(src, out, 0.6)

    manifest = json.loads((out / "face-clusters.json").read_text())
    assert manifest["total_faces"] == 9
    assert manifest["total_images"] == 7
    big, small = manifest["clusters"]
    assert (big["id"], big["face_count"], big["name"]) == (1, 8, None)
    assert sorted(big["appearances_in"]) == names
    assert (small["id"], small["face_count"], small["appearances_in"]) == (
        2,
        1,
        ["p0.png"],
    )
    assert sorted(p.name for p in (out / "person-001").iterdir()) == names
    assert [p.name for p in (out / "person-002").iterdir()] == ["p0.png"]
    worksheet = (out / "id-worksheet.md").read_text()
    assert "### Person 1 (8 appearances)" in worksheet
    assert "  ... and 2 more" in worksheet
    assert "### Person 2 (1 appearances)" in worksheet
