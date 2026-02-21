#!/usr/bin/env python3
"""
Character data quality pass 2: faction assignments, DOB estimation, title backfill.

Fixes three issues:
1. 63 characters with empty faction_ids → assign correct faction or "independent"
2. 76 characters with 0000-00-00 born → estimate DOB from age clues and context
3. 15 characters with empty title → assign correct title or "(untitled)"

Also adds an "independent" faction entry to factions.json for characters
genuinely unaffiliated with any defined faction.
"""

import json
import os
import sys

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "resources", "data")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


# ============================================================
# FACTION ASSIGNMENTS
# ============================================================
# For each of the 63 characters with empty faction_ids,
# assign either an existing faction or "independent".
#
# "independent" = evaluated, genuinely has no defined faction affiliation.
# This covers: foreign rulers from untracked states, commoners,
# lone artisans, and minor characters with no institutional ties.

FACTION_ASSIGNMENTS = {
    # --- Castilian Church ---
    "archbishop_contreras": ["castilian_church"],  # Archbishop of Toledo
    "father_miguel": ["castilian_church"],          # Chaplain
    "brother_guillem": ["castilian_church"],         # Benedictine monk, spiritual counsel

    # --- Royal Court ---
    "marquis_de_santillana": ["royal_court"],       # Mendoza family, regency council
    "dona_catarina": ["royal_court"],               # Queen's lady-in-waiting
    "don_fadrique": ["royal_court"],                # Toledo family head, aligned with crown
    "dona_maria_de_sousa": ["royal_court"],         # Portuguese noblewoman, close associate
    "dona_ines_de_castro": ["royal_court"],          # Household member, close associate
    "doctor_fernandez": ["royal_court"],             # Royal physician
    "maria_wet_nurse": ["royal_court"],              # Royal wet nurse
    "baron_de_medina": ["royal_court"],              # Legal/political advisor

    # --- Royal Family ---
    "fernando_de_castilla": ["royal_family"],        # Juan II's infant son

    # --- Papacy ---
    "pope_martin_v": ["papacy"],                     # Pope Martin V (d. 1431)
    "brother_giuliano": ["papacy"],                  # Close associate in Italy

    # --- Council of Basel + Castilian Church ---
    "abbott_rodrigo": ["castilian_church", "council_of_basel"],  # Chief Castilian delegate

    # --- Granada ---
    "abu_al_zaghal": ["granada"],                    # Granadan ambassador
    "ibrahim_ibn_yusuf": ["granada"],                # Former Granadan officer (converted)
    "ahmad_al_zarqali": ["granada", "royal_court"],  # Former qadi, now royal advisor
    "sheikh_ibrahim_al_hamri": ["granada"],           # Ronda administrator
    "qaid_yusuf_ibn_musa": ["granada"],              # Former Loja fortress commander
    "qaid_ibrahim_al_najjar": ["granada"],           # Former Malaga Alcazaba commander
    "muhammad_ibn_rashid": ["granada"],              # Former Ronda fortress commander
    "yusuf_ibn_hassan": ["granada", "castile"],      # Switched to Castilian service
    "commander_yahya_ibn_nasir": ["granada"],         # Fortress commander

    # --- Castile (kingdom/military service) ---
    "garcia_fernandez_de_baeza": ["castile"],        # Cavalry Commander, First Battle
    "rodrigo_de_narvaez": ["castile"],               # Commander Third Battle
    "alvar_perez_de_guzman": ["castile"],            # Cavalry Column Commander
    "juan_de_luna": ["castile"],                     # Deep Reconnaissance Specialist
    "sancho_de_rojas": ["castile", "military_orders"],  # Calatrava Order veteran
    "martin_de_oviedo": ["castile"],                 # Guardian Knight
    "alvaro_de_estuniga": ["castile"],               # Western Crusade Army commander
    "fadrique_enriquez": ["castile"],                # Admiral of Castile
    "inigo_lopez_de_orozco": ["castile"],            # Crown Marshal New Castile
    "garcia_fernandez_de_villalobos": ["castile"],   # Crown Marshal León
    "pedro_alvarez_de_osorio": ["castile"],          # Crown Marshal Galicia
    "diego_de_sotomayor": ["castile"],               # Castilian Military Commander
    "rodrigo_fernandez_castellan": ["castile"],      # Castellan of Niebla, defected to crown
    "baron_alfonso_de_guzman": ["castile"],          # Military leader
    "luis_de_guzman_niebla": ["castile"],            # Defected from Niebla to crown
    "master_gonzalo_de_burgos": ["castile"],         # Royal Armorer
    "pietro_calabrese": ["castile"],                 # Master Gunner (Italian, hired by Castile)
    "giovanni_rossi": ["castile"],                   # Standard-bearer of True Cross, crusader
    "andrea_vescovi": ["castile"],                   # Florentine crusader, company commander
    "count_of_niebla": ["castile"],                  # Excommunicated rebel, still Castilian noble

    # --- Castilian fleet (ch 2.19 naval captains) ---
    "diego_fernandez": ["castile"],                  # Master of the San Marcos
    "luis_de_cordoba": ["castile"],                  # Ship captain
    "gaspar_de_vega": ["castile"],                   # Captain of the Santa Clara
    "rodrigo_ibanez": ["castile"],                   # Ship captain
    "martin_de_soria": ["castile"],                  # Ship captain
    "alonso_pardo": ["castile"],                     # Ship captain
    "tomas_de_lepe": ["castile"],                    # Ship captain
    "francisco_ruiz": ["castile"],                   # Ship captain
    "cristobal_medina": ["castile"],                 # Ship captain
    "captain_vargas": ["castile"],                   # Military captain
    "admiral_berenguer": ["castile"],                # Admiral
    "pascual": ["castile"],                          # Sailor / rigger

    # --- Independent (genuinely no faction affiliation) ---
    "isabel_ruiz": ["independent"],                  # Converso cloth merchant's daughter
    "moshe_ben_yitzhak": ["independent"],            # Jewish community leader, Ronda
    "janos_hunyadi": ["independent"],                # Hungarian military commander (foreign)
    "jean_de_metz": ["independent"],                 # French captain (foreign)
    "emperor_sigismund": ["independent"],            # Holy Roman Emperor (foreign sovereign)
    "joao_i": ["independent"],                       # King of Portugal (foreign sovereign)
    "fra_angelico": ["independent"],                 # Dominican friar / artist, itinerant
}


