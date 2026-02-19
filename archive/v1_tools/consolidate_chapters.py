#!/usr/bin/env python3
"""Merge all individual chapter JSON files into a single consolidated file.

Reads every chapter_*.json in resources/data/, combines them sorted by chapter
number, and writes resources/data/all_chapters.json. The individual chapter
files are kept as-is.

Usage:
    python tools/consolidate_chapters.py
"""

import json
import glob
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "resources", "data")
OUTPUT_FILE = os.path.join(DATA_DIR, "all_chapters.json")


def main():
    pattern = os.path.join(DATA_DIR, "chapter_*.json")
    files = sorted(glob.glob(pattern))

    if not files:
        print("No chapter files found.")
        sys.exit(1)

    chapters = []
    all_encounters = []

    for path in files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        chapter_info = {
            "chapter": data["chapter"],
            "title": data["title"],
            "date_range": data["date_range"],
            "encounter_count": len(data["encounters"]),
        }
        chapters.append(chapter_info)
        all_encounters.extend(data["encounters"])

        print(f"  Loaded {os.path.basename(path)}: chapter {data['chapter']} "
              f"— {len(data['encounters'])} encounters")

    # Sort encounters by their id to ensure chronological order
    all_encounters.sort(key=lambda e: e["id"])

    # Build date range from first and last encounter dates
    dates = [e["date"] for e in all_encounters if e.get("date")]
    overall_range = f"{min(dates)} / {max(dates)}" if dates else "unknown"

    consolidated = {
        "generated": True,
        "description": "Consolidated chapter data — do not edit manually. "
                       "Edit the individual chapter_*.json files instead.",
        "date_range": overall_range,
        "chapters": chapters,
        "encounters": all_encounters,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(consolidated, f, indent=2, ensure_ascii=False)

    print(f"\n[Done] Wrote {len(all_encounters)} encounters from "
          f"{len(chapters)} chapter(s) to {os.path.basename(OUTPUT_FILE)}")
    print(f"       Date range: {overall_range}")


if __name__ == "__main__":
    main()
