# Prufrock

**Your life. Your voice. Your book.**

Transform boxes of physical artifacts — letters, journals, photos, negatives, home videos — into searchable digital archives, memoir scaffolds, and AI writing companions.

Named after T.S. Eliot's *The Love Song of J. Alfred Prufrock*.

## What It Does

1. **Intake** — Inventory, categorize, and process incoming materials
2. **Transcribe** — OCR handwritten pages using Claude Vision (letters, margins, journals)
3. **Faces** — Detect and cluster faces across all photos for identification
4. **Timeline** — Extract dates from transcriptions and EXIF data, build chronology
5. **Assemble** — Merge everything into a client-ready deliverable package

## Install

```bash
pip install -e .
```

For facial recognition:
```bash
pip install face-recognition  # requires dlib
```

## Usage

```bash
# 1. Process incoming materials
prufrock intake ./client-box/

# 2. Transcribe handwritten pages
prufrock transcribe ./client-box/scanned-pages/ \
  --context "Family: John (father), Pat (mother), Rob, Thomas, Bill, Kathleen. Location: Warwick, NY."

# 3. Cluster faces across photos
prufrock faces ./client-box/photos/

# 4. Build timeline from all sources
prufrock timeline ./client-box/

# 5. Assemble final deliverable
prufrock assemble ./client-box/ --client-name "The Chuvala Family"
```

## Pipeline

```
Physical Box
    ↓
[intake] → Inventory, resize, categorize
    ↓
[transcribe] → Claude Vision OCR → tagged markdown
    ↓
[faces] → DeepFace clustering → ID worksheet
    ↓
[timeline] → Date extraction → chronology
    ↓
[assemble] → Merged deliverable package
    ↓
Client Archive + Memoir Scaffold
```

## Service Tiers

| Tier | Deliverable |
|------|------------|
| **Archive** | Digitized, tagged, cataloged, searchable, timeline |
| **Story** | Archive + thread analysis + memoir scaffold + walkthrough |
| **Companion** | Story + custom AI spec with client voice profile |

## Model backend

Prufrock's model calls (`transcribe`, `voice`, thread analysis in `assemble`) go through one helper, `prufrock/llm.py`.

- **Default: `PRUFROCK_BACKEND=fleet`.** Requests go through `prufrock/fleet_bridge.ts` (needs `bun`) to a PAI install's `Inference.ts`, which runs on a Claude subscription, not an API key. It looks for Inference.ts at `$PRUFROCK_INFERENCE`, then `$PAI_DIR/TOOLS/Inference.ts`, then `$HOME/.claude/PAI/TOOLS/Inference.ts`.
- **`PRUFROCK_BACKEND=api`** uses the Anthropic API directly. Install with `pip install -e ".[api]"` and set `ANTHROPIC_API_KEY`. It's never used unless you set it.

The fleet backend reads images through Claude Code's Read tool: JPEG, PNG, GIF and WebP. Convert TIFF or BMP scans first.

## Requirements

- Python 3.10+
- `bun` and a PAI install (default fleet backend), or an Anthropic API key with `PRUFROCK_BACKEND=api`
- dlib + face_recognition (for facial clustering)

## License

MIT

---

*"Do I dare disturb the universe?"*

---

## Northwoods Sentinel Labs

Part of the [Northwoods Sentinel Labs](https://northwoodssentinel.com) ecosystem — open-source tools for human-centered AI.

[Blog](https://northwoodssentinel.com) · [Substack](https://substack.com/@chewvala) · [GitHub](https://github.com/NorthwoodsSentinel)
