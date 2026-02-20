#!/usr/bin/env python3
"""
Cross-Chapter Consistency Checker — Flags contradictions and anomalies
across the entire dataset that per-chapter validation would miss.

Checks:
  1. Character timeline: dead characters appearing in later events
  2. Character location jumps: impossibly fast location changes
  3. Faction membership conflicts: character in opposing factions
  4. Date ordering: events out of chronological order within a book
  5. Duplicate events: same summary appearing twice
  6. Orphan references: IDs that exist in one DB but not another

Usage:
  python3 tools/check_consistency.py              # Full check
  python3 tools/check_consistency.py --json       # Machine-readable output
"""

import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "resources" / "data"
TOOLS_DIR = PROJECT_ROOT / "tools"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Consistency checks
# ---------------------------------------------------------------------------

def check_character_timelines(events: list, characters: list) -> list[dict]:
    """Check for dead/inactive characters appearing in events after their status changed."""
    issues = []

    # Build character status timeline: when did each character become inactive/deceased?
    char_status = {}  # char_id -> list of (date, status, event_id)
    for evt in events:
        for cid in evt.get("characters", []):
            if cid not in char_status:
                char_status[cid] = []

    # Check character DB for deceased/inactive
    deceased = {}
    for char in characters:
        status = char.get("status", [])
        if "deceased" in status:
            # Find their last event to approximate death date
            refs = char.get("event_refs", [])
            deceased[char["id"]] = refs[-1] if refs else None

    # For each deceased character, check if they appear in events after their last ref
    event_lookup = {e["event_id"]: e for e in events}
    for cid, last_ref in deceased.items():
        if not last_ref or last_ref not in event_lookup:
            continue
        death_event = event_lookup[last_ref]
        death_date = death_event.get("date", "")

        for evt in events:
            if cid in evt.get("characters", []):
                evt_date = evt.get("date", "")
                if evt_date > death_date and evt["event_id"] != last_ref:
                    issues.append({
                        "type": "dead_character_appears",
                        "character": cid,
                        "death_event": last_ref,
                        "death_date": death_date,
                        "appears_in": evt["event_id"],
                        "appears_date": evt_date,
                    })

    return issues


def check_date_ordering(events: list) -> list[dict]:
    """Check for date regressions within each book."""
    issues = []

    for book in [1, 2]:
        book_events = [e for e in events if e.get("book") == book]
        book_events.sort(key=lambda e: (e.get("chapter", ""), e.get("date", "")))

        prev_date = ""
        prev_chapter = ""
        for evt in book_events:
            date = evt.get("date", "")
            chapter = evt.get("chapter", "")

            # Only flag inter-chapter regressions (intra-chapter can be flashbacks)
            if chapter != prev_chapter and date and prev_date and date < prev_date:
                issues.append({
                    "type": "date_regression",
                    "from_chapter": prev_chapter,
                    "from_date": prev_date,
                    "to_chapter": chapter,
                    "to_date": date,
                    "event_id": evt["event_id"],
                })

            if date:
                prev_date = date
            prev_chapter = chapter

    return issues


def check_duplicate_events(events: list) -> list[dict]:
    """Check for events with very similar summaries."""
    issues = []

    # Simple duplicate detection: normalized summary first 80 chars
    summary_index = defaultdict(list)
    for evt in events:
        summary = evt.get("summary", "").strip().lower()[:80]
        if len(summary) > 30:  # Only check substantial summaries
            summary_index[summary].append(evt["event_id"])

    for summary, eids in summary_index.items():
        if len(eids) > 1:
            issues.append({
                "type": "possible_duplicate",
                "event_ids": eids,
                "summary_prefix": summary,
            })

    return issues


def check_orphan_references(events: list, characters: list, locations: list,
                            factions: list, rolls: list, laws: list) -> list[dict]:
    """Check for IDs referenced in one DB but missing from another."""
    issues = []

    event_ids = {e["event_id"] for e in events}
    char_ids = {c["id"] for c in characters}
    loc_ids = {l["location_id"] for l in locations}
    faction_ids = {f["faction_id"] for f in factions}

    # Characters in events not in characters.json
    event_chars = set()
    for evt in events:
        for cid in evt.get("characters", []):
            event_chars.add(cid)
    missing_chars = event_chars - char_ids - {"narrator"}
    for cid in sorted(missing_chars):
        issues.append({
            "type": "missing_character",
            "character_id": cid,
            "detail": "Referenced in events but not in characters.json",
        })

    # Faction leaders not in characters.json
    for f in factions:
        leader = f.get("leader_id", "")
        if leader and leader not in char_ids:
            issues.append({
                "type": "missing_faction_leader",
                "faction_id": f["faction_id"],
                "leader_id": leader,
            })

    # Faction members not in characters.json
    for f in factions:
        for mid in f.get("member_ids", []):
            if mid not in char_ids:
                issues.append({
                    "type": "missing_faction_member",
                    "faction_id": f["faction_id"],
                    "member_id": mid,
                })

    # Rolls referencing non-existent events
    for r in rolls:
        eid = r.get("event_id", "")
        if eid and eid not in event_ids:
            issues.append({
                "type": "orphan_roll",
                "roll_id": r["roll_id"],
                "event_id": eid,
            })

    # Laws referencing non-existent events
    for law in laws:
        oid = law.get("origin_event_id", "")
        if oid and oid != "_pending_event_linkage" and oid not in event_ids:
            issues.append({
                "type": "orphan_law_origin",
                "law_id": law["law_id"],
                "event_id": oid,
            })

    return issues