# ============================================================
# DOB ESTIMATION
# ============================================================
# For characters with born = "0000-00-00", estimate a year
# based on age clues in core_characteristics and category defaults.
# Campaign starts in 1430.
#
# Format: "YYYY-00-00" (year only, month/day unknown)

DOB_ESTIMATES = {
    # --- Characters with explicit age clues ---
    # (age clue → year = campaign_year - age, or birth year from historical record)

    # archbishop_contreras: Archbishop of Toledo 1423-1434, senior cleric
    "archbishop_contreras": "1375-00-00",  # ~55 in 1430, senior churchman
    # marquis_de_santillana: "Elder" Mendoza representative
    "marquis_de_santillana": "1370-00-00",  # ~60, "elder" representative
    # abu_al_zaghal: "~50 years old" in core
    "abu_al_zaghal": "1380-00-00",          # ~50 in 1430
    # baron_de_medina: legal/political advisor, appears in 2 events
    "baron_de_medina": "1385-00-00",        # ~45, senior advisor
    # brother_giuliano: close associate, Italian monk
    "brother_giuliano": "1395-00-00",       # ~35, active monk
    # baron_alfonso_de_guzman: military leader
    "baron_alfonso_de_guzman": "1390-00-00",  # ~40, military leader
    # dona_maria_de_sousa: Portuguese noblewoman, close associate
    "dona_maria_de_sousa": "1405-00-00",    # ~25, young noblewoman
    # dona_ines_de_castro: household member, close associate
    "dona_ines_de_castro": "1405-00-00",    # ~25, young household member
    # diego_de_sotomayor: Castilian military commander, close associate
    "diego_de_sotomayor": "1390-00-00",    # ~40, military commander
    # diego_fernandez: "older man, grey-bearded, survivor of a dozen campaigns" (ch 2.19)
    "diego_fernandez": "1380-00-00",        # ~54 in 1434, "older man, grey-bearded"
    # luis_de_cordoba: ship captain
    "luis_de_cordoba": "1395-00-00",        # ~39 in 1434, experienced captain
    # gaspar_de_vega: "younger captain" (ch 2.19)
    "gaspar_de_vega": "1404-00-00",         # ~30 in 1434, "younger captain"
    # rodrigo_ibanez: ship captain
    "rodrigo_ibanez": "1395-00-00",         # ~39 in 1434, experienced captain
    # martin_de_soria: ship captain
    "martin_de_soria": "1396-00-00",        # ~38 in 1434
    # alonso_pardo: ship captain
    "alonso_pardo": "1397-00-00",           # ~37 in 1434
    # tomas_de_lepe: ship captain
    "tomas_de_lepe": "1398-00-00",          # ~36 in 1434
    # francisco_ruiz: ship captain
    "francisco_ruiz": "1396-00-00",         # ~38 in 1434
    # cristobal_medina: ship captain
    "cristobal_medina": "1397-00-00",       # ~37 in 1434
    # pascual: sailor/rigger "spent more of his life aloft than on solid ground" (ch 2.19)
    "pascual": "1405-00-00",                # ~29 in 1434, young experienced sailor
    # captain_vargas: military captain, 4 events
    "captain_vargas": "1395-00-00",         # ~39, seasoned captain
    # admiral_berenguer: admiral, 1 event
    "admiral_berenguer": "1385-00-00",      # ~49, senior admiral rank
    # luis_de_guzman_niebla: Count's younger brother
    "luis_de_guzman_niebla": "1385-00-00",  # ~47 in 1432, younger brother of count (born ~1380)
    # doctor_fernandez: "Longtime royal physician who attended Juan's birth"
    "doctor_fernandez": "1375-00-00",       # ~55, attended Juan's birth in 1405
    # maria_wet_nurse: "Sturdy Toledo woman"
    "maria_wet_nurse": "1400-00-00",        # ~33 in 1433, childbearing age for wet nurse
    # rodrigo_fernandez_castellan: led garrison mutiny
    "rodrigo_fernandez_castellan": "1390-00-00",  # ~42 in 1432, experienced castellan
    # father_miguel: chaplain
    "father_miguel": "1395-00-00",          # ~38, active chaplain
    # giovanni_rossi: "one-handed blacksmith turned crusader"
    "giovanni_rossi": "1395-00-00",         # ~38, experienced blacksmith/crusader
    # brother_guillem: Benedictine monk
    "brother_guillem": "1390-00-00",        # ~43, senior monk
    # andrea_vescovi: "Florentine farmer's son turned company commander. Scarred and hardened"
    "andrea_vescovi": "1400-00-00",         # ~33, hardened by service
    # commander_yahya_ibn_nasir: fortress commander
    "commander_yahya_ibn_nasir": "1388-00-00",  # ~44, experienced commander

    # --- Characters with faction_ids but 0000-00-00 birth ---
    # (these 46 already have factions from the previous fix)

    # fernan_alonso_de_robles: "Practical soldier" captain of ~30 men
    "fernan_alonso_de_robles": "1390-00-00",  # ~40, experienced captain
    # fray_hernando: "Young Franciscan monk chosen... for his youth"
    "fray_hernando": "1405-00-00",           # ~25 in 1430, chosen for youth
    # archbishop_cerezuela: Archbishop of Toledo (predecessor to Contreras? or successor?)
    "archbishop_cerezuela": "1370-00-00",    # ~60, senior churchman
    # juan_de_daza: Treasury official, "meticulous record-keeper"
    "juan_de_daza": "1390-00-00",            # ~40, experienced bureaucrat
    # rodrigo_manrique: "Frontier veteran of 20+ years"
    "rodrigo_manrique": "1380-00-00",        # ~50, 20+ years frontier service
    # garcia_fernandez: city representative, raised practical concerns
    "garcia_fernandez": "1385-00-00",        # ~45, civic representative
    # sergeant_garcia: "Grizzled veteran in his forties"
    "sergeant_garcia": "1388-00-00",         # ~42, "in his forties"
    # corporal_rodrigo: "Eight-year veteran"
    "corporal_rodrigo": "1400-00-00",        # ~30, 8-year veteran
    # thomas_beaumont: English knight, "experienced with French tactics"
    "thomas_beaumont": "1392-00-00",         # ~38, experienced knight
    # marco_tornesi: "Former mercenary (~30 years old)"
    "marco_tornesi": "1400-00-00",           # ~30 per core
    # archbishop_gutierrez: political advisor, 13 events
    "archbishop_gutierrez": "1375-00-00",    # ~55, senior archbishop
    # garcia_fernandez_manrique: political advisor, 1 event
    "garcia_fernandez_manrique": "1390-00-00",  # ~40, advisor
    # bishop_de_isorna: political advisor/courtier, 11 events
    "bishop_de_isorna": "1380-00-00",        # ~50, senior bishop
    # bishop_of_palencia: political advisor, 7 events
    "bishop_of_palencia": "1378-00-00",      # ~52, senior bishop
    # bishop_of_leon: political advisor, 5 events
    "bishop_of_leon": "1380-00-00",          # ~50, bishop
    # bishop_of_avila: political advisor, 10 events
    "bishop_of_avila": "1378-00-00",         # ~52, senior bishop
    # abbott_of_valladolid: political advisor/courtier, 11 events
    "abbott_of_valladolid": "1380-00-00",    # ~50, senior abbot
    # brother_tomas: political advisor, 1 event
    "brother_tomas": "1395-00-00",           # ~35, active monk
    # hamza_ibn_fadil: military leader/diplomat, 3 events
    "hamza_ibn_fadil": "1390-00-00",         # ~40, military/diplomat
    # rahman_al_zagal: diplomat, 2 events
    "rahman_al_zagal": "1385-00-00",         # ~45, Granadan diplomat
    # fray_sebastian: diplomat, 1 event
    "fray_sebastian": "1390-00-00",          # ~40, friar diplomat
    # fray_miguel: diplomat, 1 event
    "fray_miguel": "1392-00-00",             # ~38, friar diplomat
    # ahmad_ibn_khalil: diplomat/courtier/advisor, 3 events
    "ahmad_ibn_khalil": "1385-00-00",        # ~45, senior diplomat
    # bernat_de_centelles: diplomat/military, 9 events
    "bernat_de_centelles": "1390-00-00",     # ~40, active military/diplomat
    # lucia_deste: "Queen", 55 events — major character
    "lucia_deste": "1412-00-00",             # ~18-22 in 1430-1434, young queen
    # donna_francesca: close associate, 5 events
    "donna_francesca": "1400-00-00",         # ~30, court lady
    # isabella_strozzi: close associate, 3 events
    "isabella_strozzi": "1405-00-00",        # ~25, young noblewoman
    # ramon_de_perellos: diplomat/advisor, 9 events
    "ramon_de_perellos": "1385-00-00",       # ~45, senior diplomat
    # don_guillem_de_vic: advisor/diplomat/religious, 6 events
    "don_guillem_de_vic": "1385-00-00",      # ~45, senior advisor
    # hug_roger_iii_pallars: Count of Pallars, advisor/diplomat, 7 events
    "hug_roger_iii_pallars": "1390-00-00",   # ~40, count/diplomat
    # bishop_climent_sapera: diplomat/religious, 2 events
    "bishop_climent_sapera": "1375-00-00",   # ~55, senior bishop
    # pere_joan_de_sant_climent: diplomat, 2 events
    "pere_joan_de_sant_climent": "1390-00-00",  # ~40, diplomat
    # bernat_fiveller: diplomat, 2 events
    "bernat_fiveller": "1385-00-00",         # ~45, diplomat
    # viscount_of_rocaberti: political advisor, 2 events
    "viscount_of_rocaberti": "1380-00-00",   # ~50, viscount
    # rodrigo_de_cervantes: military leader, 2 events
    "rodrigo_de_cervantes": "1395-00-00",    # ~35, military leader
    # vasco_de_orozco: military leader, 2 events
    "vasco_de_orozco": "1393-00-00",         # ~37, military leader
    # tomas_de_palencia: military leader, 1 event
    "tomas_de_palencia": "1395-00-00",       # ~35, military leader
    # sebastian_de_morales: military/advisor, 7 events
    "sebastian_de_morales": "1388-00-00",    # ~46 in 1434, "grizzled" veteran fleet captain
    # captain_rodrigo: military, 1 event
    "captain_rodrigo": "1395-00-00",         # ~35, captain
    # marco_contarini: diplomat/legal, 9 events
    "marco_contarini": "1380-00-00",         # ~54, senior Venetian diplomat
    # demetrios_kantakouzenos: political advisor, 2 events
    "demetrios_kantakouzenos": "1400-00-00", # ~34, younger Kantakouzenos
    # alexios_philanthropenos: political advisor, 1 event
    "alexios_philanthropenos": "1402-00-00", # ~32, younger Philanthropenos
    # kantakouzenos: family head, 16 events
    "kantakouzenos": "1375-00-00",           # ~59, family head/elder
    # philanthropenos: family head, 2 events
    "philanthropenos": "1378-00-00",         # ~56, family head/elder
    # raffaele_lomellini: diplomat/legal/religious, 8 events
    "raffaele_lomellini": "1385-00-00",      # ~49, Genoese leader
    # alessandro_duodo: legal advisor, 1 event
    "alessandro_duodo": "1390-00-00",        # ~44, Venetian legal advisor
}


