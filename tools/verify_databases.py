#!/usr/bin/env python3
"""
Verify Databases — Validates all game databases for consistency and integrity.

Checks:
  Per-chapter: event ID uniqueness, date monotonicity, character refs, location refs,
               roll linkage, summary quality
  Cross-chapter: alias consistency, chronological order, faction membership,
                 law linkage
  Comparison: new data vs archived v1 data (for Book 2 chapters 1-28)
  Review mode: shows raw chapter content alongside extracted events

Usage:
  python3 tools/verify_databases.py                     # Full validation
  python3 tools/verify_databases.py --chapter 1.01       # Single chapter
  python3 tools/verify_databases.py --review 1.01        # Review mode
  python3 tools/verify_databases.py --compare            # Compare vs v1 data
  python3 tools/verify_databases.py --stats              # Database statistics
"""

import json
import re
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "resources" / "data"
TOOLS_DIR = PROJECT_ROOT / "tools"
ARCHIVE_DIR = PROJECT_ROOT / "archive" / "v1_data"
EXTRACTIONS_DIR = TOOLS_DIR / "extractions"
PREPROCESSED_DIR = TOOLS_DIR / "preprocessed"

# Import normalize_location_id from merge_chapter
sys.path.insert(0, str(TOOLS_DIR))
try:
    from merge_chapter import normalize_location_id
except ImportError:
    def normalize_location_id(s):
        import unicodedata
        city = s.split(",")[0].strip()
        nfkd = unicodedata.normalize("NFKD", city)
        ascii_only = nfkd.encode("ASCII", "ignore").decode("ASCII")
        return re.sub(r"[^a-z0-9]+", "_", ascii_only.lower()).strip("_")


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Per-Chapter Validation
# ---------------------------------------------------------------------------

def validate_chapter(chapter_id: str, events: list, characters: list,
                     locations: list, rolls: list) -> tuple[list, list]:
    """Validate a single chapter's data. Returns (errors, warnings)."""
    errors = []
    warnings = []

    chapter_events = [e for e in events if e.get("chapter") == chapter_id]
    if not chapter_events:
        warnings.append(f"No events for chapter {chapter_id}")
        return errors, warnings

    char_ids = {c["id"] for c in characters}
    loc_ids = {l["location_id"] for l in locations}
    event_ids = {e["event_id"] for e in events}

    # 1. Event ID uniqueness
    seen = set()
    for evt in chapter_events:
        eid = evt["event_id"]
        if eid in seen:
            errors.append(f"Duplicate event ID: {eid}")
        seen.add(eid)

    # 2. Date monotonicity
    dates = [e["date"] for e in chapter_events if e.get("date")]
    for i in range(1, len(dates)):
        if dates[i] < dates[i - 1]:
            warnings.append(f"Date regression in {chapter_events[i]['event_id']}: {dates[i-1]} → {dates[i]}")

    # 3. Character refs exist
    for evt in chapter_events:
        for cid in evt.get("characters", []):
            if cid not in char_ids and cid != "narrator":
                errors.append(f"{evt['event_id']}: unknown character '{cid}'")

    # 4. Location refs
    for evt in chapter_events:
        loc = evt.get("location", "")
        if not loc:
            warnings.append(f"{evt['event_id']}: no location")

    # 5. Summary quality
    for evt in chapter_events:
        if not evt.get("summary"):
            errors.append(f"{evt['event_id']}: no summary")
        if not evt.get("exchanges"):
            warnings.append(f"{evt['event_id']}: no exchanges")

    # 6. Roll linkage
    chapter_rolls = [r for r in rolls if r.get("chapter") == chapter_id]
    for roll in chapter_rolls:
        if roll.get("event_id") and roll["event_id"] not in event_ids:
            errors.append(f"Roll {roll['roll_id']}: unknown event {roll['event_id']}")

    return errors, warnings


# ---------------------------------------------------------------------------
# Cross-Chapter Validation
# ---------------------------------------------------------------------------

