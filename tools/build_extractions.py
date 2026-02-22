#!/usr/bin/env python3
"""
Build Extractions — Generates extraction files from event_defs + database state.

Reads event definition files (tools/event_defs/) and cross-references against
the current database state to produce extraction files suitable for
merge_chapter.py --enrichment-only.

Auto-detects:
  - New characters (IDs in events but not in characters.json)
  - New factions (IDs in events but not in factions.json)
  - Roll data (parsed from event summaries)
  - New locations (from event location strings)

Usage:
  python3 tools/build_extractions.py                    # All chapters with defs but no extraction
  python3 tools/build_extractions.py 1.23 1.24 1.25     # Specific chapters
  python3 tools/build_extractions.py --range 1.23 2.24   # Chapter range
  python3 tools/build_extractions.py --dry-run           # Preview without writing
  python3 tools/build_extractions.py --force             # Overwrite existing extractions
"""

import json
import re
import sys
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = PROJECT_ROOT / "tools"
DATA_DIR = PROJECT_ROOT / "resources" / "data"
DEFS_DIR = TOOLS_DIR / "event_defs"
EXTRACTIONS_DIR = TOOLS_DIR / "extractions"
PREPROCESSED_DIR = TOOLS_DIR / "preprocessed"

CHARACTERS_FILE = DATA_DIR / "characters.json"
FACTIONS_FILE = DATA_DIR / "factions.json"
LOCATIONS_FILE = DATA_DIR / "locations.json"
LAWS_FILE = DATA_DIR / "laws.json"
ALIASES_FILE = TOOLS_DIR / "known_aliases.json"


# ---------------------------------------------------------------------------
# Character name/category inference
# ---------------------------------------------------------------------------

# Patterns in character IDs that suggest categories
CATEGORY_PATTERNS = {
    r"^(pope|cardinal|bishop|archbishop|abbot|abbott|fray|friar|brother|padre|imam|sheikh|monk|prior|deacon|canon)": "clergy",
    r"^(captain|sergeant|corporal|admiral|commander|marshal)": "military",
    r"^(king|queen|prince|princess|infante|infanta|duke|duchess|count|countess|baron|marquis|don_|dona_)": "nobility",
    r"^(ambassador|envoy|legate|nuncio)": "diplomacy",
    r"(merchant|banker|trader)": "merchant",
}

# ID-to-name heuristic: special cases for common prefixes
TITLE_PREFIXES = {
    "pope": "Pope",
    "cardinal": "Cardinal",
    "bishop": "Bishop",
    "archbishop": "Archbishop",
    "abbott": "Abbot",
    "abbot": "Abbot",
    "fray": "Fray",
    "brother": "Brother",
    "captain": "Captain",
    "sergeant": "Sergeant",
    "corporal": "Corporal",
    "admiral": "Admiral",
    "don": "Don",
    "dona": "Doña",
    "sheikh": "Sheikh",
    "imam": "Imam",
    "baron": "Baron",
    "count": "Count",
    "duke": "Duke",
    "prince": "Prince",
    "princess": "Princess",
    "infante": "Infante",
    "infanta": "Infanta",
    "king": "King",
    "queen": "Queen",
}

# Known faction metadata
FACTION_METADATA = {
    "apostolic_camera": {"name": "Apostolic Camera", "type": "institutional", "region": "Rome"},
    "aragonese_crown": {"name": "Crown of Aragon", "type": "monarchy", "region": "Aragon"},
    "aragonese_faction": {"name": "Aragonese Faction", "type": "political", "region": "Castile"},
    "byzantine_court": {"name": "Byzantine Imperial Court", "type": "monarchy", "region": "Constantinople"},
    "byzantine_merchants": {"name": "Byzantine Merchants", "type": "commercial", "region": "Constantinople"},
    "byzantine_nobility": {"name": "Byzantine Nobility", "type": "nobility", "region": "Constantinople"},
    "castile": {"name": "Kingdom of Castile", "type": "monarchy", "region": "Castile"},
    "castilian_church": {"name": "Castilian Church", "type": "ecclesiastical", "region": "Castile"},
    "college_of_cardinals": {"name": "College of Cardinals", "type": "ecclesiastical", "region": "Rome"},
    "colonna_family": {"name": "Colonna Family", "type": "noble_house", "region": "Rome"},
    "council_of_basel": {"name": "Council of Basel", "type": "ecclesiastical", "region": "Basel"},
    "french_faction": {"name": "French Faction", "type": "political", "region": "France"},
    "genoese_quarter": {"name": "Genoese Quarter", "type": "commercial", "region": "Constantinople"},
    "granada": {"name": "Kingdom of Granada", "type": "monarchy", "region": "Granada"},
    "granada_emirate": {"name": "Emirate of Granada", "type": "monarchy", "region": "Granada"},
    "medici_bank": {"name": "Medici Bank", "type": "financial", "region": "Florence"},
    "military_orders": {"name": "Military Orders", "type": "military_religious", "region": "Castile"},
    "orsini_family": {"name": "Orsini Family", "type": "noble_house", "region": "Rome"},
    "orthodox_church": {"name": "Orthodox Church", "type": "ecclesiastical", "region": "Constantinople"},
    "papacy": {"name": "The Papacy", "type": "ecclesiastical", "region": "Rome"},
    "papal_court": {"name": "Papal Court", "type": "institutional", "region": "Rome"},
    "papal_curia": {"name": "Papal Curia", "type": "institutional", "region": "Rome"},
    "royal_court": {"name": "Royal Court of Castile", "type": "political", "region": "Castile"},
    "royal_family": {"name": "Royal Family of Castile", "type": "dynasty", "region": "Castile"},
    "vatican_guard": {"name": "Vatican Guard", "type": "military", "region": "Rome"},
    "venetian_quarter": {"name": "Venetian Quarter", "type": "commercial", "region": "Constantinople"},
}


