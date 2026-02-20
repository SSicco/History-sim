#!/usr/bin/env python3
"""
Validate Quality — Checks all databases against QUALITY_STANDARD.md.

Reports PASS/FAIL per rule with counts and specific violations.
Complements verify_databases.py (which checks cross-reference integrity).

Usage:
  python3 tools/validate_quality.py                # Full report
  python3 tools/validate_quality.py --chapter 1.23 # Single chapter
  python3 tools/validate_quality.py --summary      # Counts only
  python3 tools/validate_quality.py --json          # Machine-readable output
"""

import json
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "resources" / "data"
TOOLS_DIR = PROJECT_ROOT / "tools"
EXTRACTIONS_DIR = TOOLS_DIR / "extractions"

# Outcome range label-to-numeric mapping
LABEL_TO_RANGE = {
    "critical_failure": "01-10",
    "failure": "11-25",
    "partial_failure": "26-40",
    "status_quo": "41-60",
    "success": "61-80",
    "major_success": "81-93",
    "critical_success": "94-100",
}

VALID_NUMERIC_RANGES = {"01-10", "11-25", "26-40", "41-60", "61-80", "81-93", "94-100"}

VALID_EVENT_TYPES = {
    "council", "decision", "military_action", "battle", "siege", "diplomacy",
    "negotiation", "ceremony", "personal", "intrigue", "espionage", "travel",
    "religious", "economic", "legal", "crisis", "discovery", "chapter_wrap",
    # Allow some near-matches that exist in data
    "military", "political",
}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def word_count(s: str) -> int:
    if not s:
        return 0
    return len(s.split())


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------

class CheckResult:
    def __init__(self, name: str, category: str):
        self.name = name
        self.category = category
        self.passed = True
        self.total = 0
        self.failures = 0
        self.violations = []  # (item_id, detail)

    def check(self, item_id: str, condition: bool, detail: str = ""):
        self.total += 1
        if not condition:
            self.passed = False
            self.failures += 1
            self.violations.append((item_id, detail))

    @property
    def status(self):
        return "PASS" if self.passed else "FAIL"


class QualityReport:
    def __init__(self):
        self.checks: list[CheckResult] = []

    def add(self, check: CheckResult):
        self.checks.append(check)

    def print_report(self, summary_only=False, max_violations=5):
        categories = {}
        for c in self.checks:
            categories.setdefault(c.category, []).append(c)

        total_pass = sum(1 for c in self.checks if c.passed)
        total_fail = sum(1 for c in self.checks if not c.passed)

        print("=" * 70)
        print("  QUALITY VALIDATION REPORT")
        print("=" * 70)
        print()

        for cat_name, checks in categories.items():
            cat_total = checks[0].total if checks else 0
            print(f"{cat_name} ({cat_total} items)")

            for c in checks:
                if c.passed:
                    print(f"  [{c.status}] {c.name}")
                else:
                    print(f"  [{c.status}] {c.name} — {c.failures}/{c.total} failing")
                    if not summary_only:
                        for item_id, detail in c.violations[:max_violations]:
                            msg = f"         {item_id}"
                            if detail:
                                msg += f": {detail}"
                            print(msg)
                        if len(c.violations) > max_violations:
                            print(f"         ... +{len(c.violations) - max_violations} more")
            print()

        print("-" * 70)
        print(f"  TOTAL: {total_pass} passed, {total_fail} failed, "
              f"{len(self.checks)} checks")
        print("-" * 70)

        return total_fail == 0

    def to_json(self):
        return {
            "total_checks": len(self.checks),
            "passed": sum(1 for c in self.checks if c.passed),
            "failed": sum(1 for c in self.checks if not c.passed),
            "checks": [
                {
                    "category": c.category,
                    "name": c.name,
                    "status": c.status,
                    "total": c.total,
                    "failures": c.failures,
                    "violations": [{"id": v[0], "detail": v[1]} for v in c.violations],
                }
                for c in self.checks
            ],
        }


# ---------------------------------------------------------------------------
# Event checks
# ---------------------------------------------------------------------------

EVENT_REQUIRED_FIELDS = [
    "event_id", "book", "chapter", "date", "end_date", "type", "summary",
    "characters", "factions_affected", "location", "tags", "status",
    "exchanges", "roll",
]