def validate_cross_chapter(events: list, characters: list, locations: list,
                           rolls: list, factions: list, laws: list) -> tuple[list, list]:
    """Validate cross-chapter consistency. Returns (errors, warnings)."""
    errors = []
    warnings = []

    event_ids = {e["event_id"] for e in events}
    char_ids = {c["id"] for c in characters}

    # 1. Alias uniqueness: no alias should map to two different canonical IDs
    alias_to_canonical = {}
    for char in characters:
        for alias in char.get("aliases", []):
            if alias in alias_to_canonical and alias_to_canonical[alias] != char["id"]:
                errors.append(f"Alias '{alias}' maps to both '{alias_to_canonical[alias]}' and '{char['id']}'")
            alias_to_canonical[alias] = char["id"]

    # 2. Global event ID uniqueness
    seen_ids = set()
    for evt in events:
        if evt["event_id"] in seen_ids:
            errors.append(f"Globally duplicate event ID: {evt['event_id']}")
        seen_ids.add(evt["event_id"])

    # 3. Event chronology (broadly monotonic within each book)
    for book in [1, 2]:
        book_events = [e for e in events if e.get("book") == book and e.get("date")]
        dates = [e["date"] for e in book_events]
        regressions = 0
        for i in range(1, len(dates)):
            if dates[i] < dates[i - 1]:
                regressions += 1
        if regressions > len(dates) * 0.1:  # More than 10% regressions
            warnings.append(f"Book {book}: {regressions} date regressions in {len(dates)} events")

    # 4. Faction member integrity
    for faction in factions:
        for member_id in faction.get("member_ids", []):
            if member_id not in char_ids:
                warnings.append(f"Faction '{faction['faction_id']}': unknown member '{member_id}'")

    # 5. Law event linkage
    for law in laws:
        origin = law.get("origin_event_id", "")
        if origin and origin != "_pending_event_linkage" and origin not in event_ids:
            warnings.append(f"Law '{law['law_id']}': unknown origin event '{origin}'")

    # 6. Character event_refs integrity
    orphan_refs = 0
    for char in characters:
        for ref in char.get("event_refs", []):
            if ref not in event_ids:
                orphan_refs += 1
    if orphan_refs > 0:
        warnings.append(f"{orphan_refs} orphan event_refs in characters (reference nonexistent events)")

    return errors, warnings


# ---------------------------------------------------------------------------
# Comparison with v1 Data
# ---------------------------------------------------------------------------

def compare_with_v1() -> list[str]:
    """Compare new data with archived v1 data for Book 2 chapters 1-28."""
    notes = []

    v1_events_path = ARCHIVE_DIR / "starter_events.json"
    if not v1_events_path.exists():
        notes.append("No v1 starter_events.json found for comparison")
        return notes

    v1_data = load_json(v1_events_path)
    new_data = load_json(DATA_DIR / "events.json")

    v1_events = v1_data.get("events", [])
    new_events = new_data.get("events", [])

    # Count events per chapter in both
    v1_by_chapter = {}
    for evt in v1_events:
        ch = evt.get("sub_chapter", evt.get("chapter", ""))
        v1_by_chapter[str(ch)] = v1_by_chapter.get(str(ch), 0) + 1

    new_by_chapter = {}
    for evt in new_events:
        ch = evt.get("chapter", "")
        new_by_chapter[ch] = new_by_chapter.get(ch, 0) + 1

    notes.append(f"v1 total events: {len(v1_events)}")
    notes.append(f"v2 total events: {len(new_events)}")
    notes.append("")

    # Compare chapters that exist in both
    for ch_old in sorted(v1_by_chapter.keys()):
        # Map v1 chapter format to v2
        ch_new = f"2.{int(float(ch_old) * 100) // 100:02d}" if "." not in str(ch_old) else f"2.{ch_old.split('.')[-1].zfill(2)}"
        if ch_old.startswith("2."):
            ch_new = f"2.{ch_old.split('.')[1].zfill(2)}"
        else:
            ch_new = f"2.{str(ch_old).zfill(2)}"

        v1_count = v1_by_chapter.get(ch_old, 0)
        v2_count = new_by_chapter.get(ch_new, 0)

        if v2_count == 0:
            notes.append(f"  Ch {ch_old}: v1={v1_count}, v2=NOT PROCESSED")
        else:
            diff = v2_count - v1_count
            indicator = f"+{diff}" if diff > 0 else str(diff)
            notes.append(f"  Ch {ch_old} → {ch_new}: v1={v1_count}, v2={v2_count} ({indicator})")

    # Character comparison
    v1_chars_path = ARCHIVE_DIR / "characters.json"
    if v1_chars_path.exists():
        v1_chars = load_json(v1_chars_path).get("characters", [])
        new_chars = load_json(DATA_DIR / "characters.json").get("characters", [])
        v1_ids = {c["id"] for c in v1_chars}
        new_ids = {c["id"] for c in new_chars}

        missing = v1_ids - new_ids
        added = new_ids - v1_ids
        notes.append(f"\n  v1 characters: {len(v1_ids)}, v2 characters: {len(new_ids)}")
        if missing:
            notes.append(f"  Missing from v2: {', '.join(sorted(list(missing)[:10]))}")
            if len(missing) > 10:
                notes.append(f"    ... and {len(missing) - 10} more")
        if added:
            notes.append(f"  New in v2: {', '.join(sorted(list(added)[:10]))}")
            if len(added) > 10:
                notes.append(f"    ... and {len(added) - 10} more")

    return notes


