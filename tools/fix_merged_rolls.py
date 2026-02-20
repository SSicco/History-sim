#!/usr/bin/env python3
"""
Fix rolls introduced by the Haiku extraction + merge process.

Issues to fix:
  1. outcome_range has label format (e.g. "critical_success") instead of numeric
  2. rolled is None — Haiku hallucinated a roll that isn't a real d100 roll
  3. outcome_range is a descriptive phrase (e.g. "high probability of success")

Usage:
  python tools/fix_merged_rolls.py              # Dry run (default)
  python tools/fix_merged_rolls.py --apply      # Apply changes
"""

import json
import re
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "resources" / "data"

NUMERIC_RANGE_RE = re.compile(r"^\d{1,3}-\d{1,3}$")

# Label → standard numeric range mapping
LABEL_TO_RANGE = {
    "critical_failure": "01-10",
    "revolt": "01-10",
    "failure": "11-25",
    "mixed_negative": "26-40",
    "mixed": "26-40",
    "partial_failure": "26-40",
    "status_quo": "41-60",
    "success": "61-80",
    "strong_success": "81-93",
    "major_success": "81-93",
    "critical_success": "94-100",
}

RANGE_MIDPOINTS = {
    "01-10": 5,
    "11-25": 18,
    "26-40": 33,
    "41-60": 50,
    "61-80": 70,
    "81-93": 87,
    "94-100": 97,
}


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def infer_range_from_rolled(rolled):
    """Given a rolled value, return the standard range it falls in."""
    if rolled is None:
        return None
    v = int(rolled)
    if v <= 10:
        return "01-10"
    elif v <= 25:
        return "11-25"
    elif v <= 40:
        return "26-40"
    elif v <= 60:
        return "41-60"
    elif v <= 80:
        return "61-80"
    elif v <= 93:
        return "81-93"
    else:
        return "94-100"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not args.apply:
        print("=== DRY RUN (use --apply to write changes) ===\n")

    rolls_db = load_json(DATA_DIR / "roll_history.json")
    rolls = rolls_db.get("rolls", [])

    print(f"Total rolls: {len(rolls)}\n")

    # Stats
    labels_fixed = 0
    phrases_fixed = 0
    nulls_removed = 0
    nulls_estimated = 0
    ranges_inferred = 0

    to_remove = []

    for i, r in enumerate(rolls):
        rid = r.get("roll_id", f"idx_{i}")
        rolled = r.get("rolled")
        rng = r.get("outcome_range") or ""

        # Fix 1: rolled is None
        if rolled is None:
            # Check if we can salvage — does the title/context suggest a real roll?
            # If outcome_range is a label, we can estimate. Otherwise remove.
            label_key = rng.lower().replace(" ", "_")
            if label_key in LABEL_TO_RANGE:
                numeric = LABEL_TO_RANGE[label_key]
                r["outcome_range"] = numeric
                r["rolled"] = RANGE_MIDPOINTS[numeric]
                r["evaluation"] = (r.get("evaluation") or "") + " [estimated roll value]"
                nulls_estimated += 1
                print(f"  {rid}: rolled=None, range='{rng}' → rolled={r['rolled']}, range='{numeric}' (estimated)")
                continue
            else:
                to_remove.append(i)
                nulls_removed += 1
                print(f"  {rid}: rolled=None, range='{rng}' → REMOVING (not a real d100 roll)")
                continue

        # Fix 2: outcome_range is a known label
        label_key = rng.lower().replace(" ", "_")
        if label_key in LABEL_TO_RANGE:
            old = rng
            r["outcome_range"] = LABEL_TO_RANGE[label_key]
            labels_fixed += 1
            print(f"  {rid}: range '{old}' → '{r['outcome_range']}'")
            continue

        # Fix 3: outcome_range is a descriptive phrase (not numeric, not a known label)
        if rng and not NUMERIC_RANGE_RE.match(rng):
            # Infer from rolled value
            inferred = infer_range_from_rolled(rolled)
            if inferred:
                old = rng
                r["outcome_range"] = inferred
                phrases_fixed += 1
                print(f"  {rid}: range '{old}' → '{inferred}' (inferred from rolled={rolled})")
                continue

        # Fix 4: outcome_range is empty/None but we have a rolled value
        if not rng and rolled is not None:
            inferred = infer_range_from_rolled(rolled)
            if inferred:
                r["outcome_range"] = inferred
                ranges_inferred += 1
                print(f"  {rid}: range empty → '{inferred}' (inferred from rolled={rolled})")

    # Remove null-rolled entries (iterate in reverse to preserve indices)
    for i in reversed(to_remove):
        rolls.pop(i)

    # Update meta
    rolls_db["meta"]["total_rolls"] = len(rolls)

    print(f"\n{'='*60}")
    print(f"Labels → numeric:        {labels_fixed}")
    print(f"Phrases → inferred:      {phrases_fixed}")
    print(f"Null rolled, estimated:  {nulls_estimated}")
    print(f"Null rolled, removed:    {nulls_removed}")
    print(f"Empty range, inferred:   {ranges_inferred}")
    print(f"Final roll count:        {len(rolls)}")
    print(f"{'='*60}")

    if args.apply:
        save_json(DATA_DIR / "roll_history.json", rolls_db)
        print(f"\nSaved roll_history.json ({len(rolls)} rolls)")
    else:
        print("\nDry run complete. Use --apply to write changes.")


if __name__ == "__main__":
    main()
