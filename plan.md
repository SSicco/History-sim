# Plan: Single Source of Truth for Events and Characters

## Problem Statement

Multiple versions of event and character data exist across the project. The game's
search engine (`context_agent.gd`) uses **stripped-down event summaries** when richer
data is available. Duplicate files create confusion about which data is canonical.

---

## Current State (What Exists)

### Events — 4 layers of the same data

| File | Contents | Loaded by game? |
|------|----------|-----------------|
| `resources/source_material/book2/chapter*.txt` (28 files) | Raw narrative text from play sessions | No |
| `chapters/chapter*.txt` (28 files) | **Near-duplicate** of source_material | No |
| `resources/data/chapter_02_*.json` (28 files) | Structured encounters: full exchanges, rolls, recaps, participants | No |
| `resources/data/all_chapters.json` | Consolidated copy of all 28 chapter JSONs | No |
| `resources/data/starter_events.json` | **Flat summaries only** — no exchanges, no rolls | **YES** (copied to campaign `events.json`) |

**Problem**: `build_events.py` reads the rich chapter JSONs but **throws away the exchanges
and roll data**, keeping only the recap as `summary`. The context agent then searches
this stripped-down version.

### Characters — 3 layers

| File | Contents | Loaded by game? |
|------|----------|-----------------|
| `CHARACTER_DATABASE.md` (root) | Markdown format, covers up to chapter 2.54 / Sept 1439 | No |
| `resources/data/character_enrichment.json` | Build input: 260 chars with appearance, born, personality | No (build input only) |
| `resources/data/characters.json` | **Generated output**: enrichment merged in, all 260 chars have appearance + birth dates | **YES** |

**Good news**: `characters.json` already has the enrichment merged. All 260 characters
have appearance objects (12 fields), birth dates, personality, interests, speech_style.
The build pipeline (`build_characters.py`) is working correctly.

**Gap**: `CHARACTER_DATABASE.md` references events through chapter 2.54, but the JSON
data only covers chapters 2.1–2.28. Characters introduced in chapters 29–54 are in
the markdown but NOT in the JSON files.

---

## Proposed Single Sources of Truth

### Events: `starter_events.json` — enriched with full encounter data

**Change**: Modify `build_events.py` to include the full exchange text and roll data
from chapter JSONs, not just the recap summary. The event schema becomes:

```json
{
  "event_id": "evt_1433_00001",
  "date": "1433-04-06",
  "chapter": 2,
  "sub_chapter": "2.1",
  "type": "military_action",
  "summary": "Juan II addresses his eight hundred crusaders...",
  "characters": ["juan_ii", "fernan_alonso_de_robles"],
  "factions_affected": [],
  "location": "Granada, Alhambra Plaza",
  "tags": [],
  "status": "resolved",
  "exchanges": [
    {"speaker": "narrator", "text": "The crusaders are assembled..."},
    {"speaker": "fernan_alonso_de_robles", "text": "Your Majesty. The men are ready..."}
  ],
  "roll": null
}
```

This makes `starter_events.json` the **complete, single source of truth** for all
event data. The context agent's search still works on summaries for scoring, but
the full text is available when needed.

### Characters: `characters.json` — already the best file

No schema change needed. This file already has appearance, birth dates, and all
enrichment data for 260 characters. It is the single source of truth.

The `character_enrichment.json` stays as the **build input** (same relationship as
chapter JSONs → starter_events.json).

---

## Script Changes

### 1. `tools/build_events.py` — include exchanges and rolls

Current behavior (lines 86–98) throws away exchanges. Change to also copy them:

```python
event = {
    "event_id": event_id,
    "date": enc.get("date", ""),
    "chapter": chapter_int,
    "sub_chapter": chapter_str,
    "type": enc.get("type", "decision"),
    "summary": enc.get("recap", ""),
    "characters": enc.get("participants", []),
    "factions_affected": [],
    "location": enc.get("location", ""),
    "tags": enc.get("tags", []),
    "status": "resolved",
    "exchanges": enc.get("exchanges", []),   # ← NEW
    "roll": enc.get("roll", None),           # ← NEW
}
```

Then rebuild: `python3 tools/build_events.py --write`

**Impact**: `starter_events.json` grows from ~520 KB to ~4 MB (same data as the
chapter JSONs but in the events schema). This is loaded once at campaign init, so
the size increase has no runtime cost.

### 2. `scripts/context_agent.gd` — no changes needed

The search engine scores events on `summary`, `characters`, `type`, and `date`.
Adding `exchanges` and `roll` fields doesn't break scoring. The extra fields are
simply passed through when events are included in sticky context.

### 3. No changes to `data_manager.gd` or `game_state_manager.gd`

Campaign init already copies the full `starter_events.json` object as-is.
The richer data flows through automatically.

---

## File Cleanup: Archive Plan

### Move to `archive/` directory (keep in repo but out of the way)

| File | Reason |
|------|--------|
| `chapters/` (entire directory, 28 .txt files) | Duplicate of `resources/source_material/book2/` |
| `resources/data/all_chapters.json` (3.8 MB) | Redundant — its data is now fully contained in `starter_events.json` |
| `CHARACTER_DATABASE.md` | Superseded by `characters.json` for chapters 2.1–2.28. Keep in archive as reference for chapters 2.29–2.54 until those are converted to JSON |
| `TASK_chapter_02_02.md` | Stale task file |

### Keep as-is (canonical build inputs — never loaded by game)

| File | Role |
|------|------|
| `resources/data/chapter_02_*.json` (28 files) | **Source of truth inputs** — `build_events.py` reads these |
| `resources/data/character_enrichment.json` | **Source of truth input** — `build_characters.py` reads this |
| `resources/source_material/book2/*.txt` (28 files) | **Original source** — raw session text the chapter JSONs were built from |

### Keep as-is (canonical game data — generated outputs loaded at runtime)

| File | Role |
|------|------|
| `resources/data/starter_events.json` | **Game events** — generated by `build_events.py`, loaded at runtime |
| `resources/data/characters.json` | **Game characters** — generated by `build_characters.py`, loaded at runtime |
| `resources/data/roll_tables.json` | Roll table data |

---

## CLAUDE.md Updates

- Remove reference to `game_data/` directory (doesn't exist)
- Document the canonical data files and build pipeline
- Note that `starter_events.json` and `characters.json` are generated — edit the
  source files and re-run build scripts, not the outputs directly

---

## Future Work (not part of this plan)

**Chapters 2.29–2.54**: These exist only in `CHARACTER_DATABASE.md` as narrative
references. The raw session text and chapter JSONs haven't been created yet.
When they are, re-running `build_events.py --write` and `build_characters.py --write`
will pick up the new events and characters automatically.

---

## Execution Summary

| Step | Action | Files touched |
|------|--------|---------------|
| 1 | Edit `build_events.py` to include `exchanges` and `roll` | `tools/build_events.py` |
| 2 | Rebuild events: `python3 tools/build_events.py --write` | `resources/data/starter_events.json` |
| 3 | Create `archive/` and move stale files there | `chapters/`, `all_chapters.json`, `CHARACTER_DATABASE.md`, `TASK_chapter_02_02.md` |
| 4 | Update CLAUDE.md with canonical data documentation | `CLAUDE.md` |
