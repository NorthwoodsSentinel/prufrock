"""Assemble — merge all outputs into client deliverable."""
import json
from pathlib import Path
from datetime import datetime

from anthropic import Anthropic
from rich.console import Console

console = Console()

THREAD_ANALYSIS_PROMPT = """You are analyzing transcribed family documents — letters, journals, margin notes, diary entries — to find narrative threads for a memoir.

Read the transcriptions below and identify:

1. **5-8 narrative threads** — recurring themes, relationships, conflicts, transformations, or patterns visible across the documents. Each thread should have:
   - A compelling title (not generic — specific to this family)
   - A 2-3 sentence description of what the thread contains
   - Which documents/dates it appears in

2. **10 key moments** — the most emotionally resonant, surprising, or structurally important entries. For each:
   - The date (if known)
   - A one-line description
   - Why it matters for the memoir

3. **Family dynamics** — what patterns emerge about relationships between the people in these documents?

Be specific. Use their names, their words, their dates. Do not invent anything — only surface what is in the text.

Format as clean markdown."""


def load_json(path: Path) -> dict | list | None:
    """Load JSON file if it exists."""
    if path.exists():
        return json.loads(path.read_text())
    return None


def analyze_threads(transcription_text: str, client_name: str) -> str | None:
    """Use Claude to analyze transcriptions for narrative threads."""
    if not transcription_text or len(transcription_text.strip()) < 500:
        return None

    try:
        client = Anthropic()

        # Truncate if very large — keep first and last sections
        max_chars = 100_000
        if len(transcription_text) > max_chars:
            half = max_chars // 2
            transcription_text = (
                transcription_text[:half]
                + "\n\n[... middle sections omitted for length ...]\n\n"
                + transcription_text[-half:]
            )

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=THREAD_ANALYSIS_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Client: {client_name}\n\n---\n\n{transcription_text}",
            }],
        )
        return response.content[0].text
    except Exception as e:
        console.print(f"[yellow]Thread analysis failed: {e}[/yellow]")
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
    transcription_text = ""
    if transcription_dir.exists():
        for md_file in sorted(transcription_dir.glob("*.md")):
            transcription_text += md_file.read_text() + "\n\n---\n\n"

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
    if transcription_text:
        trans_out = output / "transcriptions.md"
        trans_out.write_text(transcription_text)
        word_count = len(transcription_text.split())
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

    # Memoir scaffold — AI thread analysis
    index_lines.append("## Memoir Scaffold\n")

    if transcription_text:
        console.print("Analyzing transcriptions for narrative threads...")
        threads = analyze_threads(transcription_text, client_name)

        if threads:
            threads_out = output / "memoir-threads.md"
            threads_out.write_text(f"# {client_name} — Narrative Thread Analysis\n\n{threads}")
            index_lines.append(threads)
            index_lines.append("")
            index_lines.append("*Full analysis: memoir-threads.md*\n")
        else:
            index_lines.extend([
                "*Thread analysis unavailable. Set ANTHROPIC_API_KEY to enable.*\n",
                "### Suggested Threads\n",
                "1. ___________________",
                "2. ___________________",
                "3. ___________________",
                "4. ___________________",
                "5. ___________________\n",
            ])
    else:
        index_lines.append("*No transcriptions available for thread analysis.*\n")

    # Next steps
    index_lines.extend([
        "---\n",
        "## Next Steps\n",
        "- [ ] Review transcriptions for accuracy",
        "- [ ] Complete face identification (faces/id-worksheet.md)",
        "- [ ] Review timeline for missing events",
        "- [ ] Review narrative threads — add, remove, refine",
        "- [ ] Schedule Story walkthrough session (Tier 2)",
        "- [ ] Configure AI writing companion (Tier 3)",
        "",
        "---\n",
        f"*Built with [Prufrock](https://github.com/NorthwoodsSentinel/prufrock) — Your life. Your voice. Your book.*",
    ])

    # Write index
    index_path = output / "INDEX.md"
    index_path.write_text("\n".join(index_lines))

    console.print(f"Deliverable: [bold]{output}[/bold]")
    console.print(f"Index: [bold]{index_path}[/bold]\n")
