#!/usr/bin/env python3
"""
Build events.json from individual chapter JSON files.

Reads all resources/data/chapter_02_*.json files, extracts each encounter,
and maps it to the events.json schema defined in CONVENTIONS.md.

Field mapping:
    chapter file                 events.json
    ──────────────               ───────────
    id                     →     event_id
    date                   →     date
    parent chapter "2.5"   →     chapter (int: 2)
    type                   →     type
    recap                  →     summary
    participants           →     characters
    location               →     location
    (derived)              →     tags
    (always "resolved")    →     status
    (empty)                →     factions_affected

Usage:
    python3 tools/build_events.py                   # preview to stdout
    python3 tools/build_events.py --write            # write to resources/data/starter_events.json
    python3 tools/build_events.py --query cesarini   # find events involving a character
"""

import json
import glob
import os
import sys
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "resources", "data")
OUTPUT_PATH = os.path.join(DATA_DIR, "starter_events.json")


def load_chapter_files():
    """Load all chapter_02_*.json files sorted by filename."""
    pattern = os.path.join(DATA_DIR, "chapter_02_*.json")
    files = sorted(glob.glob(pattern))
    if not files:
        print(f"ERROR: No chapter files found in {DATA_DIR}", file=sys.stderr)
        sys.exit(1)
    return files


def extract_chapter_number(chapter_str):
    """Convert '2.5' → 2 (integer chapter number)."""
    return int(chapter_str.split(".")[0])


def extract_sequence(event_id):
    """Extract the numeric sequence from an event ID like 'evt_1433_00062' → 62."""
    match = re.search(r"_(\d+)$", event_id)
    return int(match.group(1)) if match else 0


def build_events():
    """Read all chapter files and build the events list."""
    events = []
    max_sequence = 0

    for filepath in load_chapter_files():
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        chapter_str = data.get("chapter", "2")
        chapter_int = extract_chapter_number(chapter_str)

        encounters = data.get("encounters", [])
        for enc in encounters:
            event_id = enc.get("id", "")
            if not event_id:
                print(f"  WARNING: encounter without id in {filename}, skipping",
                      file=sys.stderr)
                continue

            seq = extract_sequence(event_id)
            if seq > max_sequence:
                max_sequence = seq

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
            }
            events.append(event)

        print(f"  {filename}: {len(encounters)} encounters (ch. {chapter_str})",
              file=sys.stderr)

    # Sort by event_id to ensure chronological order
    events.sort(key=lambda e: e["event_id"])

    return {
        "events": events,
        "next_id": max_sequence + 1,
    }


def query_character(events_data, search_term):
    """Find all events involving a character (partial match on ID)."""
    search = search_term.lower()
    matches = []
    for evt in events_data["events"]:
        for char_id in evt["characters"]:
            if search in char_id.lower():
                matches.append(evt)
                break
    return matches


def print_event(evt, verbose=False):
    """Print a single event in readable format."""
    chars = ", ".join(evt["characters"])
    print(f"  {evt['event_id']}  [{evt['date']}]  {evt['type']}")
    print(f"    Location:   {evt['location']}")
    print(f"    Characters: {chars}")
    if evt["summary"]:
        # Wrap summary at ~90 chars
        summary = evt["summary"]
        if not verbose and len(summary) > 120:
            summary = summary[:117] + "..."
        print(f"    Summary:    {summary}")
    print()


def main():
    args = sys.argv[1:]

    # Build events from chapter files
    print("Reading chapter files...", file=sys.stderr)
    events_data = build_events()
    total = len(events_data["events"])
    next_id = events_data["next_id"]
    print(f"\nTotal: {total} events, next_id: {next_id}", file=sys.stderr)

    # Collect unique characters
    all_chars = set()
    for evt in events_data["events"]:
        all_chars.update(evt["characters"])
    print(f"Unique characters: {len(all_chars)}", file=sys.stderr)

    # --query mode: find events for a character
    if "--query" in args:
        idx = args.index("--query")
        if idx + 1 >= len(args):
            print("ERROR: --query requires a character name/id", file=sys.stderr)
            sys.exit(1)
        search = args[idx + 1]
        matches = query_character(events_data, search)
        print(f"\nEvents involving '{search}': {len(matches)}\n")
        for evt in matches:
            print_event(evt, verbose="--verbose" in args)
        return

    # --characters mode: list all unique character IDs
    if "--characters" in args:
        print(f"\nAll characters ({len(all_chars)}):\n")
        for char_id in sorted(all_chars):
            count = sum(1 for e in events_data["events"] if char_id in e["characters"])
            print(f"  {char_id:40s} ({count} events)")
        return

    # --write mode: save to starter_events.json
    if "--write" in args:
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(events_data, f, indent=2, ensure_ascii=False)
        print(f"\nWritten to {OUTPUT_PATH}", file=sys.stderr)
        return

    # Default: print summary + sample
    print(f"\nFirst 5 events:")
    for evt in events_data["events"][:5]:
        print_event(evt)

    print(f"Last 5 events:")
    for evt in events_data["events"][-5:]:
        print_event(evt)

    print(f"Run with --write to save to {OUTPUT_PATH}")
    print(f"Run with --query <name> to search by character")
    print(f"Run with --characters to list all characters")


if __name__ == "__main__":
    main()
