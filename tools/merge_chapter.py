#!/usr/bin/env python3
"""
Merge Chapter — Merges extraction output into all 6 game databases.

Reads a structured extraction JSON (produced by Claude Code agents) and merges
the extracted data into events.json, characters.json, locations.json,
roll_history.json, factions.json, and laws.json.

Operations:
  1. Load current database state + build_state.json
  2. Read extraction JSON for the specified chapter
  3. Assign event IDs (evt_{year}_{seq}) using global sequence counter
  4. Create/update characters (alias resolution via known_aliases.json)
  5. Create/update locations (add event_refs)
  6. Create/update factions (add members, event_refs)
  7. Append rolls with sequential IDs
  8. Update laws (link events, add effectiveness modifiers)
  9. Save all databases + update build_state.json

Usage:
  python3 tools/merge_chapter.py 1.01              # Merge single chapter
  python3 tools/merge_chapter.py 1.01 1.02 1.03    # Merge multiple (in order)
  python3 tools/merge_chapter.py --all              # Merge all unmerged extractions
  python3 tools/merge_chapter.py 1.01 --dry-run     # Preview without writing
  python3 tools/merge_chapter.py --validate         # Run validation only
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "resources" / "data"
TOOLS_DIR = PROJECT_ROOT / "tools"
EXTRACTIONS_DIR = TOOLS_DIR / "extractions"

# Database file paths
EVENTS_FILE = DATA_DIR / "events.json"
CHARACTERS_FILE = DATA_DIR / "characters.json"
LOCATIONS_FILE = DATA_DIR / "locations.json"
ROLL_HISTORY_FILE = DATA_DIR / "roll_history.json"
FACTIONS_FILE = DATA_DIR / "factions.json"
LAWS_FILE = DATA_DIR / "laws.json"
BUILD_STATE_FILE = TOOLS_DIR / "build_state.json"
ALIASES_FILE = TOOLS_DIR / "known_aliases.json"


# ---------------------------------------------------------------------------
# Database Loading / Saving
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict:
    """Load a JSON file, returning empty dict if not found."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    """Save data to JSON file with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_all_databases() -> dict:
    """Load all 6 databases + build state + aliases into a single dict."""
    return {
        "events": load_json(EVENTS_FILE),
        "characters": load_json(CHARACTERS_FILE),
        "locations": load_json(LOCATIONS_FILE),
        "roll_history": load_json(ROLL_HISTORY_FILE),
        "factions": load_json(FACTIONS_FILE),
        "laws": load_json(LAWS_FILE),
        "build_state": load_json(BUILD_STATE_FILE),
        "aliases": load_json(ALIASES_FILE),
    }


def save_all_databases(db: dict) -> None:
    """Save all 6 databases + build state."""
    # Update meta counts before saving
    db["events"].setdefault("meta", {})["total_events"] = len(db["events"].get("events", []))
    db["characters"].setdefault("meta", {})["total_characters"] = len(db["characters"].get("characters", []))
    db["locations"].setdefault("meta", {})["total_locations"] = len(db["locations"].get("locations", []))
    db["roll_history"].setdefault("meta", {})["total_rolls"] = len(db["roll_history"].get("rolls", []))
    db["factions"].setdefault("meta", {})["total_factions"] = len(db["factions"].get("factions", []))

    save_json(EVENTS_FILE, db["events"])
    save_json(CHARACTERS_FILE, db["characters"])
    save_json(LOCATIONS_FILE, db["locations"])
    save_json(ROLL_HISTORY_FILE, db["roll_history"])
    save_json(FACTIONS_FILE, db["factions"])
    save_json(LAWS_FILE, db["laws"])
    save_json(BUILD_STATE_FILE, db["build_state"])


# ---------------------------------------------------------------------------
# Alias Resolution
# ---------------------------------------------------------------------------

