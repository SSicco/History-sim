#!/usr/bin/env python3
"""
Verify extraction quality across all chapters.
Shows what data each extraction file contains so you can spot gaps.

Usage:
  python tools/verify_extractions.py           # All chapters
  python tools/verify_extractions.py --book 1  # Book 1 only
"""

import json
import os
import sys
from pathlib import Path

EXTRACTIONS_DIR = Path(__file__).resolve().parent / "extractions"


def main():
    book_filter = None
    if "--book" in sys.argv:
        idx = sys.argv.index("--book")
        if idx + 1 < len(sys.argv):
            book_filter = int(sys.argv[idx + 1])

    files = sorted(EXTRACTIONS_DIR.glob("chapter_*_extracted.json"))
    if not files:
        print("No extraction files found!")
        return

    # Parse and sort by chapter number
    chapters = []
    for f in files:
        ch = f.stem.replace("chapter_", "").replace("_extracted", "")
        book_str, num_str = ch.split(".")
        book, num = int(book_str), int(num_str)
        if book_filter and book != book_filter:
            continue
        chapters.append((book * 100 + num, ch, f))
    chapters.sort()

    print(f"{'Ch':>5}  {'Evts':>4}  {'NewCh':>5}  {'ChUpd':>5}  {'Rolls':>5}  "
          f"{'RDet':>4}  {'Locs':>4}  {'Fac':>3}  {'Laws':>4}  {'Flags':>5}  Status")
    print("-" * 95)

    total_ok = 0
    total_warn = 0
    total_bad = 0
    issues = []

    for _, ch, fpath in chapters:
        data = json.load(open(fpath, encoding="utf-8"))

        n_events = len(data.get("events", []))
        n_new_chars = len(data.get("new_characters", []))
        n_updates = len(data.get("character_updates", []))
        n_rolls = len(data.get("rolls", []))
        n_new_locs = len(data.get("new_locations", []))
        n_factions = len(data.get("faction_updates", []))
        n_laws = len(data.get("law_references", []))
        n_flags = len(data.get("_review_flags", []))

        # Check roll detail quality
        rolls_detailed = 0
        for r in data.get("rolls", []):
            if r.get("outcome_detail") or r.get("evaluation") or r.get("success_factors"):
                rolls_detailed += 1

        # Check character update quality
        updates_filled = 0
        for cu in data.get("character_updates", []):
            if cu.get("current_task") or cu.get("task") or cu.get("location"):
                updates_filled += 1

        # Determine status
        flags = []
        if n_updates == 0 and n_new_chars == 0:
            flags.append("NO_CHARS")
        if n_rolls == 0:
            flags.append("NO_ROLLS")
        if n_rolls > 0 and rolls_detailed == 0:
            flags.append("ROLLS_EMPTY")
        if n_updates > 0 and updates_filled == 0:
            flags.append("UPDATES_EMPTY")

        if not flags:
            status = "OK"
            total_ok += 1
        elif "NO_CHARS" in flags and "NO_ROLLS" in flags:
            status = "STUB"
            total_bad += 1
            issues.append((ch, "Looks like a stub — no character data and no rolls"))
        else:
            status = " ".join(flags)
            total_warn += 1
            issues.append((ch, status))

        print(f"{ch:>5}  {n_events:>4}  {n_new_chars:>5}  {n_updates:>5}  {n_rolls:>5}  "
              f"{rolls_detailed:>4}  {n_new_locs:>4}  {n_factions:>3}  {n_laws:>4}  {n_flags:>5}  {status}")

    print("-" * 95)
    print(f"Total: {len(chapters)} chapters — {total_ok} OK, {total_warn} warnings, {total_bad} stubs/bad")

    if issues:
        print(f"\nIssues ({len(issues)}):")
        for ch, issue in issues:
            print(f"  {ch}: {issue}")


if __name__ == "__main__":
    main()
