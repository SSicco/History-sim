#!/usr/bin/env python3
"""
Enrich Characters — Derives character state from their linked events.

For each character in characters.json, reads their event_refs, fetches
the corresponding event summaries from events.json, and updates:
  - location: from the last event's location field
  - current_task: synthesized from the last few events
  - personality: inferred from event types, tags, and summary keywords
  - faction_ids: accumulated from events' factions_affected

Usage:
  python3 tools/enrich_characters.py                 # Enrich all characters
  python3 tools/enrich_characters.py --dry-run       # Preview without writing
  python3 tools/enrich_characters.py --id juan_ii    # Enrich single character
  python3 tools/enrich_characters.py --stats         # Show enrichment statistics
"""

import json
import re
import sys
import argparse
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "resources" / "data"
CHARACTERS_FILE = DATA_DIR / "characters.json"
EVENTS_FILE = DATA_DIR / "events.json"
ROLLS_FILE = DATA_DIR / "roll_history.json"
ALIASES_FILE = PROJECT_ROOT / "tools" / "known_aliases.json"


# ---------------------------------------------------------------------------
# Trait inference rules
# ---------------------------------------------------------------------------

# Event type → personality trait suggestions (if character has 3+ events of this type)
TYPE_TRAITS = {
    "military": ["martial", "decisive"],
    "diplomatic": ["diplomatic", "politically_astute"],
    "diplomacy": ["diplomatic", "politically_astute"],
    "council": ["political", "deliberative"],
    "personal": ["introspective"],
    "religious": ["pious"],
    "ceremony": ["ceremonial"],
    "legal": ["legalistic", "reformist"],
    "economic": ["pragmatic"],
    "crisis": ["resilient"],
    "travel": ["adventurous"],
}

# Event tags → personality traits (if character has 2+ events with this tag)
TAG_TRAITS = {
    "prayer": "pious",
    "religion": "pious",
    "religious": "pious",
    "faith": "pious",
    "crusade": "zealous",
    "speech": "charismatic",
    "negotiation": "diplomatic",
    "strategy": "strategic",
    "reform": "reformist",
    "church_reform": "reformist",
    "siege": "martial",
    "intelligence": "shrewd",
    "deception": "cunning",
    "intrigue": "cunning",
    "family": "family_oriented",
    "succession": "dynastic",
    "taxation": "pragmatic",
    "bold": "bold",
    "emotional": "passionate",
    "pious": "pious",
}

# Keywords in summaries → personality traits
KEYWORD_TRAITS = [
    (r"\b(cautious|careful|prudent)\b", "cautious"),
    (r"\b(bold|daring|brave|courageous)\b", "bold"),
    (r"\b(loyal|faithful|devoted)\b", "loyal"),
    (r"\b(ambitious|aspir)\b", "ambitious"),
    (r"\b(pious|pray|devout|faith)\b", "pious"),
    (r"\b(cunning|scheming|plot|manipulat)\b", "cunning"),
    (r"\b(merciful|mercy|compassion)\b", "merciful"),
    (r"\b(ruthless|cruel|harsh)\b", "ruthless"),
    (r"\b(wise|wisdom|sagac)\b", "wise"),
    (r"\b(eloquen|rhetori|persuasive|rousing speech)\b", "eloquent"),
    (r"\b(stoic|endur|patient)\b", "stoic"),
    (r"\b(charisma|inspir|rally|rallies)\b", "charismatic"),
    (r"\b(pragmatic|practical|realistic)\b", "pragmatic"),
    (r"\b(stubborn|obstinate|inflexible)\b", "stubborn"),
    (r"\b(generous|magnanimous)\b", "generous"),
    (r"\b(suspicious|distrustful|wary)\b", "suspicious"),
    (r"\b(strategic|tactician|calculated)\b", "strategic"),
    (r"\b(scholarly|intellectual|learned)\b", "scholarly"),
    (r"\b(zealous|fervent|ardent)\b", "zealous"),
    (r"\b(diplomatic|diplomat|mediator)\b", "diplomatic"),
]