def build_alias_index(aliases: dict, characters: list) -> dict:
    """Build a reverse lookup: any alias → canonical_id.

    Combines known_aliases.json with existing character aliases.
    """
    index = {}

    # From known_aliases.json
    for canonical_id, info in aliases.items():
        index[canonical_id] = canonical_id
        for alias in info.get("aliases", []):
            index[alias] = canonical_id

    # From existing characters.json
    for char in characters:
        cid = char["id"]
        index[cid] = cid
        for alias in char.get("aliases", []):
            index[alias] = cid

    return index


def resolve_character_id(raw_id: str, alias_index: dict) -> str:
    """Resolve a character ID through the alias index."""
    return alias_index.get(raw_id, raw_id)


# ---------------------------------------------------------------------------
# Event Merging
# ---------------------------------------------------------------------------

def make_event_id(year: int, seq: int) -> str:
    """Generate event ID: evt_{year}_{5digit}."""
    return f"evt_{year}_{seq:05d}"


def lookup_existing_event_ids(db: dict, extraction: dict) -> dict:
    """Build event_id_map from already-existing events in events.json.

    Used in --enrichment-only mode where events were created by the
    assemble pipeline (assemble_chapter.py + build_events_db.py) and
    we only need to run character/location/faction/roll/law merging.

    Matches extraction events to existing events by chapter + order.
    Returns a mapping of extraction event indices to existing event IDs.
    """
    chapter_id = extraction["chapter"]
    events_db = db["events"]

    # Find all existing events for this chapter, preserving order
    chapter_events = [
        e for e in events_db.get("events", [])
        if e.get("chapter") == chapter_id
    ]

    id_map = {}
    extraction_events = extraction.get("events", [])

    if len(chapter_events) != len(extraction_events):
        print(f"  WARNING: Chapter {chapter_id} has {len(chapter_events)} events "
              f"in events.json but {len(extraction_events)} in extraction. "
              f"Matching by order (may be partial).")

    for i in range(min(len(chapter_events), len(extraction_events))):
        id_map[i] = chapter_events[i]["event_id"]

    return id_map


def merge_events(db: dict, extraction: dict) -> dict:
    """Merge extracted events into the events database.

    Returns a mapping of extraction event indices to assigned event IDs.
    """
    events_db = db["events"]
    events_db.setdefault("events", [])
    build_state = db["build_state"]

    chapter_id = extraction["chapter"]
    book = extraction.get("book", int(chapter_id.split(".")[0]))
    alias_index = build_alias_index(db["aliases"], db["characters"].get("characters", []))

    seq = build_state.get("next_event_seq", 1)
    id_map = {}  # index → event_id

    for i, evt in enumerate(extraction.get("events", [])):
        # Extract year from date
        date_str = evt.get("date", "")
        try:
            year = int(date_str[:4]) if date_str and len(date_str) >= 4 else 1430
        except ValueError:
            year = 1430

        event_id = make_event_id(year, seq)
        id_map[i] = event_id

        # Resolve character IDs through alias index
        characters = [resolve_character_id(c, alias_index) for c in evt.get("characters", [])]
        # Deduplicate while preserving order
        seen = set()
        unique_chars = []
        for c in characters:
            if c not in seen:
                seen.add(c)
                unique_chars.append(c)

        event_entry = {
            "event_id": event_id,
            "book": book,
            "chapter": chapter_id,
            "date": date_str,
            "end_date": evt.get("end_date"),
            "type": evt.get("type", "decision"),
            "summary": evt.get("summary", ""),
            "characters": unique_chars,
            "factions_affected": evt.get("factions_affected", []),
            "location": evt.get("location", ""),
            "tags": evt.get("tags", []),
            "status": evt.get("status", "resolved"),
            "exchanges": evt.get("exchanges", []),
            "roll": evt.get("roll"),
        }

        events_db["events"].append(event_entry)
        seq += 1

    build_state["next_event_seq"] = seq

    # Update date range in meta
    if events_db["events"]:
        dates = [e["date"] for e in events_db["events"] if e.get("date")]
        if dates:
            events_db["meta"]["date_range"] = f"{min(dates)} / {max(dates)}"

    return id_map


