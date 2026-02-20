#!/usr/bin/env python3
"""
Merge Extractions — Apply extraction data to all databases in chronological order.

Reads extraction files (tools/extractions/chapter_*.json) in chapter order
and applies their data to the main databases:
  - characters.json  ← new_characters + character_updates
  - locations.json    ← new_locations
  - roll_history.json ← rolls (match existing + add new)
  - factions.json     ← faction_updates
  - laws.json         ← law_references

Chronological order ensures the final state of each character/location/faction
reflects the latest chapter they appeared in.

Usage:
  python tools/merge_extractions.py              # Dry run (default)
  python tools/merge_extractions.py --apply      # Actually write changes
  python tools/merge_extractions.py --verbose     # Show per-chapter detail
"""

import json
import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "resources" / "data"
EXTRACTIONS_DIR = PROJECT_ROOT / "tools" / "extractions"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved {path.name}")


def get_sorted_extractions():
    """Get extraction files sorted by chapter order."""
    files = list(EXTRACTIONS_DIR.glob("chapter_*_extracted.json"))
    result = []
    for f in files:
        ch = f.stem.replace("chapter_", "").replace("_extracted", "")
        parts = ch.split(".")
        if len(parts) != 2:
            continue
        book, num = int(parts[0]), int(parts[1])
        result.append((book * 100 + num, ch, f))
    result.sort()
    return result


def build_event_index_map(events_data):
    """Build mapping: (chapter_id) -> [event_id, event_id, ...] in order."""
    chapter_events = defaultdict(list)
    for evt in events_data.get("events", []):
        ch = evt.get("chapter", "")
        chapter_events[ch].append(evt["event_id"])
    return chapter_events


def merge_characters(characters_db, extraction, chapter_id, stats):
    """Apply new_characters and character_updates to characters database."""
    char_lookup = {c["id"]: c for c in characters_db["characters"]}

    # 1. Add new characters
    for nc in extraction.get("new_characters", []):
        cid = nc.get("id", "")
        if not cid:
            continue
        if cid in char_lookup:
            # Character already exists — enrich with appearance/speech if missing
            existing = char_lookup[cid]
            if nc.get("appearance") and not existing.get("appearance"):
                existing["appearance"] = nc["appearance"]
                stats["chars_enriched"] += 1
            if nc.get("speech_style") and not existing.get("speech_style"):
                existing["speech_style"] = nc["speech_style"]
                stats["chars_enriched"] += 1
            if nc.get("personality") and not existing.get("personality"):
                existing["personality"] = nc["personality"]
                stats["chars_enriched"] += 1
            if nc.get("interests") and not existing.get("interests"):
                existing["interests"] = nc["interests"]
                stats["chars_enriched"] += 1
            if nc.get("core_characteristics") and not existing.get("core_characteristics"):
                existing["core_characteristics"] = nc["core_characteristics"]
                stats["chars_enriched"] += 1
            continue

        # Build new character entry
        new_char = {
            "id": cid,
            "name": nc.get("name", cid.replace("_", " ").title()),
            "aliases": nc.get("aliases", [cid]),
            "title": nc.get("title", ""),
            "born": nc.get("born", ""),
            "status": nc.get("status", ["active"]),
            "category": nc.get("category", []),
            "location": nc.get("location", ""),
            "current_task": nc.get("current_task", ""),
            "personality": nc.get("personality", []),
            "interests": nc.get("interests", []),
            "speech_style": nc.get("speech_style", ""),
            "core_characteristics": nc.get("core_characteristics", ""),
            "rolled_traits": nc.get("rolled_traits", []),
            "faction_ids": nc.get("faction_ids", []),
            "event_refs": [],
            "first_appearance_chapter": chapter_id,
        }
        if nc.get("appearance"):
            new_char["appearance"] = nc["appearance"]

        characters_db["characters"].append(new_char)
        char_lookup[cid] = new_char
        stats["chars_added"] += 1

    # 2. Apply character updates (chronological — later chapters overwrite)
    for cu in extraction.get("character_updates", []):
        cid = cu.get("id", "")
        if not cid or cid not in char_lookup:
            stats["chars_update_skipped"] += 1
            continue

        char = char_lookup[cid]

        # Update current_task
        task = cu.get("current_task") or cu.get("task")
        if task:
            char["current_task"] = task
            stats["chars_updated"] += 1

        # Update location
        loc = cu.get("location")
        if loc:
            char["location"] = loc

        # Update status
        status = cu.get("status")
        if status and isinstance(status, list):
            char["status"] = status