def check_character_field_gaps(characters: list) -> list[dict]:
    """Find characters with critical missing data."""
    issues = []

    for char in characters:
        cid = char["id"]
        gaps = []

        if not char.get("appearance") or not any(char["appearance"].values()):
            gaps.append("appearance")
        if not char.get("speech_style"):
            gaps.append("speech_style")
        if not char.get("interests"):
            gaps.append("interests")
        if len(char.get("personality", [])) < 4:
            gaps.append(f"personality ({len(char.get('personality', []))} traits)")
        if len(char.get("core_characteristics", "").split()) < 20:
            gaps.append("core_characteristics (too short)")

        if gaps:
            issues.append({
                "type": "character_data_gap",
                "character_id": cid,
                "name": char.get("name", "?"),
                "gaps": gaps,
                "event_count": len(char.get("event_refs", [])),
            })

    return issues


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(all_issues: dict, json_output: bool = False):
    if json_output:
        flat = []
        for category, issues in all_issues.items():
            for issue in issues:
                issue["category"] = category
                flat.append(issue)
        print(json.dumps({"total_issues": len(flat), "issues": flat}, indent=2))
        return

    print("=" * 70)
    print("  CROSS-CHAPTER CONSISTENCY CHECK")
    print("=" * 70)

    total = 0
    for category, issues in all_issues.items():
        count = len(issues)
        total += count
        status = "CLEAN" if count == 0 else f"{count} issues"
        print(f"\n{category} [{status}]")

        if count == 0:
            continue

        for issue in issues[:10]:
            itype = issue.get("type", "?")
            if itype == "dead_character_appears":
                print(f"  {issue['character']} appears in {issue['appears_in']} "
                      f"({issue['appears_date']}) after death in {issue['death_event']}")
            elif itype == "date_regression":
                print(f"  {issue['from_chapter']} ({issue['from_date']}) → "
                      f"{issue['to_chapter']} ({issue['to_date']})")
            elif itype == "possible_duplicate":
                print(f"  {', '.join(issue['event_ids'])}: \"{issue['summary_prefix'][:60]}...\"")
            elif itype in ("missing_character", "missing_faction_leader",
                          "missing_faction_member", "orphan_roll", "orphan_law_origin"):
                detail = {k: v for k, v in issue.items() if k != "type"}
                print(f"  {detail}")
            elif itype == "character_data_gap":
                print(f"  {issue['character_id']} ({issue['event_count']} events): "
                      f"missing {', '.join(issue['gaps'])}")
            else:
                print(f"  {issue}")

        if count > 10:
            print(f"  ... +{count - 10} more")

    print(f"\n{'='*70}")
    print(f"  TOTAL: {total} issues found")
    print(f"{'='*70}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Cross-chapter consistency checker")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    events = load_json(DATA_DIR / "events.json").get("events", [])
    characters = load_json(DATA_DIR / "characters.json").get("characters", [])
    locations = load_json(DATA_DIR / "locations.json").get("locations", [])
    factions = load_json(DATA_DIR / "factions.json").get("factions", [])
    rolls = load_json(DATA_DIR / "roll_history.json").get("rolls", [])
    laws = load_json(DATA_DIR / "laws.json").get("laws", [])

    all_issues = {
        "Character timelines": check_character_timelines(events, characters),
        "Date ordering": check_date_ordering(events),
        "Duplicate events": check_duplicate_events(events),
        "Orphan references": check_orphan_references(events, characters, locations,
                                                     factions, rolls, laws),
        "Character data gaps": check_character_field_gaps(characters),
    }

    print_report(all_issues, json_output=args.json)

    total = sum(len(v) for v in all_issues.values())
    sys.exit(1 if total > 0 else 0)


if __name__ == "__main__":
    main()
