#!/usr/bin/env python3
"""
Assemble Chapter — Builds a chapter event file from event definitions + preprocessed messages.

Takes event definitions (message ranges + metadata) and a preprocessed chapter file,
copies full message text verbatim into exchanges, and outputs the chapter event file.

Usage:
  python3 tools/assemble_chapter.py 1.33 --defs tools/event_defs/chapter_1.33_defs.json
  python3 tools/assemble_chapter.py 1.33 --defs-stdin < defs.json
  python3 tools/assemble_chapter.py 1.33 --preview   # Show message index/preview for planning

Event definition format (JSON):
{
  "events": [
    {
      "msgs": [1, 18],
      "date": "1432-02-24",
      "type": "council",
      "summary": "...",
      "characters": ["juan_ii", "alvaro_de_luna"],
      "factions_affected": ["royal_court"],
      "location": "Toledo",
      "tags": ["politics"],
      "end_date": null
    },
    ...
  ]
}
"""

import json
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED_DIR = PROJECT_ROOT / "tools" / "preprocessed"
EVENTS_DIR = PROJECT_ROOT / "resources" / "data" / "events"
DEFS_DIR = PROJECT_ROOT / "tools" / "event_defs"


def load_preprocessed(chapter_id: str) -> dict:
    path = PREPROCESSED_DIR / f"chapter_{chapter_id}_preprocessed.json"
    if not path.exists():
        print(f"ERROR: Preprocessed file not found: {path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def preview_messages(chapter_id: str):
    """Show message indices and previews for planning event boundaries."""
    data = load_preprocessed(chapter_id)
    messages = data["messages"]
    print(f"Chapter {chapter_id}: {len(messages)} messages\n")
    for m in messages:
        preview = m["text"][:120].replace("\n", " ")
        print(f"  [{m['index']:3d}] {m['role']:6s}  {preview}...")
    print(f"\nTotal: {len(messages)} messages")


def assemble_chapter(chapter_id: str, event_defs: dict) -> dict:
    """Build a chapter event file from definitions + preprocessed messages."""
    data = load_preprocessed(chapter_id)
    messages = data["messages"]
    msg_by_index = {m["index"]: m for m in messages}

    book = int(chapter_id.split(".")[0])
    events = []

    for i, edef in enumerate(event_defs["events"]):
        start, end = edef["msgs"]

        # Collect exchanges (full text, verbatim)
        exchanges = []
        for idx in range(start, end + 1):
            if idx in msg_by_index:
                m = msg_by_index[idx]
                exchanges.append({
                    "role": m["role"],
                    "text": m["text"],
                })

        event = {
            "event_id": f"evt_PLACEHOLDER_{i+1:03d}",
            "book": book,
            "chapter": chapter_id,
            "date": edef["date"],
            "end_date": edef.get("end_date", None),
            "type": edef["type"],
            "summary": edef["summary"],
            "characters": edef["characters"],
            "factions_affected": edef.get("factions_affected", []),
            "location": edef["location"],
            "tags": edef.get("tags", []),
            "status": "resolved",
            "exchanges": exchanges,
            "roll": edef.get("roll", None),
        }
        events.append(event)

    # Compute date range
    dates = [e["date"] for e in events if e.get("date")]
    date_range = f"{min(dates)} / {max(dates)}" if dates else ""

    chapter_data = {
        "chapter": chapter_id,
        "book": book,
        "event_count": len(events),
        "date_range": date_range,
        "events": events,
    }

    return chapter_data


def main():
    parser = argparse.ArgumentParser(description="Assemble chapter event file from definitions")
    parser.add_argument("chapter", help="Chapter ID (e.g., 1.33)")
    parser.add_argument("--defs", type=str, help="Path to event definitions JSON file")
    parser.add_argument("--defs-stdin", action="store_true", help="Read definitions from stdin")
    parser.add_argument("--preview", action="store_true", help="Preview messages for planning")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    args = parser.parse_args()

    if args.preview:
        preview_messages(args.chapter)
        return

    # Load definitions
    if args.defs_stdin:
        event_defs = json.load(sys.stdin)
    elif args.defs:
        with open(args.defs, "r", encoding="utf-8") as f:
            event_defs = json.load(f)
    else:
        # Try default location
        default_path = DEFS_DIR / f"chapter_{args.chapter}_defs.json"
        if default_path.exists():
            with open(default_path, "r", encoding="utf-8") as f:
                event_defs = json.load(f)
        else:
            print(f"ERROR: No definitions found. Use --defs or --defs-stdin, or create {default_path}")
            sys.exit(1)

    # Assemble
    chapter_data = assemble_chapter(args.chapter, event_defs)

    if args.dry_run:
        total_exchanges = sum(len(e["exchanges"]) for e in chapter_data["events"])
        total_chars = sum(len(ex["text"]) for e in chapter_data["events"] for ex in e["exchanges"])
        print(f"Chapter {args.chapter}: {len(chapter_data['events'])} events, {total_exchanges} exchanges, {total_chars:,} chars")
        for e in chapter_data["events"]:
            print(f"  [{e['type']}] {e['date']} msgs {event_defs['events'][chapter_data['events'].index(e)]['msgs']} → {len(e['exchanges'])} exchanges")
            print(f"    {e['summary'][:100]}...")
    else:
        EVENTS_DIR.mkdir(parents=True, exist_ok=True)
        outpath = EVENTS_DIR / f"chapter_{args.chapter}.json"
        with open(outpath, "w", encoding="utf-8") as f:
            json.dump(chapter_data, f, indent=2, ensure_ascii=False)
        total_exchanges = sum(len(e["exchanges"]) for e in chapter_data["events"])
        total_chars = sum(len(ex["text"]) for e in chapter_data["events"] for ex in e["exchanges"])
        print(f"Wrote {outpath.name}: {len(chapter_data['events'])} events, {total_exchanges} exchanges, {total_chars:,} chars ({outpath.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