# ============================================================
# TITLE BACKFILL
# ============================================================
# For 15 characters with empty title field.
# Assign a proper title, or "(untitled)" for commoners/servants.

TITLE_ASSIGNMENTS = {
    # Clearly should have a title:
    "joao_i": "King of Portugal",
    "gennadios_scholarios": "Scholar and Theologian",
    "sebastian_de_morales": "Captain of the Princess Catalina",
    "garcia_fernandez_manrique": "Don",

    # Ship captains / naval officers from ch 2.19:
    "diego_fernandez": "Master of the San Marcos",
    "luis_de_cordoba": "Ship Captain",
    "gaspar_de_vega": "Captain of the Santa Clara",
    "rodrigo_ibanez": "Ship Captain",
    "martin_de_soria": "Ship Captain",
    "alonso_pardo": "Ship Captain",
    "tomas_de_lepe": "Ship Captain",
    "francisco_ruiz": "Ship Captain",
    "cristobal_medina": "Ship Captain",

    # Genuinely untitled:
    "isabel_ruiz": "(untitled)",     # Converso cloth merchant's daughter, commoner
    "pascual": "(untitled)",         # Common sailor / rigger
}


# ============================================================
# INDEPENDENT FACTION DEFINITION
# ============================================================
INDEPENDENT_FACTION = {
    "faction_id": "independent",
    "name": "Independent (No Faction)",
    "type": "none",
    "region": "Various",
    "description": "Characters confirmed to have no affiliation with any defined faction. "
                   "Includes foreign sovereigns from untracked states, commoners, itinerant "
                   "individuals, and minor characters operating outside established political, "
                   "military, or institutional structures. This is an explicit classification "
                   "meaning 'evaluated and found to be unaffiliated', distinct from an empty "
                   "faction_ids list which means 'not yet evaluated'.",
    "leader_id": "",
    "member_ids": [],  # Will be populated by the script
    "event_refs": [],
    "first_mentioned_chapter": ""
}


