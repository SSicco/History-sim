#!/usr/bin/env python3
"""
Build Events Database — Split and merge events by chapter.

The chapter files in resources/data/events/ are the SOURCE OF TRUTH.
The merged events.json is a BUILD ARTIFACT generated from them.

Commands:
  split   — Split events.json into per-chapter files (one-time migration)
  merge   — Merge all chapter files back into events.json
  verify  — Check that a merge would produce identical output to current events.json
  status  — Show chapter file inventory and event counts

Usage:
  python3 tools/build_events_db.py split              # One-time: split events.json into chapters
  python3 tools/build_events_db.py merge              # Rebuild events.json from chapter files
  python3 tools/build_events_db.py merge --dry-run    # Preview without writing
  python3 tools/build_events_db.py verify             # Verify round-trip integrity
  python3 tools/build_events_db.py status             # Show chapter inventory
"""

import json
import sys
import argparse
from pathlib import Path
from collections import OrderedDict

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "resources" / "data"
EVENTS_FILE = DATA_DIR / "events.json"
CHAPTERS_DIR = DATA_DIR / "events"


def load_json(path: Path) -> dict:
    """Load a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data, indent: int = 2) -> None:
    """Save data to JSON with pretty formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
    print(f"  Wrote {path.name} ({path.stat().st_size:,} bytes)")


# ---------------------------------------------------------------------------
# Split: events.json → per-chapter files
# ---------------------------------------------------------------------------

def cmd_split(args):
    """Split events.json into per-chapter files."""
    if not EVENTS_FILE.exists():
        print(f"ERROR: {EVENTS_FILE} not found.")
        sys.exit(1)

    data = load_json(EVENTS_FILE)
    events = data.get("events", [])
    meta = data.get("meta", {})
    next_id = data.get("next_id", 1)

    if not events:
        print("No events found in events.json.")
        sys.exit(1)

    # Group events by chapter
    chapters = OrderedDict()
    for evt in events:
        ch = evt.get("chapter", "unknown")
        chapters.setdefault(ch, []).append(evt)

    # Check for existing chapter files
    existing = list(CHAPTERS_DIR.glob("chapter_*.json"))
    if existing and not args.force:
        print(f"ERROR: {len(existing)} chapter files already exist in {CHAPTERS_DIR}/")
        print("       Use --force to overwrite them.")
        sys.exit(1)

    # Write each chapter file
    CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Splitting {len(events)} events across {len(chapters)} chapters...\n")

    for chapter_id, chapter_events in chapters.items():
        # Build chapter file with its own mini-metadata
        chapter_data = {
            "chapter": chapter_id,
            "book": chapter_events[0].get("book", 1),
            "event_count": len(chapter_events),
            "date_range": _date_range(chapter_events),
            "events": chapter_events,
        }

        filename = f"chapter_{chapter_id}.json"
        save_json(CHAPTERS_DIR / filename, chapter_data)

    # Save merge metadata (next_id, version) separately
    merge_meta = {
        "version": meta.get("version", "2.0"),
        "next_id": next_id,
        "note": "This file stores metadata for the merge process. Do not edit.",
    }
    save_json(CHAPTERS_DIR / "_merge_meta.json", merge_meta)

    print(f"\nDone. {len(chapters)} chapter files written to {CHAPTERS_DIR}/")
    print(f"\nNext steps:")
    print(f"  1. Verify: python3 tools/build_events_db.py verify")
    print(f"  2. Add events.json to .gitignore")
    print(f"  3. Commit the chapter files")


# ---------------------------------------------------------------------------
# Merge: per-chapter files → events.json
# ---------------------------------------------------------------------------

def cmd_merge(args):
    """Merge all chapter files into events.json."""
    chapter_files = sorted(CHAPTERS_DIR.glob("chapter_*.json"))

    if not chapter_files:
        print(f"ERROR: No chapter files found in {CHAPTERS_DIR}/")
        sys.exit(1)

    # Load merge metadata
    meta_path = CHAPTERS_DIR / "_merge_meta.json"
    if meta_path.exists():
        merge_meta = load_json(meta_path)
    else:
        merge_meta = {"version": "2.0", "next_id": 1}

    # Collect all events in chapter order
    all_events = []
    print(f"Merging {len(chapter_files)} chapter files...\n")

    for cf in chapter_files:
        chapter_data = load_json(cf)
        events = chapter_data.get("events", [])
        chapter_id = chapter_data.get("chapter", cf.stem)
        all_events.extend(events)
        print(f"  {cf.name}: {len(events)} events")

    # Compute date range
    dates = [e["date"] for e in all_events if e.get("date")]
    date_range = f"{min(dates)} / {max(dates)}" if dates else ""

    # Build merged output
    merged = {
        "meta": {
            "version": merge_meta.get("version", "2.0"),
            "total_events": len(all_events),
            "date_range": date_range,
        },
        "next_id": merge_meta.get("next_id", 1),
        "events": all_events,
    }

    if args.dry_run:
        print(f"\n[DRY RUN] Would write {len(all_events)} events to {EVENTS_FILE}")
    else:
        save_json(EVENTS_FILE, merged)
        print(f"\nMerged {len(all_events)} events into {EVENTS_FILE.name}")


