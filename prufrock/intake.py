"""Intake — inventory and process incoming materials."""
import json
import shutil
from pathlib import Path
from datetime import datetime

from PIL import Image
from rich.console import Console
from rich.table import Table

console = Console()

PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".heic", ".webp"}
DOC_EXTS = {".pdf", ".docx", ".doc", ".txt", ".rtf"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".mpg", ".mpeg", ".m4v"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac", ".wma"}

MAX_DIMENSION = 1800


def classify_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in PHOTO_EXTS:
        return "photo"
    if ext in DOC_EXTS:
        return "document"
    if ext in VIDEO_EXTS:
        return "video"
    if ext in AUDIO_EXTS:
        return "audio"
    return "unknown"


def resize_image(src: Path, dst: Path, max_dim: int = MAX_DIMENSION) -> dict:
    """Resize image if needed, return metadata."""
    img = Image.open(src)
    original_size = img.size
    needs_resize = max(img.size) > max_dim

    if needs_resize:
        img.thumbnail((max_dim, max_dim), Image.LANCZOS)

    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, quality=92)

    return {
        "original_size": list(original_size),
        "processed_size": list(img.size),
        "resized": needs_resize,
    }


def run_intake(source: Path, output: Path):
    """Inventory source directory and process files."""
    console.print(f"\n[bold]Prufrock Intake[/bold] — scanning {source}\n")

    output.mkdir(parents=True, exist_ok=True)
    processed_dir = output / "processed"
    processed_dir.mkdir(exist_ok=True)

    manifest = {
        "source": str(source),
        "output": str(output),
        "timestamp": datetime.now().isoformat(),
        "items": [],
        "summary": {"photo": 0, "document": 0, "video": 0, "audio": 0, "unknown": 0},
    }

    # Collect all files recursively, skip output dir
    files = sorted(
        f for f in source.rglob("*")
        if f.is_file() and not str(f).startswith(str(output))
    )

    console.print(f"Found [bold]{len(files)}[/bold] files\n")

    for f in files:
        file_type = classify_file(f)
        manifest["summary"][file_type] = manifest["summary"].get(file_type, 0) + 1

        item = {
            "source_path": str(f.relative_to(source)),
            "type": file_type,
            "size_bytes": f.stat().st_size,
            "extension": f.suffix.lower(),
        }

        if file_type == "photo":
            try:
                dst = processed_dir / f.relative_to(source)
                meta = resize_image(f, dst)
                item["processed_path"] = str(dst.relative_to(output))
                item.update(meta)
            except Exception as e:
                item["error"] = str(e)
        else:
            # Copy non-photo files as-is
            dst = processed_dir / f.relative_to(source)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst)
            item["processed_path"] = str(dst.relative_to(output))

        manifest["items"].append(item)

    # Write manifest
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    # Print summary
    table = Table(title="Intake Summary")
    table.add_column("Type", style="cyan")
    table.add_column("Count", style="bold")
    for file_type, count in manifest["summary"].items():
        if count > 0:
            table.add_row(file_type, str(count))
    table.add_row("TOTAL", str(len(files)), style="bold green")
    console.print(table)

    console.print(f"\nManifest: [bold]{manifest_path}[/bold]")
    console.print(f"Processed files: [bold]{processed_dir}[/bold]\n")
