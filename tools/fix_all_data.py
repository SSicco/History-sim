#!/usr/bin/env python3
"""
Comprehensive data quality fix script for History-sim.
Fixes factions, characters, locations, laws, and cross-references.
"""
import json
import os
import shutil
import glob as globmod

DATA_DIR = "resources/data"
EVENTS_DIR = os.path.join(DATA_DIR, "events")

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Saved {path}")

# ============================================================================
# PHASE 1: Fix factions.json
# ============================================================================
def fix_factions():
    print("\n=== PHASE 1: Fixing factions.json ===")
    data = load_json(os.path.join(DATA_DIR, "factions.json"))
    factions_list = data["factions"]
    factions = {f["faction_id"]: f for f in factions_list}

    # 1a. Merge granada_emirate into granada
    if "granada_emirate" in factions and "granada" in factions:
        ge = factions["granada_emirate"]
        g = factions["granada"]
        # Merge event_refs
        merged_events = sorted(set(g["event_refs"] + ge["event_refs"]))
        g["event_refs"] = merged_events
        # Use earliest first_mentioned_chapter
        if ge.get("first_mentioned_chapter", "9") < g.get("first_mentioned_chapter", "9"):
            g["first_mentioned_chapter"] = ge["first_mentioned_chapter"]
        # Remove granada_emirate
        factions_list = [f for f in factions_list if f["faction_id"] != "granada_emirate"]
        factions = {f["faction_id"]: f for f in factions_list}
        print("  Merged granada_emirate into granada")

    # 1b. juan_ii should only be in: royal_court, royal_family, castile
    juan_factions = {"royal_court", "royal_family", "castile"}
    removed_from = []
    for f in factions_list:
        if f["faction_id"] not in juan_factions and "juan_ii" in f.get("member_ids", []):
            f["member_ids"].remove("juan_ii")
            removed_from.append(f["faction_id"])
    print(f"  Removed juan_ii from {len(removed_from)} factions: {removed_from}")

    # 1c. Fix copy-pasted member lists with correct members
    correct_members = {
        "colonna_family": ["prospero_colonna"],
        "orsini_family": ["cardinal_orsini"],
        "french_faction": ["cardinal_rochetaillee"],
        "medici_bank": ["cosimo_de_medici"],
        "vatican_guard": ["giacomo_pallavicini"],
        "apostolic_camera": ["francesco_condulmer", "tommaso_parentucelli"],
        "papacy": ["pope_eugenius_iv"],
        "papal_court": ["pope_eugenius_iv", "tommaso_parentucelli"],
        "papal_curia": ["pope_eugenius_iv", "tommaso_parentucelli", "nicolo_albergati",
                        "cardinal_capranica", "cardinal_rochetaillee", "marco_tornesi"],
        "college_of_cardinals": ["cardinal_orsini", "cardinal_rochetaillee",
                                  "cardinal_capranica", "nicolo_albergati",
                                  "francesco_condulmer", "cardinal_giuliano_cesarini",
                                  "cardinal_louis_aleman"],
        "council_of_basel": ["cardinal_giuliano_cesarini", "cardinal_louis_aleman"],
        "castilian_church": ["bishop_de_cartagena", "lope_de_barrientos",
                              "archbishop_cerezuela"],
        "military_orders": ["luis_de_guzman", "pedro_gonzalez_de_padilla",
                            "rodrigo_de_perea", "juan_de_sotomayor"],
        "royal_family": ["juan_ii", "isabel_of_portugal", "catalina_de_castilla", "dona_beatriz"],
        "castile": ["juan_ii", "alvaro_de_luna"],
        "granada": ["muhammad_ix", "rahman_al_zagal", "yusuf_ibn_rashid"],
        "aragonese_crown": ["alfonso_v", "rene_of_anjou", "maria_of_aragon",
                            "inigo_lopez_de_mendoza"],
        "byzantine_court": ["john_viii_palaiologos", "patriarch_joseph_ii",
                            "loukas_notaras", "kantakouzenos", "philanthropenos",
                            "george_sphrantzes"],
        "byzantine_merchants": ["kantakouzenos"],
        "byzantine_nobility": ["kantakouzenos", "philanthropenos",
                               "demetrios_kantakouzenos", "alexios_philanthropenos"],
        "orthodox_church": ["patriarch_joseph_ii", "gennadios_scholarios"],
        "venetian_quarter": ["marco_contarini", "alessandro_duodo"],
        "genoese_quarter": ["raffaele_lomellini"],
    }

    for fid, members in correct_members.items():
        if fid in factions:
            factions[fid]["member_ids"] = members

    # 1d. Add descriptions and leader_ids
    faction_meta = {
        "royal_court": {
            "description": "The inner circle of King Juan II of Castile. Includes the king's closest advisors, led by Constable Álvaro de Luna, and key administrators who direct royal policy.",
            "leader_id": "juan_ii"
        },
        "aragonese_faction": {
            "description": "Political faction of the Infantes de Aragón in Castile. Effectively dissolved after both Infantes were found guilty of rebellion at the November 1431 Royal Council, renounced all Castilian claims, and were sentenced to serve in the crusade as common soldiers.",
            "leader_id": "infante_juan_de_aragon"
        },
        "military_orders": {
            "description": "The three great military-religious orders of Castile: Santiago, Calatrava, and Alcántara. Their knights form the professional core of the crusade army. Placed under royal command by the papal crusade bull.",
            "leader_id": "luis_de_guzman"
        },
        "castilian_church": {
            "description": "The ecclesiastical hierarchy of Castile, including bishops and abbots who participate in royal councils and provide spiritual authority to the crown's policies.",
            "leader_id": "bishop_de_cartagena"
        },
        "royal_family": {
            "description": "The immediate Trastámara royal family: King Juan II, Queen Isabel of Portugal, and their children and close relatives.",
            "leader_id": "juan_ii"
        },
        "granada": {
            "description": "The Nasrid Kingdom of Granada, last Moorish state in Iberia. Ruled by Sultan Muhammad IX 'el Zurdo'. Under sustained military pressure from the Castilian crusade, with Morocco providing financial and military support.",
            "leader_id": "muhammad_ix"
        },
        "papacy": {
            "description": "The papal institution under Pope Eugenius IV (Gabriele Condulmer), locked in a power struggle with the Council of Basel over Church authority and reform.",
            "leader_id": "pope_eugenius_iv"
        },
        "council_of_basel": {
            "description": "The ecumenical council convened in Basel in 1431, asserting conciliar supremacy over the Pope. Originally led by Cardinal Cesarini, later by Cardinal Aleman. Juan II's Castilian delegation played a key mediating role.",
            "leader_id": "cardinal_giuliano_cesarini"
        },
        "college_of_cardinals": {
            "description": "The body of senior clergy who advise the Pope and elect his successor. Deeply divided between pro-papal loyalists and conciliarist sympathizers during the Basel crisis.",
            "leader_id": ""
        },
        "castile": {
            "description": "The Kingdom of Castile and León, the largest Christian kingdom in Iberia. Under the personal rule of Juan II with Álvaro de Luna as Constable and chief minister.",
            "leader_id": "juan_ii"
        },
        "vatican_guard": {
            "description": "The military guard protecting the Vatican and the person of Pope Eugenius IV, led by Captain Giacomo Pallavicini.",
            "leader_id": "giacomo_pallavicini"
        },
        "apostolic_camera": {
            "description": "The financial administration of the Holy See, managing papal revenues, taxation, and the treasury. Critical during the Basel crisis as both pope and council competed for Church finances.",
            "leader_id": "francesco_condulmer"
        },
        "papal_curia": {
            "description": "The administrative apparatus of the papacy, including offices, tribunals, and officials managing day-to-day governance of the Church.",
            "leader_id": "pope_eugenius_iv"
        },
        "colonna_family": {
            "description": "Powerful Roman noble family, traditional rivals of the Orsini. Pope Martin V was a Colonna. Their control of fortified positions around Rome makes them a major factor in papal politics.",
            "leader_id": "prospero_colonna"
        },
        "orsini_family": {
            "description": "Major Roman noble house and traditional rivals of the Colonna. Cardinal Giordano Orsini was one of the most influential cardinals in the Sacred College.",
            "leader_id": "cardinal_orsini"
        },
        "french_faction": {
            "description": "The pro-French faction within the Church, generally supporting conciliarism and the Council of Basel against papal authority. Seeks to limit Italian dominance of the Church.",
            "leader_id": "cardinal_rochetaillee"
        },
        "medici_bank": {
            "description": "The Medici banking house of Florence, the wealthiest financial institution in Europe. Manages papal finances and provides crucial loans to the papacy. Cosimo de' Medici is its head.",
            "leader_id": "cosimo_de_medici"
        },
        "papal_court": {
            "description": "The ceremonial and political court surrounding the Pope, including his closest advisors, household officials, and diplomatic representatives.",
            "leader_id": "pope_eugenius_iv"
        },
        "aragonese_crown": {
            "description": "The Crown of Aragon under King Alfonso V, who campaigns from Naples. Queen María governs as lieutenant in Iberia. Complex relationship with Castile due to the Infantes de Aragón.",
            "leader_id": "alfonso_v"
        },
        "byzantine_court": {
            "description": "The imperial court of Constantinople under Emperor John VIII Palaiologos. Facing existential Ottoman threat and debating Church union with Rome as a means to secure Western military aid.",
            "leader_id": "john_viii_palaiologos"
        },
        "byzantine_merchants": {
            "description": "The Greek merchant class of Constantinople, squeezed between Venetian and Genoese commercial dominance, hoping Western alliance will strengthen their trading position.",
            "leader_id": ""
        },
        "byzantine_nobility": {
            "description": "The Byzantine aristocracy, including the powerful Kantakouzenos and Philanthropenos families. Divided between pro-union and anti-union factions regarding Rome.",
            "leader_id": "kantakouzenos"
        },
        "orthodox_church": {
            "description": "The Orthodox Church of Constantinople, led by Patriarch Joseph II. Deeply divided over Church union with Rome, which many clergy view as theological betrayal but others see as necessary for survival.",
            "leader_id": "patriarch_joseph_ii"
        },
        "venetian_quarter": {
            "description": "The Venetian trading colony in Constantinople, centered on their fortified quarter. Venice's commercial interests dominate Eastern Mediterranean trade routes.",
            "leader_id": "marco_contarini"
        },
        "genoese_quarter": {
            "description": "The Genoese trading colony based in Galata across the Golden Horn from Constantinople. Commercial rivals of the Venetians for Eastern Mediterranean trade.",
            "leader_id": "raffaele_lomellini"
        },
    }

    for fid, meta in faction_meta.items():
        if fid in factions:
            factions[fid]["description"] = meta["description"]
            factions[fid]["leader_id"] = meta["leader_id"]

    data["factions"] = factions_list
    data["meta"]["total_factions"] = len(factions_list)
    save_json(os.path.join(DATA_DIR, "factions.json"), data)
    print(f"  Total factions: {len(factions_list)}")