# ---------------------------------------------------------------------------
# Character Merging
# ---------------------------------------------------------------------------

def find_character(characters: list, char_id: str) -> dict | None:
    """Find a character by ID in the characters list."""
    for char in characters:
        if char["id"] == char_id:
            return char
    return None


def create_character_stub(char_data: dict) -> dict:
    """Create a new character entry from extraction data."""
    return {
        "id": char_data.get("id", ""),
        "name": char_data.get("name", ""),
        "aliases": char_data.get("aliases", [char_data.get("id", "")]),
        "title": char_data.get("title", ""),
        "born": char_data.get("born", "0000-00-00"),
        "status": char_data.get("status", ["active"]),
        "category": char_data.get("category", []),
        "location": char_data.get("location", ""),
        "current_task": char_data.get("current_task", ""),
        "personality": char_data.get("personality", []),
        "interests": char_data.get("interests", []),
        "speech_style": char_data.get("speech_style", ""),
        "core_characteristics": char_data.get("core_characteristics", ""),
        "rolled_traits": char_data.get("rolled_traits", []),
        "faction_ids": char_data.get("faction_ids", []),
        "event_refs": [],
        "appearance": char_data.get("appearance", {}),
        "portrait_prompt": "",
    }


def apply_character_update(char: dict, update: dict) -> None:
    """Apply a character update using merge rules.

    String fields: overwrite
    Array fields: apply add/remove operations
    rolled_traits: always append
    """
    fields = update.get("fields", {})

    for field, value in fields.items():
        if field == "rolled_traits":
            # Always append
            if isinstance(value, dict) and "append" in value:
                char.setdefault("rolled_traits", []).append(value["append"])
            elif isinstance(value, list):
                char.setdefault("rolled_traits", []).extend(value)

        elif field in ("personality", "interests", "status", "faction_ids", "category"):
            # Array fields: add/remove operations
            if isinstance(value, dict):
                current = char.get(field, [])
                for item in value.get("remove", []):
                    if item in current:
                        current.remove(item)
                for item in value.get("add", []):
                    if item not in current:
                        current.append(item)
                char[field] = current
            elif isinstance(value, list):
                # Direct replacement
                char[field] = value
            else:
                char[field] = value

        elif field in ("core_characteristics", "current_task", "title", "location",
                       "speech_style", "name", "born"):
            # String fields: overwrite
            char[field] = value

        elif field == "appearance":
            # Merge appearance subfields
            if isinstance(value, dict):
                char.setdefault("appearance", {}).update(value)

        elif field == "event_refs":
            # Always append
            if isinstance(value, list):
                for ref in value:
                    if ref not in char.get("event_refs", []):
                        char.setdefault("event_refs", []).append(ref)


def merge_characters(db: dict, extraction: dict, event_id_map: dict) -> None:
    """Merge new characters and character updates into the database."""
    chars_db = db["characters"]
    chars_db.setdefault("characters", [])
    alias_index = build_alias_index(db["aliases"], chars_db["characters"])

    # 1. Create new characters
    for new_char in extraction.get("new_characters", []):
        char_id = new_char.get("id", "")
        if not char_id:
            continue

        # Check if already exists (via alias)
        canonical = resolve_character_id(char_id, alias_index)
        existing = find_character(chars_db["characters"], canonical)

        if existing is None:
            # Also check by the raw ID
            existing = find_character(chars_db["characters"], char_id)

        if existing is None:
            # Truly new character — create stub
            # Pull category from known_aliases if available
            alias_info = db["aliases"].get(char_id, {})
            if alias_info and not new_char.get("category"):
                new_char["category"] = alias_info.get("category", [])
            if alias_info and not new_char.get("name"):
                new_char["name"] = alias_info.get("name", "")

            stub = create_character_stub(new_char)
            chars_db["characters"].append(stub)

            # Update alias index
            alias_index[char_id] = char_id
            for alias in stub.get("aliases", []):
                alias_index[alias] = char_id
        # If exists, skip creation (updates happen below)

    # 2. Apply character updates
    for update in extraction.get("character_updates", []):
        char_id = update.get("id", "")
        if not char_id:
            continue

        canonical = resolve_character_id(char_id, alias_index)
        char = find_character(chars_db["characters"], canonical)
        if char is None:
            char = find_character(chars_db["characters"], char_id)

        if char is not None:
            apply_character_update(char, update)

    # 3. Add event_refs to all characters mentioned in events
    for evt_idx, event_id in event_id_map.items():
        events_list = extraction.get("events", [])
        if evt_idx < len(events_list):
            for char_id in events_list[evt_idx].get("characters", []):
                canonical = resolve_character_id(char_id, alias_index)
                char = find_character(chars_db["characters"], canonical)
                if char is None:
                    char = find_character(chars_db["characters"], char_id)
                if char is not None:
                    if event_id not in char.get("event_refs", []):
                        char.setdefault("event_refs", []).append(event_id)


