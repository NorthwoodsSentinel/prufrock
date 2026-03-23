"""Voice — extract voice profile from zoom recording or transcript."""
import json
import re
from pathlib import Path
from collections import Counter

from anthropic import Anthropic
from rich.console import Console

console = Console()

VOICE_ANALYSIS_PROMPT = """You are a linguistic analyst building a voice profile for a memoir writing AI companion.

Analyze this transcript of a person speaking naturally (from a zoom call or recorded conversation). Extract:

1. **Vocabulary patterns**
   - Words/phrases they use repeatedly
   - Domain-specific language (profession, hobbies, region)
   - Filler words and verbal tics
   - Characteristic exclamations or interjections

2. **Sentence structure**
   - Average sentence length tendency (short/punchy, long/flowing, mixed)
   - How they start sentences (do they lead with "So," "I mean," "Look," etc.)
   - Use of fragments vs. complete sentences
   - Rhetorical patterns (lists of three, questions then answers, etc.)

3. **Storytelling style**
   - How they introduce a story or memory
   - How they handle chronology (linear, jumping, circling back)
   - Use of dialogue vs. summary when recounting events
   - How they signal emotional weight (understatement, emphasis, silence)

4. **Emotional register**
   - How they express strong feelings (direct, deflected, humor, metaphor)
   - Self-deprecation patterns
   - How they talk about people they love vs. people who hurt them

5. **Anti-patterns** — things they would NEVER say
   - Vocabulary that would feel wrong in their voice
   - Sentence structures they avoid
   - Tones that don't match

Output as a structured JSON voice profile with these sections. Include specific examples from the transcript for each pattern.

This profile will be used to configure an AI writing companion that writes in this person's voice. Accuracy is critical — if the AI sounds wrong, the client will reject it."""


def transcribe_audio(audio_path: Path, output_dir: Path) -> Path | None:
    """Transcribe audio file using Whisper if available."""
    try:
        import subprocess
        transcript_path = output_dir / "zoom-transcript.txt"

        result = subprocess.run(
            ["whisper", str(audio_path), "--model", "base", "--output_format", "txt",
             "--output_dir", str(output_dir)],
            capture_output=True, text=True, timeout=600,
        )

        # Whisper outputs as filename.txt
        whisper_output = output_dir / (audio_path.stem + ".txt")
        if whisper_output.exists():
            whisper_output.rename(transcript_path)
            return transcript_path

        console.print(f"[yellow]Whisper output not found. stderr: {result.stderr[:200]}[/yellow]")
        return None
    except FileNotFoundError:
        console.print("[yellow]Whisper not installed. Install with: pip install openai-whisper[/yellow]")
        return None
    except Exception as e:
        console.print(f"[red]Transcription failed: {e}[/red]")
        return None


def analyze_voice(transcript: str, client_name: str) -> dict | None:
    """Use Claude to analyze transcript for voice patterns."""
    try:
        client = Anthropic()

        # Truncate if needed
        if len(transcript) > 80_000:
            transcript = transcript[:40_000] + "\n\n[...]\n\n" + transcript[-40_000:]

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=VOICE_ANALYSIS_PROMPT,
            messages=[{
                "role": "user",
                "content": f"Speaker: {client_name}\n\nTranscript:\n\n{transcript}",
            }],
        )

        text = response.content[0].text

        # Try to extract JSON from response
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            return json.loads(json_match.group())

        # If no JSON, return the raw analysis as structured dict
        return {"raw_analysis": text}
    except Exception as e:
        console.print(f"[red]Voice analysis failed: {e}[/red]")
        return None


def run_voice(source: Path, output: Path, client_name: str):
    """Extract voice profile from recording or transcript."""
    console.print(f"\n[bold]Prufrock Voice[/bold] — profiling {client_name}\n")

    output.mkdir(parents=True, exist_ok=True)

    # Determine input type
    audio_exts = {".mp3", ".wav", ".m4a", ".mp4", ".mov", ".ogg", ".flac", ".webm"}
    text_exts = {".txt", ".md", ".vtt", ".srt"}

    if source.is_file():
        if source.suffix.lower() in audio_exts:
            console.print(f"Audio file detected: {source.name}")
            console.print("Transcribing with Whisper...")
            transcript_path = transcribe_audio(source, output)
            if not transcript_path:
                return
            transcript = transcript_path.read_text()
        elif source.suffix.lower() in text_exts:
            console.print(f"Transcript file detected: {source.name}")
            transcript = source.read_text()
        else:
            console.print(f"[red]Unsupported file type: {source.suffix}[/red]")
            return
    elif source.is_dir():
        # Concatenate all text files in directory
        texts = []
        for f in sorted(source.rglob("*")):
            if f.suffix.lower() in text_exts:
                texts.append(f.read_text())
        if not texts:
            console.print("[yellow]No transcript files found in directory.[/yellow]")
            return
        transcript = "\n\n---\n\n".join(texts)
    else:
        console.print(f"[red]Source not found: {source}[/red]")
        return

    word_count = len(transcript.split())
    console.print(f"Transcript: {word_count:,} words\n")

    # Basic statistics
    sentences = re.split(r'[.!?]+', transcript)
    words_per_sentence = [len(s.split()) for s in sentences if s.strip()]
    avg_sentence_len = sum(words_per_sentence) / len(words_per_sentence) if words_per_sentence else 0

    # Word frequency
    words = re.findall(r'\b[a-z]+\b', transcript.lower())
    common_words = {"the", "a", "an", "is", "was", "are", "were", "be", "been",
                    "have", "has", "had", "do", "does", "did", "will", "would",
                    "could", "should", "may", "might", "to", "of", "in", "for",
                    "on", "with", "at", "by", "from", "and", "or", "but", "not",
                    "that", "this", "it", "i", "you", "he", "she", "we", "they",
                    "my", "your", "his", "her", "our", "their", "me", "him",
                    "us", "them", "so", "just", "like", "know", "think", "get",
                    "go", "can", "all", "about", "up", "out", "if", "what",
                    "when", "how", "which", "there", "then", "than", "very"}
    distinctive_words = Counter(w for w in words if w not in common_words and len(w) > 3)

    stats = {
        "total_words": word_count,
        "avg_sentence_length": round(avg_sentence_len, 1),
        "top_distinctive_words": distinctive_words.most_common(30),
    }

    # AI voice analysis
    console.print("Analyzing voice patterns with Claude...")
    voice_profile = analyze_voice(transcript, client_name)

    if voice_profile:
        voice_profile["statistics"] = stats
    else:
        voice_profile = {"statistics": stats, "note": "AI analysis unavailable"}

    # Write outputs
    profile_path = output / "voice-profile.json"
    profile_path.write_text(json.dumps(voice_profile, indent=2))

    console.print(f"\nVoice profile: [bold]{profile_path}[/bold]")
    console.print(f"Avg sentence length: [bold]{avg_sentence_len:.1f} words[/bold]")
    console.print(f"Top vocabulary: [bold]{', '.join(w for w, _ in distinctive_words.most_common(10))}[/bold]\n")
