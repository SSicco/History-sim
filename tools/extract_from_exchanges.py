#!/usr/bin/env python3
"""
Extract from Exchanges — Phase 3 of the quality remediation plan.

Reads chapter event files (with full exchange text) and sends them to
Claude Haiku to extract structured enrichment data: character updates,
roll details, character descriptions, faction updates, law references,
and location descriptions.

Outputs enriched extraction files that replace the current stubs.

Usage:
  # Process a single chapter
  python3 tools/extract_from_exchanges.py --chapter 1.23

  # Process a range
  python3 tools/extract_from_exchanges.py --from 1.23 --to 1.30

  # Process all chapters needing enrichment
  python3 tools/extract_from_exchanges.py --all

  # Dry run (show what would be processed, don't call API)
  python3 tools/extract_from_exchanges.py --chapter 1.23 --dry-run

  # Set API key (or use ANTHROPIC_API_KEY env var)
  ANTHROPIC_API_KEY=sk-ant-... python3 tools/extract_from_exchanges.py --chapter 1.23

Options:
  --force         Overwrite existing extraction even if non-stub
  --review-only   Write review_needed.json without calling API
"""

import json
import os
import re
import sys
import time
import argparse
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "resources" / "data"
TOOLS_DIR = PROJECT_ROOT / "tools"
EXTRACTIONS_DIR = TOOLS_DIR / "extractions"
EVENTS_DIR = DATA_DIR / "events"

API_URL = "https://api.anthropic.com/v1/messages"
API_MODEL = "claude-haiku-4-5-20251001"
API_VERSION = "2023-06-01"
MAX_TOKENS = 8192

# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def get_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        config_path = PROJECT_ROOT / ".api_key"
        if config_path.exists():
            key = config_path.read_text().strip()
    if not key:
        print("ERROR: No API key found.")
        print("Set ANTHROPIC_API_KEY env var or create .api_key file in project root.")
        sys.exit(1)
    return key