# ---------------------------------------------------------------------------
# Location Merging
# ---------------------------------------------------------------------------

def normalize_location_id(location_str: str) -> str:
    """Normalize a location string to a location_id.

    'Valladolid, Royal Palace' → 'valladolid'
    'Council of Basel' → 'council_of_basel'
    """
    # Take just the city/place part (before comma)
    city = location_str.split(",")[0].strip()
    # Lowercase, strip accents, replace spaces with underscores
    import unicodedata
    nfkd = unicodedata.normalize("NFKD", city)
    ascii_only = nfkd.encode("ASCII", "ignore").decode("ASCII")
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_only.lower()).strip("_")
    return slug


def find_location(locations: list, loc_id: str) -> dict | None:
    """Find a location by ID."""
    for loc in locations:
        if loc["location_id"] == loc_id:
            return loc
    return None


def merge_locations(db: dict, extraction: dict, event_id_map: dict) -> None:
    """Merge new locations and update event_refs."""
    locs_db = db["locations"]
    locs_db.setdefault("locations", [])
    chapter_id = extraction["chapter"]

    # 1. Create explicitly new locations from extraction
    for new_loc in extraction.get("new_locations", []):
        loc_id = new_loc.get("location_id", "")
        if not loc_id:
            loc_id = normalize_location_id(new_loc.get("name", ""))
        if not loc_id:
            continue

        existing = find_location(locs_db["locations"], loc_id)
        if existing is None:
            loc_entry = {
                "location_id": loc_id,
                "name": new_loc.get("name", ""),
                "region": new_loc.get("region", ""),
                "description": new_loc.get("description", ""),
                "sub_locations": new_loc.get("sub_locations", []),
                "event_refs": [],
                "first_mentioned_chapter": chapter_id,
                "image_prompt": "",
            }
            locs_db["locations"].append(loc_entry)

    # 2. Auto-create locations from events and update event_refs
    for evt_idx, event_id in event_id_map.items():
        events_list = extraction.get("events", [])
        if evt_idx < len(events_list):
            location_str = events_list[evt_idx].get("location", "")
            if not location_str:
                continue

            loc_id = normalize_location_id(location_str)
            if not loc_id:
                continue

            existing = find_location(locs_db["locations"], loc_id)
            if existing is None:
                # Auto-create minimal location entry
                city = location_str.split(",")[0].strip()
                loc_entry = {
                    "location_id": loc_id,
                    "name": city,
                    "region": "",
                    "description": "",
                    "sub_locations": [],
                    "event_refs": [event_id],
                    "first_mentioned_chapter": chapter_id,
                    "image_prompt": "",
                }
                locs_db["locations"].append(loc_entry)
            else:
                # Update event_refs and sub_locations
                if event_id not in existing["event_refs"]:
                    existing["event_refs"].append(event_id)

                # Extract sub-location if present
                parts = location_str.split(",", 1)
                if len(parts) > 1:
                    sub = parts[1].strip()
                    if sub and sub not in existing.get("sub_locations", []):
                        existing.setdefault("sub_locations", []).append(sub)


