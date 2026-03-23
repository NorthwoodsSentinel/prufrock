"""Faces — facial recognition clustering across photos."""
import json
import shutil
from pathlib import Path
from collections import defaultdict

from rich.console import Console

console = Console()

PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}


def run_faces(source: Path, output: Path, tolerance: float):
    """Detect and cluster faces across all photos."""
    console.print(f"\n[bold]Prufrock Faces[/bold] — clustering faces in {source}\n")

    try:
        import face_recognition
    except ImportError:
        console.print(
            "[red]face_recognition not installed.[/red]\n"
            "Install with: pip install face-recognition\n"
            "Requires dlib — see https://github.com/ageitgey/face_recognition#installation\n"
        )
        return

    output.mkdir(parents=True, exist_ok=True)

    images = sorted(
        f for f in source.rglob("*")
        if f.is_file() and f.suffix.lower() in PHOTO_EXTS
    )

    if not images:
        console.print("[yellow]No images found.[/yellow]")
        return

    console.print(f"Found [bold]{len(images)}[/bold] images\n")

    # Detect faces and compute encodings
    all_encodings = []
    all_locations = []
    all_files = []

    for img_path in images:
        try:
            image = face_recognition.load_image_file(str(img_path))
            locations = face_recognition.face_locations(image, model="hog")
            encodings = face_recognition.face_encodings(image, locations)

            for enc, loc in zip(encodings, locations):
                all_encodings.append(enc)
                all_locations.append(loc)
                all_files.append(img_path)

            if locations:
                console.print(f"  {img_path.name}: {len(locations)} face(s)")
        except Exception as e:
            console.print(f"  [red]{img_path.name}: {e}[/red]")

    if not all_encodings:
        console.print("[yellow]No faces detected in any images.[/yellow]")
        return

    console.print(f"\nTotal faces detected: [bold]{len(all_encodings)}[/bold]")
    console.print("Clustering...\n")

    # Cluster faces
    clusters = defaultdict(list)
    assigned = [False] * len(all_encodings)

    cluster_id = 0
    for i in range(len(all_encodings)):
        if assigned[i]:
            continue

        assigned[i] = True
        clusters[cluster_id].append(i)

        for j in range(i + 1, len(all_encodings)):
            if assigned[j]:
                continue

            distance = face_recognition.face_distance([all_encodings[i]], all_encodings[j])[0]
            if distance <= tolerance:
                assigned[j] = True
                clusters[cluster_id].append(j)

        cluster_id += 1

    # Output clusters
    manifest = {"clusters": [], "total_faces": len(all_encodings), "total_images": len(images)}

    for cid, face_indices in sorted(clusters.items(), key=lambda x: -len(x[1])):
        cluster_dir = output / f"person-{cid + 1:03d}"
        cluster_dir.mkdir(exist_ok=True)

        cluster_files = []
        for idx in face_indices:
            src_file = all_files[idx]
            dst_file = cluster_dir / src_file.name
            if not dst_file.exists():
                shutil.copy2(src_file, dst_file)
            cluster_files.append(str(src_file.relative_to(source)))

        manifest["clusters"].append({
            "id": cid + 1,
            "name": None,  # Populated during zoom ID session
            "face_count": len(face_indices),
            "appearances_in": list(set(cluster_files)),
        })

        console.print(f"  Person {cid + 1}: {len(face_indices)} appearance(s) across {len(set(cluster_files))} photo(s)")

    # Write manifest
    manifest_path = output / "face-clusters.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    # Write ID worksheet for zoom session
    worksheet = output / "id-worksheet.md"
    lines = ["# Face Identification Worksheet",
             "## For Zoom ID Session with Client\n",
             "Review each cluster folder and identify the person.\n"]
    for cluster in manifest["clusters"]:
        lines.append(f"### Person {cluster['id']} ({cluster['face_count']} appearances)")
        lines.append(f"- **Name:** ___________________")
        lines.append(f"- **Relationship:** ___________________")
        lines.append(f"- **Notes:** ___________________")
        lines.append(f"- Photos: {', '.join(cluster['appearances_in'][:5])}")
        if len(cluster["appearances_in"]) > 5:
            lines.append(f"  ... and {len(cluster['appearances_in']) - 5} more")
        lines.append("")

    worksheet.write_text("\n".join(lines))

    console.print(f"\nClusters: [bold]{output}[/bold]")
    console.print(f"ID Worksheet: [bold]{worksheet}[/bold]")
    console.print(f"Total clusters: [bold]{len(clusters)}[/bold]\n")
