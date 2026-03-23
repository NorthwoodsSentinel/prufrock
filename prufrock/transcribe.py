"""Transcribe — handwriting OCR via Claude Vision."""
import base64
import json
from pathlib import Path

from anthropic import Anthropic
from rich.console import Console
from rich.progress import Progress

console = Console()

PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp", ".webp"}

SYSTEM_PROMPT = """You are a meticulous transcriber of handwritten documents and annotated books.
For each image, produce structured output:

1. **Page number** (if visible, or "unnumbered")
2. **Printed text context** — title, heading, or entry name if this is an annotated book
3. **Highlighted passages** — exact text that appears highlighted
4. **Handwritten notes** — transcribe ALL handwriting exactly as written.
   Note location (top margin, bottom margin, left margin, right margin, between entries).
   Use [illegible] for words you cannot read. Never guess.
5. **Tags** — apply relevant tags:
   - [FAMILY] — names of people
   - [MEDICAL] — health references
   - [LOCATION] — places mentioned
   - [DATE] — dates written by hand
   - [WEATHER] — weather observations
   - [EMOTION] — strong emotional content
   - [RECOVERY] — recovery/spiritual references
   - [MEMOIR] — especially resonant material

Be thorough. Every word of handwriting matters. These may be the only surviving
words of someone who has died."""


def encode_image(path: Path) -> tuple[str, str]:
    """Read and base64-encode an image file."""
    suffix = path.suffix.lower()
    media_type = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
        ".tiff": "image/tiff", ".tif": "image/tiff",
        ".bmp": "image/bmp",
    }.get(suffix, "image/jpeg")

    data = base64.standard_b64encode(path.read_bytes()).decode("utf-8")
    return data, media_type


def transcribe_batch(client: Anthropic, images: list[Path], context: str | None) -> str:
    """Send a batch of images to Claude Vision for transcription."""
    content = []

    for img_path in images:
        data, media_type = encode_image(img_path)
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": data},
        })
        content.append({
            "type": "text",
            "text": f"Transcribe this page: {img_path.name}",
        })

    system = SYSTEM_PROMPT
    if context:
        system += f"\n\nAdditional context from the client:\n{context}"

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=system,
        messages=[{"role": "user", "content": content}],
    )

    return response.content[0].text


def run_transcribe(source: Path, output: Path, batch_size: int, context: str | None):
    """Transcribe all handwritten pages in source directory."""
    console.print(f"\n[bold]Prufrock Transcribe[/bold] — processing {source}\n")

    output.mkdir(parents=True, exist_ok=True)

    # Find all images
    images = sorted(
        f for f in source.rglob("*")
        if f.is_file() and f.suffix.lower() in PHOTO_EXTS
    )

    if not images:
        console.print("[yellow]No images found in source directory.[/yellow]")
        return

    console.print(f"Found [bold]{len(images)}[/bold] images, batch size {batch_size}\n")

    # Load context file if it's a path
    if context and Path(context).is_file():
        context = Path(context).read_text()

    client = Anthropic()
    batches = [images[i:i + batch_size] for i in range(0, len(images), batch_size)]
    all_transcriptions = []

    with Progress() as progress:
        task = progress.add_task("Transcribing...", total=len(batches))

        for batch_idx, batch in enumerate(batches):
            try:
                result = transcribe_batch(client, batch, context)
                all_transcriptions.append(result)

                # Write individual batch file
                batch_file = output / f"batch-{batch_idx + 1:03d}.md"
                batch_file.write_text(
                    f"# Transcription Batch {batch_idx + 1}\n"
                    f"## Files: {', '.join(f.name for f in batch)}\n\n"
                    f"{result}\n"
                )
            except Exception as e:
                console.print(f"[red]Batch {batch_idx + 1} failed: {e}[/red]")
                all_transcriptions.append(f"# Batch {batch_idx + 1} — FAILED\nError: {e}\n")

            progress.update(task, advance=1)

    # Write merged output
    merged = output / "all-transcriptions.md"
    merged.write_text("\n\n---\n\n".join(all_transcriptions))

    console.print(f"\nTranscriptions: [bold]{output}[/bold]")
    console.print(f"Merged file: [bold]{merged}[/bold]")
    console.print(f"Batches: [bold]{len(batches)}[/bold]\n")