# ---------------------------------------------------------------------------
# Roll Merging
# ---------------------------------------------------------------------------

def merge_rolls(db: dict, extraction: dict, event_id_map: dict) -> None:
    """Merge roll data into roll_history.json."""
    rolls_db = db["roll_history"]
    rolls_db.setdefault("rolls", [])
    build_state = db["build_state"]

    roll_seq = build_state.get("next_roll_seq", 1)
    chapter_id = extraction["chapter"]
    book = extraction.get("book", int(chapter_id.split(".")[0]))

    for roll in extraction.get("rolls", []):
        roll_id = f"roll_{roll_seq:03d}"

        # Resolve event_id reference
        evt_idx = roll.get("event_index")
        event_id = event_id_map.get(evt_idx, roll.get("event_id", ""))

        roll_entry = {
            "roll_id": roll_id,
            "book": book,
            "chapter": chapter_id,
            "event_id": event_id,
            "title": roll.get("title", ""),
            "context": roll.get("context", ""),
            "roll_type": roll.get("roll_type", "chaos"),
            "date": roll.get("date", ""),
            "rolled": roll.get("rolled"),
            "outcome_range": roll.get("outcome_range", ""),
            "outcome_label": roll.get("outcome_label", ""),
            "outcome_detail": roll.get("outcome_detail", ""),
            "evaluation": roll.get("evaluation", ""),
            "success_factors": roll.get("success_factors", []),
            "failure_factors": roll.get("failure_factors", []),
            "character_effects": roll.get("character_effects", []),
            "ranges": roll.get("ranges", []),
        }

        rolls_db["rolls"].append(roll_entry)
        roll_seq += 1

    build_state["next_roll_seq"] = roll_seq


# ---------------------------------------------------------------------------
# Faction Merging
# ---------------------------------------------------------------------------

def find_faction(factions: list, faction_id: str) -> dict | None:
    """Find a faction by ID."""
    for f in factions:
        if f["faction_id"] == faction_id:
            return f
    return None


def merge_factions(db: dict, extraction: dict, event_id_map: dict) -> None:
    """Merge new factions and faction updates."""
    factions_db = db["factions"]
    factions_db.setdefault("factions", [])
    chapter_id = extraction["chapter"]

    # 1. Create new factions
    for new_faction in extraction.get("new_factions", []):
        fid = new_faction.get("faction_id", "")
        if not fid:
            continue

        existing = find_faction(factions_db["factions"], fid)
        if existing is None:
            faction_entry = {
                "faction_id": fid,
                "name": new_faction.get("name", ""),
                "type": new_faction.get("type", ""),
                "region": new_faction.get("region", ""),
                "description": new_faction.get("description", ""),
                "leader_id": new_faction.get("leader_id", ""),
                "member_ids": new_faction.get("member_ids", []),
                "event_refs": [],
                "first_mentioned_chapter": chapter_id,
            }
            factions_db["factions"].append(faction_entry)

    # 2. Apply faction updates
    for update in extraction.get("faction_updates", []):
        fid = update.get("faction_id", "")
        if not fid:
            continue

        faction = find_faction(factions_db["factions"], fid)
        if faction is None:
            continue

        # Add new members
        for member_id in update.get("add_members", []):
            if member_id not in faction.get("member_ids", []):
                faction.setdefault("member_ids", []).append(member_id)

        # Remove members
        for member_id in update.get("remove_members", []):
            if member_id in faction.get("member_ids", []):
                faction["member_ids"].remove(member_id)

        # Update description if provided
        if "description" in update:
            faction["description"] = update["description"]

        # Update leader if provided
        if "leader_id" in update:
            faction["leader_id"] = update["leader_id"]

    # 3. Add event_refs to factions mentioned in events
    for evt_idx, event_id in event_id_map.items():
        events_list = extraction.get("events", [])
        if evt_idx < len(events_list):
            for fid in events_list[evt_idx].get("factions_affected", []):
                faction = find_faction(factions_db["factions"], fid)
                if faction is not None:
                    if event_id not in faction.get("event_refs", []):
                        faction.setdefault("event_refs", []).append(event_id)