def check_events(events: list, char_ids: set, chapter_filter: str = None) -> list[CheckResult]:
    results = []

    if chapter_filter:
        events = [e for e in events if e.get("chapter") == chapter_filter]

    cat = f"EVENTS ({len(events)})"

    # Required fields
    c = CheckResult("All events have required fields", cat)
    for evt in events:
        missing = [f for f in EVENT_REQUIRED_FIELDS if f not in evt]
        if missing:
            c.check(evt.get("event_id", "?"), False, f"missing: {', '.join(missing)}")
        else:
            c.check(evt.get("event_id", "?"), True)
    results.append(c)

    # Characters array non-empty and valid
    c = CheckResult("Characters array non-empty, all IDs in characters.json", cat)
    for evt in events:
        chars = evt.get("characters", [])
        eid = evt.get("event_id", "?")
        if not chars:
            c.check(eid, False, "empty characters array")
        else:
            unknown = [cid for cid in chars if cid not in char_ids and cid != "narrator"]
            if unknown:
                c.check(eid, False, f"unknown: {', '.join(unknown)}")
            else:
                c.check(eid, True)
    results.append(c)

    # Tags non-empty
    c = CheckResult("Tags array non-empty", cat)
    for evt in events:
        c.check(evt.get("event_id", "?"), bool(evt.get("tags", [])))
    results.append(c)

    # Exchanges minimum 2
    c = CheckResult("Exchanges array has 2+ entries", cat)
    for evt in events:
        exch = evt.get("exchanges", [])
        c.check(evt.get("event_id", "?"), len(exch) >= 2,
                f"has {len(exch)} exchanges")
    results.append(c)

    # Location specificity
    c = CheckResult("Location is specific (contains comma or sub-location)", cat)
    for evt in events:
        loc = evt.get("location", "")
        c.check(evt.get("event_id", "?"), "," in loc or len(loc) > 20,
                f"location: '{loc}'")
    results.append(c)

    # Event type validity
    c = CheckResult("Event type is a recognized type", cat)
    for evt in events:
        etype = evt.get("type", "")
        c.check(evt.get("event_id", "?"), etype in VALID_EVENT_TYPES,
                f"type: '{etype}'")
    results.append(c)

    return results


# ---------------------------------------------------------------------------
# Character checks
# ---------------------------------------------------------------------------

CHARACTER_REQUIRED_FIELDS = [
    "id", "name", "aliases", "title", "born", "status", "category",
    "location", "current_task", "personality", "interests", "speech_style",
    "core_characteristics", "faction_ids", "event_refs", "appearance",
]


def check_characters(characters: list, event_ids: set, chapter_filter: str = None) -> list[CheckResult]:
    results = []

    if chapter_filter:
        # Filter to characters that appear in events from this chapter
        chapter_event_ids = {eid for eid in event_ids}
        # Can't easily filter by chapter for characters, so check all
        pass

    cat = f"CHARACTERS ({len(characters)})"

    # Required fields present
    c = CheckResult("All 18 fields present", cat)
    for char in characters:
        missing = [f for f in CHARACTER_REQUIRED_FIELDS if f not in char]
        if missing:
            c.check(char.get("id", "?"), False, f"missing: {', '.join(missing)}")
        else:
            c.check(char.get("id", "?"), True)
    results.append(c)

    # Personality has 4+ traits
    c = CheckResult("personality has 4+ traits", cat)
    for char in characters:
        traits = char.get("personality", [])
        count = len(traits) if isinstance(traits, list) else 0
        c.check(char["id"], count >= 4, f"has {count} traits")
    results.append(c)

    # Interests has 2+ items
    c = CheckResult("interests has 2+ items", cat)
    for char in characters:
        interests = char.get("interests", [])
        count = len(interests) if isinstance(interests, list) else 0
        c.check(char["id"], count >= 2, f"has {count} interests")
    results.append(c)

    # Speech style 10+ words
    c = CheckResult("speech_style has 10+ words", cat)
    for char in characters:
        ss = char.get("speech_style", "")
        wc = word_count(ss)
        c.check(char["id"], wc >= 10, f"has {wc} words")
    results.append(c)

    # Core characteristics 20+ words
    c = CheckResult("core_characteristics has 20+ words", cat)
    for char in characters:
        cc = char.get("core_characteristics", "")
        wc = word_count(cc)
        c.check(char["id"], wc >= 20, f"has {wc} words")
    results.append(c)

    # Appearance has 2+ subfields
    c = CheckResult("appearance has 2+ subfields", cat)
    for char in characters:
        app = char.get("appearance", {})
        if isinstance(app, dict):
            non_empty = sum(1 for v in app.values() if v)
            c.check(char["id"], non_empty >= 2, f"has {non_empty} populated subfields")
        else:
            c.check(char["id"], False, "appearance is not a dict")
    results.append(c)

    # Event refs non-empty
    c = CheckResult("event_refs non-empty", cat)
    for char in characters:
        refs = char.get("event_refs", [])
        c.check(char["id"], len(refs) > 0, "no event_refs")
    results.append(c)

    return results


