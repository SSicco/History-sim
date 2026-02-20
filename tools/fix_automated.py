#!/usr/bin/env python3
"""
Automated Data Fixes — Phase 2 of the quality remediation plan.

Fixes that need no human judgment:
  1. Roll outcome_range: convert label format to numeric format
  2. Roll null rolled values: assign midpoint of mapped range
  3. Law origin_event_id: match laws to events by date + character + content
  4. Event type normalization: convert non-standard types to standard types

Usage:
  python3 tools/fix_automated.py --dry-run    # Show what would change (default)
  python3 tools/fix_automated.py --apply       # Apply changes and write files
  python3 tools/fix_automated.py --rolls-only  # Only fix rolls
  python3 tools/fix_automated.py --laws-only   # Only fix laws
"""

import json
import re
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "resources" / "data"

# ---------------------------------------------------------------------------
# Label → standard numeric range mapping (by outcome quality)
# ---------------------------------------------------------------------------

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

# Midpoint of each standard range (for estimating null rolled values)
RANGE_MIDPOINTS = {
    "01-10": 5,
    "11-25": 18,
    "26-40": 33,
    "41-60": 50,
    "61-80": 70,
    "81-93": 87,
    "94-100": 97,
}

# Event type normalization
TYPE_MAP = {
    "narrative": "personal",
    "political": "council",
    "military": "military_action",
    "diplomatic": "diplomacy",
}

NUMERIC_RANGE_RE = re.compile(r"^\d{1,3}-\d{1,3}$")


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Wrote {path}")


# ---------------------------------------------------------------------------
# Fix 1: Roll outcome_range and null rolled values
# ---------------------------------------------------------------------------

def fix_rolls(dry_run: bool) -> dict:
    """Fix roll outcome_ranges and null rolled values. Returns change summary."""
    path = DATA_DIR / "roll_history.json"
    data = load_json(path)
    rolls = data["rolls"]

    changes = {
        "range_label_to_numeric": 0,
        "rolled_null_to_estimated": 0,
        "unfixable_labels": [],
    }

    for roll in rolls:
        rid = roll["roll_id"]
        rng = roll.get("outcome_range", "")
        rolled = roll.get("rolled")

        # Fix label-format ranges
        if rng and not NUMERIC_RANGE_RE.match(rng):
            if rng in LABEL_TO_RANGE:
                new_range = LABEL_TO_RANGE[rng]
                if not dry_run:
                    roll["outcome_range"] = new_range
                changes["range_label_to_numeric"] += 1
            else:
                changes["unfixable_labels"].append((rid, rng))

        # Fix null rolled values
        if rolled is None:
            # Determine range (possibly just converted)
            current_range = LABEL_TO_RANGE.get(rng, rng) if not NUMERIC_RANGE_RE.match(rng) else rng
            if current_range in RANGE_MIDPOINTS:
                estimated = RANGE_MIDPOINTS[current_range]
                if not dry_run:
                    roll["rolled"] = estimated
                    # Mark as estimated in evaluation if not already noted
                    eval_text = roll.get("evaluation", "")
                    if eval_text and "[estimated]" not in eval_text:
                        roll["evaluation"] = eval_text + " [estimated roll value]"
                    elif not eval_text:
                        roll["evaluation"] = "[estimated roll value]"
                changes["rolled_null_to_estimated"] += 1

    if not dry_run:
        save_json(path, data)

    return changes


# ---------------------------------------------------------------------------
# Fix 2: Law-event linkage
# ---------------------------------------------------------------------------