# ---------------------------------------------------------------------------
# Law Merging
# ---------------------------------------------------------------------------

def merge_laws(db: dict, extraction: dict, event_id_map: dict) -> None:
    """Update laws with event linkages from extraction."""
    laws_db = db["laws"]
    laws_db.setdefault("laws", [])

    for law_ref in extraction.get("law_references", []):
        action = law_ref.get("action", "")  # "enacted", "referenced", "amended", "repealed"
        law_id = law_ref.get("law_id", "")
        evt_idx = law_ref.get("event_index")
        event_id = event_id_map.get(evt_idx, law_ref.get("event_id", ""))

        if not law_id:
            continue

        # Find the law
        law = None
        for l in laws_db["laws"]:
            if l["law_id"] == law_id:
                law = l
                break

        if law is None:
            # Law not found — might be a new law to create
            if action == "enacted" and "new_law" in law_ref:
                new_law = law_ref["new_law"]
                new_law["origin_event_id"] = event_id
                laws_db["laws"].append(new_law)
            continue

        # Update existing law
        if action == "enacted" and law.get("origin_event_id") == "_pending_event_linkage":
            law["origin_event_id"] = event_id

        elif action == "referenced":
            law.setdefault("related_events", []).append({
                "event_id": event_id,
                "date": law_ref.get("date", ""),
                "relationship": "referenced",
                "summary": law_ref.get("summary", ""),
            })

        elif action == "amended":
            law.setdefault("effectiveness_modifiers", []).append({
                "event_id": event_id,
                "date": law_ref.get("date", ""),
                "type": "decree",
                "summary": law_ref.get("summary", ""),
            })

        elif action == "repealed":
            law["status"] = "repealed"
            law["repeal"] = {
                "date": law_ref.get("date", ""),
                "event_id": event_id,
                "reason": law_ref.get("summary", ""),
            }


# ---------------------------------------------------------------------------
# Main Merge Pipeline
# ---------------------------------------------------------------------------

def merge_chapter(chapter_id: str, dry_run: bool = False,
                   enrichment_only: bool = False) -> dict:
    """Merge a single chapter's extraction into all databases.

    Args:
        chapter_id: Chapter identifier (e.g., "1.01", "2.15")
        dry_run: If True, preview without writing files
        enrichment_only: If True, skip event creation and use existing
            event IDs from events.json. Use this when events were already
            created by the assemble pipeline (assemble_chapter.py +
            build_events_db.py) and you only need to enrich characters,
            locations, factions, rolls, and laws.

    Returns a stats dict with counts of created/updated entities.
    """
    extraction_path = EXTRACTIONS_DIR / f"chapter_{chapter_id}_extracted.json"
    if not extraction_path.exists():
        raise FileNotFoundError(f"Extraction not found: {extraction_path}")

    extraction = load_json(extraction_path)
    db = load_all_databases()

    # Check if already processed
    processed = db["build_state"].get("chapters_processed", {})
    if chapter_id in processed:
        print(f"  WARNING: Chapter {chapter_id} already merged. Skipping.")
        print(f"           (Processed at {processed[chapter_id].get('timestamp', '?')})")
        return {"skipped": True}

    # Get event ID mapping
    if enrichment_only:
        event_id_map = lookup_existing_event_ids(db, extraction)
        if not event_id_map:
            print(f"  WARNING: No existing events found for chapter {chapter_id} "
                  f"in events.json. Enrichment will proceed without event linkage.")
    else:
        event_id_map = merge_events(db, extraction)

    # Merge enrichment data
    merge_characters(db, extraction, event_id_map)
    merge_locations(db, extraction, event_id_map)
    merge_rolls(db, extraction, event_id_map)
    merge_factions(db, extraction, event_id_map)
    merge_laws(db, extraction, event_id_map)

    # Build stats
    mode_label = "enrichment_only" if enrichment_only else "full"
    stats = {
        "mode": mode_label,
        "events": len(extraction.get("events", [])),
        "events_created": 0 if enrichment_only else len(extraction.get("events", [])),
        "events_linked": len(event_id_map),
        "new_characters": len(extraction.get("new_characters", [])),
        "character_updates": len(extraction.get("character_updates", [])),
        "new_locations": len(extraction.get("new_locations", [])),
        "rolls": len(extraction.get("rolls", [])),
        "new_factions": len(extraction.get("new_factions", [])),
        "faction_updates": len(extraction.get("faction_updates", [])),
        "law_references": len(extraction.get("law_references", [])),
        "timestamp": datetime.now().isoformat(),
    }

    # Update build state
    db["build_state"]["last_completed_chapter"] = chapter_id
    db["build_state"].setdefault("chapters_processed", {})[chapter_id] = stats

    if not dry_run:
        save_all_databases(db)

    return stats