# ---------------------------------------------------------------------------
# Verify: check round-trip integrity
# ---------------------------------------------------------------------------

def cmd_verify(args):
    """Verify that merging chapter files reproduces events.json exactly."""
    if not EVENTS_FILE.exists():
        print("No events.json to verify against. Run 'merge' first.")
        sys.exit(1)

    chapter_files = sorted(CHAPTERS_DIR.glob("chapter_*.json"))
    if not chapter_files:
        print(f"No chapter files found in {CHAPTERS_DIR}/")
        sys.exit(1)

    # Load original
    original = load_json(EVENTS_FILE)
    original_events = original.get("events", [])

    # Build merged from chapters
    merged_events = []
    for cf in chapter_files:
        chapter_data = load_json(cf)
        merged_events.extend(chapter_data.get("events", []))

    # Compare
    if len(original_events) != len(merged_events):
        print(f"MISMATCH: original has {len(original_events)} events, "
              f"chapters have {len(merged_events)} events")
        sys.exit(1)

    mismatches = 0
    for i, (orig, merged) in enumerate(zip(original_events, merged_events)):
        if orig != merged:
            mismatches += 1
            if mismatches <= 5:
                print(f"  Event {i} ({orig.get('event_id', '?')}): DIFFERS")
                # Find which fields differ
                for key in set(list(orig.keys()) + list(merged.keys())):
                    if orig.get(key) != merged.get(key):
                        print(f"    Field '{key}' differs")

    if mismatches == 0:
        print(f"VERIFIED: All {len(original_events)} events match perfectly.")
        print("events.json can safely be treated as a build artifact.")
    else:
        print(f"\nFAILED: {mismatches} events differ between events.json and chapter files.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Status: show inventory
# ---------------------------------------------------------------------------

def cmd_status(args):
    """Show chapter file inventory."""
    chapter_files = sorted(CHAPTERS_DIR.glob("chapter_*.json"))

    if not chapter_files:
        print(f"No chapter files in {CHAPTERS_DIR}/")
        if EVENTS_FILE.exists():
            data = load_json(EVENTS_FILE)
            print(f"\nevents.json exists with {len(data.get('events', []))} events.")
            print("Run 'split' to create chapter files from it.")
        return

    total_events = 0
    total_bytes = 0

    print(f"{'Chapter':<12} {'Events':<8} {'Date Range':<30} {'Size':>10}")
    print("-" * 65)

    for cf in chapter_files:
        chapter_data = load_json(cf)
        events = chapter_data.get("events", [])
        chapter_id = chapter_data.get("chapter", cf.stem)
        dr = chapter_data.get("date_range", "")
        size = cf.stat().st_size

        total_events += len(events)
        total_bytes += size

        print(f"  {chapter_id:<10} {len(events):<8} {dr:<30} {size:>8,} B")

    print("-" * 65)
    print(f"  {'TOTAL':<10} {total_events:<8} {'':30} {total_bytes:>8,} B")

    if EVENTS_FILE.exists():
        ev_size = EVENTS_FILE.stat().st_size
        print(f"\n  events.json: {ev_size:,} bytes")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _date_range(events: list) -> str:
    """Compute date range string from a list of events."""
    dates = [e["date"] for e in events if e.get("date")]
    if not dates:
        return ""
    return f"{min(dates)} / {max(dates)}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Build events database from per-chapter source files"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # split
    sp_split = subparsers.add_parser("split", help="Split events.json into chapter files")
    sp_split.add_argument("--force", action="store_true", help="Overwrite existing chapter files")

    # merge
    sp_merge = subparsers.add_parser("merge", help="Merge chapter files into events.json")
    sp_merge.add_argument("--dry-run", action="store_true", help="Preview without writing")

    # verify
    subparsers.add_parser("verify", help="Verify round-trip integrity")

    # status
    subparsers.add_parser("status", help="Show chapter file inventory")

    args = parser.parse_args()

    if args.command == "split":
        cmd_split(args)
    elif args.command == "merge":
        cmd_merge(args)
    elif args.command == "verify":
        cmd_verify(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
