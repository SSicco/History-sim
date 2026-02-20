#!/usr/bin/env python3
"""
apply_review_fixes.py — One-shot script to apply review fixes to chapter event
files and characters.json.

Changes:
  1. Replace all "luis_de_guzman" refs in chapter_1.34.json characters arrays
     with "luis_de_guzman_niebla".
  2. Scan ALL chapter files for references to Juan being "twenty-eight" or
     "28 years old" (report only, no auto-fix).
  3. Add 15 new character entries to characters.json with the exact schema
     used by existing characters.

Usage:
    python3 tools/apply_review_fixes.py
"""

import json
import os
import re
import sys
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVENTS_DIR = PROJECT_ROOT / "resources" / "data" / "events"
CHARACTERS_FILE = PROJECT_ROOT / "resources" / "data" / "characters.json"
CHAPTER_134 = EVENTS_DIR / "chapter_1.34.json"

# ─── Helpers ────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def report(section: str, msg: str) -> None:
    print(f"  [{section}] {msg}")


# ─── Fix 1: Replace luis_de_guzman → luis_de_guzman_niebla in ch 1.34 ──────

def fix_luis_de_guzman_in_chapter_134() -> int:
    """Replace all 'luis_de_guzman' in characters arrays with
    'luis_de_guzman_niebla' in chapter_1.34.json.  Returns count of
    replacements made."""
    data = load_json(CHAPTER_134)
    count = 0
    already_correct = 0

    for event in data.get("events", []):
        chars = event.get("characters", [])
        for i, c in enumerate(chars):
            if c == "luis_de_guzman":
                chars[i] = "luis_de_guzman_niebla"
                count += 1
                report("FIX-1", f"  event {event['event_id']}: "
                       f"luis_de_guzman → luis_de_guzman_niebla")
            elif c == "luis_de_guzman_niebla":
                already_correct += 1

    if already_correct and not count:
        report("FIX-1", f"  Already correct: {already_correct} "
               f"luis_de_guzman_niebla reference(s) found")

    if count:
        save_json(CHAPTER_134, data)

    return count


# ─── Fix 2: Scan for wrong-age Juan references ─────────────────────────────

def scan_age_references() -> list[str]:
    """Search all chapter files for 'twenty-eight' or '28 years old' in
    exchange text or summaries.  Returns list of findings (report only)."""
    findings: list[str] = []
    patterns = [
        re.compile(r"twenty[\-\s]eight", re.IGNORECASE),
        re.compile(r"28\s+years?\s+old", re.IGNORECASE),
    ]

    for chapter_file in sorted(EVENTS_DIR.glob("chapter_*.json")):
        data = load_json(chapter_file)
        for event in data.get("events", []):
            eid = event.get("event_id", "?")

            # Check summary
            summary = event.get("summary", "")
            for pat in patterns:
                for m in pat.finditer(summary):
                    findings.append(
                        f"{chapter_file.name} / {eid} / summary: "
                        f"'{m.group()}' at pos {m.start()}"
                    )

            # Check exchanges
            for ex in event.get("exchanges", []):
                text = ex.get("text", "")
                for pat in patterns:
                    for m in pat.finditer(text):
                        findings.append(
                            f"{chapter_file.name} / {eid} / "
                            f"{ex.get('role','?')} exchange: "
                            f"'{m.group()}' at pos {m.start()}"
                        )

    return findings


# ─── Fix 3: Add new characters ─────────────────────────────────────────────

def make_char(
    *,
    char_id: str,
    name: str,
    aliases: list[str] | None = None,
    title: str = "",
    born: str = "0000-00-00",
    status: list[str] | None = None,
    category: list[str] | None = None,
    location: str = "",
    current_task: str = "",
    personality: list[str] | None = None,
    interests: list[str] | None = None,
    speech_style: str = "",
    core_characteristics: str = "",
    rolled_traits: list[str] | None = None,
    faction_ids: list[str] | None = None,
    event_refs: list[str] | None = None,
    appearance: dict | None = None,
    portrait_prompt: str = "",
) -> dict:
    """Build a character dict matching the exact schema used in
    characters.json."""
    return {
        "id": char_id,
        "name": name,
        "aliases": aliases if aliases is not None else [char_id],
        "title": title,
        "born": born,
        "status": status if status is not None else ["active"],
        "category": category if category is not None else [],
        "location": location,
        "current_task": current_task,
        "personality": personality if personality is not None else [],
        "interests": interests if interests is not None else [],
        "speech_style": speech_style,
        "core_characteristics": core_characteristics,
        "rolled_traits": rolled_traits if rolled_traits is not None else [],
        "faction_ids": faction_ids if faction_ids is not None else [],
        "event_refs": event_refs if event_refs is not None else [],
        "appearance": appearance if appearance is not None else {},
        "portrait_prompt": portrait_prompt,
    }