def id_to_name(char_id: str) -> str:
    """Convert a character ID to a human-readable name."""
    parts = char_id.split("_")
    # Handle "of" connections
    result = []
    skip_next = False
    for i, part in enumerate(parts):
        if skip_next:
            skip_next = False
            continue
        if part == "de" or part == "del" or part == "di" or part == "al" or part == "ibn" or part == "bin" or part == "bint" or part == "ben":
            result.append(part)
        elif part == "of":
            result.append("of")
        elif part == "el" or part == "la" or part == "le":
            result.append(part)
        else:
            result.append(part.capitalize())
    return " ".join(result)


def infer_title(char_id: str, name: str) -> str:
    """Infer a title from the character ID."""
    first = char_id.split("_")[0]
    if first in TITLE_PREFIXES:
        return TITLE_PREFIXES[first]
    return ""


def infer_categories(char_id: str) -> list:
    """Infer character categories from their ID."""
    cats = []
    for pattern, cat in CATEGORY_PATTERNS.items():
        if re.search(pattern, char_id):
            cats.append(cat)
    return cats if cats else ["other"]


def extract_character_from_summary(char_id: str, summaries: list[str]) -> dict:
    """Try to extract character info from event summaries."""
    name = id_to_name(char_id)
    title = ""
    location = ""

    # Search for the character mentioned with a title/description in parentheses
    # Pattern: "Name (description)" or "Title Name"
    id_parts = char_id.replace("_", " ")
    for summary in summaries:
        # Look for parenthetical descriptions near the character name
        pattern = rf"({re.escape(name)}|{re.escape(id_parts)})\s*\(([^)]+)\)"
        match = re.search(pattern, summary, re.IGNORECASE)
        if match:
            desc = match.group(2).strip()
            if len(desc) < 60:
                title = desc
            break

    return {
        "name_from_summary": name,
        "title_from_summary": title,
    }


def parse_rolls_from_summary(summary: str, event_index: int, date: str) -> list:
    """Extract roll data from an event summary.

    Looks for patterns like: "Roll 18 (Bad Complications):"
    """
    rolls = []
    # Pattern: Roll <number> (<label>):
    pattern = r"Roll\s+(\d+)\s*\(([^)]+)\)"
    for match in re.finditer(pattern, summary):
        rolled = int(match.group(1))
        label = match.group(2).strip()

        # Extract context: text around the roll
        start = max(0, match.start() - 100)
        end = min(len(summary), match.end() + 200)
        context = summary[start:end].strip()

        # Infer roll type from label and surrounding text
        roll_type = "chaos"  # default
        label_lower = label.lower()
        if any(w in label_lower for w in ["negotiation", "diplomacy", "reception", "treaty"]):
            roll_type = "diplomacy"
        elif any(w in label_lower for w in ["persuasion", "speech", "breakthrough", "grateful"]):
            roll_type = "persuasion"
        elif any(w in label_lower for w in ["battle", "ambush", "attack", "siege", "combat"]):
            roll_type = "military"
        elif any(w in label_lower for w in ["passage", "travel", "journey", "delay", "weather"]):
            roll_type = "travel"

        # Determine outcome range from roll number
        if rolled <= 10:
            outcome_range = "critical_failure"
        elif rolled <= 25:
            outcome_range = "failure"
        elif rolled <= 40:
            outcome_range = "mixed_negative"
        elif rolled <= 60:
            outcome_range = "mixed"
        elif rolled <= 75:
            outcome_range = "success"
        elif rolled <= 90:
            outcome_range = "strong_success"
        else:
            outcome_range = "critical_success"

        rolls.append({
            "event_index": event_index,
            "date": date,
            "rolled": rolled,
            "title": label,
            "context": context[:200],
            "roll_type": roll_type,
            "outcome_range": outcome_range,
            "outcome_label": label,
            "outcome_detail": "",
            "evaluation": "",
            "success_factors": [],
            "failure_factors": [],
            "character_effects": [],
            "ranges": [],
        })

    return rolls