# ---------------------------------------------------------------------------
# Review Mode
# ---------------------------------------------------------------------------

def review_chapter(chapter_id: str) -> None:
    """Display extracted data alongside preprocessed source for review."""
    # Load extraction
    extraction_path = EXTRACTIONS_DIR / f"chapter_{chapter_id}_extracted.json"
    if not extraction_path.exists():
        print(f"No extraction found for chapter {chapter_id}")
        return

    extraction = load_json(extraction_path)

    # Load preprocessed source (if available)
    preprocessed_path = PREPROCESSED_DIR / f"chapter_{chapter_id}_preprocessed.json"
    preprocessed = load_json(preprocessed_path) if preprocessed_path.exists() else None

    print(f"=" * 80)
    print(f"REVIEW: Chapter {chapter_id}")
    print(f"=" * 80)

    if preprocessed:
        print(f"\nSource: {preprocessed.get('source_file', '?')}")
        print(f"Raw messages: {preprocessed.get('total_raw_messages', '?')}")
        print(f"Clean messages: {preprocessed.get('total_clean_messages', '?')}")

    print(f"\n--- EVENTS ({len(extraction.get('events', []))}) ---")
    for i, evt in enumerate(extraction.get("events", [])):
        print(f"\n  Event {i+1}: [{evt.get('type', '?')}] {evt.get('date', '?')} @ {evt.get('location', '?')}")
        print(f"  Characters: {', '.join(evt.get('characters', []))}")
        print(f"  Summary: {evt.get('summary', '')[:200]}")
        exchanges = evt.get("exchanges", [])
        print(f"  Exchanges: {len(exchanges)}")
        if exchanges:
            first = exchanges[0]
            print(f"    First: [{first.get('speaker', '?')}] {first.get('text', '')[:100]}...")

    print(f"\n--- NEW CHARACTERS ({len(extraction.get('new_characters', []))}) ---")
    for char in extraction.get("new_characters", []):
        print(f"  {char.get('id', '?')}: {char.get('name', '?')} [{', '.join(char.get('category', []))}]")
        cc = char.get("core_characteristics", "")
        if cc:
            print(f"    Core: {cc[:120]}")

    print(f"\n--- CHARACTER UPDATES ({len(extraction.get('character_updates', []))}) ---")
    for update in extraction.get("character_updates", []):
        print(f"  {update.get('id', '?')}: {update.get('reason', '')[:100]}")

    print(f"\n--- NEW LOCATIONS ({len(extraction.get('new_locations', []))}) ---")
    for loc in extraction.get("new_locations", []):
        print(f"  {loc.get('location_id', '?')}: {loc.get('name', '?')} ({loc.get('region', '?')})")

    print(f"\n--- ROLLS ({len(extraction.get('rolls', []))}) ---")
    for roll in extraction.get("rolls", []):
        print(f"  {roll.get('title', '?')}: rolled {roll.get('rolled', '?')} → {roll.get('outcome_label', '?')}")

    print(f"\n--- NEW FACTIONS ({len(extraction.get('new_factions', []))}) ---")
    for faction in extraction.get("new_factions", []):
        print(f"  {faction.get('faction_id', '?')}: {faction.get('name', '?')} [{faction.get('type', '?')}]")

    print(f"\n--- LAW REFERENCES ({len(extraction.get('law_references', []))}) ---")
    for ref in extraction.get("law_references", []):
        print(f"  {ref.get('law_id', '?')}: {ref.get('action', '?')}")


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def print_statistics() -> None:
    """Print detailed database statistics."""
    events = load_json(DATA_DIR / "events.json").get("events", [])
    characters = load_json(DATA_DIR / "characters.json").get("characters", [])
    locations = load_json(DATA_DIR / "locations.json").get("locations", [])
    rolls = load_json(DATA_DIR / "roll_history.json").get("rolls", [])
    factions = load_json(DATA_DIR / "factions.json").get("factions", [])
    laws = load_json(DATA_DIR / "laws.json").get("laws", [])
    build_state = load_json(TOOLS_DIR / "build_state.json")

    print("DATABASE STATISTICS")
    print("=" * 60)
    print(f"  Events:       {len(events)}")
    print(f"  Characters:   {len(characters)}")
    print(f"  Locations:    {len(locations)}")
    print(f"  Rolls:        {len(rolls)}")
    print(f"  Factions:     {len(factions)}")
    print(f"  Laws:         {len(laws)}")

    processed = build_state.get("chapters_processed", {})
    print(f"\n  Chapters processed: {len(processed)}")
    print(f"  Last chapter:       {build_state.get('last_completed_chapter', 'none')}")
    print(f"  Next event seq:     {build_state.get('next_event_seq', 1)}")
    print(f"  Next roll seq:      {build_state.get('next_roll_seq', 1)}")

    if events:
        dates = sorted([e["date"] for e in events if e.get("date")])
        if dates:
            print(f"\n  Date range: {dates[0]} → {dates[-1]}")

        # Events per book
        book_counts = {}
        for e in events:
            b = e.get("book", "?")
            book_counts[b] = book_counts.get(b, 0) + 1
        for b in sorted(book_counts.keys()):
            print(f"  Book {b}: {book_counts[b]} events")

        # Event types
        type_counts = {}
        for e in events:
            t = e.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        print(f"\n  Event types:")
        for t in sorted(type_counts.keys(), key=lambda k: -type_counts[k]):
            print(f"    {t}: {type_counts[t]}")

    if characters:
        # Top characters by event count
        char_events = [(c["id"], len(c.get("event_refs", []))) for c in characters]
        char_events.sort(key=lambda x: -x[1])
        print(f"\n  Top 10 characters by events:")
        for cid, count in char_events[:10]:
            print(f"    {cid}: {count} events")

        # Characters by category
        cat_counts = {}
        for c in characters:
            for cat in c.get("category", []):
                cat_counts[cat] = cat_counts.get(cat, 0) + 1
        print(f"\n  Characters by category:")
        for cat in sorted(cat_counts.keys(), key=lambda k: -cat_counts[k]):
            print(f"    {cat}: {cat_counts[cat]}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Validate game databases")
    parser.add_argument("--chapter", type=str, help="Validate single chapter")
    parser.add_argument("--review", type=str, help="Review mode for chapter")
    parser.add_argument("--compare", action="store_true", help="Compare with v1 data")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    args = parser.parse_args()

    if args.review:
        review_chapter(args.review)
        return

    if args.compare:
        notes = compare_with_v1()
        print("COMPARISON: v2 vs v1 (archived) data")
        print("=" * 60)
        for note in notes:
            print(note)
        return

    if args.stats:
        print_statistics()
        return

    # Full validation
    events = load_json(DATA_DIR / "events.json").get("events", [])
    characters = load_json(DATA_DIR / "characters.json").get("characters", [])
    locations = load_json(DATA_DIR / "locations.json").get("locations", [])
    rolls = load_json(DATA_DIR / "roll_history.json").get("rolls", [])
    factions = load_json(DATA_DIR / "factions.json").get("factions", [])
    laws = load_json(DATA_DIR / "laws.json").get("laws", [])
    build_state = load_json(TOOLS_DIR / "build_state.json")

    processed = build_state.get("chapters_processed", {})

    if args.chapter:
        chapters_to_check = [args.chapter]
    elif processed:
        chapters_to_check = sorted(processed.keys(),
                                   key=lambda c: (int(c.split(".")[0]), int(c.split(".")[1])))
    else:
        print("No chapters processed yet. Nothing to validate.")
        return

    total_errors = 0
    total_warnings = 0

    print("PER-CHAPTER VALIDATION")
    print("=" * 60)

    for ch in chapters_to_check:
        errs, warns = validate_chapter(ch, events, characters, locations, rolls)
        total_errors += len(errs)
        total_warnings += len(warns)

        status = "OK" if not errs else f"{len(errs)} ERRORS"
        if warns:
            status += f", {len(warns)} warnings"
        print(f"  {ch}: {status}")

        for e in errs:
            print(f"    ERROR: {e}")
        for w in warns[:5]:
            print(f"    WARN:  {w}")
        if len(warns) > 5:
            print(f"    ... +{len(warns) - 5} more warnings")

    # Cross-chapter validation
    if len(chapters_to_check) > 1:
        print(f"\nCROSS-CHAPTER VALIDATION")
        print("=" * 60)
        errs, warns = validate_cross_chapter(events, characters, locations, rolls, factions, laws)
        total_errors += len(errs)
        total_warnings += len(warns)

        for e in errs:
            print(f"  ERROR: {e}")
        for w in warns:
            print(f"  WARN:  {w}")
        if not errs and not warns:
            print("  All cross-chapter checks passed.")

    print(f"\nTOTAL: {total_errors} errors, {total_warnings} warnings")
    sys.exit(1 if total_errors > 0 else 0)


if __name__ == "__main__":
    main()
