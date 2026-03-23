"""Timeline — extract dates and construct chronology."""
import json
import re
from pathlib import Path
from datetime import datetime

from rich.console import Console

console = Console()

# Patterns for date extraction from transcriptions
DATE_PATTERNS = [
    # MM/DD/YY or MM/DD/YYYY
    (r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})\b', "mdy"),
    # Month DD, YYYY
    (r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s+(\d{4})\b', "month_name"),
    # YYYY-MM-DD
    (r'\b(\d{4})-(\d{2})-(\d{2})\b', "iso"),
    # Handwritten style: 1/1/96, 11/21/94
    (r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{2})\b', "mdy_short"),
]

MONTH_MAP = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}


def parse_year(y: str) -> int | None:
    """Convert 2 or 4 digit year string to full year."""
    val = int(y)
    if val > 2100:
        return None
    if val < 100:
        return val + 1900 if val > 25 else val + 2000
    return val


def extract_dates_from_text(text: str) -> list[dict]:
    """Extract all dates from text with surrounding context."""
    found = []

    for pattern, fmt in DATE_PATTERNS:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start = max(0, match.start() - 80)
            end = min(len(text), match.end() + 80)
            context = text[start:end].replace("\n", " ").strip()

            try:
                if fmt == "month_name":
                    month = MONTH_MAP[match.group(1).lower()]
                    day = int(match.group(2))
                    year = int(match.group(3))
                elif fmt == "iso":
                    year = int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3))
                elif fmt in ("mdy", "mdy_short"):
                    month = int(match.group(1))
                    day = int(match.group(2))
                    year = parse_year(match.group(3))
                    if year is None:
                        continue
                else:
                    continue

                if 1 <= month <= 12 and 1 <= day <= 31 and 1800 <= year <= 2100:
                    date_str = f"{year}-{month:02d}-{day:02d}"
                    found.append({
                        "date": date_str,
                        "raw": match.group(0),
                        "context": context,
                    })
            except (ValueError, TypeError):
                continue

    return found


def extract_exif_dates(source: Path) -> list[dict]:
    """Extract dates from EXIF data in photos."""
    found = []
    try:
        import exifread
    except ImportError:
        return found

    photo_exts = {".jpg", ".jpeg", ".tiff", ".tif"}
    for f in source.rglob("*"):
        if f.suffix.lower() not in photo_exts:
            continue
        try:
            with open(f, "rb") as fh:
                tags = exifread.process_file(fh, stop_tag="DateTimeOriginal")
                date_tag = tags.get("EXIF DateTimeOriginal") or tags.get("Image DateTime")
                if date_tag:
                    dt = datetime.strptime(str(date_tag), "%Y:%m:%d %H:%M:%S")
                    found.append({
                        "date": dt.strftime("%Y-%m-%d"),
                        "raw": str(date_tag),
                        "context": f"EXIF from {f.name}",
                        "source": str(f.name),
                    })
        except Exception:
            continue

    return found


def run_timeline(source: Path, output: Path):
    """Build timeline from transcriptions and EXIF data."""
    console.print(f"\n[bold]Prufrock Timeline[/bold] — building chronology from {source}\n")

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    all_dates = []

    # Extract from transcription markdown files
    md_files = sorted(source.rglob("*.md"))
    for md_file in md_files:
        text = md_file.read_text()
        dates = extract_dates_from_text(text)
        for d in dates:
            d["source"] = str(md_file.name)
        all_dates.extend(dates)
        if dates:
            console.print(f"  {md_file.name}: {len(dates)} date(s)")

    # Extract EXIF dates
    exif_dates = extract_exif_dates(source)
    all_dates.extend(exif_dates)
    if exif_dates:
        console.print(f"  EXIF data: {len(exif_dates)} date(s)")

    if not all_dates:
        console.print("[yellow]No dates found.[/yellow]")
        return

    # Deduplicate and sort
    seen = set()
    unique_dates = []
    for d in all_dates:
        key = (d["date"], d.get("context", "")[:40])
        if key not in seen:
            seen.add(key)
            unique_dates.append(d)

    unique_dates.sort(key=lambda x: x["date"])

    # Write markdown timeline
    lines = [
        "# Timeline",
        f"## Constructed from {len(md_files)} transcription(s) and EXIF data",
        f"## {len(unique_dates)} events\n",
        "| Date | Context | Source |",
        "|------|---------|--------|",
    ]
    for d in unique_dates:
        ctx = d["context"][:100].replace("|", "/").replace("\n", " ")
        src = d.get("source", "unknown")
        lines.append(f"| {d['date']} | {ctx} | {src} |")

    output.write_text("\n".join(lines))

    # Write JSON for programmatic use
    json_path = output.with_suffix(".json")
    json_path.write_text(json.dumps(unique_dates, indent=2))

    console.print(f"\nTimeline: [bold]{output}[/bold]")
    console.print(f"JSON: [bold]{json_path}[/bold]")
    console.print(f"Events: [bold]{len(unique_dates)}[/bold]\n")