def parse_law_references_from_events(events: list) -> list:
    """Detect law-related events and create law references."""
    refs = []
    for i, evt in enumerate(events):
        event_type = evt.get("type", "")
        summary = evt.get("summary", "")
        tags = evt.get("tags", [])

        if event_type == "legal" or "legal" in tags or "law" in tags or "decree" in tags:
            # This event likely involves a law
            refs.append({
                "event_index": i,
                "action": "referenced",
                "law_id": "",  # needs manual assignment
                "date": evt.get("date", ""),
                "summary": summary[:200] if summary else "",
                "_note": "Auto-detected legal event — needs law_id assignment"
            })

    return refs


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

def build_alias_index(aliases: dict, existing_char_ids: set) -> dict:
    """Build reverse lookup: any alias or ID → canonical_id."""
    index = {}
    for canonical_id, info in aliases.items():
        index[canonical_id] = canonical_id
        for alias in info.get("aliases", []):
            index[alias] = canonical_id
    # Also map existing character IDs to themselves
    for cid in existing_char_ids:
        if cid not in index:
            index[cid] = cid
    return index


def resolve_id(raw_id: str, alias_index: dict) -> str:
    """Resolve an ID through the alias index."""
    return alias_index.get(raw_id, raw_id)


def build_extraction(chapter_id: str, existing_chars: set, existing_factions: set,
                     aliases: dict, existing_locs: set) -> dict:
    """Build an extraction file for a single chapter."""

    defs_path = DEFS_DIR / f"chapter_{chapter_id}_defs.json"
    if not defs_path.exists():
        raise FileNotFoundError(f"No event defs for chapter {chapter_id}: {defs_path}")

    with open(defs_path, "r", encoding="utf-8") as f:
        defs = json.load(f)

    book = int(chapter_id.split(".")[0])
    events_list = defs.get("events", [])

    # Build alias index for deduplication
    alias_index = build_alias_index(aliases, existing_chars)

    # Collect all summaries for character name extraction
    all_summaries = [e.get("summary", "") for e in events_list]

    # Build events section (for merge_chapter event ID matching)
    events = []
    for evt in events_list:
        events.append({
            "date": evt.get("date", ""),
            "end_date": evt.get("end_date"),
            "type": evt.get("type", "decision"),
            "summary": evt.get("summary", ""),
            "characters": evt.get("characters", []),
            "factions_affected": evt.get("factions_affected", []),
            "location": evt.get("location", ""),
            "tags": evt.get("tags", []),
        })

    # Detect new characters
    seen_new_chars = set()
    new_characters = []
    for evt in events_list:
        for cid in evt.get("characters", []):
            # Resolve through aliases to find canonical ID
            canonical = resolve_id(cid, alias_index)
            if canonical not in existing_chars and cid not in seen_new_chars and canonical not in seen_new_chars:
                seen_new_chars.add(cid)
                seen_new_chars.add(canonical)

                # Use canonical ID for creation (prefer the canonical form)
                create_id = canonical if canonical in aliases else cid

                # Get info from aliases if available (check both raw and canonical)
                alias_info = aliases.get(canonical, aliases.get(cid, {}))
                alias_name = alias_info.get("name", "")
                alias_category = alias_info.get("category", [])
                alias_aliases = alias_info.get("aliases", [cid])

                # Try to extract from summaries
                summary_info = extract_character_from_summary(cid, all_summaries)

                # Build name: prefer alias, then summary, then ID conversion
                name = alias_name or summary_info["name_from_summary"] or id_to_name(create_id)
                title = summary_info["title_from_summary"] or infer_title(create_id, name)
                categories = alias_category or infer_categories(create_id)

                # Get first location from events
                location = ""
                for e in events_list:
                    if cid in e.get("characters", []):
                        location = e.get("location", "")
                        break

                # Get faction_ids from factions_affected where this character appears
                faction_ids = []
                for e in events_list:
                    if cid in e.get("characters", []):
                        for fid in e.get("factions_affected", []):
                            if fid not in faction_ids:
                                faction_ids.append(fid)

                char_stub = {
                    "id": create_id,
                    "name": name,
                    "aliases": alias_aliases if alias_aliases != [cid] else [cid],
                    "title": title,
                    "born": "0000-00-00",
                    "status": ["active"],
                    "category": categories,
                    "location": location,
                    "current_task": "",
                    "personality": [],
                    "interests": [],
                    "speech_style": "",
                    "core_characteristics": "",
                    "rolled_traits": [],
                    "faction_ids": faction_ids,
                    "appearance": {},
                }
                new_characters.append(char_stub)

    # Detect new factions
    seen_new_factions = set()
    new_factions = []
    for evt in events_list:
        for fid in evt.get("factions_affected", []):
            if fid not in existing_factions and fid not in seen_new_factions:
                seen_new_factions.add(fid)

                meta = FACTION_METADATA.get(fid, {})
                name = meta.get("name", fid.replace("_", " ").title())
                faction_type = meta.get("type", "")
                region = meta.get("region", "")

                # Collect member_ids: characters that appear in events with this faction
                member_ids = []
                for e in events_list:
                    if fid in e.get("factions_affected", []):
                        for cid in e.get("characters", []):
                            if cid not in member_ids:
                                member_ids.append(cid)

                faction_stub = {
                    "faction_id": fid,
                    "name": name,
                    "type": faction_type,
                    "region": region,
                    "description": "",
                    "leader_id": "",
                    "member_ids": member_ids,
                }
                new_factions.append(faction_stub)

    # Extract rolls from summaries
    rolls = []
    for i, evt in enumerate(events_list):
        summary = evt.get("summary", "")
        date = evt.get("date", "")
        rolls.extend(parse_rolls_from_summary(summary, i, date))

    # Detect new locations
    new_locations = []
    seen_locs = set()
    for evt in events_list:
        loc_str = evt.get("location", "")
        if not loc_str:
            continue
        city = loc_str.split(",")[0].strip()
        import unicodedata
        nfkd = unicodedata.normalize("NFKD", city)
        ascii_only = nfkd.encode("ASCII", "ignore").decode("ASCII")
        loc_id = re.sub(r"[^a-z0-9]+", "_", ascii_only.lower()).strip("_")
        if loc_id and loc_id not in existing_locs and loc_id not in seen_locs:
            seen_locs.add(loc_id)
            new_locations.append({
                "location_id": loc_id,
                "name": city,
                "region": "",
                "description": "",
            })

    # Detect law references
    law_references = parse_law_references_from_events(events_list)

    extraction = {
        "chapter": chapter_id,
        "book": book,
        "events": events,
        "new_characters": new_characters,
        "character_updates": [],  # Requires manual/LLM extraction from narrative
        "new_locations": new_locations,
        "rolls": rolls,
        "new_factions": new_factions,
        "faction_updates": [],  # Requires manual/LLM extraction
        "law_references": [r for r in law_references if r.get("law_id")],  # Only include if law_id assigned
    }

    return extraction