# ============================================================================
# PHASE 2: Fix characters.json
# ============================================================================
def fix_characters():
    print("\n=== PHASE 2: Fixing characters.json ===")
    data = load_json(os.path.join(DATA_DIR, "characters.json"))
    chars = {c["id"]: c for c in data["characters"]}

    # 2a. Fix Capranica birth year (1369 -> 1400)
    if "cardinal_capranica" in chars:
        old = chars["cardinal_capranica"].get("born", "")
        chars["cardinal_capranica"]["born"] = "1400-00-00"
        print(f"  Fixed cardinal_capranica born: {old} -> 1400-00-00")

    # 2b. Backfill historically verifiable birth years
    birth_fixes = {
        "lope_de_barrientos": "1382-00-00",
        "pedro_manrique": "1381-00-00",
        "muhammad_ix": "1396-00-00",
        "juan_de_silva": "1399-00-00",
        "luis_de_guzman": "1380-00-00",
        "emperor_sigismund": "1368-02-15",
        "pope_eugenius_iv": "1383-00-00",
        "nicolo_albergati": "1375-00-00",
        "cardinal_rochetaillee": "1373-00-00",
        "francesco_condulmer": "1390-00-00",
        "rene_of_anjou": "1409-01-16",
        "george_sphrantzes": "1401-08-30",
        "john_viii_palaiologos": "1392-12-18",
        "loukas_notaras": "1402-00-00",
        "patriarch_joseph_ii": "1360-00-00",
        "gennadios_scholarios": "1400-00-00",
        "cardinal_louis_aleman": "1390-00-00",
        "joao_i": "1358-04-11",
        "pedro_fernandez_de_velasco": "1399-00-00",
        "berenguer_de_bardaxi": "1370-00-00",
        "prospero_colonna": "1410-00-00",
        "giacomo_pallavicini": "1395-00-00",
        "leonor_of_portugal": "1402-00-00",
        "juan_de_sotomayor": "1390-00-00",
        "tomas_de_torquemada": "1420-00-00",
    }
    count_births = 0
    for cid, born in birth_fixes.items():
        if cid in chars and chars[cid].get("born") == "0000-00-00":
            chars[cid]["born"] = born
            count_births += 1
    print(f"  Backfilled {count_births} birth years")

    # 2c. Backfill missing titles
    title_fixes = {
        "pedro_manrique": "Adelantado Mayor of León, Lord of Amusco",
        "emperor_sigismund": "Holy Roman Emperor, King of Hungary",
        "nicolo_albergati": "Cardinal, Bishop of Bologna",
        "prospero_colonna": "Prince of Salerno, Head of House Colonna",
        "francesco_condulmer": "Cardinal, Papal Nephew",
        "rene_of_anjou": "Duke of Anjou, titular King of Naples",
        "george_sphrantzes": "Imperial Secretary and Historian",
        "john_viii_palaiologos": "Byzantine Emperor",
        "patriarch_joseph_ii": "Ecumenical Patriarch of Constantinople",
        "giacomo_pallavicini": "Captain of the Vatican Guard",
        "juan_de_sotomayor": "Master of the Order of Alcántara",
        "marco_contarini": "Venetian Bailo of Constantinople",
        "raffaele_lomellini": "Genoese Podestà of Galata",
        "alessandro_duodo": "Venetian Merchant Captain",
        "leonor_of_portugal": "Infanta of Portugal",
        "ramon_de_perellos": "Commander of the Valencian Delegation",
        "hug_roger_iii_pallars": "Count of Pallars",
        "berenguer_de_bardaxi": "Justicia of Aragon",
        "bernat_fiveller": "Conseller-en-Cap of Barcelona",
        "pere_joan_de_sant_climent": "Catalan Merchant and Civic Leader",
        "viscount_of_rocaberti": "Viscount of Rocabertí",
        "rahman_al_zagal": "Granadan Military Commander",
        "hamza_ibn_fadil": "Granadan Noble and Diplomat",
        "ahmad_ibn_khalil": "Granadan Court Advisor",
        "bernat_de_centelles": "Aragonese Noble",
        "cardinal_louis_aleman": "Cardinal, Archbishop of Arles",
        "cardinal_giuliano_cesarini": "Cardinal, President of the Council of Basel",
        "rodrigo_de_cervantes": "Knight Commander of Santiago",
        "vasco_de_orozco": "Knight Commander of Calatrava",
        "diego_de_sotomayor": "Castilian Military Commander",
        "kantakouzenos": "Byzantine Noble, Kantakouzenos Family",
        "philanthropenos": "Byzantine Noble, Philanthropenos Family",
        "alexios_philanthropenos": "Byzantine Military Commander",
        "demetrios_kantakouzenos": "Byzantine Military Commander",
        "tomas_de_torquemada": "Dominican Friar",
        "lucia_deste": "Lady of the House of Este",
        "donna_francesca": "Roman Noblewoman",
        "isabella_strozzi": "Florentine Lady of House Strozzi",
        "alfonso_de_guzman": "Castilian Noble of House Guzmán",
        "juan_de_silva": "Alférez Mayor of Castile, Lord of Cifuentes",
    }
    count_titles = 0
    for cid, title in title_fixes.items():
        if cid in chars and not chars[cid].get("title", "").strip():
            chars[cid]["title"] = title
            count_titles += 1
    print(f"  Backfilled {count_titles} titles")

    # 2d. Backfill faction_ids
    faction_assignments = {
        "alvaro_de_luna": ["royal_court"],
        "fernan_alonso_de_robles": ["royal_court"],
        "fray_hernando": ["royal_court", "castilian_church"],
        "lope_de_barrientos": ["royal_court", "castilian_church"],
        "infante_juan_de_aragon": ["aragonese_faction"],
        "infante_enrique_de_aragon": ["aragonese_faction"],
        "pedro_manrique": ["royal_court"],
        "archbishop_cerezuela": ["castilian_church"],
        "bishop_de_cartagena": ["castilian_church"],
        "isabel_of_portugal": ["royal_family"],
        "catalina_de_castilla": ["royal_family"],
        "dona_beatriz": ["royal_family"],
        "muhammad_ix": ["granada"],
        "rahman_al_zagal": ["granada"],
        "yusuf_ibn_rashid": ["granada"],
        "hamza_ibn_fadil": ["granada"],
        "ahmad_ibn_khalil": ["granada"],
        "luis_de_guzman": ["military_orders"],
        "pedro_gonzalez_de_padilla": ["military_orders"],
        "rodrigo_de_perea": ["military_orders"],
        "juan_de_sotomayor": ["military_orders"],
        "rodrigo_de_cervantes": ["military_orders"],
        "vasco_de_orozco": ["military_orders"],
        "pope_eugenius_iv": ["papacy", "papal_curia"],
        "tommaso_parentucelli": ["papal_curia", "apostolic_camera"],
        "nicolo_albergati": ["college_of_cardinals", "papal_curia"],
        "cardinal_capranica": ["college_of_cardinals", "papal_curia"],
        "cardinal_orsini": ["college_of_cardinals", "orsini_family"],
        "cardinal_rochetaillee": ["college_of_cardinals", "french_faction", "papal_curia"],
        "cardinal_giuliano_cesarini": ["college_of_cardinals", "council_of_basel"],
        "cardinal_louis_aleman": ["college_of_cardinals", "council_of_basel"],
        "francesco_condulmer": ["college_of_cardinals", "apostolic_camera"],
        "prospero_colonna": ["colonna_family"],
        "giacomo_pallavicini": ["vatican_guard"],
        "marco_tornesi": ["papal_curia"],
        "cosimo_de_medici": ["medici_bank"],
        "alfonso_v": ["aragonese_crown"],
        "maria_of_aragon": ["aragonese_crown"],
        "rene_of_anjou": ["aragonese_crown"],
        "inigo_lopez_de_mendoza": ["royal_court"],
        "john_viii_palaiologos": ["byzantine_court"],
        "patriarch_joseph_ii": ["byzantine_court", "orthodox_church"],
        "loukas_notaras": ["byzantine_court", "byzantine_nobility"],
        "george_sphrantzes": ["byzantine_court"],
        "kantakouzenos": ["byzantine_court", "byzantine_nobility", "byzantine_merchants"],
        "philanthropenos": ["byzantine_nobility"],
        "demetrios_kantakouzenos": ["byzantine_nobility"],
        "alexios_philanthropenos": ["byzantine_nobility"],
        "gennadios_scholarios": ["orthodox_church"],
        "marco_contarini": ["venetian_quarter"],
        "alessandro_duodo": ["venetian_quarter"],
        "raffaele_lomellini": ["genoese_quarter"],
        "pedro_fernandez_de_velasco": ["royal_court"],
        "rodrigo_manrique": ["royal_court"],
        "juan_de_silva": ["royal_court"],
        "juan_de_daza": ["royal_court"],
        "garcia_fernandez": ["royal_court"],
        "leonor_of_portugal": ["royal_family"],
        "ramon_de_perellos": ["aragonese_crown"],
        "hug_roger_iii_pallars": ["aragonese_crown"],
        "berenguer_de_bardaxi": ["aragonese_crown"],
        "bernat_fiveller": ["aragonese_crown"],
        "pere_joan_de_sant_climent": ["aragonese_crown"],
        "bernat_de_centelles": ["aragonese_crown"],
        "fray_sebastian": ["castilian_church"],
        "fray_miguel": ["castilian_church"],
    }
    count_factions = 0
    for cid, fids in faction_assignments.items():
        if cid in chars:
            existing = set(chars[cid].get("faction_ids", []))
            new = set(fids)
            merged = sorted(existing | new)
            if merged != sorted(existing):
                chars[cid]["faction_ids"] = merged
                count_factions += 1
    print(f"  Updated faction_ids on {count_factions} characters")

    # 2e. Resolve villalobos alias collision
    # Remove shared alias from don_rodrigo, keep on garcia_fernandez
    if "don_rodrigo_de_villalobos" in chars:
        aliases = chars["don_rodrigo_de_villalobos"].get("aliases", [])
        if "villalobos" in aliases:
            aliases.remove("villalobos")
            chars["don_rodrigo_de_villalobos"]["aliases"] = aliases
            print("  Removed shared 'villalobos' alias from don_rodrigo_de_villalobos")

    # 2f. Merge duplicate characters: alfonso_de_guzman / baron_alfonso_de_guzman
    if "alfonso_de_guzman" in chars and "baron_alfonso_de_guzman" in chars:
        main = chars["baron_alfonso_de_guzman"]
        dup = chars["alfonso_de_guzman"]
        # Merge aliases
        all_aliases = list(set(main.get("aliases", []) + dup.get("aliases", []) + ["alfonso_de_guzman"]))
        main["aliases"] = all_aliases
        # Merge event_refs
        all_events = sorted(set(main.get("event_refs", []) + dup.get("event_refs", [])))
        main["event_refs"] = all_events
        # Remove duplicate
        data["characters"] = [c for c in data["characters"] if c["id"] != "alfonso_de_guzman"]
        chars = {c["id"]: c for c in data["characters"]}
        print("  Merged alfonso_de_guzman into baron_alfonso_de_guzman")

    # 2g. Merge duplicate: pedro_manrique / pedro_manrique_de_lara
    if "pedro_manrique" in chars and "pedro_manrique_de_lara" in chars:
        main = chars["pedro_manrique"]
        dup = chars["pedro_manrique_de_lara"]
        all_aliases = list(set(main.get("aliases", []) + dup.get("aliases", []) + ["pedro_manrique_de_lara"]))
        main["aliases"] = all_aliases
        all_events = sorted(set(main.get("event_refs", []) + dup.get("event_refs", [])))
        main["event_refs"] = all_events
        # Keep the richer data
        if not main.get("title") and dup.get("title"):
            main["title"] = dup["title"]
        if main.get("born") == "0000-00-00" and dup.get("born") != "0000-00-00":
            main["born"] = dup["born"]
        data["characters"] = [c for c in data["characters"] if c["id"] != "pedro_manrique_de_lara"]
        chars = {c["id"]: c for c in data["characters"]}
        print("  Merged pedro_manrique_de_lara into pedro_manrique")

    # 2h. Trim Juan II personality traits - remove contradictory/redundant ones
    if "juan_ii" in chars:
        old_traits = chars["juan_ii"].get("personality", [])
        # Keep a focused set, removing contradictions and redundancy
        trimmed = [
            "strategic", "pious", "ambitious", "bold",
            "deceptive_when_needed", "charismatic_speaker",
            "diplomatic", "decisive", "reformist",
            "pragmatic", "introspective"
        ]
        chars["juan_ii"]["personality"] = trimmed
        print(f"  Trimmed Juan II personality: {len(old_traits)} -> {len(trimmed)} traits")

    # 2i. Remove phantom event refs (evt_1432_00158, evt_1432_00159)
    phantom_events = {"evt_1432_00158", "evt_1432_00159"}
    count_phantom = 0
    for c in data["characters"]:
        if "event_refs" in c:
            before = len(c["event_refs"])
            c["event_refs"] = [e for e in c["event_refs"] if e not in phantom_events]
            count_phantom += before - len(c["event_refs"])
    print(f"  Removed {count_phantom} phantom event references")

    data["meta"]["total_characters"] = len(data["characters"])
    save_json(os.path.join(DATA_DIR, "characters.json"), data)
    print(f"  Total characters: {len(data['characters'])}")