# Minimum event count thresholds for trait inference
MIN_TYPE_EVENTS = 3
MIN_TAG_EVENTS = 2
MIN_KEYWORD_MENTIONS = 2


def extract_character_sentence(summary: str, char_name: str, char_id: str) -> str:
    """Extract the sentence(s) most relevant to a specific character."""
    # Build name variants to search for
    name_parts = char_name.split()
    search_terms = [char_name]
    if len(name_parts) >= 2:
        search_terms.append(name_parts[-1])  # Last name
    # Also add ID-based names
    id_name = char_id.replace("_", " ")
    search_terms.append(id_name)

    sentences = re.split(r'(?<=[.!?])\s+', summary)
    relevant = []
    for sent in sentences:
        for term in search_terms:
            if term.lower() in sent.lower():
                relevant.append(sent)
                break

    if relevant:
        return " ".join(relevant[:3])  # Max 3 sentences
    return ""


def infer_personality(events: list, char_name: str, char_id: str,
                       existing_traits: list) -> list:
    """Infer personality traits from a character's events."""
    traits = Counter()
    num_events = len(events)

    # Adaptive thresholds based on event count
    # Characters with few events get lower thresholds
    type_threshold = max(1, min(MIN_TYPE_EVENTS, num_events // 2))
    tag_threshold = max(1, min(MIN_TAG_EVENTS, num_events // 2))
    keyword_threshold = max(1, min(MIN_KEYWORD_MENTIONS, num_events // 2))

    # 1. From event types
    type_counts = Counter()
    for evt in events:
        etype = evt.get("type", "")
        type_counts[etype] += 1

    for etype, count in type_counts.items():
        if count >= type_threshold and etype in TYPE_TRAITS:
            for trait in TYPE_TRAITS[etype]:
                traits[trait] += count

    # 2. From event tags
    tag_counts = Counter()
    for evt in events:
        for tag in evt.get("tags", []):
            tag_counts[tag] += 1

    for tag, count in tag_counts.items():
        if count >= tag_threshold and tag in TAG_TRAITS:
            traits[TAG_TRAITS[tag]] += count

    # 3. From summary keywords (search for character-relevant sentences)
    keyword_counts = Counter()
    for evt in events:
        summary = evt.get("summary", "")
        # Get character-relevant text
        relevant = extract_character_sentence(summary, char_name, char_id)
        text_to_search = relevant if relevant else summary

        for pattern, trait in KEYWORD_TRAITS:
            matches = re.findall(pattern, text_to_search, re.IGNORECASE)
            if matches:
                keyword_counts[trait] += len(matches)

    for trait, count in keyword_counts.items():
        if count >= keyword_threshold:
            traits[trait] += count

    # 4. Category-based defaults for characters with no inferred traits
    if not traits and not existing_traits:
        # Read character's categories and infer basic traits
        id_lower = char_id.lower()
        if any(w in id_lower for w in ["bishop", "archbishop", "cardinal", "fray",
                                        "brother", "abbott", "abbot", "patriarch",
                                        "imam", "sheikh"]):
            traits["pious"] = 1
        if any(w in id_lower for w in ["captain", "sergeant", "corporal", "admiral",
                                        "commander"]):
            traits["martial"] = 1
        if any(w in id_lower for w in ["baron", "count", "duke", "don_", "dona_"]):
            traits["noble"] = 1

    # Combine with existing traits (preserve them, add new ones)
    result = list(existing_traits)  # Keep existing
    # Add inferred traits, sorted by confidence (frequency)
    for trait, score in traits.most_common():
        if trait not in result:
            result.append(trait)

    # Cap total: keep all existing + up to 6 new inferred traits
    max_new = 6
    new_count = len(result) - len(existing_traits)
    if new_count > max_new:
        result = list(existing_traits) + [t for t in result if t not in existing_traits][:max_new]

    return result


def derive_current_task(events: list, char_name: str, char_id: str) -> str:
    """Derive current_task from the character's most recent events."""
    if not events:
        return ""

    # Take the last 3 events (or fewer)
    recent = events[-3:]

    # For each recent event, extract character-relevant sentences
    parts = []
    for evt in reversed(recent):  # Most recent first
        summary = evt.get("summary", "")
        relevant = extract_character_sentence(summary, char_name, char_id)
        if relevant:
            parts.append(relevant)
        elif len(recent) <= 2:
            # If few events, use full summary
            parts.append(summary[:200])

    if not parts:
        # Fallback: use the last event's summary
        return events[-1].get("summary", "")[:300]

    # Combine and truncate
    combined = " ".join(parts)
    # Truncate to ~300 chars at sentence boundary
    if len(combined) > 300:
        truncated = combined[:300]
        last_period = truncated.rfind(".")
        if last_period > 150:
            truncated = truncated[:last_period + 1]
        combined = truncated

    return combined


def derive_location(events: list) -> str:
    """Get the character's location from their most recent event."""
    for evt in reversed(events):
        loc = evt.get("location", "")
        if loc:
            return loc
    return ""


def derive_factions(events: list, existing_factions: list, char_id: str) -> list:
    """Derive faction_ids — only add factions where this character is a core actor.

    factions_affected means 'factions impacted by this event', NOT 'factions
    the character belongs to'. We only infer membership when the character
    is the primary actor in a faction-specific event (solo or with < 3 others).
    """
    factions = list(existing_factions)
    for evt in events:
        chars_in_event = evt.get("characters", [])
        factions_in_event = evt.get("factions_affected", [])
        # Only infer membership if this is a small event (few characters)
        # where the faction connection is likely personal, not incidental
        if len(chars_in_event) <= 3 and len(factions_in_event) == 1:
            fid = factions_in_event[0]
            if fid not in factions:
                factions.append(fid)
    return factions


def enrich_character(char: dict, event_map: dict, rolls: list) -> dict:
    """Enrich a single character from their event data. Returns update dict."""
    char_id = char["id"]
    char_name = char.get("name", char_id)
    event_refs = char.get("event_refs", [])

    if not event_refs:
        return {}

    # Collect events in chronological order
    events = []
    for ref in event_refs:
        evt = event_map.get(ref)
        if evt:
            events.append(evt)

    # Sort by date (event_refs should already be ordered, but ensure it)
    events.sort(key=lambda e: e.get("date", ""))

    if not events:
        return {}

    updates = {}

    # 1. Location — from last event
    new_location = derive_location(events)
    if new_location and new_location != char.get("location", ""):
        updates["location"] = new_location

    # 2. Current task — from recent events
    new_task = derive_current_task(events, char_name, char_id)
    if new_task:
        updates["current_task"] = new_task

    # 3. Personality — inferred from all events
    existing_traits = char.get("personality", [])
    new_traits = infer_personality(events, char_name, char_id, existing_traits)
    if new_traits != existing_traits:
        updates["personality"] = new_traits

    # 4. Faction IDs — conservative inference
    existing_factions = char.get("faction_ids", [])
    new_factions = derive_factions(events, existing_factions, char_id)
    if new_factions != existing_factions:
        updates["faction_ids"] = new_factions

    # 5. Core characteristics — brief summary based on event pattern
    if not char.get("core_characteristics"):
        type_counts = Counter(e.get("type", "") for e in events)
        top_types = [t for t, _ in type_counts.most_common(3) if t]
        if top_types:
            role_map = {
                "military": "military leader",
                "diplomatic": "diplomat",
                "diplomacy": "diplomat",
                "council": "political advisor",
                "personal": "close associate",
                "religious": "religious figure",
                "ceremony": "courtier",
                "legal": "legal advisor",
                "economic": "economic actor",
                "travel": "traveler",
            }
            roles = [role_map.get(t, t) for t in top_types]
            # Deduplicate
            seen = set()
            unique_roles = []
            for r in roles:
                if r not in seen:
                    unique_roles.append(r)
                    seen.add(r)
            updates["core_characteristics"] = f"Primarily a {', '.join(unique_roles)}. Appears in {len(events)} events across the campaign."

    return updates


def main():
    parser = argparse.ArgumentParser(description="Enrich characters from event data")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--id", type=str, help="Enrich a specific character by ID")
    parser.add_argument("--stats", action="store_true", help="Show enrichment statistics")
    parser.add_argument("--verbose", action="store_true", help="Show detailed updates")
    args = parser.parse_args()

    # Load data
    chars_db = json.load(open(CHARACTERS_FILE, "r", encoding="utf-8"))
    events_db = json.load(open(EVENTS_FILE, "r", encoding="utf-8"))
    rolls_db = json.load(open(ROLLS_FILE, "r", encoding="utf-8"))

    # Build event lookup
    event_map = {e["event_id"]: e for e in events_db.get("events", [])}
    rolls = rolls_db.get("rolls", [])

    characters = chars_db.get("characters", [])

    if args.stats:
        # Show current enrichment state
        empty_task = sum(1 for c in characters if not c.get("current_task"))
        empty_personality = sum(1 for c in characters if not c.get("personality"))
        empty_location = sum(1 for c in characters if not c.get("location"))
        empty_core = sum(1 for c in characters if not c.get("core_characteristics"))
        no_refs = sum(1 for c in characters if not c.get("event_refs"))

        print(f"Character enrichment state ({len(characters)} total):")
        print(f"  Empty current_task:       {empty_task}")
        print(f"  Empty personality:        {empty_personality}")
        print(f"  Empty location:           {empty_location}")
        print(f"  Empty core_characteristics: {empty_core}")
        print(f"  No event_refs:            {no_refs}")
        return

    # Filter to specific character if requested
    if args.id:
        characters = [c for c in characters if c["id"] == args.id]
        if not characters:
            print(f"Character '{args.id}' not found.")
            sys.exit(1)

    print(f"Enriching {len(characters)} character(s)...\n")

    total_updates = {
        "location": 0,
        "current_task": 0,
        "personality": 0,
        "faction_ids": 0,
        "core_characteristics": 0,
    }

    for char in characters:
        updates = enrich_character(char, event_map, rolls)

        if not updates:
            continue

        if args.verbose or args.id:
            print(f"  {char['id']} ({len(char.get('event_refs', []))} events):")
            for field, value in updates.items():
                old = char.get(field, "")
                if field == "personality":
                    print(f"    personality: {old} → {value}")
                elif field == "current_task":
                    print(f"    current_task: {str(value)[:100]}...")
                elif field == "location":
                    print(f"    location: {old} → {value}")
                elif field == "faction_ids":
                    print(f"    faction_ids: {old} → {value}")
                elif field == "core_characteristics":
                    print(f"    core_char: {value[:80]}...")

        # Apply updates
        if not args.dry_run:
            for field, value in updates.items():
                char[field] = value

        # Track stats
        for field in updates:
            if field in total_updates:
                total_updates[field] += 1

    # Print summary
    prefix = "[DRY RUN] " if args.dry_run else ""
    print(f"\n{prefix}Enrichment summary:")
    for field, count in total_updates.items():
        print(f"  {field}: {count} characters updated")

    # Save
    if not args.dry_run and not args.id:
        with open(CHARACTERS_FILE, "w", encoding="utf-8") as f:
            json.dump(chars_db, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {CHARACTERS_FILE.name}")
    elif not args.dry_run and args.id:
        # Save the whole file even for single character update
        all_chars = json.load(open(CHARACTERS_FILE, "r", encoding="utf-8"))
        for i, c in enumerate(all_chars["characters"]):
            if c["id"] == characters[0]["id"]:
                all_chars["characters"][i] = characters[0]
                break
        with open(CHARACTERS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_chars, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {CHARACTERS_FILE.name}")


if __name__ == "__main__":
    main()
