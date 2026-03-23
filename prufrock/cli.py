"""Prufrock CLI — memoir pipeline from physical artifacts."""
import click
from pathlib import Path

from prufrock.intake import run_intake
from prufrock.transcribe import run_transcribe
from prufrock.faces import run_faces
from prufrock.timeline import run_timeline
from prufrock.assemble import run_assemble
from prufrock.voice import run_voice
from prufrock.companion import run_companion


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


@cli.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), default=None,
              help="Output directory for voice profile.")
@click.option("--client-name", type=str, required=True, help="Client name.")
def voice(source: Path, output: Path | None, client_name: str):
    """Extract voice profile from recording or transcript.

    SOURCE can be an audio file (mp3, wav, m4a), a transcript file (txt, md),
    or a directory of transcripts. Outputs a voice-profile.json.
    """
    output = output or Path(str(source).rsplit(".", 1)[0] if source.is_file() else source) / "prufrock-output" / "voice"
    run_voice(source, output, client_name)


@cli.command()
@click.argument("source", type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), default=None,
              help="Output directory for companion spec.")
@click.option("--client-name", type=str, required=True, help="Client name.")
def companion(source: Path, output: Path | None, client_name: str):
    """Generate AI writing companion from all pipeline outputs.

    Reads transcriptions, timeline, face IDs, threads, and voice profile
    from SOURCE/prufrock-output/ and generates a companion spec the client
    can paste into Claude or ChatGPT to start writing their memoir.
    """
    output = output or source / "prufrock-output" / "companion"
    run_companion(source, output, client_name)