def get_chapter_range(start: str, end: str) -> list:
    """Generate chapter IDs from start to end inclusive."""
    chapters = []
    s_book, s_num = int(start.split(".")[0]), int(start.split(".")[1])
    e_book, e_num = int(end.split(".")[0]), int(end.split(".")[1])

    for defs_file in sorted(DEFS_DIR.glob("chapter_*_defs.json")):
        match = re.search(r"chapter_(.+?)_defs\.json", defs_file.name)
        if match:
            ch = match.group(1)
            b, n = int(ch.split(".")[0]), int(ch.split(".")[1])
            if (b > s_book or (b == s_book and n >= s_num)) and \
               (b < e_book or (b == e_book and n <= e_num)):
                chapters.append(ch)

    return chapters


def discover_missing_extractions() -> list:
    """Find chapters that have event_defs but no extraction file."""
    missing = []
    for defs_file in sorted(DEFS_DIR.glob("chapter_*_defs.json")):
        match = re.search(r"chapter_(.+?)_defs\.json", defs_file.name)
        if match:
            ch = match.group(1)
            extraction_path = EXTRACTIONS_DIR / f"chapter_{ch}_extracted.json"
            if not extraction_path.exists():
                missing.append(ch)
    return missing


def main():
    parser = argparse.ArgumentParser(description="Build extraction files from event definitions")
    parser.add_argument("chapters", nargs="*", help="Chapter IDs to build (e.g., 1.23 2.01)")
    parser.add_argument("--range", nargs=2, metavar=("START", "END"),
                        help="Chapter range (e.g., --range 1.23 2.24)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--force", action="store_true", help="Overwrite existing extractions")
    args = parser.parse_args()

    # Load current database state
    chars_db = json.load(open(CHARACTERS_FILE, encoding="utf-8")) if CHARACTERS_FILE.exists() else {"characters": []}
    factions_db = json.load(open(FACTIONS_FILE, encoding="utf-8")) if FACTIONS_FILE.exists() else {"factions": []}
    locs_db = json.load(open(LOCATIONS_FILE, encoding="utf-8")) if LOCATIONS_FILE.exists() else {"locations": []}
    aliases = json.load(open(ALIASES_FILE, encoding="utf-8")) if ALIASES_FILE.exists() else {}

    existing_chars = {c["id"] for c in chars_db.get("characters", [])}
    existing_factions = {f["faction_id"] for f in factions_db.get("factions", [])}
    existing_locs = {l["location_id"] for l in locs_db.get("locations", [])}

    # Determine chapters to process
    if args.range:
        chapter_ids = get_chapter_range(args.range[0], args.range[1])
    elif args.chapters:
        chapter_ids = args.chapters
    else:
        chapter_ids = discover_missing_extractions()

    if not chapter_ids:
        print("No chapters to process.")
        return

    print(f"Building extractions for {len(chapter_ids)} chapter(s)...\n")
    print(f"Current DB: {len(existing_chars)} chars, {len(existing_factions)} factions, "
          f"{len(existing_locs)} locations\n")

    total_new_chars = 0
    total_new_factions = 0
    total_rolls = 0
    total_new_locs = 0

    # Build alias index for deduplication across chapters
    alias_index = build_alias_index(aliases, existing_chars)

    # Track cumulative new entities across chapters (so we don't create duplicates)
    cumulative_chars = set(existing_chars)
    # Also add all canonical IDs from aliases that map to existing chars
    for raw_id, canonical in alias_index.items():
        if canonical in existing_chars:
            cumulative_chars.add(raw_id)
            cumulative_chars.add(canonical)
    cumulative_factions = set(existing_factions)
    cumulative_locs = set(existing_locs)

    for ch in chapter_ids:
        extraction_path = EXTRACTIONS_DIR / f"chapter_{ch}_extracted.json"
        if extraction_path.exists() and not args.force:
            print(f"  {ch}: SKIP (extraction exists, use --force to overwrite)")
            continue

        try:
            extraction = build_extraction(ch, cumulative_chars, cumulative_factions,
                                          aliases, cumulative_locs)

            # Update cumulative sets with both raw IDs and canonical IDs
            for c in extraction["new_characters"]:
                cumulative_chars.add(c["id"])
                canonical = resolve_id(c["id"], alias_index)
                cumulative_chars.add(canonical)
            for f in extraction["new_factions"]:
                cumulative_factions.add(f["faction_id"])
            for l in extraction["new_locations"]:
                cumulative_locs.add(l["location_id"])

            nc = len(extraction["new_characters"])
            nf = len(extraction["new_factions"])
            nr = len(extraction["rolls"])
            nl = len(extraction["new_locations"])
            ne = len(extraction["events"])

            total_new_chars += nc
            total_new_factions += nf
            total_rolls += nr
            total_new_locs += nl

            if args.dry_run:
                print(f"  [DRY RUN] {ch}: {ne} events, {nc} new chars, "
                      f"{nf} new factions, {nr} rolls, {nl} new locs")
                if nc > 0:
                    for c in extraction["new_characters"]:
                        print(f"    + char: {c['id']} → {c['name']}")
                if nf > 0:
                    for f in extraction["new_factions"]:
                        print(f"    + faction: {f['faction_id']} → {f['name']}")
            else:
                EXTRACTIONS_DIR.mkdir(parents=True, exist_ok=True)
                with open(extraction_path, "w", encoding="utf-8") as f:
                    json.dump(extraction, f, indent=2, ensure_ascii=False)
                size = extraction_path.stat().st_size
                print(f"  {ch}: {ne} events, {nc} new chars, "
                      f"{nf} new factions, {nr} rolls, {nl} new locs "
                      f"({size:,} bytes)")

        except FileNotFoundError as e:
            print(f"  {ch}: ERROR - {e}")
        except Exception as e:
            print(f"  {ch}: ERROR - {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    print(f"\nTotals: {total_new_chars} new characters, {total_new_factions} new factions, "
          f"{total_rolls} rolls, {total_new_locs} new locations")


if __name__ == "__main__":
    main()