NEW_CHARACTERS = [
    make_char(
        char_id="luis_de_guzman_niebla",
        name="Don Luis de Guzmán (Niebla)",
        aliases=["luis_de_guzman_niebla"],
        title="Brother of the Count of Niebla",
        born="0000-00-00",
        status=["active"],
        category=["nobility"],
        location="Niebla",
        current_task="",
        personality=["conflicted", "emotional", "loyal"],
        interests=[],
        speech_style="",
        core_characteristics=(
            "Count Diego de Medina-Sidonia's younger brother. Appeared during "
            "the siege of Niebla (ch 1.34), where he defected during the "
            "garrison mutiny alongside the castellan Rodrigo Fernández. "
            "Emotional and conflicted, but ultimately loyal to the crown "
            "after his defection."
        ),
        event_refs=[
            "evt_1432_00275",
            "evt_1432_00276",
            "evt_1432_00277",
            "evt_1432_00278",
            "evt_1432_00279",
        ],
    ),
    make_char(
        char_id="doctor_fernandez",
        name="Doctor Fernández",
        aliases=["doctor_fernandez"],
        title="Royal Physician",
        born="0000-00-00",
        status=["active"],
        category=["royal_court"],
        location="Toledo",
        current_task="",
        personality=["experienced", "dedicated", "competent"],
        interests=["medicine"],
        speech_style="",
        core_characteristics=(
            "Longtime royal physician who attended Juan's birth and revived "
            "baby Catalina during the traumatic delivery."
        ),
        event_refs=["evt_1432_00158", "evt_1432_00159"],
    ),
    make_char(
        char_id="maria_wet_nurse",
        name="María",
        aliases=["maria_wet_nurse"],
        title="Royal Wet Nurse",
        born="0000-00-00",
        status=["active"],
        category=["royal_court"],
        location="Toledo",
        current_task="",
        personality=["sturdy", "reliable"],
        interests=[],
        speech_style="",
        core_characteristics=(
            "Sturdy Toledo woman serving as wet nurse for Princess Catalina."
        ),
        event_refs=["evt_1432_00158"],
    ),
    make_char(
        char_id="rodrigo_fernandez_castellan",
        name="Rodrigo Fernández",
        aliases=["rodrigo_fernandez_castellan"],
        title="Castellan of Niebla",
        born="0000-00-00",
        status=["active"],
        category=["military"],
        location="Niebla",
        current_task="",
        personality=["experienced", "pragmatic", "loyal"],
        interests=[],
        speech_style="",
        core_characteristics=(
            "Castellan of Niebla fortress who led the garrison mutiny "
            "against Count Diego, opening the gates to the royal army."
        ),
        event_refs=["evt_1432_00275", "evt_1432_00276"],
    ),
    make_char(
        char_id="father_miguel",
        name="Father Miguel",
        aliases=["father_miguel"],
        title="Chaplain",
        born="0000-00-00",
        status=["active"],
        category=["clergy"],
        location="Mediterranean (with crusade fleet)",
        current_task="",
        personality=["pious", "dedicated"],
        interests=["Latin instruction", "faith"],
        speech_style="",
        core_characteristics=(
            "Chaplain providing Latin instruction, involved in cathedral "
            "conversion plans."
        ),
        event_refs=["evt_1433_00370"],
    ),
    make_char(
        char_id="giovanni_rossi",
        name="Giovanni Rossi",
        aliases=["giovanni_rossi"],
        title="Standard-bearer of the True Cross",
        born="0000-00-00",
        status=["active"],
        category=["military"],
        location="Mediterranean (with crusade fleet)",
        current_task="",
        personality=["devoted", "resilient"],
        interests=[],
        speech_style="",
        core_characteristics=(
            "One-handed blacksmith turned crusader who carries the True "
            "Cross banner."
        ),
        event_refs=["evt_1433_00370"],
    ),
    make_char(
        char_id="brother_guillem",
        name="Brother Guillem",
        aliases=["brother_guillem"],
        title="Benedictine Monk",
        born="0000-00-00",
        status=["active"],
        category=["clergy"],
        location="Basel",
        current_task="",
        personality=["scholarly", "diplomatic", "pious"],
        interests=["theology", "diplomacy"],
        speech_style="",
        core_characteristics=(
            "Benedictine monk providing spiritual counsel and serving as "
            "intermediary to the Byzantine delegation."
        ),
        event_refs=["evt_1433_00370", "evt_1433_00384"],
    ),
    make_char(
        char_id="andrea_vescovi",
        name="Andrea Vescovi",
        aliases=["andrea_vescovi"],
        title="Crusader Company Commander",
        born="0000-00-00",
        status=["active"],
        category=["military"],
        location="Basel",
        current_task="",
        personality=["devoted", "humble_origins", "transformed"],
        interests=[],
        speech_style="",
        core_characteristics=(
            "First crusader sworn, Florentine farmer's son turned company "
            "commander. Scarred and hardened by service."
        ),
        appearance={"build": "scarred/hardened"},
        event_refs=["evt_1433_00370", "evt_1433_00384"],
    ),
    make_char(
        char_id="abbott_rodrigo_gonzalez",
        name="Abbott Rodrigo González",
        aliases=["abbott_rodrigo_gonzalez"],
        title="Abbott, Chief Castilian Delegate to Basel",
        born="1360-00-00",
        status=["active"],
        category=["clergy"],
        location="Basel",
        current_task="",
        personality=["experienced", "precise", "energetic"],
        interests=["church politics", "council proceedings"],
        speech_style="",
        core_characteristics=(
            "73 years old, Castilian chief delegate at the Council of Basel. "
            "Despite his age, remarkably energetic and precise."
        ),
        event_refs=["evt_1433_00384", "evt_1433_00385"],
    ),
    make_char(
        char_id="cardinal_giuliano_cesarini",
        name="Cardinal Giuliano Cesarini",
        aliases=["cardinal_giuliano_cesarini", "cesarini"],
        title="Cardinal, President of the Council of Basel",
        born="1398-00-00",
        status=["active"],
        category=["clergy"],
        location="Basel",
        current_task="",
        personality=["intelligent", "exhausted", "diplomatic", "sincere"],
        interests=["church reform", "council politics"],
        speech_style="",
        core_characteristics=(
            "President of the Council of Basel and papal legate. Key NPC in "
            "ch 2.05 onwards. Perhaps forty, intelligent face, dark circles "
            "under eyes, lines around mouth."
        ),
        appearance={
            "age_appearance": "perhaps forty",
            "build": "average",
            "hair": "dark",
        },
        event_refs=[
            "evt_1433_00389",
            "evt_1433_00390",
            "evt_1433_00391",
        ],
    ),
    make_char(
        char_id="jean_de_rochetaillee",
        name="Jean de Rochetaillée",
        aliases=["jean_de_rochetaillee"],
        title="Bishop of Senez",
        born="0000-00-00",
        status=["active"],
        category=["clergy"],
        location="Basel",
        current_task="",
        personality=["radical", "intellectual", "passionate"],
        interests=["conciliarism", "Hussite theology"],
        speech_style="",
        core_characteristics=(
            "French conciliarist who influenced Juan's thinking on Hussites. "
            "Bishop of Senez, radical intellectual."
        ),
        event_refs=["evt_1433_00387"],
    ),
    make_char(
        char_id="cardinal_louis_aleman",
        name="Cardinal Louis Aleman",
        aliases=["cardinal_louis_aleman"],
        title="Cardinal",
        born="0000-00-00",
        status=["active"],
        category=["clergy"],
        location="Basel",
        current_task="",
        personality=["radical", "ambitious", "antagonistic"],
        interests=["conciliarism", "church politics"],
        speech_style="",
        core_characteristics=(
            "French radical leader at the Council of Basel who opposes "
            "papal authority."
        ),
        event_refs=["evt_1433_00384"],
    ),
    make_char(
        char_id="fernando_de_castilla",
        name="Prince Fernando of Castile",
        aliases=["fernando_de_castilla"],
        title="Infante of Castile",
        born="1433-09-01",
        status=["active"],
        category=["royal_family"],
        location="Toledo",
        current_task="",
        personality=["infant"],
        interests=[],
        speech_style="",
        core_characteristics=(
            "Son of Juan II and Queen Isabel, born September 1433."
        ),
        event_refs=["evt_1433_00421", "evt_1433_00422"],
    ),
    make_char(
        char_id="lucia_d_este",
        name="Lucia d'Este",
        aliases=["lucia_d_este", "lucia"],
        title="Queen of Castile",
        born="1410-00-00",
        status=["active"],
        category=["royal_family"],
        location="Constantinople",
        current_task="",
        personality=[
            "sharp",
            "intelligent",
            "politically_astute",
            "witty",
            "Florentine",
        ],
        interests=[],
        speech_style="",
        core_characteristics=(
            "Age 23, legendary beauty, politically astute. Juan's second "
            "wife (after Isabel's death in childbirth). From House of Este, "
            "Ferrara. Dark hair, grey-green eyes."
        ),
        appearance={
            "age_appearance": "23",
            "build": "average",
            "hair": "dark",
        },
        event_refs=[],
    ),
    make_char(
        char_id="commander_yahya_ibn_nasir",
        name="Commander Yahya ibn Nasir",
        aliases=["commander_yahya_ibn_nasir", "yahya_ibn_nasir"],
        title="Fortress Commander",
        born="0000-00-00",
        status=["active"],
        category=["military"],
        location="Morocco",
        current_task="",
        personality=["military", "strategic"],
        interests=[],
        speech_style="",
        core_characteristics=(
            "Fortress commander who appeared in ch 1.42-1.44. Identity "
            "sometimes confused with Commander Martin."
        ),
        event_refs=["evt_1432_00300"],
    ),
]