# ============================================================================
# PHASE 3: Fix locations.json
# ============================================================================
def fix_locations():
    print("\n=== PHASE 3: Fixing locations.json ===")
    data = load_json(os.path.join(DATA_DIR, "locations.json"))
    locs = {loc["location_id"]: loc for loc in data["locations"]}

    # 3a. Merge granada_city into granada (keep granada as primary)
    if "granada" in locs and "granada_city" in locs:
        main = locs["granada"]
        dup = locs["granada_city"]
        # Merge sub_locations
        all_subs = list(set(main.get("sub_locations", []) + dup.get("sub_locations", [])))
        main["sub_locations"] = sorted(all_subs)
        # Merge event_refs
        all_events = sorted(set(main.get("event_refs", []) + dup.get("event_refs", [])))
        main["event_refs"] = all_events
        # Keep richer description
        if len(dup.get("description", "")) > len(main.get("description", "")):
            main["description"] = dup["description"]
        # Remove duplicate
        data["locations"] = [l for l in data["locations"] if l["location_id"] != "granada_city"]
        locs = {loc["location_id"]: loc for loc in data["locations"]}
        print("  Merged granada_city into granada")

    # 3b. Fix Vatican sub_locations inversion
    if "vatican" in locs:
        locs["vatican"]["sub_locations"] = [
            "Papal Audience Chamber",
            "Sistine Chapel",
            "Apostolic Palace",
            "St. Peter's Basilica"
        ]
        locs["vatican"]["region"] = "Papal States"
        locs["vatican"]["description"] = "The papal complex in Rome, seat of the Bishop of Rome and center of Catholic Church administration. Includes the Apostolic Palace, St. Peter's Basilica, and the papal audience chambers."
        print("  Fixed Vatican sub_locations and added description")

    # 3c. Fix at_sea name
    if "at_sea" in locs:
        locs["at_sea"]["name"] = "At Sea"
        locs["at_sea"]["region"] = "Mediterranean"
        locs["at_sea"]["description"] = "Open waters of the Mediterranean Sea, traversed by Juan II's fleet during voyages between Iberia, Italy, and Constantinople."
        print("  Fixed at_sea name and added description")

    # 3d. Fill missing descriptions and regions
    location_meta = {
        "valladolid_outskirts": {
            "region": "Castile",
            "description": "The approaches and surrounding countryside of Valladolid, including roads and farmland near the royal capital."
        },
        "road_north_of_valladolid": {
            "region": "Castile",
            "description": "The road leading north from Valladolid toward the Cantabrian coast and the pilgrimage route to Santiago."
        },
        "castile": {
            "region": "Iberia",
            "description": "The Kingdom of Castile and León, the largest Christian kingdom in the Iberian Peninsula, stretching from the Cantabrian coast to the Granadan frontier."
        },
        "loja": {
            "region": "Granada frontier",
            "description": "Fortified Granadan town on the road between Málaga and Granada city. Strategic waypoint for military operations in the western Granada campaign."
        },
        "sanlucar_de_barrameda": {
            "region": "Andalusia",
            "description": "Port town at the mouth of the Guadalquivir River. Controlled by the Guzmán family. Key point for Atlantic maritime trade and naval operations."
        },
        "moclin": {
            "region": "Granada frontier",
            "description": "Strong Granadan hilltop fortress northwest of Granada city, guarding the approach from Castilian territory. Key defensive position in the eastern campaign."
        },
        "alhama_de_granada": {
            "region": "Granada interior",
            "description": "Fortified town in the interior of the Emirate of Granada, south of Granada city. Known for its hot springs and strategic position on inland routes."
        },
        "iznalloz": {
            "region": "Granada frontier",
            "description": "Granadan frontier fortress on the northern approach to Granada city, along the road from Jaén."
        },
        "granada_to_toledo": {
            "region": "Castile",
            "description": "The long road from conquered Granada northward through La Mancha to Toledo, traversing the heart of Castile."
        },
        "road_to_malaga": {
            "region": "Granada coast",
            "description": "Coastal road leading to the port city of Málaga, passing through mountainous terrain along Granada's Mediterranean coast."
        },
        "road_to_ronda": {
            "region": "Granada interior",
            "description": "Mountain road leading to the fortress city of Ronda, through the rugged Serranía de Ronda."
        },
        "road_to_toledo": {
            "region": "Castile",
            "description": "Road leading to Toledo through central Castile, passing through La Mancha."
        },
        "road_from_granada_to_malaga": {
            "region": "Granada",
            "description": "The road connecting Granada city to the Mediterranean port of Málaga, crossing the Axarquía mountain region."
        },
        "mediterranean_sea": {
            "region": "Mediterranean",
            "description": "The great inland sea connecting Europe, Africa, and Asia. Primary route for Juan II's fleet traveling between Iberia and the eastern Mediterranean."
        },
        "ostia": {
            "region": "Papal States",
            "description": "Ancient port city at the mouth of the Tiber River, serving as Rome's maritime gateway. Key landing point for arrivals by sea to the papal capital."
        },
        "road_from_rome_to_basel": {
            "region": "Italy/Holy Roman Empire",
            "description": "The long overland route from Rome northward through Italy, across the Alps, to the Swiss city of Basel."
        },
        "basel": {
            "region": "Holy Roman Empire",
            "description": "Swiss city on the Rhine hosting the ecumenical Council of Basel (1431-1449). Site of fierce debates over Church reform and papal authority, where Juan II's delegation played a mediating role."
        },
        "basel_to_como": {
            "region": "Italy/Holy Roman Empire",
            "description": "Route from Basel southward across the Alps to the Italian lakeside city of Como."
        },
        "como": {
            "region": "Italy",
            "description": "Lakeside city in northern Italy at the southern tip of Lake Como. Waypoint on Juan II's return journey from Basel to Castile."
        },
        "como_to_toledo": {
            "region": "Italy/Castile",
            "description": "The long return route from Como across the Mediterranean and through Iberia back to Toledo."
        },
        "alcazar_of_toledo": {
            "region": "Castile",
            "description": "The royal fortress-palace crowning the highest point of Toledo. Seat of royal government and site of major council meetings and state ceremonies."
        },
        "madrid": {
            "region": "Castile",
            "description": "Castilian town between Toledo and the northern territories. Used as a waypoint and occasional meeting place for royal business."
        },
        "toledo_to_barcelona": {
            "region": "Castile/Aragon",
            "description": "Route from Toledo eastward across the Castilian meseta and into the Crown of Aragon to the Mediterranean port of Barcelona."
        },
        "cagliari": {
            "region": "Sardinia",
            "description": "Port city and capital of Sardinia, under Aragonese rule. Stopover point for ships traveling between Iberia and Italy."
        },
        "tiber_river": {
            "region": "Papal States",
            "description": "The river flowing through Rome to the sea at Ostia. Navigable for smaller vessels between Rome and its port."
        },
        "tyrrhenian_sea": {
            "region": "Mediterranean",
            "description": "The western basin of the Mediterranean Sea, bounded by Italy, Sardinia, Corsica, and Sicily. Traversed by Juan II's fleet en route to Naples."
        },
        "naples": {
            "region": "Italy",
            "description": "Major Mediterranean port and capital of the Kingdom of Naples. Contested between René of Anjou and Alfonso V of Aragon. Key strategic stopover for Juan II's eastern voyage."
        },
        "ionian_sea": {
            "region": "Mediterranean",
            "description": "The body of water between southern Italy and western Greece, crossed by Juan II's fleet en route to Constantinople."
        },
        "candia": {
            "region": "Crete (Venetian)",
            "description": "Capital of Venetian Crete (modern Heraklion). Major Venetian naval base and trading hub in the eastern Mediterranean. Stopover for ships traveling to Constantinople."
        },
        "constantinople": {
            "region": "Byzantine Empire",
            "description": "Capital of the Byzantine Empire under Emperor John VIII Palaiologos. Ancient city on the Bosporus facing existential Ottoman threat. Juan II arrives as a diplomatic envoy seeking to broker Church union and coordinate anti-Ottoman strategy."
        },
    }

    count_locs = 0
    for lid, meta in location_meta.items():
        if lid in locs:
            changed = False
            if not locs[lid].get("description", "").strip() and meta.get("description"):
                locs[lid]["description"] = meta["description"]
                changed = True
            if not locs[lid].get("region", "").strip() and meta.get("region"):
                locs[lid]["region"] = meta["region"]
                changed = True
            if changed:
                count_locs += 1
    print(f"  Filled descriptions/regions for {count_locs} locations")

    data["meta"]["total_locations"] = len(data["locations"])
    save_json(os.path.join(DATA_DIR, "locations.json"), data)
    print(f"  Total locations: {len(data['locations'])}")