def merge_locations(locations_db, extraction, stats):
    """Apply new_locations to locations database."""
    loc_lookup = {l["location_id"]: l for l in locations_db["locations"]}

    for nl in extraction.get("new_locations", []):
        lid = nl.get("location_id", "")
        if not lid:
            continue

        if lid in loc_lookup:
            # Enrich existing location with description if missing
            existing = loc_lookup[lid]
            if nl.get("description") and not existing.get("description"):
                existing["description"] = nl["description"]
                stats["locs_enriched"] += 1
            if nl.get("sub_locations") and not existing.get("sub_locations"):
                existing["sub_locations"] = nl["sub_locations"]
                stats["locs_enriched"] += 1
            continue

        # Add new location
        new_loc = {
            "location_id": lid,
            "name": nl.get("name", lid.replace("_", " ").title()),
            "region": nl.get("region", ""),
            "description": nl.get("description", ""),
            "sub_locations": nl.get("sub_locations", []),
            "event_refs": [],
            "first_mentioned_chapter": "",
            "image_prompt": "",
        }
        locations_db["locations"].append(new_loc)
        loc_lookup[lid] = new_loc
        stats["locs_added"] += 1


def merge_rolls(rolls_db, extraction, chapter_id, chapter_event_ids, stats):
    """Match extraction rolls to existing roll_history entries and update detail fields."""
    book_str = chapter_id.split(".")[0]
    book = int(book_str)

    # Build lookup for existing rolls by (chapter, rolled, date)
    existing_by_key = defaultdict(list)
    for r in rolls_db["rolls"]:
        key = (r.get("chapter"), r.get("rolled"), r.get("date"))
        existing_by_key[key].append(r)

    # Find next roll_id
    max_id = 0
    for r in rolls_db["rolls"]:
        rid = r.get("roll_id", "")
        if rid.startswith("roll_"):
            try:
                num = int(rid.replace("roll_", ""))
                max_id = max(max_id, num)
            except ValueError:
                pass
    next_id = max_id + 1

    for ext_roll in extraction.get("rolls", []):
        rolled = ext_roll.get("rolled")
        date = ext_roll.get("date", "")
        event_index = ext_roll.get("event_index")

        # Try to resolve event_id from index
        event_id = ""
        if event_index is not None and chapter_event_ids:
            if 0 <= event_index < len(chapter_event_ids):
                event_id = chapter_event_ids[event_index]

        # Try to match existing roll
        key = (chapter_id, rolled, date)
        matches = existing_by_key.get(key, [])

        if matches:
            # Update the first match with detail fields
            existing = matches[0]
            updated = False

            if ext_roll.get("outcome_detail") and not existing.get("outcome_detail"):
                existing["outcome_detail"] = ext_roll["outcome_detail"]
                updated = True
            if ext_roll.get("evaluation") and not existing.get("evaluation"):
                existing["evaluation"] = ext_roll["evaluation"]
                updated = True
            if ext_roll.get("success_factors") and not existing.get("success_factors"):
                existing["success_factors"] = ext_roll["success_factors"]
                updated = True
            if ext_roll.get("failure_factors") and not existing.get("failure_factors"):
                existing["failure_factors"] = ext_roll["failure_factors"]
                updated = True
            if ext_roll.get("title") and not existing.get("title"):
                existing["title"] = ext_roll["title"]
                updated = True
            if ext_roll.get("context") and not existing.get("context"):
                existing["context"] = ext_roll["context"]
                updated = True
            if ext_roll.get("roll_type") and not existing.get("roll_type"):
                existing["roll_type"] = ext_roll["roll_type"]
                updated = True
            if ext_roll.get("outcome_range") and existing.get("outcome_range") in ("", None):
                existing["outcome_range"] = ext_roll["outcome_range"]
                updated = True
            if ext_roll.get("outcome_label") and not existing.get("outcome_label"):
                existing["outcome_label"] = ext_roll["outcome_label"]
                updated = True

            # Update event_id if we have one and existing doesn't
            if event_id and not existing.get("event_id"):
                existing["event_id"] = event_id

            if updated:
                stats["rolls_updated"] += 1
            else:
                stats["rolls_already_complete"] += 1

            # Remove from matches so next duplicate roll uses next match
            matches.pop(0)
        else:
            # New roll — add to database
            new_roll = {
                "roll_id": f"roll_{next_id:03d}",
                "book": book,
                "chapter": chapter_id,
                "event_id": event_id,
                "title": ext_roll.get("title", ""),
                "context": ext_roll.get("context", ""),
                "roll_type": ext_roll.get("roll_type", ""),
                "date": date,
                "rolled": rolled,
                "outcome_range": ext_roll.get("outcome_range", ""),
                "outcome_label": ext_roll.get("outcome_label", ""),
                "outcome_detail": ext_roll.get("outcome_detail", ""),
                "evaluation": ext_roll.get("evaluation", ""),
                "success_factors": ext_roll.get("success_factors", []),
                "failure_factors": ext_roll.get("failure_factors", []),
                "character_effects": ext_roll.get("character_effects", []),
                "ranges": ext_roll.get("ranges", []),
            }
            rolls_db["rolls"].append(new_roll)
            next_id += 1
            stats["rolls_added"] += 1


