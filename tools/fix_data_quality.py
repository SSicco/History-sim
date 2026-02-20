#!/usr/bin/env python3
"""
Fix critical data quality issues found during the comprehensive review.

Fixes applied:
1. factions.json: Replace orphaned member_ids with canonical character IDs
   - eugenius_iv -> pope_eugenius_iv (5 factions)
   - giordano_orsini -> cardinal_orsini (6 factions)
   - prospero_capranica -> cardinal_capranica (7 factions)
   - captain_fernan -> fernan_alonso_de_robles (1 faction)

2. characters.json: Add missing alias "giordano_orsini" to cardinal_orsini

3. characters.json: Merge duplicate jean_de_rochetaillee into cardinal_rochetaillee
   - Merge event_refs, aliases, and any unique data
   - Remove the standalone jean_de_rochetaillee entry

4. factions.json: Update jean_de_rochetaillee references to cardinal_rochetaillee

5. roll_history.json: Renumber duplicate roll_ids (roll_090-117 Book 2 duplicates)
"""

import json
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "data")


def fix_faction_member_ids(factions_data):
    """Fix orphaned member_ids in factions.json."""
    replacements = {
        "eugenius_iv": "pope_eugenius_iv",
        "giordano_orsini": "cardinal_orsini",
        "prospero_capranica": "cardinal_capranica",
        "captain_fernan": "fernan_alonso_de_robles",
        "jean_de_rochetaillee": "cardinal_rochetaillee",
    }

    fixed_count = 0
    for faction in factions_data["factions"]:
        new_members = []
        for mid in faction.get("member_ids", []):
            if mid in replacements:
                new_id = replacements[mid]
                # Avoid duplicates if the canonical ID is already in the list
                if new_id not in faction["member_ids"] and new_id not in new_members:
                    new_members.append(new_id)
                    print(f"  [{faction['faction_id']}] {mid} -> {new_id}")
                    fixed_count += 1
                else:
                    print(f"  [{faction['faction_id']}] {mid} -> SKIPPED (duplicate of existing {new_id})")
                    fixed_count += 1
            else:
                new_members.append(mid)
        faction["member_ids"] = new_members

    return fixed_count


def add_giordano_orsini_alias(characters_data):
    """Add 'giordano_orsini' as an alias to cardinal_orsini."""
    for char in characters_data["characters"]:
        if char["id"] == "cardinal_orsini":
            if "giordano_orsini" not in char.get("aliases", []):
                char["aliases"].append("giordano_orsini")
                print(f"  Added alias 'giordano_orsini' to cardinal_orsini")
                return 1
            else:
                print(f"  Alias 'giordano_orsini' already exists on cardinal_orsini")
                return 0
    print("  WARNING: cardinal_orsini not found!")
    return 0


def merge_jean_de_rochetaillee(characters_data):
    """Merge jean_de_rochetaillee into cardinal_rochetaillee."""
    cardinal = None
    jean = None
    jean_idx = None

    for i, char in enumerate(characters_data["characters"]):
        if char["id"] == "cardinal_rochetaillee":
            cardinal = char
        elif char["id"] == "jean_de_rochetaillee":
            jean = char
            jean_idx = i

    if not cardinal:
        print("  WARNING: cardinal_rochetaillee not found!")
        return 0
    if not jean:
        print("  jean_de_rochetaillee already removed or not found")
        return 0

    # Merge event_refs
    existing_refs = set(cardinal.get("event_refs", []))
    for ref in jean.get("event_refs", []):
        if ref not in existing_refs:
            cardinal["event_refs"].append(ref)
            existing_refs.add(ref)
            print(f"  Merged event_ref: {ref}")

    # Merge aliases (ensure no duplicates)
    existing_aliases = set(cardinal.get("aliases", []))
    for alias in jean.get("aliases", []):
        if alias not in existing_aliases:
            cardinal["aliases"].append(alias)
            existing_aliases.add(alias)
            print(f"  Merged alias: {alias}")

    # If jean has a title that cardinal doesn't, note it
    if jean.get("title") and not cardinal.get("title"):
        cardinal["title"] = jean["title"]
        print(f"  Merged title: {jean['title']}")

    # Remove the duplicate entry
    characters_data["characters"].pop(jean_idx)
    characters_data["meta"]["total_characters"] = len(characters_data["characters"])
    print(f"  Removed duplicate entry jean_de_rochetaillee (was at index {jean_idx})")
    print(f"  Updated total_characters: {characters_data['meta']['total_characters']}")

    return 1


def fix_roll_ids(roll_data):
    """Renumber duplicate roll_ids in roll_history.json."""
    seen_ids = {}
    duplicates = []

    for i, roll in enumerate(roll_data["rolls"]):
        rid = roll["roll_id"]
        if rid in seen_ids:
            duplicates.append(i)
        else:
            seen_ids[rid] = i

    if not duplicates:
        print("  No duplicate roll_ids found")
        return 0

    # Find the max roll number
    max_num = 0
    for roll in roll_data["rolls"]:
        rid = roll["roll_id"]
        if rid.startswith("roll_"):
            try:
                num = int(rid.replace("roll_", ""))
                max_num = max(max_num, num)
            except ValueError:
                pass

    # Renumber duplicates starting from max_num + 1
    next_num = max_num + 1
    fixed_count = 0
    for idx in duplicates:
        old_id = roll_data["rolls"][idx]["roll_id"]
        new_id = f"roll_{next_num:03d}"
        roll_data["rolls"][idx]["roll_id"] = new_id
        print(f"  {old_id} (index {idx}) -> {new_id}")
        next_num += 1
        fixed_count += 1

    # Update total
    roll_data["meta"]["total_rolls"] = len(roll_data["rolls"])

    return fixed_count


def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(filename, data):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"  Saved {path}")


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN MODE (no files will be modified) ===\n")

    # Load data
    print("Loading data files...")
    factions = load_json("factions.json")
    characters = load_json("characters.json")
    roll_history = load_json("roll_history.json")

    # Fix 1: Faction member_ids
    print("\n--- Fix 1: Faction member_id mismatches ---")
    f1 = fix_faction_member_ids(factions)
    print(f"  Total: {f1} references fixed")

    # Fix 2: Add giordano_orsini alias
    print("\n--- Fix 2: Add giordano_orsini alias to cardinal_orsini ---")
    f2 = add_giordano_orsini_alias(characters)

    # Fix 3: Merge jean_de_rochetaillee
    print("\n--- Fix 3: Merge jean_de_rochetaillee into cardinal_rochetaillee ---")
    f3 = merge_jean_de_rochetaillee(characters)

    # Fix 4: Duplicate roll_ids
    print("\n--- Fix 4: Renumber duplicate roll_ids ---")
    f4 = fix_roll_ids(roll_history)
    print(f"  Total: {f4} roll_ids renumbered")

    # Save
    if not dry_run:
        print("\n--- Saving files ---")
        save_json("factions.json", factions)
        save_json("characters.json", characters)
        save_json("roll_history.json", roll_history)
        print("\nAll fixes applied successfully.")
    else:
        print("\nDry run complete. No files modified.")

    print(f"\nSummary: {f1} faction refs fixed, {f2} aliases added, {f3} characters merged, {f4} rolls renumbered")


if __name__ == "__main__":
    main()