def add_new_characters() -> list[str]:
    """Add new characters to characters.json.  Returns list of IDs added."""
    data = load_json(CHARACTERS_FILE)
    existing_ids = {c["id"] for c in data["characters"]}
    added: list[str] = []

    for char in NEW_CHARACTERS:
        if char["id"] in existing_ids:
            report("FIX-3", f"  SKIPPED (already exists): {char['id']}")
            continue
        data["characters"].append(char)
        added.append(char["id"])
        report("FIX-3", f"  ADDED: {char['id']} — {char['name']}")

    # Update total_characters count in meta
    data["meta"]["total_characters"] = len(data["characters"])

    if added:
        save_json(CHARACTERS_FILE, data)

    return added


# ─── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 70)
    print("apply_review_fixes.py — Applying review fixes")
    print("=" * 70)

    # ── Fix 1 ───────────────────────────────────────────────────────────
    print("\n[FIX-1] Replacing luis_de_guzman → luis_de_guzman_niebla "
          "in chapter_1.34.json ...")
    fix1_count = fix_luis_de_guzman_in_chapter_134()
    print(f"  → {fix1_count} replacement(s) made.\n")

    # ── Fix 2 ───────────────────────────────────────────────────────────
    print("[FIX-2] Scanning ALL chapter files for wrong-age Juan references "
          "(twenty-eight / 28 years old) ...")
    findings = scan_age_references()
    if findings:
        for f in findings:
            report("FIX-2", f"  FOUND: {f}")
        print(f"  → {len(findings)} finding(s) — NOT auto-fixed, manual "
              "review needed.\n")
    else:
        print("  → No wrong-age references found.\n")

    # ── Fix 3 ───────────────────────────────────────────────────────────
    print("[FIX-3] Adding new characters to characters.json ...")
    added = add_new_characters()
    print(f"  → {len(added)} character(s) added.\n")

    # ── Summary ─────────────────────────────────────────────────────────
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Fix 1: {fix1_count} luis_de_guzman → luis_de_guzman_niebla "
          f"replacements in chapter_1.34.json")
    print(f"  Fix 2: {len(findings)} wrong-age Juan reference(s) found "
          f"(report only)")
    print(f"  Fix 3: {len(added)} new character(s) added to characters.json")
    if added:
        for cid in added:
            print(f"         - {cid}")
    print()

    # Exit code: 0 if anything was changed or reported, always 0 for this
    # one-shot script
    sys.exit(0)


if __name__ == "__main__":
    main()
