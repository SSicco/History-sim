#!/usr/bin/env python3
"""
Chapter Converter — Converts raw chapter text from Claude.ai chat transcripts
into structured JSON encounters for the Castile 1430 game database.

Two-pass architecture:
  Pass 1: Send entire chapter to Claude to identify all events (compact plan).
  Pass 2: For each event, extract text and send to Claude for full JSON conversion.

Usage:
  # Convert a chapter
  ANTHROPIC_API_KEY=sk-... python3 tools/chapter_converter.py chapter3.txt --chapter-id 2.3

  # Resume an interrupted conversion
  ANTHROPIC_API_KEY=sk-... python3 tools/chapter_converter.py chapter3.txt --chapter-id 2.3 --resume

  # Preview: show event plan without converting
  ANTHROPIC_API_KEY=sk-... python3 tools/chapter_converter.py chapter3.txt --chapter-id 2.3 --dry-run

  # Override starting event sequence number
  ANTHROPIC_API_KEY=sk-... python3 tools/chapter_converter.py chapter3.txt --chapter-id 2.3 --start-seq 25
"""

import os
import sys
import json
import re
import time
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_URL = "https://api.anthropic.com/v1/messages"
API_MODEL = "claude-sonnet-4-20250514"
API_VERSION = "2023-06-01"
MAX_TOKENS_PLAN = 4096      # Pass 1 output (event list is compact)
MAX_TOKENS_CONVERT = 8192   # Pass 2 output (full encounter JSON)
RETRY_ATTEMPTS = 5
RETRY_BASE_DELAY = 3        # seconds, doubles on each retry (3, 6, 12, 24, 48)
PAUSE_BETWEEN_CALLS = 3     # seconds between API calls


def _set_model(model_name):
    global API_MODEL
    API_MODEL = model_name

# Paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = PROJECT_ROOT / "resources" / "source_material" / "book2"
DATA_DIR = PROJECT_ROOT / "resources" / "data"
PROGRESS_DIR = PROJECT_ROOT / "tools" / "progress"

# Canonical event types from CONVENTIONS.md
VALID_EVENT_TYPES = {
    "decision", "diplomatic_proposal", "promise", "battle", "law_enacted",
    "law_repealed", "relationship_change", "npc_action", "economic_event",
    "roll_result", "ceremony", "death", "birth", "marriage", "treaty",
    "betrayal", "military_action", "construction", "religious_event",
}

# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def get_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("ERROR: Set the ANTHROPIC_API_KEY environment variable.")
        sys.exit(1)
    return key


def call_claude(api_key, system_prompt, user_message, max_tokens):
    """Send a message to Claude and return the text response."""
    import requests

    headers = {
        "x-api-key": api_key,
        "anthropic-version": API_VERSION,
        "content-type": "application/json",
    }
    payload = {
        "model": API_MODEL,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    }

    for attempt in range(RETRY_ATTEMPTS):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            if resp.status_code == 200:
                data = resp.json()
                return data["content"][0]["text"]
            elif resp.status_code == 429:
                # Use Retry-After header if provided, otherwise exponential backoff
                retry_after = resp.headers.get("retry-after")
                if retry_after:
                    wait = int(float(retry_after)) + 1
                else:
                    wait = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"  Rate limited. Waiting {wait}s...")
                time.sleep(wait)
                continue
            elif resp.status_code >= 500:
                wait = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"  Server error {resp.status_code}. Retrying in {wait}s...")
                time.sleep(wait)
                continue
            else:
                print(f"  API error {resp.status_code}: {resp.text[:500]}")
                return None
        except requests.exceptions.Timeout:
            wait = RETRY_BASE_DELAY * (2 ** attempt)
            print(f"  Timeout. Retrying in {wait}s...")
            time.sleep(wait)
        except requests.exceptions.ConnectionError:
            wait = RETRY_BASE_DELAY * (2 ** attempt)
            print(f"  Connection error. Retrying in {wait}s...")
            time.sleep(wait)

    print("  ERROR: All retry attempts failed.")
    return None


