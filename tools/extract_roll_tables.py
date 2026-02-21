#!/usr/bin/env python3
"""
Extract Roll Tables — AI-assisted extraction of d100 roll tables from source material.

Reads chapter source JSON files from resources/source_material/ and sends them
to Claude Haiku to extract structured roll table data with full outcome ranges.

Book 1 chapters 1-10 used a d6 system with no fixed ranges — these are skipped.
All other chapters (Book 1 ch 11+, all of Book 2) use d100 tables.

Commands:
  extract   — Extract roll tables from source chapters (default)
  merge     — Merge per-chapter extractions into roll_tables.json
  status    — Show extraction progress

Usage:
  # Extract a single chapter
  python3 tools/extract_roll_tables.py extract --chapter 2.1

  # Extract a range of chapters
  python3 tools/extract_roll_tables.py extract --from 1.11 --to 1.20

  # Extract all d100 chapters
  python3 tools/extract_roll_tables.py extract --all

  # Dry run (show what would be processed, don't call API)
  python3 tools/extract_roll_tables.py extract --chapter 2.1 --dry-run

  # Force re-extraction of already-extracted chapters
  python3 tools/extract_roll_tables.py extract --chapter 2.1 --force

  # Merge all extractions into roll_tables.json
  python3 tools/extract_roll_tables.py merge

  # Show extraction status
  python3 tools/extract_roll_tables.py status

  # Set API key (or use ANTHROPIC_API_KEY env var or .api_key file)
  ANTHROPIC_API_KEY=sk-ant-... python3 tools/extract_roll_tables.py extract --all
"""

import json
import os
import re
import sys
import time
import argparse
from pathlib import Path
from datetime import datetime

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "resources" / "data"
TOOLS_DIR = PROJECT_ROOT / "tools"
SOURCE_BOOK1 = PROJECT_ROOT / "resources" / "source_material" / "book1"
SOURCE_BOOK2 = PROJECT_ROOT / "resources" / "source_material" / "book2"
ROLL_TABLES_FILE = DATA_DIR / "roll_tables.json"
ROLL_HISTORY_FILE = DATA_DIR / "roll_history.json"
OUTPUT_DIR = TOOLS_DIR / "extractions" / "roll_tables"

API_URL = "https://api.anthropic.com/v1/messages"
API_MODEL = "claude-haiku-4-5-20251001"
API_VERSION = "2023-06-01"
MAX_TOKENS = 16384