def merge_factions(factions_db, extraction, stats):
    """Apply faction_updates to factions database."""
    fac_lookup = {f["faction_id"]: f for f in factions_db["factions"]}

    for fu in extraction.get("faction_updates", []):
        fid = fu.get("faction_id", "")
        if not fid or fid not in fac_lookup:
            stats["factions_skipped"] += 1
            continue

        fac = fac_lookup[fid]
        if fu.get("description"):
            fac["description"] = fu["description"]
            stats["factions_updated"] += 1


def merge_laws(laws_db, extraction, chapter_event_ids, stats):
    """Apply law_references to laws database."""
    law_lookup = {l["law_id"]: l for l in laws_db["laws"]}

    for lr in extraction.get("law_references", []):
        lid = lr.get("law_id", "")
        if not lid:
            continue

        # Resolve event_id
        event_index = lr.get("event_index")
        event_id = ""
        if event_index is not None and chapter_event_ids:
            if 0 <= event_index < len(chapter_event_ids):
                event_id = chapter_event_ids[event_index]

        if lid in law_lookup:
            law = law_lookup[lid]
            # Add to related_events if not already there
            related = law.get("related_events", [])
            if event_id and event_id not in related:
                related.append(event_id)
                law["related_events"] = related
                stats["laws_linked"] += 1
        else:
            stats["laws_skipped"] += 1


