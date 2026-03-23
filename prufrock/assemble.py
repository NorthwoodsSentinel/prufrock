"""Assemble — merge all outputs into client deliverable."""
import json
from pathlib import Path
from datetime import datetime

from rich.console import Console

console = Console()


def load_json(path: Path) -> dict | list | None:
    """Load JSON file if it exists."""
    if path.exists():
        return json.loads(path.read_text())
    return None


def run_assemble(source: Path, output: Path, client_name: str):
    """Assemble all processed outputs into final deliverable."""
    console.print(f"\n[bold]Prufrock Assemble[/bold] — building deliverable for {client_name}\n")

    output.mkdir(parents=True, exist_ok=True)
    prufrock_dir = source / "prufrock-output"

    # Locate components — search common paths
    manifest = load_json(prufrock_dir / "manifest.json")

    face_clusters = None
    for face_path in [
        prufrock_dir / "faces" / "face-clusters.json",
        *prufrock_dir.rglob("face-clusters.json"),
    ]:
        face_clusters = load_json(face_path)
        if face_clusters:
            break

    timeline_data = load_json(prufrock_dir / "timeline.json")

    # Collect transcriptions
    transcription_dir = prufrock_dir / "transcriptions"
    transcriptions = []
    if transcription_dir.exists():
        merged = transcription_dir / "all-transcriptions.md"
        if merged.exists():
            transcriptions.append(merged.read_text())

    # Build deliverable index
    index_lines = [
        f"# {client_name} — Prufrock Archive",
        f"*Generated {datetime.now().strftime('%B %d, %Y')}*\n",
        "---\n",
        "## What's In This Archive\n",
    ]

    # Summary
    if manifest:
        summary = manifest.get("summary", {})
        total = sum(summary.values())
        index_lines.append(f"**Total items processed:** {total}\n")
        for file_type, count in summary.items():
            if count > 0:
                index_lines.append(f"- {file_type.title()}s: {count}")
        index_lines.append("")

    # Transcriptions
    index_lines.append("## Transcriptions\n")
    if transcriptions:
        trans_out = output / "transcriptions.md"
        trans_out.write_text("\n\n---\n\n".join(transcriptions))
        word_count = sum(len(t.split()) for t in transcriptions)
        index_lines.append(f"All handwritten content has been transcribed and tagged.")
        index_lines.append(f"- **File:** transcriptions.md")
        index_lines.append(f"- **Word count:** ~{word_count:,}")
        index_lines.append("")
    else:
        index_lines.append("*No transcriptions found. Run `prufrock transcribe` first.*\n")

    # Faces
    index_lines.append("## People Identified\n")
    if face_clusters:
        clusters = face_clusters.get("clusters", [])
        named = [c for c in clusters if c.get("name")]
        unnamed = [c for c in clusters if not c.get("name")]

        if named:
            for c in named:
                index_lines.append(f"- **{c['name']}**: {c['face_count']} appearance(s)")
        if unnamed:
            index_lines.append(f"- {len(unnamed)} unidentified person(s) — see faces/id-worksheet.md")
        index_lines.append(f"\n**Total unique people:** {len(clusters)}")
        index_lines.append("")
    else:
        index_lines.append("*No face clustering found. Run `prufrock faces` first.*\n")

    # Timeline
    index_lines.append("## Timeline\n")
    if timeline_data:
        timeline_out = output / "timeline.md"
        # Copy timeline markdown
        timeline_src = prufrock_dir / "timeline.md"
        if timeline_src.exists():
            timeline_out.write_text(timeline_src.read_text())

        dates = sorted(set(d["date"][:4] for d in timeline_data))
        index_lines.append(f"**Date range:** {timeline_data[0]['date']} to {timeline_data[-1]['date']}")
        index_lines.append(f"**Total events:** {len(timeline_data)}")
        index_lines.append(f"**Years covered:** {', '.join(dates)}")
        index_lines.append(f"- **File:** timeline.md")
        index_lines.append("")
    else:
        index_lines.append("*No timeline found. Run `prufrock timeline` first.*\n")

    # Memoir scaffold
    index_lines.extend([
        "## Memoir Scaffold\n",
        "Based on the threads found in your archive, here are potential",
        "narrative arcs for your memoir:\n",
        "*This section is populated during the Story tier walkthrough session.*\n",
        "### Suggested Threads",
        "",
        "1. ___________________",
        "2. ___________________",
        "3. ___________________",
        "4. ___________________",
        "5. ___________________",
        "",
        "### Key Moments (from timeline + transcriptions)",
        "",
        "*Populated during assembly review.*\n",
    ])

    # Next steps
    index_lines.extend([
        "---\n",
        "## Next Steps\n",
        "- [ ] Review transcriptions for accuracy",
        "- [ ] Complete face identification (faces/id-worksheet.md)",
        "- [ ] Review timeline for missing events",
        "- [ ] Schedule Story walkthrough session",
        "- [ ] Begin writing with AI companion (Tier 3)",
        "",
        "---\n",
        f"*Built with [Prufrock](https://github.com/NorthwoodsSentinel/prufrock) — Your life. Your voice. Your book.*",
    ])

    # Write index
    index_path = output / "INDEX.md"
    index_path.write_text("\n".join(index_lines))

    console.print(f"Deliverable: [bold]{output}[/bold]")
    console.print(f"Index: [bold]{index_path}[/bold]\n")
