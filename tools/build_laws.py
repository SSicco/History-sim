#!/usr/bin/env python3
"""
Build laws.json from Laws.txt source file.

Reads Laws.txt (a single JSON object keyed by filename), extracts each law,
validates against the schema in CONVENTIONS.md Section 8, and outputs the
runtime format expected by context_agent.gd.

Source format (Laws.txt):
    {
      "_index.json": { ... },
      "law_001.json": { law object },
      "law_002.json": { law object },
      ...
    }

Output format (laws.json):
    {
      "laws": [ law_001, law_002, ... ]
    }

Usage:
    python3 tools/build_laws.py                  # preview to stdout
    python3 tools/build_laws.py --write          # write to resources/data/laws.json
    python3 tools/build_laws.py --query fueros   # search laws by keyword
    python3 tools/build_laws.py --validate       # check all laws against schema
"""

import json
import os
import sys
import re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
DATA_DIR = os.path.join(PROJECT_ROOT, "resources", "data")
SOURCE_PATH = os.path.join(PROJECT_ROOT, "Laws.txt")
OUTPUT_PATH = os.path.join(DATA_DIR, "laws.json")

REQUIRED_FIELDS = [
    "law_id", "title", "summary", "full_text", "date_enacted", "location",
    "proposed_by", "enacted_by", "status", "scope", "tags",
    "origin_event_id", "effectiveness_modifiers", "repeal",
]

VALID_STATUSES = {"active", "repealed", "suspended"}
VALID_SCOPES = {
    "castile", "aragon", "papal", "byzantine", "constantinople",
    "military_orders", "international",
}


def load_source():
    """Load Laws.txt and return the parsed JSON."""
    if not os.path.exists(SOURCE_PATH):
        print(f"ERROR: Source file not found: {SOURCE_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(SOURCE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data


def extract_laws(source_data):
    """Extract law objects from the source, skipping the _index.json key."""
    laws = []
    for key, value in source_data.items():
        if key == "_index.json":
            continue
        if not isinstance(value, dict) or "law_id" not in value:
            print(f"  WARNING: skipping key '{key}' (not a law object)",
                  file=sys.stderr)
            continue
        laws.append(value)

    # Sort by law_id for consistent ordering
    laws.sort(key=lambda l: l["law_id"])
    return laws


def validate_law(law):
    """Validate a single law against the schema. Returns list of issues."""
    issues = []
    law_id = law.get("law_id", "???")

    # Required fields
    for field in REQUIRED_FIELDS:
        if field not in law:
            issues.append(f"missing required field: {field}")

    # law_id format
    if not re.match(r"^law_\d{3}$", law.get("law_id", "")):
        issues.append(f"law_id '{law.get('law_id')}' does not match law_XXX format")

    # Status
    status = law.get("status", "")
    if status not in VALID_STATUSES:
        issues.append(f"invalid status '{status}' (expected: {VALID_STATUSES})")

    # Scope
    scope = law.get("scope", "")
    if scope not in VALID_SCOPES:
        issues.append(f"invalid scope '{scope}' (expected: {VALID_SCOPES})")

    # Tags count
    tags = law.get("tags", [])
    if not isinstance(tags, list) or len(tags) < 2 or len(tags) > 4:
        issues.append(f"tags should have 2-4 entries, has {len(tags)}")

    # Date format
    date = law.get("date_enacted", "")
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        issues.append(f"date_enacted '{date}' not in YYYY-MM-DD format")

    # Repeal consistency
    if status == "repealed" and law.get("repeal") is None:
        issues.append("status is 'repealed' but repeal field is null")
    if status != "repealed" and law.get("repeal") is not None:
        issues.append(f"status is '{status}' but repeal field is populated")

    return issues


def query_laws(laws, search_term):
    """Find laws matching a search term in title or summary."""
    search = search_term.lower()
    matches = []
    for law in laws:
        title = law.get("title", "").lower()
        summary = law.get("summary", "").lower()
        tags = " ".join(law.get("tags", [])).lower()
        if search in title or search in summary or search in tags:
            matches.append(law)
    return matches


def print_law(law, verbose=False):
    """Print a single law in readable format."""
    print(f"  {law['law_id']}  [{law['date_enacted']}]  {law['scope']}")
    print(f"    Title:  {law['title']}")
    print(f"    Status: {law['status']}")
    print(f"    Tags:   {', '.join(law.get('tags', []))}")
    summary = law.get("summary", "")
    if not verbose and len(summary) > 120:
        summary = summary[:117] + "..."
    print(f"    Summary: {summary}")
    if verbose:
        full_text = law.get("full_text", "")
        print(f"    Full text: {len(full_text)} chars")
    print()


def main():
    args = sys.argv[1:]

    # Load and extract
    print("Reading Laws.txt...", file=sys.stderr)
    source_data = load_source()
    laws = extract_laws(source_data)
    print(f"Extracted {len(laws)} laws", file=sys.stderr)

    # Collect stats
    scopes = {}
    statuses = {}
    for law in laws:
        s = law.get("scope", "unknown")
        scopes[s] = scopes.get(s, 0) + 1
        st = law.get("status", "unknown")
        statuses[st] = statuses.get(st, 0) + 1

    print(f"Scopes: {scopes}", file=sys.stderr)
    print(f"Statuses: {statuses}", file=sys.stderr)

    # --validate mode
    if "--validate" in args:
        print(f"\nValidating {len(laws)} laws...\n")
        total_issues = 0
        for law in laws:
            issues = validate_law(law)
            if issues:
                print(f"  {law.get('law_id', '???')}: {len(issues)} issue(s)")
                for issue in issues:
                    print(f"    - {issue}")
                total_issues += len(issues)
        if total_issues == 0:
            print("  All laws pass validation.")
        else:
            print(f"\n  Total: {total_issues} issue(s) across {len(laws)} laws")
        return

    # --query mode
    if "--query" in args:
        idx = args.index("--query")
        if idx + 1 >= len(args):
            print("ERROR: --query requires a search term", file=sys.stderr)
            sys.exit(1)
        search = args[idx + 1]
        matches = query_laws(laws, search)
        print(f"\nLaws matching '{search}': {len(matches)}\n")
        for law in matches:
            print_law(law, verbose="--verbose" in args)
        return

    # --write mode
    if "--write" in args:
        output = {"laws": laws}
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        size_kb = os.path.getsize(OUTPUT_PATH) / 1024
        print(f"\nWritten {len(laws)} laws to {OUTPUT_PATH} ({size_kb:.1f} KB)",
              file=sys.stderr)
        return

    # Default: preview
    print(f"\nFirst 3 laws:")
    for law in laws[:3]:
        print_law(law)

    print(f"Last 3 laws:")
    for law in laws[-3:]:
        print_law(law)

    print(f"Run with --write to save to {OUTPUT_PATH}")
    print(f"Run with --query <term> to search laws")
    print(f"Run with --validate to check against schema")


if __name__ == "__main__":
    main()