# Book 1 chapters 1-10 used d6 — no fixed range tables
D6_LAST_CHAPTER = 10


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def get_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        config_path = PROJECT_ROOT / ".api_key"
        if config_path.exists():
            key = config_path.read_text().strip()
    if not key:
        import getpass
        print("No API key found in ANTHROPIC_API_KEY env var or .api_key file.")
        key = getpass.getpass("Enter your Anthropic API key: ").strip()
        if not key:
            print("ERROR: No API key provided.")
            sys.exit(1)
        # Offer to save for future runs
        save = input("Save key to .api_key file for future runs? [y/N] ").strip().lower()
        if save == "y":
            config_path = PROJECT_ROOT / ".api_key"
            config_path.write_text(key + "\n")
            print(f"  Saved to {config_path}")
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
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=300)

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

            return {"text": "", "usage": {},
                    "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

        except requests.exceptions.Timeout:
            wait = 2 ** (attempt + 1)
            print(f"    Timeout, waiting {wait}s...")
            time.sleep(wait)
        except requests.exceptions.RequestException as e:
            return {"text": "", "usage": {}, "error": str(e)}

    return {"text": "", "usage": {}, "error": "Max retries exceeded"}


# ---------------------------------------------------------------------------
# Source file discovery
# ---------------------------------------------------------------------------

def find_source_file(chapter_id: str) -> Path | None:
    """Map a chapter ID like '1.11' or '2.5' to its source JSON file."""
    parts = chapter_id.split(".")
    if len(parts) != 2:
        return None

    book = int(parts[0])
    chapter_num = int(parts[1])

    if book == 1:
        # Book 1: "Claude-Chapter {N}.json"
        path = SOURCE_BOOK1 / f"Claude-Chapter {chapter_num}.json"
    elif book == 2:
        # Book 2: "Claude-Chapter 2.{N}.json"
        path = SOURCE_BOOK2 / f"Claude-Chapter 2.{chapter_num}.json"
    else:
        return None

    return path if path.exists() else None


def discover_all_chapters() -> list[str]:
    """Find all available chapter IDs from source files, sorted."""
    chapters = []

    if SOURCE_BOOK1.exists():
        for f in SOURCE_BOOK1.glob("Claude-Chapter *.json"):
            m = re.match(r"Claude-Chapter (\d+)\.json", f.name)
            if m:
                num = int(m.group(1))
                chapters.append(f"1.{num}")

    if SOURCE_BOOK2.exists():
        for f in SOURCE_BOOK2.glob("Claude-Chapter 2.*.json"):
            m = re.match(r"Claude-Chapter 2\.(\d+)\.json", f.name)
            if m:
                num = int(m.group(1))
                chapters.append(f"2.{num}")

    # Sort by book then chapter number
    def sort_key(ch):
        b, n = ch.split(".")
        return (int(b), int(n))

    return sorted(chapters, key=sort_key)


def is_d100_chapter(chapter_id: str) -> bool:
    """Check if a chapter uses the d100 system (has range tables)."""
    parts = chapter_id.split(".")
    book = int(parts[0])
    chapter_num = int(parts[1])
    if book == 1 and chapter_num <= D6_LAST_CHAPTER:
        return False
    return True


# ---------------------------------------------------------------------------
# Source file loading
# ---------------------------------------------------------------------------

def load_source_chapter(path: Path) -> list[dict]:
    """Load a source chapter JSON and return messages."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("messages", [])


def format_messages_for_prompt(messages: list[dict], max_chars: int = 500000) -> str:
    """Format chapter messages into a readable transcript for the AI."""
    lines = []
    total_chars = 0

    for i, msg in enumerate(messages):
        role = msg.get("role", "Unknown")
        text = msg.get("say", "")

        # Map roles
        if role == "Prompt":
            role_label = "PLAYER"
        elif role == "Response":
            role_label = "GM"
        else:
            role_label = role.upper()

        entry = f"[Message {i+1} — {role_label}]\n{text}\n"

        if total_chars + len(entry) > max_chars:
            lines.append(f"\n[... TRUNCATED at message {i+1} of {len(messages)} ...]")
            break

        lines.append(entry)
        total_chars += len(entry)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Extraction prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a data extraction specialist for a tabletop RPG campaign. You read session transcripts and extract structured d100 roll table data.

The transcript is from a historical simulation game (Castile, 1430s). A GM (labeled "GM") and player (labeled "PLAYER") interact. The GM frequently presents d100 roll tables with numbered outcome ranges, then the player reports their dice roll, and the GM narrates the result.

YOUR TASK: Find EVERY d100 roll table in the transcript and extract it as structured data.

HOW TO IDENTIFY A D100 ROLL TABLE:
- The GM presents numbered ranges that span 1-100 (e.g., "1-10: ...", "11-25: ...", "26-40: ..." etc.)
- Each range has a label and a description of what happens
- The ranges cover the full 1-100 spectrum (though exact breakpoints vary)
- After the table, the player reports a roll result (e.g., "I rolled 33", "Roll: 74", "d100 result: 51")
- The GM then narrates the outcome matching that range

CRITICAL RULES:
1. Extract EVERY table in the chapter, not just the first one
2. Include ALL ranges from each table — don't skip any, even single-value ranges like "100"
3. The "rolled" field is the actual number the player reported
4. The "outcome_range" is the specific range that contains the rolled value
5. For dates: use the IN-GAME date (1430s era), not real-world timestamps
6. For roll_type, classify as one of: military, diplomacy, persuasion, chaos, travel, espionage, religion, economy, intrigue, personal
7. If a table is presented but the player hasn't rolled against it yet (or the roll is in a later chapter), set rolled to null
8. For the summary in each range: capture the key outcome in 1-2 sentences, preserving specific numbers and details
9. Some rolls may appear WITHOUT a formal table (GM just states a result). Skip these — only extract rolls that have explicit numbered ranges.

RESPOND WITH VALID JSON ONLY. No markdown fences, no commentary outside the JSON object.

Output schema:
{
  "tables": [
    {
      "title": "Brief descriptive title for this roll",
      "context": "Roll Type — 1-2 sentence description of the situation and why this roll is happening",
      "roll_type": "chaos|persuasion|military|diplomacy|travel|espionage|religion|economy|intrigue|personal",
      "date": "YYYY-MM-DD",
      "rolled": 33,
      "outcome_range": "31-45",
      "outcome_label": "Label of the matched range",
      "ranges": [
        {"range": "1-5", "label": "Short Label", "summary": "1-2 sentence description of this outcome"},
        {"range": "6-15", "label": "...", "summary": "..."}
      ],
      "confidence": "high|medium|low"
    }
  ],
  "notes": "Any observations about edge cases, uncertain extractions, or tables that were hard to parse"
}

If the chapter contains NO d100 roll tables with explicit ranges, return:
{"tables": [], "notes": "No d100 roll tables found in this chapter"}"""


def build_user_prompt(chapter_id: str, transcript: str) -> str:
    """Build the user message for a chapter extraction."""
    return f"""# Chapter {chapter_id} — Extract all d100 roll tables

Read the full transcript below. Find every d100 roll table (numbered ranges from 1-100) and extract the complete table data.

Remember:
- Only extract rolls with EXPLICIT numbered range tables (not rolls where the GM just announces a result)
- Include every range in each table
- The rolled value is what the PLAYER reported, not the range
- Use in-game dates (1430s), not real-world dates

## Transcript

{transcript}"""


# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

def extract_json_from_response(text: str) -> dict | None:
    """Parse JSON from the API response, handling common formatting issues."""
    text = text.strip()

    # Remove markdown fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the text
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
    return None


def validate_table(table: dict) -> list[str]:
    """Validate a single extracted table, return list of warnings."""
    warnings = []

    # Check required fields
    for field in ["title", "rolled", "ranges"]:
        if field not in table:
            warnings.append(f"Missing field: {field}")

    # Check ranges cover 1-100
    ranges = table.get("ranges", [])
    if not ranges:
        warnings.append("Empty ranges array")
    else:
        # Parse range strings to check coverage
        covered = set()
        for r in ranges:
            range_str = r.get("range", "")
            m = re.match(r"(\d+)(?:-(\d+))?", range_str)
            if m:
                low = int(m.group(1))
                high = int(m.group(2)) if m.group(2) else low
                covered.update(range(low, high + 1))

        if 1 not in covered:
            warnings.append("Ranges don't start at 1")
        if 100 not in covered:
            warnings.append("Ranges don't reach 100")

        missing = set(range(1, 101)) - covered
        if missing:
            warnings.append(f"Gaps in ranges: {len(missing)} values uncovered")

    # Check rolled value falls in outcome_range
    rolled = table.get("rolled")
    outcome_range = table.get("outcome_range", "")
    if rolled is not None and outcome_range:
        m = re.match(r"(\d+)(?:-(\d+))?", outcome_range)
        if m:
            low = int(m.group(1))
            high = int(m.group(2)) if m.group(2) else low
            if not (low <= rolled <= high):
                warnings.append(f"Rolled {rolled} not in outcome_range {outcome_range}")

    return warnings


def process_chapter(chapter_id: str, api_key: str, dry_run: bool = False,
                    force: bool = False) -> dict:
    """Process a single chapter and extract roll tables."""
    output_path = OUTPUT_DIR / f"chapter_{chapter_id}.json"

    # Check if already extracted
    if output_path.exists() and not force:
        print(f"  SKIP {chapter_id} — already extracted (use --force to re-extract)")
        return {"status": "skipped", "tables": 0}

    # Find source file
    source_path = find_source_file(chapter_id)
    if not source_path:
        print(f"  ERROR {chapter_id} — source file not found")
        return {"status": "error", "tables": 0, "error": "Source not found"}

    # Load and format
    messages = load_source_chapter(source_path)
    transcript = format_messages_for_prompt(messages)
    prompt = build_user_prompt(chapter_id, transcript)

    file_size_kb = source_path.stat().st_size / 1024
    est_tokens = len(transcript) // 4
    print(f"  {chapter_id}: {len(messages)} messages, {file_size_kb:.0f}KB, ~{est_tokens:,} tokens")

    if dry_run:
        return {"status": "dry_run", "tables": 0, "est_tokens": est_tokens}

    # Call API
    print(f"    Calling Haiku...")
    start = time.time()
    result = call_haiku(api_key, SYSTEM_PROMPT, prompt)
    elapsed = time.time() - start

    if result["error"]:
        print(f"    ERROR: {result['error']}")
        return {"status": "error", "tables": 0, "error": result["error"]}

    usage = result["usage"]
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cost_input = input_tokens * 0.80 / 1_000_000
    cost_output = output_tokens * 4.00 / 1_000_000
    cost_total = cost_input + cost_output
    print(f"    {elapsed:.1f}s — {input_tokens:,} in / {output_tokens:,} out — ${cost_total:.4f}")

    # Parse response
    parsed = extract_json_from_response(result["text"])
    if not parsed:
        print(f"    ERROR: Failed to parse JSON response")
        # Save raw response for debugging
        error_path = OUTPUT_DIR / f"chapter_{chapter_id}_error.txt"
        error_path.parent.mkdir(parents=True, exist_ok=True)
        error_path.write_text(result["text"], encoding="utf-8")
        return {"status": "parse_error", "tables": 0}

    tables = parsed.get("tables", [])
    notes = parsed.get("notes", "")

    # Validate tables
    for i, table in enumerate(tables):
        warnings = validate_table(table)
        if warnings:
            print(f"    Table {i+1} warnings: {'; '.join(warnings)}")

    # Save extraction
    output = {
        "chapter": chapter_id,
        "book": int(chapter_id.split(".")[0]),
        "extraction_date": datetime.now().isoformat(),
        "model": API_MODEL,
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens,
                  "cost_usd": round(cost_total, 4)},
        "table_count": len(tables),
        "tables": tables,
        "notes": notes,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"    Saved {len(tables)} table(s) → {output_path.name}")

    return {"status": "ok", "tables": len(tables), "cost": cost_total}