def extract_json(text):
    """Extract JSON from a response that may contain markdown fences or preamble."""
    # Try the whole string first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code fence
    match = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding the first [ or { and matching to the end
    for start_char, end_char in [("[", "]"), ("{", "}")]:
        start = text.find(start_char)
        if start == -1:
            continue
        end = text.rfind(end_char)
        if end == -1 or end <= start:
            continue
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            continue

    return None


# ---------------------------------------------------------------------------
# Event ID management
# ---------------------------------------------------------------------------

def find_highest_event_seq():
    """Scan existing chapter JSONs to find the highest event sequence number."""
    highest = 0
    for path in DATA_DIR.glob("chapter_*.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        for enc in data.get("encounters", []):
            eid = enc.get("id", "")
            m = re.match(r"evt_\d{4}_(\d{5})", eid)
            if m:
                highest = max(highest, int(m.group(1)))
    return highest


def make_event_id(year, seq):
    return f"evt_{year}_{seq:05d}"


# ---------------------------------------------------------------------------
# Progress management
# ---------------------------------------------------------------------------

def progress_path(chapter_id):
    return PROGRESS_DIR / f"progress_{chapter_id.replace('.', '_')}.json"


def save_progress(chapter_id, plan, results_map, next_seq):
    """Save conversion progress.

    results_map: dict mapping plan index (str key) → encounter dict or None.
    """
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "chapter_id": chapter_id,
        "plan": plan,
        "results_map": results_map,   # {str(index): encounter_or_null}
        "next_seq": next_seq,
    }
    with open(progress_path(chapter_id), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_progress(chapter_id):
    p = progress_path(chapter_id)
    if not p.exists():
        return None
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Migrate old format (encounters + next_index) to new (results_map)
    if "results_map" not in data and "encounters" in data:
        old_enc = data["encounters"]
        old_next = data.get("next_index", len(old_enc))
        results_map = {}
        for i, enc in enumerate(old_enc):
            results_map[str(i)] = enc
        data["results_map"] = results_map
        data["next_seq"] = data.get("next_seq", 0)
        data.pop("encounters", None)
        data.pop("next_index", None)
    return data


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_encounter(enc, errors):
    """Validate encounter fields. Appends error strings to `errors` list."""
    required = ["id", "type", "date", "location", "participants", "exchanges", "recap"]
    for field in required:
        if field not in enc:
            errors.append(f"Missing required field: {field}")

    eid = enc.get("id", "")
    if eid and not re.match(r"evt_\d{4}_\d{5}$", eid):
        errors.append(f"Bad event ID format: {eid}")

    etype = enc.get("type", "")
    if etype and etype not in VALID_EVENT_TYPES:
        errors.append(f"Unknown event type: {etype}")

    date = enc.get("date", "")
    if date and not re.match(r"\d{4}-\d{2}-\d{2}$", date):
        errors.append(f"Bad date format: {date}")

    end_date = enc.get("end_date")
    if end_date and not re.match(r"\d{4}-\d{2}-\d{2}$", end_date):
        errors.append(f"Bad end_date format: {end_date}")

    participants = enc.get("participants", [])
    if not isinstance(participants, list):
        errors.append("participants must be a list")

    exchanges = enc.get("exchanges", [])
    if not isinstance(exchanges, list):
        errors.append("exchanges must be a list")
    for i, ex in enumerate(exchanges):
        if "speaker" not in ex:
            errors.append(f"Exchange {i}: missing speaker")
        if "text" not in ex:
            errors.append(f"Exchange {i}: missing text")


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

PLAN_SYSTEM = """\
You are a data extraction assistant for a medieval RPG game called "Castile 1430".
You will receive a raw chapter text file — a Claude.ai chat transcript containing a
mix of GM narrative, player input, timestamps, meta-commentary, and d100 roll tables.

Your job is to identify ALL distinct events/encounters in this text and return a
compact JSON plan. Each event is a discrete scene: a conversation, a ceremony, a
battle, a journey, a d100 roll, etc.

Rules for identifying events:
- A new event starts when the scene shifts (new date, new location, new topic,
  or new set of characters).
- d100 roll tables count as their own event of type "roll_result".
- Player meta-instructions (e.g., "GM: Read NPC guide") are NOT events — skip them.
- Timestamps ("13 nov 2025") and thinking summaries ("Orchestrated...") are NOT
  events — skip them.
- Chat preamble (greetings, file loading confirmations) is NOT an event — skip it.
- A long continuous scene (same location, same characters, flowing dialogue) should
  be ONE event, not split into multiple.

Return ONLY a JSON array — no explanation, no markdown fences. Each element:
{
  "title": "Short descriptive title",
  "line_start": <approximate 1-based line number where this event begins>,
  "line_end": <approximate 1-based line number where this event ends>,
  "date": "YYYY-MM-DD or best estimate",
  "type": "<event type from: decision, diplomatic_proposal, promise, battle, law_enacted, law_repealed, relationship_change, npc_action, economic_event, roll_result, ceremony, death, birth, marriage, treaty, betrayal, military_action, construction, religious_event>",
  "location": "City, Specific Place"
}
"""

CONVERT_SYSTEM = """\
You are a data extraction assistant for a medieval RPG game called "Castile 1430".
You will receive a segment of raw chapter text and must convert it into a single
structured encounter JSON object.

The raw text is a Claude.ai chat transcript — it contains GM narrative (long prose),
player input (short, informal, first-person "I"), NPC dialogue (in quotes), timestamps,
and meta-commentary. You must extract only the narrative and dialogue content.

ENCOUNTER SCHEMA:
{
  "id": "<will be provided — use exactly as given>",
  "type": "<event type>",
  "date": "YYYY-MM-DD",
  "end_date": "YYYY-MM-DD or null",
  "location": "City, Specific Place",
  "participants": ["character_id_1", "character_id_2"],
  "exchanges": [
    {"speaker": "narrator", "text": "Narrative prose..."},
    {"speaker": "character_id", "text": "Dialogue..."}
  ],
  "roll": null or {"table_id": "descriptive_snake_case_id", "value": <number>, "outcome": "description"},
  "recap": "One-paragraph summary of what happened in this event."
}

CHARACTER ID RULES:
- Lowercase ASCII only (strip accents: á→a, é→e, ñ→n, etc.)
- Underscores for spaces and particles (Álvaro de Luna → alvaro_de_luna)
- Exclude titles/ranks (King Juan II → juan_ii, Pope Eugenius IV → pope_eugenius_iv)
- Player character is always "juan_ii"
- Use "narrator" for all GM narrative/description text

EXCHANGE RULES:
- GM narrative/description → speaker: "narrator"
- Player input (the user's actions/speech) → speaker: "juan_ii"
- NPC dialogue (text in quotes attributed to a character) → speaker: "character_id"
- Consolidate consecutive narrator blocks if they form one continuous description
- Strip timestamps, meta-commentary ("Orchestrated..."), and GM instructions
  ("Read NPC guide") from exchanges
- Keep the literary quality of the GM narrative — do not summarize or truncate it

FOR ROLL EVENTS (type "roll_result"):
- The table_id should be a descriptive snake_case identifier
- Include the rolled value and outcome description
- The recap should summarize what was being rolled for and the result
- exchanges can be empty []

Return ONLY the JSON object — no explanation, no markdown fences.
"""

EXAMPLE_ENCOUNTERS = """
EXAMPLE ENCOUNTERS (for reference — match this style and structure):

Example 1 (military_action with roll):
{
  "id": "evt_1433_00003",
  "type": "military_action",
  "date": "1433-04-09",
  "end_date": "1433-04-23",
  "location": "Mediterranean Sea, Málaga to Ostia",
  "participants": ["juan_ii", "fernan_alonso_de_robles", "father_miguel", "paolo_grimaldi"],
  "exchanges": [
    {"speaker": "narrator", "text": "The fleet departs Málaga at early afternoon. Ten vessels: six broad-beamed carracks for cargo and troops, four sleeker galleys."},
    {"speaker": "father_miguel", "text": "Your Majesty, I understand you wish to improve your Latin during the voyage."},
    {"speaker": "narrator", "text": "Days 4-7: The weather turns as the fleet passes south of the Balearic Islands. The ships begin to tack against contrary wind."},
    {"speaker": "paolo_grimaldi", "text": "Your Majesty, my apologies for the delay. Worst contrary winds I've seen in April in fifteen years at sea."}
  ],
  "roll": {"table_id": "roll_ch2_1_001", "value": 33, "outcome": "Difficult passage. Contrary winds, forced to shelter at Corsica. Arrive 3-5 days late."},
  "recap": "The Mediterranean crossing takes fourteen days instead of ten due to contrary winds. The fleet shelters at Corsica, two horses are lost, but men, treasury, and relics arrive intact."
}

Example 2 (diplomatic_proposal, no roll):
{
  "id": "evt_1433_00008",
  "type": "diplomatic_proposal",
  "date": "1433-04-24",
  "end_date": null,
  "location": "Rome, Vatican Private Chambers",
  "participants": ["juan_ii", "pope_eugenius_iv", "cardinal_orsini", "bishop_carrera"],
  "exchanges": [
    {"speaker": "narrator", "text": "The group moves through St. Peter's into the papal apartments — surprisingly austere."},
    {"speaker": "pope_eugenius_iv", "text": "Let us speak plainly. The public ceremony was necessary — Rome needed to see your arrival."},
    {"speaker": "juan_ii", "text": "Holy father, I am a king and a soldier in the employ of Jezus Christ."},
    {"speaker": "narrator", "text": "Pope Eugenius slowly removes the papal tiara. He asks Cardinal Orsini and Bishop Carrera to leave."},
    {"speaker": "pope_eugenius_iv", "text": "I prayed for a sign. And then you arrived."}
  ],
  "roll": null,
  "recap": "In private chambers, Juan declares his faith and the Pope confesses his crisis of doubt. They form a deep spiritual bond. All petitions granted."
}
"""


# ---------------------------------------------------------------------------
# Pass 1 — Event plan
# ---------------------------------------------------------------------------

def run_pass1(raw_text, chapter_id, api_key):
    """Identify all events in the raw chapter text. Returns a list of event dicts."""
    print(f"\n[Pass 1] Identifying events in chapter {chapter_id}...")

    # Number the lines for reference
    lines = raw_text.split("\n")
    numbered = "\n".join(f"{i+1}: {line}" for i, line in enumerate(lines))

    user_msg = (
        f"Chapter {chapter_id} raw text ({len(lines)} lines):\n\n"
        f"{numbered}"
    )

    response = call_claude(api_key, PLAN_SYSTEM, user_msg, MAX_TOKENS_PLAN)
    if response is None:
        print("  ERROR: Failed to get event plan from API.")
        return None

    plan = extract_json(response)
    if plan is None:
        print("  ERROR: Could not parse event plan JSON.")
        print(f"  Raw response (first 1000 chars): {response[:1000]}")
        return None

    if not isinstance(plan, list):
        print("  ERROR: Event plan is not a JSON array.")
        return None

    print(f"  Found {len(plan)} events in chapter {chapter_id}")
    return plan


# ---------------------------------------------------------------------------
# Pass 2 — Per-event conversion
# ---------------------------------------------------------------------------

def run_pass2_event(raw_lines, event_plan, event_id, chapter_id, api_key):
    """Convert a single event segment to a structured encounter."""
    line_start = max(0, event_plan.get("line_start", 1) - 1)
    line_end = min(len(raw_lines), event_plan.get("line_end", len(raw_lines)))

    # Add some context overlap (10 lines before, 5 after)
    context_start = max(0, line_start - 10)
    context_end = min(len(raw_lines), line_end + 5)

    segment = "\n".join(raw_lines[context_start:context_end])

    user_msg = (
        f"Convert the following event into a structured encounter JSON.\n\n"
        f"Assigned event ID: {event_id}\n"
        f"Event type hint: {event_plan.get('type', 'unknown')}\n"
        f"Date hint: {event_plan.get('date', 'unknown')}\n"
        f"Location hint: {event_plan.get('location', 'unknown')}\n"
        f"Title: {event_plan.get('title', 'unknown')}\n\n"
        f"The core event text runs from approximately line {line_start+1} to {line_end}. "
        f"I've included a few surrounding lines for context.\n\n"
        f"{EXAMPLE_ENCOUNTERS}\n\n"
        f"--- RAW TEXT (lines {context_start+1}-{context_end}) ---\n\n"
        f"{segment}\n\n"
        f"--- END RAW TEXT ---\n\n"
        f"Return ONLY the JSON encounter object."
    )

    response = call_claude(api_key, CONVERT_SYSTEM, user_msg, MAX_TOKENS_CONVERT)
    if response is None:
        return None

    encounter = extract_json(response)
    if encounter is None:
        print(f"    WARNING: Could not parse encounter JSON.")
        print(f"    Raw response (first 500 chars): {response[:500]}")
        return None

    # Force the assigned event ID
    encounter["id"] = event_id

    return encounter


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert raw chapter text to structured JSON encounters."
    )
    parser.add_argument(
        "source_file",
        help="Raw chapter text filename (e.g., chapter3.txt). Looked up in resources/source_material/book2/",
    )
    parser.add_argument(
        "--chapter-id",
        required=True,
        help='Chapter identifier (e.g., "2.3")',
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from saved progress",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show event plan without converting",
    )
    parser.add_argument(
        "--start-seq",
        type=int,
        default=None,
        help="Override starting event sequence number (default: auto-detect from existing files)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help=f"Claude model to use (default: {API_MODEL})",
    )
    args = parser.parse_args()

    # Resolve the model override
    if args.model is not None:
        _set_model(args.model)

    # Resolve paths
    source_path = SOURCE_DIR / args.source_file
    if not source_path.exists():
        print(f"ERROR: Source file not found: {source_path}")
        sys.exit(1)

    chapter_num = args.chapter_id.replace(".", "_")
    output_path = DATA_DIR / f"chapter_{chapter_num.zfill(5 if '_' in chapter_num else 2)}.json"
    # Normalize to chapter_02_03.json format
    parts = args.chapter_id.split(".")
    if len(parts) == 2:
        output_path = DATA_DIR / f"chapter_{int(parts[0]):02d}_{int(parts[1]):02d}.json"
    else:
        output_path = DATA_DIR / f"chapter_{args.chapter_id}.json"

    api_key = get_api_key()

    print("=" * 50)
    print("  Chapter Converter")
    print("=" * 50)
    print(f"  Source:    {source_path.relative_to(PROJECT_ROOT)}")
    print(f"  Output:    {output_path.relative_to(PROJECT_ROOT)}")
    print(f"  Chapter:   {args.chapter_id}")
    print(f"  Model:     {API_MODEL}")

    # Load source text
    with open(source_path, "r", encoding="utf-8") as f:
        raw_text = f.read()
    raw_lines = raw_text.split("\n")
    print(f"  Lines:     {len(raw_lines)}")

    # Determine starting sequence number
    if args.start_seq is not None:
        next_seq = args.start_seq
    else:
        next_seq = find_highest_event_seq() + 1
    print(f"  Start seq: {next_seq:05d}")

    # Check for resume
    plan = None
    results_map = {}  # {str(plan_index): encounter_dict_or_None}

    if args.resume:
        progress = load_progress(args.chapter_id)
        if progress:
            plan = progress["plan"]
            results_map = progress.get("results_map", {})
            next_seq = progress.get("next_seq", next_seq)
            completed = sum(1 for v in results_map.values() if v is not None)
            failed = sum(1 for v in results_map.values() if v is None)
            print(f"  Resuming: {completed} completed, {failed} to retry, {len(plan)} total")
        else:
            print("  No progress file found — starting fresh.")

    # ---- Pass 1: Event Plan ----
    if plan is None:
        plan = run_pass1(raw_text, args.chapter_id, api_key)
        if plan is None:
            print("\nFailed to generate event plan. Aborting.")
            sys.exit(1)

    # Show the plan
    print(f"\n  Event plan ({len(plan)} events):")
    print("  " + "-" * 46)
    for i, evt in enumerate(plan):
        key = str(i)
        if key in results_map and results_map[key] is not None:
            marker = "✓ "
        elif key in results_map and results_map[key] is None:
            marker = "✗ "
        else:
            marker = "  "
        print(
            f"  {marker}[{i+1:2d}] {evt.get('type', '?'):25s} "
            f"{evt.get('date', '?'):12s} {evt.get('title', '?')[:40]}"
        )
    print()

    if args.dry_run:
        print("  Dry run — stopping here.")
        return

    # ---- Pass 2: Per-Event Conversion ----
    # Cooldown after the large Pass 1 call to avoid hitting rate limits
    if plan is not None and not args.resume:
        print("  Cooling down 10s before Pass 2 (rate limit buffer)...")
        time.sleep(10)
    print("[Pass 2] Converting events...\n")

    for i in range(len(plan)):
        key = str(i)

        # Skip already-completed events
        if key in results_map and results_map[key] is not None:
            print(f"  [{i+1}/{len(plan)}] Already converted — skipping")
            continue

        evt_plan = plan[i]

        # Determine the year from the event date
        date_str = evt_plan.get("date", "1433-01-01")
        year_match = re.match(r"(\d{4})", date_str)
        year = int(year_match.group(1)) if year_match else 1433

        event_id = make_event_id(year, next_seq)
        title = evt_plan.get("title", "Unknown")

        print(f"  [{i+1}/{len(plan)}] {event_id} | {evt_plan.get('type', '?')} | {date_str} | {evt_plan.get('location', '?')}")

        encounter = run_pass2_event(raw_lines, evt_plan, event_id, args.chapter_id, api_key)

        if encounter is None:
            print(f"         FAILED — skipping (will retry on --resume)")
            results_map[key] = None
            save_progress(args.chapter_id, plan, results_map, next_seq)
            time.sleep(PAUSE_BETWEEN_CALLS)
            continue

        # Validate
        errors = []
        validate_encounter(encounter, errors)
        if errors:
            print(f"         Validation warnings:")
            for err in errors:
                print(f"           - {err}")

        # Summary
        n_exchanges = len(encounter.get("exchanges", []))
        has_roll = encounter.get("roll") is not None
        recap = encounter.get("recap", "")[:80]
        print(f'         "{recap}..."')
        print(f"         → {n_exchanges} exchanges, {'roll' if has_roll else 'no roll'} ✓")

        results_map[key] = encounter
        next_seq += 1

        # Save progress after each event
        save_progress(args.chapter_id, plan, results_map, next_seq)

        # Pause between API calls
        if i < len(plan) - 1:
            time.sleep(PAUSE_BETWEEN_CALLS)

    # ---- Assemble final chapter JSON ----
    # Build ordered encounters list from results_map (skip failed/None entries)
    encounters = []
    for i in range(len(plan)):
        enc = results_map.get(str(i))
        if enc is not None:
            encounters.append(enc)

    if not encounters:
        print("\nNo encounters converted. Nothing to save.")
        return

    # Determine date range
    dates = [e.get("date", "") for e in encounters if e.get("date")]
    end_dates = [e.get("end_date", "") for e in encounters if e.get("end_date")]
    all_dates = sorted(set(dates + end_dates))
    date_range = f"{all_dates[0]} / {all_dates[-1]}" if all_dates else "unknown"

    # Build chapter title from the first event's title or plan
    chapter_title = plan[0].get("title", f"Chapter {args.chapter_id}") if plan else f"Chapter {args.chapter_id}"

    chapter_data = {
        "chapter": args.chapter_id,
        "title": chapter_title,
        "date_range": date_range,
        "encounters": encounters,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chapter_data, f, indent=2, ensure_ascii=False)

    print(f"\n[Done] Saved {len(encounters)} encounters to {output_path.relative_to(PROJECT_ROOT)}")
    print(f"       Date range: {date_range}")
    print(f"       Next event sequence: {next_seq:05d}")

    # Clean up progress file only if ALL events were converted
    if len(encounters) == len(plan):
        p = progress_path(args.chapter_id)
        if p.exists():
            p.unlink()
            print("       Progress file cleaned up.")
    else:
        print(f"       WARNING: {len(plan) - len(encounters)} event(s) failed.")
        print(f"       Run with --resume to retry failed events.")


if __name__ == "__main__":
    main()