# ---------------------------------------------------------------------------
# Location checks
# ---------------------------------------------------------------------------

def check_locations(locations: list) -> list[CheckResult]:
    results = []
    cat = f"LOCATIONS ({len(locations)})"

    # Description 30+ chars
    c = CheckResult("description has 30+ characters", cat)
    for loc in locations:
        desc = loc.get("description", "")
        c.check(loc["location_id"], len(desc) >= 30, f"has {len(desc)} chars")
    results.append(c)

    # Event refs non-empty
    c = CheckResult("event_refs non-empty", cat)
    for loc in locations:
        refs = loc.get("event_refs", [])
        c.check(loc["location_id"], len(refs) > 0, "no event_refs")
    results.append(c)

    # Region non-empty
    c = CheckResult("region non-empty", cat)
    for loc in locations:
        c.check(loc["location_id"], bool(loc.get("region", "")),
                "empty region")
    results.append(c)

    return results


# ---------------------------------------------------------------------------
# Faction checks
# ---------------------------------------------------------------------------

def check_factions(factions: list, char_ids: set) -> list[CheckResult]:
    results = []
    cat = f"FACTIONS ({len(factions)})"

    # Description 50+ chars
    c = CheckResult("description has 50+ characters", cat)
    for f in factions:
        desc = f.get("description", "")
        c.check(f["faction_id"], len(desc) >= 50,
                f"has {len(desc)} chars")
    results.append(c)

    # Leader is valid character
    c = CheckResult("leader_id is valid character ID", cat)
    for f in factions:
        lid = f.get("leader_id", "")
        c.check(f["faction_id"], lid in char_ids, f"leader: '{lid}'")
    results.append(c)

    # Member IDs non-empty and valid
    c = CheckResult("member_ids non-empty, all valid", cat)
    for f in factions:
        members = f.get("member_ids", [])
        if not members:
            c.check(f["faction_id"], False, "no members")
        else:
            unknown = [m for m in members if m not in char_ids]
            if unknown:
                c.check(f["faction_id"], False, f"unknown: {', '.join(unknown[:3])}")
            else:
                c.check(f["faction_id"], True)
    results.append(c)

    return results


# ---------------------------------------------------------------------------
# Roll checks
# ---------------------------------------------------------------------------

def check_rolls(rolls: list, event_ids: set, chapter_filter: str = None) -> list[CheckResult]:
    results = []

    if chapter_filter:
        rolls = [r for r in rolls if r.get("chapter") == chapter_filter]

    cat = f"ROLLS ({len(rolls)})"

    # Rolled is non-null integer 1-100
    c = CheckResult("rolled is non-null integer 1-100", cat)
    for r in rolls:
        val = r.get("rolled")
        c.check(r["roll_id"], isinstance(val, int) and 1 <= val <= 100,
                f"rolled={val}")
    results.append(c)

    # Event ID exists
    c = CheckResult("event_id exists in events.json", cat)
    for r in rolls:
        eid = r.get("event_id", "")
        c.check(r["roll_id"], eid in event_ids, f"event: '{eid}'")
    results.append(c)

    # Outcome range is numeric format
    c = CheckResult("outcome_range is numeric format", cat)
    for r in rolls:
        rng = r.get("outcome_range", "")
        c.check(r["roll_id"], rng in VALID_NUMERIC_RANGES,
                f"range: '{rng}'")
    results.append(c)

    # Outcome detail non-empty
    c = CheckResult("outcome_detail non-empty", cat)
    for r in rolls:
        c.check(r["roll_id"], bool(r.get("outcome_detail", "")))
    results.append(c)

    # Evaluation non-empty
    c = CheckResult("evaluation non-empty", cat)
    for r in rolls:
        c.check(r["roll_id"], bool(r.get("evaluation", "")))
    results.append(c)

    return results