# ============================================================================
# PHASE 4: Fix laws.json
# ============================================================================
def fix_laws():
    print("\n=== PHASE 4: Fixing laws.json ===")
    data = load_json(os.path.join(DATA_DIR, "laws.json"))
    laws = {law["law_id"]: law for law in data["laws"]}

    law_completions = {
        "law_042": {
            "full_text": "BE IT ENACTED by the Cortes of Valladolid, in session this fifteenth day of November, in the Year of Our Lord 1431:\n\nARTICLE I: CRUSADE TAX\nA special tax of five percent (5%) shall be levied upon all noble revenues throughout the Kingdom of Castile and León, replacing normal crown taxation for the duration of the holy crusade against Granada.\n\nARTICLE II: LEVY COMPENSATION\nAll men called to serve in the crusade army shall receive compensation as follows:\n- Knight: 120 maravedís per month\n- Man-at-arms: 80 maravedís per month\n- Foot soldier: 50 maravedís per month\n\nARTICLE III: DURATION\nThis tax shall remain in effect until December 31, 1433, or until the completion of the crusade, whichever comes first.\n\nARTICLE IV: ADMINISTRATION\nThe Crown shall appoint tax assessors to each noble estate. Resistance to assessment shall be referred to the Crown Marshals.\n\nPassed by vote of the Cortes: 52 in favor, 3 against, 5 abstaining.",
            "scope": "kingdom",
            "enacted_by": "cortes_of_valladolid",
            "tags": ["taxation", "military", "crusade"]
        },
        "law_043": {
            "full_text": "BY ROYAL DECREE of Juan II, King of Castile and León, issued this twenty-fifth day of October, 1431:\n\nARTICLE I: ESTABLISHMENT\nThe Office of Crown Marshal is hereby created as a permanent institution of royal enforcement.\n\nARTICLE II: ESCALATION PROCEDURES\nCrown Marshals shall follow structured escalation in all enforcement actions:\n1. Formal written demand citing the specific law or decree violated\n2. Proportional fines for non-compliance, scaled to the severity of the offense\n3. Escalation to military action only upon continued defiance after formal demand and fines\n\nARTICLE III: SEPARATION OF POWERS\nNo Marshal may both judge a case and enforce its penalty. Judgment shall be rendered by royal courts; Marshals shall execute the court's orders.\n\nARTICLE IV: APPOINTMENT\nCrown Marshals shall be appointed by the King and serve at royal pleasure. They shall be men of proven loyalty and sound judgment.",
            "scope": "kingdom",
            "enacted_by": "juan_ii",
            "tags": ["governance", "law_enforcement", "reform"]
        },
        "law_044": {
            "full_text": "BY THE AUTHORITY of His Majesty Juan II, King of Castile and León, and by the spiritual authority vested in the Church through the Papal Crusade Bull:\n\nWHEREAS Gómez de Sotomayor, Baron de Medina, and the Count of Niebla did threaten and assault royal tax assessors carrying out their lawful duties under the Crusade Tax Law;\n\nWHEREAS such actions constitute defiance of both royal and ecclesiastical authority;\n\nIT IS HEREBY DECREED:\n1. The aforementioned three nobles are EXCOMMUNICATED from the Holy Church, deprived of sacraments and Christian fellowship until such time as they submit and make amends.\n2. Their lands and properties are declared FORFEIT to the Crown.\n3. All vassals and retainers of said nobles are released from their oaths of fealty.\n4. Any who provide aid or shelter to the excommunicated shall themselves face ecclesiastical censure.",
            "scope": "targeted",
            "enacted_by": "juan_ii",
            "tags": ["ecclesiastical", "punishment", "enforcement"]
        },
        "law_045": {
            "full_text": "BY ROYAL DECREE of Juan II, King of Castile and León, Supreme Commander of the Holy Crusade, issued this sixteenth day of February, 1432:\n\nARTICLE I: LAND GRANTS\nNoble estates in the conquered territories of western Granada shall be awarded to deserving lords who have contributed to the crusade effort, under the following terms.\n\nARTICLE II: TAXATION\nAll granted estates shall pay a crown tax of eight percent (8%) of annual revenues.\n\nARTICLE III: REASSESSMENT\nEstate valuations and tax assessments shall be reviewed every ten (10) years to ensure fair and current taxation.\n\nARTICLE IV: CONDITIONS\nGrantees must maintain the land in productive use, provide military service when called, and ensure peaceful governance of local populations including Moorish subjects who have submitted.\n\nARTICLE V: AUTHORITY\nThese grants are made under the Supreme Commander's crusade authority as established by the Papal Bull Inter Cetera Divinae.",
            "scope": "regional",
            "enacted_by": "juan_ii",
            "tags": ["land_reform", "crusade", "taxation", "nobility"]
        },
        "law_046": {
            "full_text": "FORMAL POSITION OF THE KINGDOM OF CASTILE regarding the Council of Basel, prepared by Royal Council and approved by His Majesty Juan II, issued this twenty-third day of February, 1432:\n\nARTICLE I: VERNACULAR PREACHING\nCastile supports the right of clergy to preach in the vernacular languages of their congregations, that the Word of God may be understood by all the faithful.\n\nARTICLE II: COMMUNION\nCastile supports the practice of communion in both kinds (bread and wine) for the laity, as was the ancient practice of the Church.\n\nARTICLE III: CHURCH PROPERTY\nCastile rejects any proposal for the seizure or confiscation of Church property by secular authorities. The independence of ecclesiastical holdings must be preserved.\n\nARTICLE IV: INTERNAL OVERSIGHT\nCastile demands stronger internal oversight mechanisms within the Church hierarchy to prevent corruption, simony, and abuse of office.\n\nARTICLE V: DELEGATION\nA six-person delegation is hereby appointed to represent Castile at the Council, with authority to negotiate on these positions while keeping the Crown informed of all proceedings.",
            "scope": "diplomatic",
            "enacted_by": "juan_ii",
            "tags": ["ecclesiastical", "diplomacy", "reform", "council_of_basel"]
        },
    }

    for lid, completion in law_completions.items():
        if lid in laws:
            for key, val in completion.items():
                laws[lid][key] = val
    print(f"  Completed {len(law_completions)} law stubs")

    save_json(os.path.join(DATA_DIR, "laws.json"), data)