def run():
    # Load data
    char_path = os.path.join(DATA_DIR, "characters.json")
    fac_path = os.path.join(DATA_DIR, "factions.json")

    char_data = load_json(char_path)
    fac_data = load_json(fac_path)

    chars = {c["id"]: c for c in char_data["characters"]}

    # Track stats
    stats = {
        "factions_assigned": 0,
        "factions_independent": 0,
        "dobs_estimated": 0,
        "titles_assigned": 0,
        "titles_untitled": 0,
    }

    # ---- PHASE 1: Faction assignments ----
    print("=== Phase 1: Faction Assignments ===")

    for cid, fids in FACTION_ASSIGNMENTS.items():
        if cid not in chars:
            print(f"  WARNING: {cid} not found in characters.json")
            continue
        c = chars[cid]
        existing = set(c.get("faction_ids", []))
        new = set(fids)
        merged = sorted(existing | new)
        if merged != sorted(existing):
            c["faction_ids"] = merged
            if "independent" in fids:
                stats["factions_independent"] += 1
            else:
                stats["factions_assigned"] += 1
            print(f"  {cid}: {sorted(existing)} → {merged}")

    # Verify no characters have empty faction_ids
    still_empty = [c["id"] for c in char_data["characters"] if not c.get("faction_ids", [])]
    if still_empty:
        print(f"\n  WARNING: {len(still_empty)} characters still have no faction_ids:")
        for cid in still_empty:
            print(f"    - {cid}")
    else:
        print(f"\n  All characters now have faction_ids assigned.")

    # ---- PHASE 2: DOB estimation ----
    print("\n=== Phase 2: DOB Estimation ===")

    for cid, dob in DOB_ESTIMATES.items():
        if cid not in chars:
            print(f"  WARNING: {cid} not found in characters.json")
            continue
        c = chars[cid]
        if c.get("born", "") == "0000-00-00":
            c["born"] = dob
            stats["dobs_estimated"] += 1
            print(f"  {cid}: 0000-00-00 → {dob}")
        else:
            pass  # Already has a DOB, skip

    # Verify no characters have 0000-00-00
    still_zero = [c["id"] for c in char_data["characters"] if c.get("born", "") == "0000-00-00"]
    if still_zero:
        print(f"\n  WARNING: {len(still_zero)} characters still have 0000-00-00 born:")
        for cid in still_zero:
            print(f"    - {cid}")
    else:
        print(f"\n  All characters now have estimated birthdates.")

    # ---- PHASE 3: Title backfill ----
    print("\n=== Phase 3: Title Backfill ===")

    for cid, title in TITLE_ASSIGNMENTS.items():
        if cid not in chars:
            print(f"  WARNING: {cid} not found in characters.json")
            continue
        c = chars[cid]
        if not c.get("title", "").strip():
            c["title"] = title
            if title == "(untitled)":
                stats["titles_untitled"] += 1
            else:
                stats["titles_assigned"] += 1
            print(f"  {cid}: '' → '{title}'")
        else:
            pass  # Already has a title, skip

    # Verify no characters have empty title
    still_no_title = [c["id"] for c in char_data["characters"]
                      if not c.get("title", "").strip()]
    if still_no_title:
        print(f"\n  WARNING: {len(still_no_title)} characters still have empty title:")
        for cid in still_no_title:
            print(f"    - {cid}")
    else:
        print(f"\n  All characters now have titles assigned.")

    # ---- PHASE 4: Add independent faction to factions.json ----
    print("\n=== Phase 4: Add Independent Faction ===")

    # Check if already exists
    existing_fac_ids = {f["faction_id"] for f in fac_data["factions"]}
    if "independent" not in existing_fac_ids:
        # Collect member_ids: all characters assigned to "independent"
        independent_members = sorted([
            cid for cid, fids in FACTION_ASSIGNMENTS.items()
            if "independent" in fids and cid in chars
        ])
        INDEPENDENT_FACTION["member_ids"] = independent_members
        fac_data["factions"].append(INDEPENDENT_FACTION)
        fac_data["meta"]["total_factions"] = len(fac_data["factions"])
        print(f"  Added 'independent' faction with {len(independent_members)} members:")
        for m in independent_members:
            print(f"    - {m}: {chars[m]['name']}")
    else:
        print("  'independent' faction already exists, skipping.")

    # Also update member_ids in existing factions to reflect new assignments
    print("\n=== Phase 5: Sync faction member_ids ===")
    fac_lookup = {f["faction_id"]: f for f in fac_data["factions"]}
    for cid, fids in FACTION_ASSIGNMENTS.items():
        if cid not in chars:
            continue
        for fid in fids:
            if fid in fac_lookup:
                members = fac_lookup[fid]["member_ids"]
                if cid not in members:
                    members.append(cid)
                    print(f"  Added {cid} to {fid}.member_ids")

    # ---- Save ----
    print("\n=== Saving ===")

    # Update meta
    char_data["meta"]["total_characters"] = len(char_data["characters"])

    save_json(char_path, char_data)
    print(f"  Saved {char_path}")

    save_json(fac_path, fac_data)
    print(f"  Saved {fac_path}")

    # ---- Summary ----
    print("\n=== Summary ===")
    print(f"  Factions assigned: {stats['factions_assigned']}")
    print(f"  Marked independent: {stats['factions_independent']}")
    print(f"  DOBs estimated: {stats['dobs_estimated']}")
    print(f"  Titles assigned: {stats['titles_assigned']}")
    print(f"  Titles marked (untitled): {stats['titles_untitled']}")

    total = sum(stats.values())
    print(f"  Total changes: {total}")

    return 0


if __name__ == "__main__":
    sys.exit(run())