# ---------------------------------------------------------------------------
# Law checks
# ---------------------------------------------------------------------------

def check_laws(laws: list, event_ids: set) -> list[CheckResult]:
    results = []
    cat = f"LAWS ({len(laws)})"

    # Origin event ID is valid
    c = CheckResult("origin_event_id is valid (not pending)", cat)
    for law in laws:
        oid = law.get("origin_event_id", "")
        is_pending = not oid or oid == "_pending_event_linkage"
        if is_pending:
            c.check(law["law_id"], False, "pending linkage")
        else:
            c.check(law["law_id"], oid in event_ids, f"event: '{oid}'")
    results.append(c)

    # Full text non-empty
    c = CheckResult("full_text non-empty", cat)
    for law in laws:
        c.check(law["law_id"], bool(law.get("full_text", "")))
    results.append(c)

    # Related events non-empty
    c = CheckResult("related_events non-empty", cat)
    for law in laws:
        refs = law.get("related_events", [])
        c.check(law["law_id"], len(refs) > 0, "no related events")
    results.append(c)

    return results


# ---------------------------------------------------------------------------
# Extraction file checks
# ---------------------------------------------------------------------------

def check_extractions(chapter_filter: str = None) -> list[CheckResult]:
    results = []

    extraction_files = sorted(EXTRACTIONS_DIR.glob("chapter_*_extracted.json"))
    if chapter_filter:
        extraction_files = [f for f in extraction_files
                           if f"chapter_{chapter_filter}_extracted" in f.name]

    cat = f"EXTRACTIONS ({len(extraction_files)} files)"

    # All required top-level keys present
    REQUIRED_KEYS = [
        "chapter", "book", "events", "new_characters", "character_updates",
        "new_locations", "new_factions", "rolls", "law_references", "faction_updates",
    ]

    c = CheckResult("All 10 top-level keys present", cat)
    for path in extraction_files:
        data = load_json(path)
        ch = data.get("chapter", path.stem)
        missing = [k for k in REQUIRED_KEYS if k not in data]
        if missing:
            c.check(ch, False, f"missing: {', '.join(missing)}")
        else:
            c.check(ch, True)
    results.append(c)

    # Character updates: chapters with 5+ events and 5+ characters should
    # have at least 3 character_updates
    c = CheckResult("Chapters with 5+ events have character_updates", cat)
    for path in extraction_files:
        data = load_json(path)
        ch = data.get("chapter", path.stem)
        events = data.get("events", [])
        updates = data.get("character_updates", [])

        # Count unique characters across events
        all_chars = set()
        for evt in events:
            for cid in evt.get("characters", []):
                all_chars.add(cid)

        if len(events) >= 5 and len(all_chars) >= 5:
            c.check(ch, len(updates) >= 3,
                    f"{len(events)} events, {len(all_chars)} chars, {len(updates)} updates")
        else:
            c.check(ch, True)  # Pass small chapters
    results.append(c)

    # New characters have appearance
    c = CheckResult("New characters have appearance data", cat)
    for path in extraction_files:
        data = load_json(path)
        ch = data.get("chapter", path.stem)
        for nc in data.get("new_characters", []):
            app = nc.get("appearance", {})
            has_app = isinstance(app, dict) and sum(1 for v in app.values() if v) >= 2
            c.check(f"{ch}/{nc.get('id', '?')}", has_app,
                    f"appearance: {app}")
    results.append(c)

    # New characters have speech_style
    c = CheckResult("New characters have speech_style (10+ words)", cat)
    for path in extraction_files:
        data = load_json(path)
        ch = data.get("chapter", path.stem)
        for nc in data.get("new_characters", []):
            wc = word_count(nc.get("speech_style", ""))
            c.check(f"{ch}/{nc.get('id', '?')}", wc >= 10,
                    f"{wc} words")
    results.append(c)

    # New locations have descriptions
    c = CheckResult("New locations have descriptions (30+ chars)", cat)
    for path in extraction_files:
        data = load_json(path)
        ch = data.get("chapter", path.stem)
        for nl in data.get("new_locations", []):
            desc = nl.get("description", "")
            c.check(f"{ch}/{nl.get('location_id', '?')}", len(desc) >= 30,
                    f"{len(desc)} chars")
    results.append(c)

    # New factions have descriptions
    c = CheckResult("New factions have descriptions (50+ chars)", cat)
    for path in extraction_files:
        data = load_json(path)
        ch = data.get("chapter", path.stem)
        for nf in data.get("new_factions", []):
            desc = nf.get("description", "")
            c.check(f"{ch}/{nf.get('faction_id', '?')}", len(desc) >= 50,
                    f"{len(desc)} chars")
    results.append(c)

    return results