# ============================================================================
# PHASE 5: Fix character <-> event cross-references
# ============================================================================
def fix_cross_references():
    print("\n=== PHASE 5: Fixing character <-> event cross-references ===")

    # Build event -> characters map from all chapter files
    event_chars = {}
    chapter_files = sorted(globmod.glob(os.path.join(EVENTS_DIR, "chapter_*.json")))
    for cf in chapter_files:
        chapter_data = load_json(cf)
        events = chapter_data if isinstance(chapter_data, list) else chapter_data.get("events", [])
        for evt in events:
            eid = evt.get("event_id", "")
            chars_list = evt.get("characters", [])
            if eid:
                event_chars[eid] = chars_list

    print(f"  Loaded {len(event_chars)} events from {len(chapter_files)} chapter files")

    # Load characters
    char_data = load_json(os.path.join(DATA_DIR, "characters.json"))
    chars = {c["id"]: c for c in char_data["characters"]}

    # Build character -> events map from events (source of truth)
    char_events_from_source = {}
    for eid, clist in event_chars.items():
        for cid in clist:
            if cid not in char_events_from_source:
                char_events_from_source[cid] = set()
            char_events_from_source[cid].add(eid)

    # Update character event_refs to match source of truth
    added = 0
    removed = 0
    for c in char_data["characters"]:
        cid = c["id"]
        current_refs = set(c.get("event_refs", []))
        source_refs = char_events_from_source.get(cid, set())

        # Union: keep existing refs that are valid events + add missing ones from source
        valid_current = current_refs & set(event_chars.keys())
        new_refs = sorted(valid_current | source_refs)

        added_count = len(source_refs - current_refs)
        removed_count = len(current_refs - set(event_chars.keys()))
        added += added_count
        removed += removed_count

        c["event_refs"] = new_refs

    print(f"  Added {added} missing event refs, removed {removed} invalid refs")

    save_json(os.path.join(DATA_DIR, "characters.json"), char_data)


# ============================================================================
# PHASE 6: Copy roll_tables.json from archive
# ============================================================================
def copy_roll_tables():
    print("\n=== PHASE 6: Copying roll_tables.json ===")
    src = "archive/v1_data/roll_tables.json"
    dst = os.path.join(DATA_DIR, "roll_tables.json")
    if os.path.exists(src) and not os.path.exists(dst):
        shutil.copy2(src, dst)
        print(f"  Copied {src} -> {dst}")
    elif os.path.exists(dst):
        print(f"  {dst} already exists, skipping")
    else:
        print(f"  WARNING: {src} not found")


# ============================================================================
# MAIN
# ============================================================================
def main():
    print("=" * 60)
    print("COMPREHENSIVE DATA QUALITY FIX")
    print("=" * 60)

    fix_factions()
    fix_characters()
    fix_locations()
    fix_laws()
    fix_cross_references()
    copy_roll_tables()

    print("\n" + "=" * 60)
    print("ALL FIXES COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
