"""Prufrock CLI — memoir pipeline from physical artifacts."""
import click
from pathlib import Path

from prufrock.intake import run_intake
from prufrock.transcribe import run_transcribe
from prufrock.faces import run_faces
from prufrock.timeline import run_timeline
from prufrock.assemble import run_assemble


@click.group()
@click.version_option()
def cli():
    """Prufrock — Your life. Your voice. Your book.

    Transform boxes of physical artifacts into searchable archives,
    memoir scaffolds, and AI writing companions.
    """
    pass


@cli.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), default=None,
              help="Output directory for processed files. Defaults to SOURCE/prufrock-output/")
def intake(source: Path, output: Path | None):
    """Inventory and process incoming materials.

    Scans SOURCE directory for images, documents, videos.
    Resizes, categorizes, and generates a manifest.
    """
    output = output or source / "prufrock-output"
    run_intake(source, output)


@cli.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), default=None,
              help="Output directory for transcriptions.")
@click.option("--batch-size", default=10, help="Images per transcription batch.")
@click.option("--context", type=str, default=None,
              help="Context string for the transcriber (family names, dates, locations).")
def transcribe(source: Path, output: Path | None, batch_size: int, context: str | None):
    """Transcribe handwritten pages using Claude Vision.

    Reads images from SOURCE, transcribes all handwriting,
    captures highlights, applies tags, outputs structured markdown.
    """
    output = output or source / "prufrock-output" / "transcriptions"
    run_transcribe(source, output, batch_size, context)


@cli.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), default=None,
              help="Output directory for face clusters.")
@click.option("--tolerance", default=0.6, help="Face matching tolerance (lower = stricter).")
def faces(source: Path, output: Path | None, tolerance: float):
    """Cluster faces across all photos.

    Detects faces in all images under SOURCE, groups them
    by identity, and outputs clusters ready for human ID.
    """
    output = output or source / "prufrock-output" / "faces"
    run_faces(source, output, tolerance)


@cli.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), default=None,
              help="Output file for timeline.")
def timeline(source: Path, output: Path | None):
    """Extract dates and construct chronological timeline.

    Parses transcriptions and EXIF data from SOURCE,
    extracts all dates, and builds a unified timeline.
    """
    output = output or source / "prufrock-output" / "timeline.md"
    run_timeline(source, output)


@cli.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), default=None,
              help="Output directory for final deliverable.")
@click.option("--client-name", type=str, required=True, help="Client name for the deliverable.")
def assemble(source: Path, output: Path | None, client_name: str):
    """Assemble all outputs into client deliverable.

    Merges transcriptions, face clusters, and timeline into
    a structured archive with memoir scaffold.
    """
    output = output or source / "prufrock-output" / "deliverable"
    run_assemble(source, output, client_name)