# ---------------------------------------------------------------------------
# Merge command
# ---------------------------------------------------------------------------

def cmd_merge(args):
    """Merge per-chapter extractions into roll_tables.json."""
    if not OUTPUT_DIR.exists():
        print("No extractions found. Run 'extract' first.")
        sys.exit(1)

    extraction_files = sorted(OUTPUT_DIR.glob("chapter_*.json"),
                              key=lambda p: _chapter_sort_key(p.stem.replace("chapter_", "")))

    all_tables = []
    total_files = 0
    skipped_errors = 0

    for path in extraction_files:
        if path.name.endswith("_error.txt"):
            continue

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        chapter_id = data.get("chapter", "")
        tables = data.get("tables", [])
        total_files += 1

        for i, table in enumerate(tables):
            seq = str(i + 1).zfill(3)
            ch_label = chapter_id.replace(".", "_")
            table_id = f"roll_ch{ch_label}_{seq}"

            entry = {
                "id": table_id,
                "chapter": chapter_id,
                "event_id": "",  # To be linked later
                "title": table.get("title", ""),
                "context": table.get("context", ""),
                "date": table.get("date", ""),
                "rolled": table.get("rolled"),
                "outcome_range": table.get("outcome_range", ""),
                "outcome_label": table.get("outcome_label", ""),
                "ranges": table.get("ranges", []),
            }
            all_tables.append(entry)

    # Sort by chapter then position
    all_tables.sort(key=lambda t: (_chapter_sort_key(t["chapter"]),
                                    t["id"]))

    # Build output
    output = {
        "meta": {
            "description": "d100 roll tables from the campaign. Each table records the full range of outcomes and the actual roll result.",
            "version": "2.0",
            "generated": datetime.now().isoformat(),
            "source_chapters": total_files,
        },
        "next_table_id": len(all_tables) + 1,
        "tables": all_tables,
    }

    if args.dry_run:
        print(f"\nDry run: would write {len(all_tables)} tables from {total_files} chapters")
        # Show sample
        for t in all_tables[:5]:
            print(f"  {t['id']}: {t['title']} (ch {t['chapter']}, rolled {t['rolled']})")
        if len(all_tables) > 5:
            print(f"  ... and {len(all_tables) - 5} more")
        return

    with open(ROLL_TABLES_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    size_kb = ROLL_TABLES_FILE.stat().st_size / 1024
    print(f"\nMerged {len(all_tables)} tables from {total_files} chapters")
    print(f"Written to {ROLL_TABLES_FILE} ({size_kb:.1f}KB)")


# ---------------------------------------------------------------------------
# Status command
# ---------------------------------------------------------------------------

def cmd_status(args):
    """Show extraction progress."""
    all_chapters = discover_all_chapters()
    d100_chapters = [ch for ch in all_chapters if is_d100_chapter(ch)]
    d6_chapters = [ch for ch in all_chapters if not is_d100_chapter(ch)]

    print(f"Source chapters found: {len(all_chapters)}")
    print(f"  d6 (skipped):  {len(d6_chapters)} — chapters {d6_chapters[0]} to {d6_chapters[-1]}" if d6_chapters else "  d6: none")
    print(f"  d100 (target):  {len(d100_chapters)} — chapters {d100_chapters[0]} to {d100_chapters[-1]}" if d100_chapters else "  d100: none")

    # Check extraction status
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    extracted = set()
    total_tables = 0
    total_cost = 0.0

    for path in OUTPUT_DIR.glob("chapter_*.json"):
        if path.name.endswith("_error.txt"):
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        ch = data.get("chapter", "")
        extracted.add(ch)
        total_tables += data.get("table_count", 0)
        total_cost += data.get("usage", {}).get("cost_usd", 0)

    remaining = [ch for ch in d100_chapters if ch not in extracted]
    print(f"\nExtraction progress:")
    print(f"  Extracted: {len(extracted)} chapters ({total_tables} tables, ${total_cost:.2f})")
    print(f"  Remaining: {len(remaining)} chapters")

    if remaining:
        print(f"  Next: {', '.join(remaining[:10])}" + (" ..." if len(remaining) > 10 else ""))

    # Check existing roll_tables.json
    if ROLL_TABLES_FILE.exists():
        with open(ROLL_TABLES_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        existing_count = len(existing.get("tables", []))
        print(f"\nroll_tables.json: {existing_count} tables currently")
    else:
        print(f"\nroll_tables.json: does not exist yet")


# ---------------------------------------------------------------------------
# Extract command
# ---------------------------------------------------------------------------

def _chapter_sort_key(ch: str):
    """Sort key for chapter IDs like '1.11' or '2.5'."""
    parts = ch.split(".")
    return (int(parts[0]), int(parts[1]))


def resolve_chapter_range(from_ch: str, to_ch: str, available: list[str]) -> list[str]:
    """Get all chapters in a range."""
    from_key = _chapter_sort_key(from_ch)
    to_key = _chapter_sort_key(to_ch)
    return [ch for ch in available if from_key <= _chapter_sort_key(ch) <= to_key]


def cmd_extract(args):
    """Extract roll tables from source chapters."""
    all_chapters = discover_all_chapters()
    d100_chapters = [ch for ch in all_chapters if is_d100_chapter(ch)]

    # Determine which chapters to process
    if args.chapter:
        targets = [args.chapter]
    elif args.from_ch and args.to_ch:
        targets = resolve_chapter_range(args.from_ch, args.to_ch, d100_chapters)
    elif args.all:
        targets = d100_chapters
    else:
        print("Specify --chapter, --from/--to, or --all")
        sys.exit(1)

    # Filter to d100 only (warn about d6 chapters)
    final_targets = []
    for ch in targets:
        if not is_d100_chapter(ch):
            print(f"  SKIP {ch} — d6 chapter (no range tables)")
        elif find_source_file(ch) is None:
            print(f"  SKIP {ch} — source file not found")
        else:
            final_targets.append(ch)

    if not final_targets:
        print("No chapters to process.")
        return

    print(f"\nProcessing {len(final_targets)} chapter(s)...")
    if args.dry_run:
        print("(DRY RUN — no API calls)\n")

    api_key = "" if args.dry_run else get_api_key()

    stats = {"ok": 0, "skipped": 0, "error": 0, "total_tables": 0, "total_cost": 0.0}
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for i, ch in enumerate(final_targets):
        print(f"\n[{i+1}/{len(final_targets)}] Chapter {ch}")
        result = process_chapter(ch, api_key, dry_run=args.dry_run, force=args.force)

        status = result.get("status", "error")
        stats[status] = stats.get(status, 0) + 1
        stats["total_tables"] += result.get("tables", 0)
        stats["total_cost"] += result.get("cost", 0)

        # Brief pause between API calls to be respectful
        if not args.dry_run and status == "ok" and i < len(final_targets) - 1:
            time.sleep(1)

    print(f"\n{'='*50}")
    print(f"Done. {stats['ok']} extracted, {stats['skipped']} skipped, {stats.get('error', 0) + stats.get('parse_error', 0)} errors")
    print(f"Total: {stats['total_tables']} tables, ${stats['total_cost']:.2f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Extract roll tables from source material")
    subparsers = parser.add_subparsers(dest="command")

    # Extract command
    p_extract = subparsers.add_parser("extract", help="Extract roll tables from chapters")
    p_extract.add_argument("--chapter", type=str, help="Single chapter ID (e.g., 2.1)")
    p_extract.add_argument("--from", dest="from_ch", type=str, help="Start of range")
    p_extract.add_argument("--to", dest="to_ch", type=str, help="End of range")
    p_extract.add_argument("--all", action="store_true", help="Process all d100 chapters")
    p_extract.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    p_extract.add_argument("--force", action="store_true", help="Re-extract already-extracted chapters")

    # Merge command
    p_merge = subparsers.add_parser("merge", help="Merge extractions into roll_tables.json")
    p_merge.add_argument("--dry-run", action="store_true", help="Preview without writing")

    # Status command
    subparsers.add_parser("status", help="Show extraction progress")

    args = parser.parse_args()

    if args.command == "extract":
        cmd_extract(args)
    elif args.command == "merge":
        cmd_merge(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        # Default: show status
        parser.print_help()


if __name__ == "__main__":
    main()