def main():
    parser = argparse.ArgumentParser(description="Merge extraction data into databases")
    parser.add_argument("--apply", action="store_true",
                        help="Actually write changes (default is dry run)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show per-chapter detail")
    args = parser.parse_args()

    if not args.apply:
        print("=== DRY RUN (use --apply to write changes) ===\n")

    # Load all databases
    print("Loading databases...")
    characters_db = load_json(DATA_DIR / "characters.json")
    locations_db = load_json(DATA_DIR / "locations.json")
    rolls_db = load_json(DATA_DIR / "roll_history.json")
    factions_db = load_json(DATA_DIR / "factions.json")
    laws_db = load_json(DATA_DIR / "laws.json")
    events_db = load_json(DATA_DIR / "events.json")

    # Build event index map
    chapter_event_map = build_event_index_map(events_db)

    # Record initial counts
    initial = {
        "characters": len(characters_db["characters"]),
        "locations": len(locations_db["locations"]),
        "rolls": len(rolls_db["rolls"]),
        "factions": len(factions_db["factions"]),
        "laws": len(laws_db["laws"]),
    }

    print(f"  Characters: {initial['characters']}")
    print(f"  Locations:  {initial['locations']}")
    print(f"  Rolls:      {initial['rolls']}")
    print(f"  Factions:   {initial['factions']}")
    print(f"  Laws:       {initial['laws']}")

    # Get sorted extraction files
    extractions = get_sorted_extractions()
    print(f"\nProcessing {len(extractions)} extraction files in chronological order...\n")

    # Aggregate stats
    stats = {
        "chars_added": 0,
        "chars_updated": 0,
        "chars_enriched": 0,
        "chars_update_skipped": 0,
        "locs_added": 0,
        "locs_enriched": 0,
        "rolls_added": 0,
        "rolls_updated": 0,
        "rolls_already_complete": 0,
        "factions_updated": 0,
        "factions_skipped": 0,
        "laws_linked": 0,
        "laws_skipped": 0,
    }

    for _, chapter_id, fpath in extractions:
        extraction = load_json(fpath)
        chapter_event_ids = chapter_event_map.get(chapter_id, [])

        # Count what this chapter contributes
        before = dict(stats)

        merge_characters(characters_db, extraction, chapter_id, stats)
        merge_locations(locations_db, extraction, stats)
        merge_rolls(rolls_db, extraction, chapter_id, chapter_event_ids, stats)
        merge_factions(factions_db, extraction, stats)
        merge_laws(laws_db, extraction, chapter_event_ids, stats)

        if args.verbose:
            delta = {k: stats[k] - before[k] for k in stats}
            changes = []
            if delta["chars_added"]:
                changes.append(f"+{delta['chars_added']} chars")
            if delta["chars_updated"]:
                changes.append(f"~{delta['chars_updated']} char updates")
            if delta["locs_added"]:
                changes.append(f"+{delta['locs_added']} locs")
            if delta["rolls_added"]:
                changes.append(f"+{delta['rolls_added']} rolls")
            if delta["rolls_updated"]:
                changes.append(f"~{delta['rolls_updated']} roll details")
            if delta["factions_updated"]:
                changes.append(f"~{delta['factions_updated']} factions")
            if delta["laws_linked"]:
                changes.append(f"+{delta['laws_linked']} law links")
            summary = ", ".join(changes) if changes else "no changes"
            print(f"  {chapter_id}: {summary}")

    # Update meta counts
    characters_db["meta"]["total_characters"] = len(characters_db["characters"])
    locations_db["meta"]["total_locations"] = len(locations_db["locations"])
    rolls_db["meta"]["total_rolls"] = len(rolls_db["rolls"])
    factions_db["meta"]["total_factions"] = len(factions_db["factions"])

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Characters: {initial['characters']} → {len(characters_db['characters'])} "
          f"(+{stats['chars_added']} new, ~{stats['chars_updated']} updates, "
          f"+{stats['chars_enriched']} enrichments)")
    if stats["chars_update_skipped"]:
        print(f"  ({stats['chars_update_skipped']} updates skipped — character not in DB)")
    print(f"Locations:  {initial['locations']} → {len(locations_db['locations'])} "
          f"(+{stats['locs_added']} new, +{stats['locs_enriched']} enrichments)")
    print(f"Rolls:      {initial['rolls']} → {len(rolls_db['rolls'])} "
          f"(+{stats['rolls_added']} new, ~{stats['rolls_updated']} details filled, "
          f"{stats['rolls_already_complete']} already complete)")
    print(f"Factions:   ~{stats['factions_updated']} descriptions updated "
          f"({stats['factions_skipped']} skipped — faction not in DB)")
    print(f"Laws:       +{stats['laws_linked']} event links added "
          f"({stats['laws_skipped']} skipped — law not in DB)")
    print(f"{'='*60}")

    if args.apply:
        print("\nWriting databases...")
        save_json(DATA_DIR / "characters.json", characters_db)
        save_json(DATA_DIR / "locations.json", locations_db)
        save_json(DATA_DIR / "roll_history.json", rolls_db)
        save_json(DATA_DIR / "factions.json", factions_db)
        save_json(DATA_DIR / "laws.json", laws_db)
        print("\nDone! All databases updated.")
    else:
        print("\nDry run complete. Use --apply to write changes.")


if __name__ == "__main__":
    main()