# ---------------------------------------------------------------------------
# Cross-reference checks
# ---------------------------------------------------------------------------

def check_cross_refs(events: list, characters: list, locations: list,
                     factions: list, rolls: list, laws: list) -> list[CheckResult]:
    results = []
    cat = "CROSS-REFERENCES"

    event_ids = {e["event_id"] for e in events}
    char_ids = {c["id"] for c in characters}

    # Characters in events exist in characters.json
    c = CheckResult("All character IDs in events exist in characters.json", cat)
    missing_chars = set()
    for evt in events:
        for cid in evt.get("characters", []):
            if cid not in char_ids and cid != "narrator":
                missing_chars.add(cid)
    for cid in sorted(missing_chars):
        c.check(cid, False)
    if not missing_chars:
        c.total = len(events)
    results.append(c)

    # Event refs in characters exist in events.json
    c = CheckResult("All event_refs in characters exist in events.json", cat)
    orphan_count = 0
    for char in characters:
        for ref in char.get("event_refs", []):
            if ref not in event_ids:
                orphan_count += 1
    c.total = sum(len(ch.get("event_refs", [])) for ch in characters)
    if orphan_count > 0:
        c.failures = orphan_count
        c.passed = False
        c.violations.append(("characters", f"{orphan_count} orphan event_refs"))
    results.append(c)

    # Roll event_ids exist
    c = CheckResult("All roll event_ids exist in events.json", cat)
    for r in rolls:
        eid = r.get("event_id", "")
        c.check(r["roll_id"], eid in event_ids, f"event: '{eid}'")
    results.append(c)

    # Faction member_ids exist
    c = CheckResult("All faction member_ids exist in characters.json", cat)
    for f in factions:
        for mid in f.get("member_ids", []):
            if mid not in char_ids:
                c.check(f"{f['faction_id']}/{mid}", False)
            else:
                c.check(f"{f['faction_id']}/{mid}", True)
    results.append(c)

    # Law origin_event_ids exist (for non-pending)
    c = CheckResult("All law origin_event_ids exist in events.json", cat)
    for law in laws:
        oid = law.get("origin_event_id", "")
        if oid and oid != "_pending_event_linkage":
            c.check(law["law_id"], oid in event_ids, f"event: '{oid}'")
    results.append(c)

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Validate data quality against QUALITY_STANDARD.md")
    parser.add_argument("--chapter", type=str, help="Validate single chapter")
    parser.add_argument("--summary", action="store_true", help="Counts only, no violation details")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    # Load all databases
    events_data = load_json(DATA_DIR / "events.json")
    events = events_data.get("events", [])
    characters = load_json(DATA_DIR / "characters.json").get("characters", [])
    locations = load_json(DATA_DIR / "locations.json").get("locations", [])
    factions = load_json(DATA_DIR / "factions.json").get("factions", [])
    rolls = load_json(DATA_DIR / "roll_history.json").get("rolls", [])
    laws = load_json(DATA_DIR / "laws.json").get("laws", [])

    char_ids = {c["id"] for c in characters}
    event_ids = {e["event_id"] for e in events}

    report = QualityReport()

    # Run all checks
    for c in check_events(events, char_ids, args.chapter):
        report.add(c)
    for c in check_characters(characters, event_ids, args.chapter):
        report.add(c)
    for c in check_locations(locations):
        report.add(c)
    for c in check_factions(factions, char_ids):
        report.add(c)
    for c in check_rolls(rolls, event_ids, args.chapter):
        report.add(c)
    for c in check_laws(laws, event_ids):
        report.add(c)
    for c in check_extractions(args.chapter):
        report.add(c)
    for c in check_cross_refs(events, characters, locations, factions, rolls, laws):
        report.add(c)

    if args.json:
        print(json.dumps(report.to_json(), indent=2))
    else:
        all_passed = report.print_report(summary_only=args.summary)
        sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
