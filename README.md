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
export ANTHROPIC_API_KEY=sk-...
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

## Requirements

- Python 3.10+
- Anthropic API key (for transcription)
- dlib + face_recognition (for facial clustering)

## License

MIT

---

*Built by [Northwoods Sentinel Labs](https://northwoodssentinel.com)*

*"Do I dare disturb the universe?"*