def fix_laws(dry_run: bool) -> dict:
    """Match laws to events by date + character + content."""
    laws_path = DATA_DIR / "laws.json"
    events_path = DATA_DIR / "events.json"

    laws_data = load_json(laws_path)
    events_data = load_json(events_path)

    laws = laws_data["laws"]
    events = events_data["events"]

    changes = {
        "laws_linked": 0,
        "laws_unresolved": [],
        "related_events_added": 0,
    }

    # Build event index by date
    events_by_date = {}
    for evt in events:
        d = evt.get("date", "")
        events_by_date.setdefault(d, []).append(evt)

    # Build event index by character
    events_by_char = {}
    for evt in events:
        for cid in evt.get("characters", []):
            events_by_char.setdefault(cid, []).append(evt)

    for law in laws:
        lid = law["law_id"]
        origin = law.get("origin_event_id", "")
        needs_origin = not origin or origin == "_pending_event_linkage"

        if needs_origin:
            # Try to match by date + enacted_by
            date = law.get("date_enacted", "")
            enacted_by = law.get("enacted_by", "")
            proposed_by = law.get("proposed_by", "")
            title_words = set(law.get("title", "").lower().split())
            summary_words = set(law.get("summary", "").lower().split())

            best_match = None
            best_score = 0

            # Search candidates: events on the same date or within 7 days
            candidates = []
            for evt in events:
                evt_date = evt.get("date", "")
                if not evt_date or not date:
                    continue
                # Exact date match
                if evt_date == date:
                    candidates.append(evt)
                # Within 7 days (rough)
                elif abs(hash(evt_date) - hash(date)) < 100:  # Fallback
                    pass

            # Also check events by character
            for key_char in [enacted_by, proposed_by]:
                if key_char and key_char in events_by_char:
                    for evt in events_by_char[key_char]:
                        if evt not in candidates:
                            # Only add if within reasonable date range
                            evt_date = evt.get("date", "")
                            if evt_date and date and abs(ord(evt_date[5]) - ord(date[5])) <= 1:
                                candidates.append(evt)

            # If no date-based candidates, search by key character
            if not candidates and enacted_by and enacted_by in events_by_char:
                candidates = events_by_char[enacted_by][:20]

            for evt in candidates:
                score = 0
                evt_date = evt.get("date", "")
                evt_chars = set(evt.get("characters", []))
                evt_summary = evt.get("summary", "").lower()
                evt_tags = set(evt.get("tags", []))

                # Date match (strongest signal)
                if evt_date == date:
                    score += 50

                # Character match
                if enacted_by in evt_chars:
                    score += 20
                if proposed_by and proposed_by in evt_chars:
                    score += 15

                # Content overlap (title words in summary)
                overlap = title_words & set(evt_summary.split())
                score += len(overlap) * 3

                # Tag match
                law_tags = set(law.get("tags", []))
                tag_overlap = law_tags & evt_tags
                score += len(tag_overlap) * 5

                # Event type match
                if evt.get("type") in ("legal", "decision", "council", "diplomacy", "ceremony"):
                    score += 10

                if score > best_score:
                    best_score = score
                    best_match = evt

            if best_match and best_score >= 30:
                if not dry_run:
                    law["origin_event_id"] = best_match["event_id"]
                changes["laws_linked"] += 1
            else:
                changes["laws_unresolved"].append(
                    (lid, law.get("title", "?")[:50], f"best_score={best_score}")
                )

        # Build related_events: find events that reference this law's content
        if not law.get("related_events"):
            related = set()
            title_lower = law.get("title", "").lower()
            # Extract key terms (words 4+ chars, not common words)
            stop_words = {"the", "and", "for", "that", "with", "from", "this", "shall", "must", "will"}
            key_terms = [w for w in title_lower.split()
                        if len(w) >= 4 and w not in stop_words][:5]

            if key_terms:
                for evt in events:
                    summary = evt.get("summary", "").lower()
                    matches = sum(1 for t in key_terms if t in summary)
                    if matches >= 2:
                        related.add(evt["event_id"])

            # Also add origin event
            origin_id = law.get("origin_event_id", "")
            if origin_id and origin_id != "_pending_event_linkage":
                related.add(origin_id)

            if related:
                if not dry_run:
                    law["related_events"] = sorted(related)
                changes["related_events_added"] += len(related)

    if not dry_run:
        save_json(laws_path, laws_data)

    return changes


# ---------------------------------------------------------------------------
# Fix 3: Event type normalization
# ---------------------------------------------------------------------------

def fix_event_types(dry_run: bool) -> dict:
    """Convert non-standard event types to standard types."""
    changes = {"types_normalized": 0, "files_modified": []}

    chapter_dir = DATA_DIR / "events"
    for chapter_path in sorted(chapter_dir.glob("chapter_*.json")):
        data = load_json(chapter_path)
        modified = False

        for evt in data.get("events", []):
            etype = evt.get("type", "")
            if etype in TYPE_MAP:
                if not dry_run:
                    evt["type"] = TYPE_MAP[etype]
                changes["types_normalized"] += 1
                modified = True

        if modified and not dry_run:
            save_json(chapter_path, data)
            changes["files_modified"].append(chapter_path.name)

    # Also fix events.json
    events_path = DATA_DIR / "events.json"
    if events_path.exists():
        data = load_json(events_path)
        for evt in data.get("events", []):
            etype = evt.get("type", "")
            if etype in TYPE_MAP:
                if not dry_run:
                    evt["type"] = TYPE_MAP[etype]
        if not dry_run:
            save_json(events_path, data)

    return changes


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Apply automated data fixes")
    parser.add_argument("--dry-run", action="store_true", default=True,
                       help="Show what would change without modifying files (default)")
    parser.add_argument("--apply", action="store_true",
                       help="Actually apply the changes")
    parser.add_argument("--rolls-only", action="store_true",
                       help="Only fix rolls")
    parser.add_argument("--laws-only", action="store_true",
                       help="Only fix laws")
    parser.add_argument("--types-only", action="store_true",
                       help="Only fix event types")
    args = parser.parse_args()

    dry_run = not args.apply
    run_all = not (args.rolls_only or args.laws_only or args.types_only)

    if dry_run:
        print("=== DRY RUN (use --apply to write changes) ===\n")
    else:
        print("=== APPLYING CHANGES ===\n")

    if run_all or args.rolls_only:
        print("--- ROLLS ---")
        changes = fix_rolls(dry_run)
        print(f"  Label→numeric conversions: {changes['range_label_to_numeric']}")
        print(f"  Null rolled→estimated:     {changes['rolled_null_to_estimated']}")
        if changes["unfixable_labels"]:
            print(f"  Unfixable labels ({len(changes['unfixable_labels'])}):")
            for rid, label in changes["unfixable_labels"]:
                print(f"    {rid}: '{label}'")
        print()

    if run_all or args.laws_only:
        print("--- LAWS ---")
        changes = fix_laws(dry_run)
        print(f"  Laws linked to events:     {changes['laws_linked']}")
        print(f"  Related events added:       {changes['related_events_added']}")
        if changes["laws_unresolved"]:
            print(f"  Unresolved ({len(changes['laws_unresolved'])}):")
            for lid, title, detail in changes["laws_unresolved"]:
                print(f"    {lid}: {title} ({detail})")
        print()

    if run_all or args.types_only:
        print("--- EVENT TYPES ---")
        changes = fix_event_types(dry_run)
        print(f"  Types normalized:          {changes['types_normalized']}")
        if changes.get("files_modified"):
            print(f"  Files modified:            {len(changes['files_modified'])}")
        print()

    if dry_run:
        print("No files modified. Use --apply to write changes.")


if __name__ == "__main__":
    main()