def call_haiku(api_key: str, system_prompt: str, user_message: str,
               max_retries: int = 3) -> dict:
    """Call Claude Haiku with retry logic."""
    headers = {
        "x-api-key": api_key,
        "anthropic-version": API_VERSION,
        "content-type": "application/json",
    }
    payload = {
        "model": API_MODEL,
        "max_tokens": MAX_TOKENS,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    }

    for attempt in range(max_retries):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=180)

            if resp.status_code == 200:
                data = resp.json()
                text = data.get("content", [{}])[0].get("text", "")
                usage = data.get("usage", {})
                return {"text": text, "usage": usage, "error": None}

            if resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                print(f"    Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue

            if resp.status_code >= 500:
                wait = 2 ** (attempt + 1)
                print(f"    Server error {resp.status_code}, waiting {wait}s...")
                time.sleep(wait)
                continue

            return {"text": "", "usage": {}, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

        except requests.exceptions.Timeout:
            wait = 2 ** (attempt + 1)
            print(f"    Timeout, waiting {wait}s...")
            time.sleep(wait)
        except requests.exceptions.RequestException as e:
            return {"text": "", "usage": {}, "error": str(e)}

    return {"text": "", "usage": {}, "error": "Max retries exceeded"}


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a data extraction assistant for a historical simulation game set in 1430s Castile. You read game session transcripts (player/GM exchanges) and extract structured data.

You MUST respond with valid JSON only. No markdown, no explanation, no commentary outside the JSON.

Important rules:
- Character IDs use lowercase_with_underscores (e.g., "alvaro_de_luna", not "Álvaro de Luna")
- Only create character_updates for characters who MATERIALLY CHANGE (new task, new location, status change, personality development). Do NOT create updates for characters who merely appear.
- For appearance, extract ONLY what the GM text explicitly describes. Do not invent details.
- For speech_style, use the character's actual dialogue patterns from the text.
- For rolls, extract the actual d100 value and the specific outcome described.
- Flag anything uncertain with "confidence": "low" in the relevant entry."""


def build_extraction_prompt(chapter_id: str, events: list, known_characters: dict) -> str:
    """Build the user message for extraction."""
    parts = []
    parts.append(f"# Chapter {chapter_id} — Extract enrichment data\n")
    parts.append("Read each event's exchange text below and extract the requested data.\n")

    for i, evt in enumerate(events):
        parts.append(f"\n## Event {i} — {evt.get('type', '?')} — {evt.get('date', '?')}")
        parts.append(f"Location: {evt.get('location', '?')}")
        parts.append(f"Characters: {', '.join(evt.get('characters', []))}")
        parts.append(f"Summary: {evt.get('summary', '')}")

        # Include exchange text (truncate very long exchanges)
        exchanges = evt.get("exchanges", [])
        exchange_text = []
        total_chars = 0
        for ex in exchanges:
            text = ex.get("text", "")
            # Cap per-event exchange text at ~12000 chars to stay within limits
            if total_chars + len(text) > 12000:
                exchange_text.append(f"[{ex['role'].upper()}]: {text[:2000]}... [TRUNCATED]")
                break
            exchange_text.append(f"[{ex['role'].upper()}]: {text}")
            total_chars += len(text)

        parts.append("\n### Exchange text:")
        parts.append("\n".join(exchange_text))

    # Known characters context
    if known_characters:
        parts.append("\n\n## Known characters (already in database)")
        for cid, cdata in known_characters.items():
            parts.append(f"- {cid}: {cdata.get('name', '?')} — {cdata.get('title', '?')}")

    parts.append("""

## Requested output

Return a JSON object with these keys:

```json
{
  "character_updates": [
    {
      "id": "character_id",
      "current_task": "What they are doing now (specific, detailed)",
      "location": "Where they are now (if changed)",
      "status": ["active"],
      "confidence": "high"
    }
  ],
  "character_descriptions": [
    {
      "id": "character_id",
      "appearance": {
        "age_appearance": "description from text",
        "build": "description from text",
        "hair": "description from text",
        "distinguishing_features": "description from text"
      },
      "speech_style": "How they speak based on their dialogue (10+ words)",
      "personality_traits": ["trait1", "trait2"],
      "interests": ["interest1", "interest2"],
      "confidence": "high"
    }
  ],
  "rolls": [
    {
      "event_index": 0,
      "title": "Brief title for the roll",
      "context": "Why the roll is happening",
      "roll_type": "military|diplomacy|persuasion|chaos|travel|espionage|religion|economy|intrigue|personal",
      "date": "YYYY-MM-DD",
      "rolled": 74,
      "outcome_range": "61-80",
      "outcome_label": "Brief label",
      "outcome_detail": "What specifically happened as a result",
      "evaluation": "Assessment of significance",
      "success_factors": ["factor1"],
      "failure_factors": ["factor2"]
    }
  ],
  "faction_updates": [
    {
      "faction_id": "faction_id",
      "description": "2-4 sentences on current status, actions, and outlook",
      "confidence": "high"
    }
  ],
  "law_references": [
    {
      "law_id": "law_NNN or new_law_title",
      "event_index": 0,
      "action": "enacted|modified|repealed|referenced",
      "summary": "What the law does"
    }
  ],
  "location_descriptions": [
    {
      "location_name": "Location Name",
      "description": "1-3 sentences describing the place from the exchange text",
      "sub_locations": ["specific areas mentioned"]
    }
  ],
  "review_flags": [
    {
      "type": "character|roll|faction|law|location|continuity",
      "detail": "Description of what needs human review",
      "event_index": 0
    }
  ]
}
```

Rules:
- Only include character_updates for characters whose situation MATERIALLY CHANGES
- Only include character_descriptions when the text provides EXPLICIT physical or speech details
- For rolls, extract the ACTUAL d100 value from the text (look for "Roll NN", "d100: NN", "rolled NN")
- For location_descriptions, only include when the GM provides substantive description of a place
- Add review_flags for anything ambiguous or uncertain
- Empty arrays are fine if a category has nothing to extract
""")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Chapter processing
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_stub_extraction(extraction_path: Path) -> bool:
    """Check if an extraction file is a stub (no character_updates, no enrichment)."""
    if not extraction_path.exists():
        return True
    data = load_json(extraction_path)
    # Stub if no character_updates and chapter is 1.23+
    updates = data.get("character_updates", [])
    return len(updates) == 0


def get_known_characters(events: list, characters_db: list) -> dict:
    """Get known character data for characters appearing in events."""
    char_ids = set()
    for evt in events:
        for cid in evt.get("characters", []):
            char_ids.add(cid)

    char_lookup = {c["id"]: c for c in characters_db}
    result = {}
    for cid in sorted(char_ids):
        if cid in char_lookup:
            result[cid] = {
                "name": char_lookup[cid].get("name", ""),
                "title": char_lookup[cid].get("title", ""),
            }
    return result


def parse_api_response(text: str) -> dict:
    """Parse JSON from API response, handling markdown fences."""
    text = text.strip()
    # Remove markdown code fences
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Try to find JSON in the text
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {"error": f"Failed to parse JSON: {e}", "raw": text[:500]}


def merge_extraction_data(existing: dict, api_data: dict) -> dict:
    """Merge API extraction data into existing extraction file."""
    # Update character_updates
    if api_data.get("character_updates"):
        existing["character_updates"] = api_data["character_updates"]

    # Update rolls if API found any
    if api_data.get("rolls"):
        existing["rolls"] = api_data["rolls"]

    # Update faction_updates
    if api_data.get("faction_updates"):
        existing["faction_updates"] = api_data["faction_updates"]

    # Update law_references
    if api_data.get("law_references"):
        existing["law_references"] = api_data["law_references"]

    # Enrich new_characters with descriptions
    if api_data.get("character_descriptions"):
        desc_lookup = {d["id"]: d for d in api_data["character_descriptions"]}
        for nc in existing.get("new_characters", []):
            cid = nc.get("id", "")
            if cid in desc_lookup:
                desc = desc_lookup[cid]
                if desc.get("appearance"):
                    nc["appearance"] = desc["appearance"]
                if desc.get("speech_style"):
                    nc["speech_style"] = desc["speech_style"]
                if desc.get("personality_traits") and len(desc["personality_traits"]) > len(nc.get("personality", [])):
                    nc["personality"] = desc["personality_traits"]
                if desc.get("interests") and len(desc["interests"]) > len(nc.get("interests", [])):
                    nc["interests"] = desc["interests"]

    # Enrich new_locations with descriptions
    if api_data.get("location_descriptions"):
        loc_lookup = {}
        for ld in api_data["location_descriptions"]:
            # Normalize location name for matching
            name = ld.get("location_name", "").lower().replace(" ", "_")
            loc_lookup[name] = ld
        for nl in existing.get("new_locations", []):
            lid = nl.get("location_id", "").lower()
            name = nl.get("name", "").lower().replace(" ", "_")
            match = loc_lookup.get(lid) or loc_lookup.get(name)
            if match:
                if match.get("description"):
                    nl["description"] = match["description"]
                if match.get("sub_locations"):
                    nl["sub_locations"] = match["sub_locations"]

    # Store review flags
    if api_data.get("review_flags"):
        existing["_review_flags"] = api_data["review_flags"]

    return existing


def process_chapter(chapter_id: str, api_key: str, dry_run: bool = False,
                    force: bool = False) -> dict:
    """Process a single chapter. Returns stats dict."""
    stats = {"chapter": chapter_id, "status": "skipped", "input_tokens": 0,
             "output_tokens": 0, "cost": 0.0, "review_flags": 0}

    chapter_path = EVENTS_DIR / f"chapter_{chapter_id}.json"
    if not chapter_path.exists():
        stats["status"] = "missing"
        print(f"  {chapter_id}: SKIP (no chapter file)")
        return stats

    extraction_path = EXTRACTIONS_DIR / f"chapter_{chapter_id}_extracted.json"
    if not force and extraction_path.exists() and not is_stub_extraction(extraction_path):
        stats["status"] = "already_enriched"
        print(f"  {chapter_id}: SKIP (already enriched, use --force to overwrite)")
        return stats

    chapter_data = load_json(chapter_path)
    events = chapter_data.get("events", [])
    if not events:
        stats["status"] = "no_events"
        print(f"  {chapter_id}: SKIP (no events)")
        return stats

    # Load known characters
    characters_db = load_json(DATA_DIR / "characters.json").get("characters", [])
    known_chars = get_known_characters(events, characters_db)

    # Build prompt
    prompt = build_extraction_prompt(chapter_id, events, known_chars)
    prompt_tokens = len(prompt) // 4  # Rough estimate

    if dry_run:
        stats["status"] = "dry_run"
        stats["input_tokens"] = prompt_tokens
        print(f"  {chapter_id}: DRY RUN — {len(events)} events, "
              f"~{prompt_tokens:,} input tokens")
        return stats

    print(f"  {chapter_id}: Processing {len(events)} events (~{prompt_tokens:,} tokens)...", end="", flush=True)

    # Call API
    result = call_haiku(api_key, SYSTEM_PROMPT, prompt)

    if result["error"]:
        stats["status"] = "error"
        print(f" ERROR: {result['error']}")
        return stats

    usage = result.get("usage", {})
    stats["input_tokens"] = usage.get("input_tokens", 0)
    stats["output_tokens"] = usage.get("output_tokens", 0)
    stats["cost"] = (stats["input_tokens"] * 0.80 / 1_000_000 +
                     stats["output_tokens"] * 4.00 / 1_000_000)

    # Parse response
    api_data = parse_api_response(result["text"])
    if "error" in api_data:
        stats["status"] = "parse_error"
        print(f" PARSE ERROR: {api_data['error']}")
        # Save raw response for debugging
        debug_path = TOOLS_DIR / f"debug_response_{chapter_id}.txt"
        debug_path.write_text(result["text"])
        print(f"    Raw response saved to {debug_path}")
        return stats

    # Load or create extraction file
    if extraction_path.exists():
        existing = load_json(extraction_path)
    else:
        existing = {
            "chapter": chapter_id,
            "book": chapter_data.get("book", 1),
            "events": events,
            "new_characters": [],
            "character_updates": [],
            "new_locations": [],
            "new_factions": [],
            "rolls": [],
            "law_references": [],
            "faction_updates": [],
        }

    # Merge API data
    enriched = merge_extraction_data(existing, api_data)
    save_json(extraction_path, enriched)

    # Count results
    n_updates = len(api_data.get("character_updates", []))
    n_descs = len(api_data.get("character_descriptions", []))
    n_rolls = len(api_data.get("rolls", []))
    n_flags = len(api_data.get("review_flags", []))
    stats["review_flags"] = n_flags
    stats["status"] = "success"

    print(f" OK — {n_updates} updates, {n_descs} descriptions, "
          f"{n_rolls} rolls, {n_flags} flags, ${stats['cost']:.3f}")

    return stats


# ---------------------------------------------------------------------------
# Review flags aggregation
# ---------------------------------------------------------------------------

def collect_review_flags():
    """Collect all review flags from extraction files into review_needed.json."""
    all_flags = []
    for path in sorted(EXTRACTIONS_DIR.glob("chapter_*_extracted.json")):
        data = load_json(path)
        chapter = data.get("chapter", "?")
        for flag in data.get("_review_flags", []):
            flag["chapter"] = chapter
            all_flags.append(flag)

    output_path = TOOLS_DIR / "review_needed.json"
    save_json(output_path, {
        "total_flags": len(all_flags),
        "flags": all_flags,
    })
    print(f"\nWrote {len(all_flags)} review flags to {output_path}")


# ---------------------------------------------------------------------------
# Chapter discovery
# ---------------------------------------------------------------------------

def get_chapter_range(from_ch: str, to_ch: str) -> list[str]:
    """Generate chapter IDs from range."""
    chapters = []
    for path in sorted(EVENTS_DIR.glob("chapter_*.json")):
        ch = path.stem.replace("chapter_", "")
        chapters.append(ch)

    # Filter to range
    def ch_key(c):
        parts = c.split(".")
        return (int(parts[0]), int(parts[1]))

    from_key = ch_key(from_ch)
    to_key = ch_key(to_ch)

    return [c for c in chapters if from_key <= ch_key(c) <= to_key]


def get_all_needing_enrichment() -> list[str]:
    """Find all chapters that have stub extractions."""
    chapters = []
    for path in sorted(EVENTS_DIR.glob("chapter_*.json")):
        ch = path.stem.replace("chapter_", "")
        extraction_path = EXTRACTIONS_DIR / f"chapter_{ch}_extracted.json"
        if is_stub_extraction(extraction_path):
            chapters.append(ch)
    return chapters


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Extract enrichment data from chapter exchanges via Haiku")
    parser.add_argument("--chapter", type=str, help="Process single chapter (e.g., 1.23)")
    group = parser.add_argument_group("range")
    group.add_argument("--from", dest="from_ch", type=str, help="Start chapter")
    group.add_argument("--to", dest="to_ch", type=str, help="End chapter")
    parser.add_argument("--all", action="store_true", help="Process all chapters needing enrichment")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    parser.add_argument("--force", action="store_true", help="Overwrite existing non-stub extractions")
    parser.add_argument("--review-only", action="store_true", help="Only collect review flags")
    args = parser.parse_args()

    if args.review_only:
        collect_review_flags()
        return

    # Determine chapters to process
    if args.chapter:
        chapters = [args.chapter]
    elif args.from_ch and args.to_ch:
        chapters = get_chapter_range(args.from_ch, args.to_ch)
    elif args.all:
        chapters = get_all_needing_enrichment()
    else:
        parser.print_help()
        return

    if not chapters:
        print("No chapters to process.")
        return

    print(f"Processing {len(chapters)} chapter(s): {chapters[0]} — {chapters[-1]}\n")

    # Get API key (skip for dry run)
    api_key = "" if args.dry_run else get_api_key()

    total_stats = {
        "processed": 0, "skipped": 0, "errors": 0,
        "input_tokens": 0, "output_tokens": 0, "cost": 0.0,
        "review_flags": 0,
    }

    for ch in chapters:
        stats = process_chapter(ch, api_key, dry_run=args.dry_run, force=args.force)

        if stats["status"] == "success":
            total_stats["processed"] += 1
        elif stats["status"] in ("error", "parse_error"):
            total_stats["errors"] += 1
        else:
            total_stats["skipped"] += 1

        total_stats["input_tokens"] += stats["input_tokens"]
        total_stats["output_tokens"] += stats["output_tokens"]
        total_stats["cost"] += stats["cost"]
        total_stats["review_flags"] += stats["review_flags"]

    print(f"\n{'='*60}")
    print(f"  Processed:     {total_stats['processed']}")
    print(f"  Skipped:       {total_stats['skipped']}")
    print(f"  Errors:        {total_stats['errors']}")
    print(f"  Input tokens:  {total_stats['input_tokens']:,}")
    print(f"  Output tokens: {total_stats['output_tokens']:,}")
    print(f"  Total cost:    ${total_stats['cost']:.3f}")
    print(f"  Review flags:  {total_stats['review_flags']}")
    print(f"{'='*60}")

    # Collect review flags after processing
    if total_stats["processed"] > 0 and not args.dry_run:
        collect_review_flags()


if __name__ == "__main__":
    main()