def discover_unmerged_extractions(db: dict) -> list[str]:
    """Find extraction files that haven't been merged yet."""
    processed = db.get("build_state", {}).get("chapters_processed", {})
    unmerged = []

    for path in sorted(EXTRACTIONS_DIR.glob("chapter_*_extracted.json")):
        match = re.search(r"chapter_(.+?)_extracted\.json", path.name)
        if match:
            chapter_id = match.group(1)
            if chapter_id not in processed:
                unmerged.append(chapter_id)

    # Sort by book then chapter
    unmerged.sort(key=lambda c: (int(c.split(".")[0]), int(c.split(".")[1])))
    return unmerged


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_chapter(chapter_id: str) -> tuple[list, list]:
    """Run per-chapter validation checks. Returns (errors, warnings)."""
    db = load_all_databases()
    errors = []
    warnings = []

    events = db["events"].get("events", [])
    characters = db["characters"].get("characters", [])
    locations = db["locations"].get("locations", [])
    rolls = db["roll_history"].get("rolls", [])

    # Filter events for this chapter
    chapter_events = [e for e in events if e.get("chapter") == chapter_id]

    if not chapter_events:
        warnings.append(f"No events found for chapter {chapter_id}")
        return errors, warnings

    # Build lookup sets
    char_ids = {c["id"] for c in characters}
    loc_ids = {l["location_id"] for l in locations}
    event_ids = {e["event_id"] for e in events}

    # 1. Event ID uniqueness
    seen_ids = set()
    for evt in chapter_events:
        if evt["event_id"] in seen_ids:
            errors.append(f"Duplicate event ID: {evt['event_id']}")
        seen_ids.add(evt["event_id"])

    # 2. Date monotonicity within chapter
    dates = [e["date"] for e in chapter_events if e.get("date")]
    for i in range(1, len(dates)):
        if dates[i] < dates[i - 1]:
            warnings.append(f"Date regression: {dates[i-1]} → {dates[i]}")

    # 3. Character reference integrity
    for evt in chapter_events:
        for cid in evt.get("characters", []):
            if cid not in char_ids:
                errors.append(f"Event {evt['event_id']} references unknown character: {cid}")

    # 4. Location consistency
    for evt in chapter_events:
        loc = evt.get("location", "")
        if not loc:
            warnings.append(f"Event {evt['event_id']} has no location")
        else:
            loc_id = normalize_location_id(loc)
            if loc_id and loc_id not in loc_ids:
                warnings.append(f"Event {evt['event_id']} location '{loc}' not in locations.json")

    # 5. Summary and exchange quality
    for evt in chapter_events:
        if not evt.get("summary"):
            errors.append(f"Event {evt['event_id']} has no summary")
        if not evt.get("exchanges"):
            warnings.append(f"Event {evt['event_id']} has no exchanges")

    # 6. Roll integrity
    chapter_rolls = [r for r in rolls if r.get("chapter") == chapter_id]
    for roll in chapter_rolls:
        if roll.get("event_id") and roll["event_id"] not in event_ids:
            errors.append(f"Roll {roll['roll_id']} references unknown event: {roll['event_id']}")

    return errors, warnings


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Merge extraction output into databases")
    parser.add_argument("chapters", nargs="*", help="Chapter IDs to merge (e.g., 1.01 2.15)")
    parser.add_argument("--all", action="store_true", help="Merge all unmerged extractions")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--validate", action="store_true", help="Run validation only")
    parser.add_argument("--enrichment-only", action="store_true",
                        help="Skip event creation; use existing events from events.json. "
                             "Use when events were already built by the assemble pipeline.")
    args = parser.parse_args()

    if args.validate:
        # Run validation on all processed chapters
        db = load_all_databases()
        processed = db.get("build_state", {}).get("chapters_processed", {})
        if not processed:
            print("No chapters have been processed yet.")
            sys.exit(0)

        total_errors = 0
        total_warnings = 0
        for chapter_id in sorted(processed.keys(), key=lambda c: (int(c.split(".")[0]), int(c.split(".")[1]))):
            errors, warnings = validate_chapter(chapter_id)
            total_errors += len(errors)
            total_warnings += len(warnings)
            status = "OK" if not errors else f"{len(errors)} errors"
            if warnings:
                status += f", {len(warnings)} warnings"
            print(f"  {chapter_id}: {status}")
            for e in errors:
                print(f"    ERROR: {e}")
            for w in warnings[:3]:  # Limit warnings shown
                print(f"    WARN:  {w}")
            if len(warnings) > 3:
                print(f"    ... and {len(warnings) - 3} more warnings")

        print(f"\nTotal: {total_errors} errors, {total_warnings} warnings across {len(processed)} chapters")
        sys.exit(1 if total_errors > 0 else 0)

    if args.all:
        db = load_all_databases()
        chapter_ids = discover_unmerged_extractions(db)
        if not chapter_ids:
            print("No unmerged extractions found.")
            sys.exit(0)
    elif args.chapters:
        chapter_ids = args.chapters
    else:
        parser.print_help()
        sys.exit(1)

    print(f"Merging {len(chapter_ids)} chapter(s)...\n")

    for chapter_id in chapter_ids:
        try:
            stats = merge_chapter(chapter_id, dry_run=args.dry_run,
                                  enrichment_only=args.enrichment_only)

            if stats.get("skipped"):
                continue

            mode_prefix = ""
            if args.dry_run:
                mode_prefix = "[DRY RUN] "
            if args.enrichment_only:
                mode_prefix += "[ENRICH] "
            print(f"  {mode_prefix}{chapter_id}: "
                  f"{stats.get('events_linked', stats['events'])} events linked, "
                  f"{stats['new_characters']} new chars, "
                  f"{stats['character_updates']} char updates, "
                  f"{stats['rolls']} rolls, "
                  f"{stats['new_locations']} new locs, "
                  f"{stats['new_factions']} new factions, "
                  f"{stats['law_references']} law refs")

            # Run validation after merge
            if not args.dry_run:
                errors, warnings = validate_chapter(chapter_id)
                if errors:
                    print(f"    VALIDATION: {len(errors)} errors!")
                    for e in errors:
                        print(f"      ERROR: {e}")
                if warnings:
                    print(f"    VALIDATION: {len(warnings)} warnings")

        except FileNotFoundError as e:
            print(f"  {chapter_id}: ERROR - {e}")
        except Exception as e:
            print(f"  {chapter_id}: ERROR - {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    # Print database totals
    if not args.dry_run:
        db = load_all_databases()
        print(f"\nDatabase totals:")
        print(f"  Events:     {len(db['events'].get('events', []))}")
        print(f"  Characters: {len(db['characters'].get('characters', []))}")
        print(f"  Locations:  {len(db['locations'].get('locations', []))}")
        print(f"  Rolls:      {len(db['roll_history'].get('rolls', []))}")
        print(f"  Factions:   {len(db['factions'].get('factions', []))}")
        print(f"  Laws:       {len(db['laws'].get('laws', []))}")


if __name__ == "__main__":
    main()
