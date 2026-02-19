#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.01.

Reads tools/preprocessed/chapter_1.01_preprocessed.json and produces
tools/extractions/chapter_1.01_extracted.json in the schema expected
by merge_chapter.py.

Event boundaries and metadata are manually determined from reading the
chapter content.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.01_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.01_extracted.json"

# -----------------------------------------------------------------------
# Event definitions: (start_msg, end_msg, metadata)
# Messages are player/gm pairs. start/end are inclusive message indices.
# -----------------------------------------------------------------------

EVENT_DEFS = [
    {
        "msgs": (1, 6),
        "date": "1430-05-01",
        "type": "council",
        "summary": "Juan II takes stock of his kingdom, reads urgent letters from Seville, Toledo, the frontier, and the Infante Juan de Aragón. Álvaro de Luna warns him about how the Infantes seek to control the crown through council manipulation, information control, and physical custody.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "pedro_fernandez_de_velasco",
            "inigo_lopez_de_mendoza", "archbishop_contreras",
            "infante_juan_de_aragon", "infante_enrique_de_aragon"
        ],
        "factions_affected": ["royal_court", "aragonese_faction"],
        "location": "Valladolid, Royal Palace",
        "tags": ["politics", "intrigue", "opening"],
    },
    {
        "msgs": (7, 12),
        "date": "1430-05-01",
        "type": "decision",
        "summary": "Juan II declares his intention to rule independently, secures his immediate surroundings, and plans an advisory cabinet of trusted men including Lope de Barrientos, Íñigo López de Mendoza, and Rodrigo Manrique.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "lope_de_barrientos",
            "inigo_lopez_de_mendoza", "pedro_manrique"
        ],
        "factions_affected": ["royal_court"],
        "location": "Valladolid, Royal Palace",
        "tags": ["politics", "planning"],
    },
    {
        "msgs": (13, 18),
        "date": "1430-05-02",
        "type": "decision",
        "summary": "Juan II addresses the royal guard in the palace courtyard, attempting to inspire loyalty and morale with a speech. The dice roll results in status quo — the speech neither inspires nor alienates the guards.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "fernan_alonso_de_robles"
        ],
        "factions_affected": [],
        "location": "Valladolid, Palace Courtyard",
        "tags": ["military", "speech", "roll"],
    },
    {
        "msgs": (19, 24),
        "date": "1430-05-02",
        "type": "decision",
        "summary": "Juan II reviews the royal treasury with Álvaro and authorizes 150,000 maravedís for guard equipment. They discuss the kingdom's financial situation: ~30 million annual revenue with ~240,000 surplus. Juan begins formulating his grand strategy: papal crusade bull, noble council, and Granada campaign.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "fernan_alonso_de_robles"
        ],
        "factions_affected": ["royal_court"],
        "location": "Valladolid, Royal Palace",
        "tags": ["economy", "military", "planning"],
    },
    {
        "msgs": (25, 34),
        "date": "1430-05-02",
        "type": "decision",
        "summary": "Juan II reveals his bold plan to personally travel to Rome to secure a papal crusade bull, using a pilgrimage to Santiago de Compostela as cover. Álvaro is alarmed by the risks but impressed by the political instinct. They develop a deception strategy: meet the Infantes first, play the pliant young king, let them propose a council (which Juan already planned), then depart on 'pilgrimage' while secretly continuing to Rome.",
        "characters": [
            "juan_ii", "alvaro_de_luna"
        ],
        "factions_affected": ["royal_court", "aragonese_faction"],
        "location": "Valladolid, Royal Palace",
        "tags": ["strategy", "diplomacy", "deception"],
    },
    {
        "msgs": (35, 38),
        "date": "1430-05-03",
        "type": "decision",
        "summary": "Juan II chooses Fray Hernando de Talavera as his new confessor over two other candidates, valuing his youth, humility, and pure faith. The choice also serves a strategic purpose — Juan needs a travel companion for his pilgrimage who can keep up physically.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "fray_hernando"
        ],
        "factions_affected": [],
        "location": "Valladolid, Royal Palace",
        "tags": ["religion", "personal"],
    },
    {
        "msgs": (39, 42),
        "date": "1430-05-10",
        "type": "decision",
        "summary": "Juan II spends a week in preparation: training in combat with Captain Fernán (sword, mounted combat, physical conditioning), rehearsing his role for the upcoming meeting with the Infantes, and assembling his advisory cabinet.",
        "characters": [
            "juan_ii", "fernan_alonso_de_robles", "alvaro_de_luna"
        ],
        "factions_affected": [],
        "location": "Valladolid, Palace Courtyard",
        "tags": ["military", "training", "preparation"],
    },
    {
        "msgs": (43, 60),
        "date": "1430-05-15",
        "type": "diplomacy",
        "summary": "Juan II meets the Infantes de Aragón at Medina del Campo, executing his deception plan. He plays the earnest but overwhelmed young king, lets them propose a noble council (which he already planned), negotiates regency arrangements for his 'pilgrimage', and directly confronts them about Álvaro de Luna — ultimately striking a deal where Álvaro is constrained but not removed, the Infantes get a regency council with real power during his absence, and Juan can depart on pilgrimage.",
        "characters": [
            "juan_ii", "infante_juan_de_aragon", "infante_enrique_de_aragon",
            "alvaro_de_luna"
        ],
        "factions_affected": ["royal_court", "aragonese_faction"],
        "location": "Medina del Campo",
        "tags": ["diplomacy", "negotiation", "deception"],
    },
    {
        "msgs": (61, 76),
        "date": "1430-05-15",
        "end_date": "1430-05-20",
        "type": "diplomacy",
        "summary": "Juan II and the Infantes finalize the council arrangements: drafting invitations for 18-20 members (great houses, military orders, church, city representatives), setting the council date for December 1430 in Seville, formally establishing the regency council's powers, and preparing royal sealed invitations. Juan schedules a formal regency declaration ceremony with the Infantes for the following week.",
        "characters": [
            "juan_ii", "infante_juan_de_aragon", "infante_enrique_de_aragon",
            "archbishop_cerezuela"
        ],
        "factions_affected": ["royal_court", "aragonese_faction"],
        "location": "Medina del Campo",
        "tags": ["diplomacy", "administration", "council"],
    },
    {
        "msgs": (77, 80),
        "date": "1430-05-20",
        "type": "crisis",
        "summary": "Juan II's plan to prevent the Infantes from revolting during his pilgrimage is put to the dice. Despite careful negotiation and giving the Infantes real power, the roll comes up badly — a revolt WILL take place during Juan's absence. The chapter ends with the dice's cruel verdict hanging over all the young king's careful planning.",
        "characters": [
            "juan_ii", "infante_juan_de_aragon", "infante_enrique_de_aragon",
            "alvaro_de_luna"
        ],
        "factions_affected": ["royal_court", "aragonese_faction"],
        "location": "Medina del Campo",
        "tags": ["crisis", "roll", "revolt", "cliffhanger"],
    },
]

# -----------------------------------------------------------------------
# New characters (not in known_aliases.json)
# -----------------------------------------------------------------------

NEW_CHARACTERS = [
    # --- Bootstrap: known characters referenced in chapter 1.01 ---
    {
        "id": "juan_ii",
        "name": "King Juan II of Castile",
        "aliases": ["juan_ii"],
        "title": "King of Castile and León",
        "born": "1405-03-06",
        "status": ["active"],
        "category": ["royal_family"],
        "location": "Valladolid",
        "current_task": "Beginning personal rule; planning pilgrimage to Rome",
        "personality": ["strategic", "pious", "ambitious", "inexperienced"],
        "interests": ["poetry", "governance", "religion"],
        "speech_style": "Earnest and direct when speaking privately; can adopt a naive persona strategically",
        "core_characteristics": "Young king of Castile, age 25 in 1430. Has ruled nominally since infancy but only recently begun personal rule. Surprisingly strategic for his youth. Relies heavily on Álvaro de Luna but desires true independence.",
        "faction_ids": ["royal_court"],
        "appearance": {
            "age_appearance": "mid-20s",
            "build": "average",
            "hair": "dark",
        },
    },
    {
        "id": "alvaro_de_luna",
        "name": "Álvaro de Luna",
        "aliases": ["alvaro_de_luna"],
        "title": "Constable of Castile",
        "born": "1390-00-00",
        "status": ["active"],
        "category": ["court_advisor"],
        "location": "Valladolid",
        "current_task": "Preparing the kingdom for Juan's departure; constrained by regency council agreement",
        "personality": ["calculating", "loyal_to_king", "intense", "politically_astute"],
        "interests": ["governance", "maintaining royal authority", "strategy"],
        "speech_style": "Carefully controlled intensity. Dark watchful eyes. Shifts between calculated calm and passionate urgency.",
        "core_characteristics": "Juan II's closest confidant and de facto ruler of Castile. Of minor nobility, resented by great nobles as a 'low-born upstart.' Extraordinarily capable administrator and politician. Genuinely loyal to the king but wields enormous power.",
        "faction_ids": ["royal_court"],
        "appearance": {
            "age_appearance": "early 40s",
            "build": "lean",
            "hair": "dark",
            "distinguishing_features": "dark, watchful eyes"
        },
    },
    {
        "id": "fernan_alonso_de_robles",
        "name": "Fernán Alonso de Robles",
        "aliases": ["fernan_alonso_de_robles", "captain_fernan"],
        "title": "Captain of the Royal Guard",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["court_advisor", "military"],
        "location": "Valladolid",
        "current_task": "Training the king in combat; equipping the royal guard",
        "personality": ["practical", "frank", "professional", "loyal"],
        "interests": ["military training", "guard equipment", "royal security"],
        "speech_style": "Direct and soldierly. Assesses situations frankly. Professional but warm.",
        "core_characteristics": "Captain of the royal guard of ~30 men. Practical soldier who assesses the king honestly. Trains Juan II in combat. Given 150,000 maravedís to equip the guard.",
        "faction_ids": ["royal_court"],
        "appearance": {},
    },
    {
        "id": "fray_hernando",
        "name": "Fray Hernando de Talavera",
        "aliases": ["fray_hernando", "fray_hernando_de_talavera"],
        "title": "Royal Confessor",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["court_advisor", "religious"],
        "location": "Valladolid",
        "current_task": "Appointed as Juan II's new confessor; preparing for the pilgrimage",
        "personality": ["humble", "pious", "young", "energetic"],
        "interests": ["faith", "spiritual guidance"],
        "speech_style": "Humble and sincere",
        "core_characteristics": "Young Franciscan monk chosen by Juan II as his confessor. Selected for his youth (can keep up on travels), humility, and pure Christian faith.",
        "faction_ids": ["royal_court"],
        "appearance": {},
    },
    {
        "id": "pedro_fernandez_de_velasco",
        "name": "Pedro Fernández de Velasco",
        "aliases": ["pedro_fernandez_de_velasco"],
        "title": "Corregidor of Seville",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["nobility"],
        "location": "Seville",
        "current_task": "Serving as corregidor in Seville; reporting on noble feuds and Aragonese infiltration",
        "personality": ["dutiful", "concerned", "loyal"],
        "interests": ["governance", "urban administration"],
        "speech_style": "Respectful and formal in correspondence, with undertones of concern",
        "core_characteristics": "Royal magistrate (corregidor) in Seville. Reports on Guzmán-Ponce de León feuds and suspicious Aragonese gold flowing to local nobles.",
        "faction_ids": [],
        "appearance": {},
    },
    {
        "id": "inigo_lopez_de_mendoza",
        "name": "Íñigo López de Mendoza",
        "aliases": ["inigo_lopez_de_mendoza", "don_inigo"],
        "title": "Adelantado of the Frontier",
        "born": "1398-08-19",
        "status": ["active"],
        "category": ["military", "nobility"],
        "location": "Granada frontier",
        "current_task": "Serving as Adelantado of the frontier; reporting on Moorish raids near Alcalá la Real",
        "personality": ["military-minded", "direct", "pragmatic", "literary"],
        "interests": ["frontier defense", "poetry", "military strategy"],
        "speech_style": "Brief and direct, a soldier's report style",
        "core_characteristics": "Military governor of the Granada frontier. Reports on raids and assesses offensive capability. Future Marquis of Santillana and renowned poet. Considered a potential royal supporter.",
        "faction_ids": [],
        "appearance": {},
    },
    {
        "id": "lope_de_barrientos",
        "name": "Lope de Barrientos",
        "aliases": ["lope_de_barrientos"],
        "title": "Bishop",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["religious"],
        "location": "Salamanca",
        "current_task": "Summoned to join Juan II's advisory cabinet",
        "personality": ["learned", "politically savvy"],
        "interests": ["theology", "education", "governance"],
        "speech_style": "",
        "core_characteristics": "Bishop and scholar at Salamanca University. Summoned to join Juan II's advisory cabinet. Trusted as a potential loyalist.",
        "faction_ids": ["royal_court"],
        "appearance": {},
    },
    {
        "id": "pedro_manrique",
        "name": "Pedro Manrique",
        "aliases": ["pedro_manrique"],
        "title": "",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["nobility"],
        "location": "",
        "current_task": "Summoned to join Juan II's advisory cabinet",
        "personality": [],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "Noble mentioned as a potential member of Juan II's advisory cabinet. From the Manrique family.",
        "faction_ids": [],
        "appearance": {},
    },
    {
        "id": "archbishop_cerezuela",
        "name": "Archbishop Cerezuela of Toledo",
        "aliases": ["archbishop_cerezuela", "juan_de_cerezuela"],
        "title": "Archbishop of Toledo",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["religious"],
        "location": "Toledo",
        "current_task": "Mentioned as potential council member",
        "personality": [],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "Archbishop of Toledo. Mentioned as a suitable member for the planned noble council.",
        "faction_ids": [],
        "appearance": {},
    },
    # --- New characters not in known_aliases.json ---
    {
        "id": "infante_juan_de_aragon",
        "name": "Infante Juan de Aragón, King of Navarra",
        "aliases": [
            "infante_juan_de_aragon", "infante_juan",
            "juan_of_aragon", "king_of_navarra"
        ],
        "title": "Infante of Aragón, King of Navarra",
        "born": "1398-06-29",
        "status": ["active"],
        "category": ["iberian_royalty", "nobility"],
        "location": "Medina del Campo",
        "current_task": "Seeking to control Castilian governance through a noble council",
        "personality": ["ambitious", "calculating", "charming", "diplomatic"],
        "interests": ["power", "governance", "Castilian politics"],
        "speech_style": "Honeyed and diplomatic, wraps demands in fraternal concern, careful word choice",
        "core_characteristics": "Elder of the Infantes de Aragón. Politically astute, uses charm and family ties to disguise his ambition. Holds vast estates in Castile. Cousin of Juan II.",
        "faction_ids": ["aragonese_faction"],
        "appearance": {
            "age_appearance": "early 30s",
            "build": "lean",
            "hair": "dark",
            "distinguishing_features": "narrow, watchful eyes; practiced smile"
        },
    },
    {
        "id": "infante_enrique_de_aragon",
        "name": "Infante Enrique de Aragón",
        "aliases": [
            "infante_enrique_de_aragon", "infante_enrique",
            "enrique_de_aragon"
        ],
        "title": "Infante of Aragón, Master of Santiago",
        "born": "1400-00-00",
        "status": ["active"],
        "category": ["iberian_royalty", "military", "nobility"],
        "location": "Medina del Campo",
        "current_task": "Supporting his brother's bid to control Castilian governance",
        "personality": ["bold", "impulsive", "less subtle than his brother", "military-minded"],
        "interests": ["military affairs", "power", "Santiago Order"],
        "speech_style": "More direct and blunt than his brother Juan, less diplomatic, speaks with an edge",
        "core_characteristics": "Younger Infante de Aragón. More impulsive and militaristic than his brother. Previously controlled Juan II's household during the regency. Master of the Order of Santiago.",
        "faction_ids": ["aragonese_faction"],
        "appearance": {
            "age_appearance": "late 20s",
            "build": "broad-shouldered",
            "hair": "dark",
            "distinguishing_features": "military bearing; broad grin"
        },
    },
    {
        "id": "archbishop_contreras",
        "name": "Archbishop Juan Martínez de Contreras",
        "aliases": [
            "archbishop_contreras", "juan_martinez_de_contreras",
            "archbishop_of_toledo_1430"
        ],
        "title": "Archbishop of Toledo",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["religious"],
        "location": "Toledo",
        "current_task": "Advocating for a crusade against Granada and proper Church tithes",
        "personality": ["pious", "politically aware", "ambitious for the Church"],
        "interests": ["Reconquista", "Church authority", "converso oversight"],
        "speech_style": "Elegant clerical register with Latin phrases, combines spiritual authority with political messaging",
        "core_characteristics": "Archbishop of Toledo (1423-1434). Advocates for crusade against Granada and increased Church authority. Concerned about converso prominence in Toledo.",
        "faction_ids": [],
        "appearance": {},
    },
    {
        "id": "muhammad_ix",
        "name": "Sultan Muhammad IX of Granada",
        "aliases": ["muhammad_ix", "sultan_muhammad", "muhammad_of_granada"],
        "title": "Sultan of the Nasrid Kingdom of Granada",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["foreign_ruler"],
        "location": "Granada",
        "personality": [],
        "speech_style": "",
        "core_characteristics": "Sultan of the Nasrid Kingdom. Pays tribute (parias) to Castile for peace. Mentioned in reports but does not appear directly.",
        "faction_ids": [],
        "appearance": {},
    },
]

# -----------------------------------------------------------------------
# Character updates
# -----------------------------------------------------------------------

# Since all referenced characters are being created in new_characters above
# (this is the first chapter), no updates are needed.
CHARACTER_UPDATES = []

# -----------------------------------------------------------------------
# New locations
# -----------------------------------------------------------------------

NEW_LOCATIONS = [
    {
        "location_id": "valladolid",
        "name": "Valladolid",
        "region": "Castile",
        "description": "Royal capital of Castile. Seat of the royal court and Juan II's primary residence.",
        "sub_locations": ["Royal Palace", "Palace Courtyard", "Council Chamber"],
    },
    {
        "location_id": "medina_del_campo",
        "name": "Medina del Campo",
        "region": "Castile",
        "description": "Important Castilian town near Valladolid. Site of the crucial negotiation between Juan II and the Infantes de Aragón.",
        "sub_locations": [],
    },
    {
        "location_id": "seville",
        "name": "Seville",
        "region": "Castile",
        "description": "Major Castilian trade city on the Guadalquivir. Produces ~420,000 maravedís in quarterly customs revenues. Noble feuds between Guzmán and Ponce de León families.",
        "sub_locations": ["Alcázar District", "Cathedral"],
    },
    {
        "location_id": "toledo",
        "name": "Toledo",
        "region": "Castile",
        "description": "Religious center of Castile and seat of the Archbishop. Strategic importance for controlling central Castile.",
        "sub_locations": [],
    },
    {
        "location_id": "granada",
        "name": "Granada",
        "region": "Al-Andalus",
        "description": "Capital of the Nasrid Kingdom. Last Moorish stronghold in Iberia. Pays tribute to Castile but raids continue on the frontier.",
        "sub_locations": [],
    },
]

# -----------------------------------------------------------------------
# New factions
# -----------------------------------------------------------------------

NEW_FACTIONS = [
    {
        "faction_id": "royal_court",
        "name": "Royal Court of Castile",
        "type": "political",
        "region": "Castile",
        "description": "The inner circle loyal to Juan II. Centered around Álvaro de Luna and the king's personal appointees. Includes the royal guard, key officials, and the newly formed advisory cabinet.",
        "leader_id": "juan_ii",
        "member_ids": [
            "juan_ii", "alvaro_de_luna", "fernan_alonso_de_robles",
            "fray_hernando", "lope_de_barrientos"
        ],
    },
    {
        "faction_id": "aragonese_faction",
        "name": "Faction of the Infantes de Aragón",
        "type": "political",
        "region": "Castile",
        "description": "Coalition of nobles allied with the Infantes Juan and Enrique de Aragón. They seek to control Castilian governance through a noble council, limiting royal authority and Álvaro de Luna's influence. Commands ~25% of Castile's military power through 8-10 major noble houses.",
        "leader_id": "infante_juan_de_aragon",
        "member_ids": [
            "infante_juan_de_aragon", "infante_enrique_de_aragon"
        ],
    },
]

# -----------------------------------------------------------------------
# Rolls
# -----------------------------------------------------------------------

ROLLS = [
    {
        "event_index": 2,   # The Guard Speech event (0-indexed)
        "title": "Royal Guard Morale Speech",
        "context": "Juan II addresses the royal guard to inspire personal loyalty. He gives a speech invoking religious duty and promising better equipment.",
        "roll_type": "persuasion",
        "date": "1430-05-02",
        "rolled": None,  # Exact number not recorded, but "rolled low"
        "outcome_range": "status_quo",
        "outcome_label": "Status Quo",
        "outcome_detail": "The speech neither inspires special loyalty nor alienates the guards. They remain professional but not personally devoted. The king is reminded he has much to learn about leadership.",
        "evaluation": "Despite favorable conditions (royal authority, new equipment promised, religious framing), the delivery fell flat. The guards remain dutiful but uninspired.",
        "success_factors": ["Royal authority", "Equipment promise", "Religious framing", "Captain's support"],
        "failure_factors": ["King's youth and inexperience", "Overly formal delivery"],
    },
    {
        "event_index": 9,   # The revolt roll (0-indexed)
        "title": "Infantes Revolt During Pilgrimage",
        "context": "After successfully negotiating with the Infantes and establishing a regency council, Juan II rolls to see if the Infantes revolt during his absence on pilgrimage.",
        "roll_type": "chaos",
        "date": "1430-05-20",
        "rolled": None,  # "rolled very low" — bad luck
        "outcome_range": "revolt",
        "outcome_label": "Critical Failure",
        "outcome_detail": "Despite careful planning and giving the Infantes real power through a regency council, the dice decree that a revolt WILL take place during Juan's pilgrimage. The how and why will be determined later.",
        "evaluation": "The GM assessed 70-75% probability of no revolt. The dice overruled the careful diplomacy. This sets up the central crisis of the early game.",
        "success_factors": [
            "Infantes have a bloodless path to power through the council",
            "They believe they're controlling governance",
            "No immediate reason to rebel — they got what they wanted"
        ],
        "failure_factors": [
            "King's extended absence creates opportunity",
            "Noble ambitions may exceed council powers",
            "Aragonese interference possible"
        ],
    },
]

# -----------------------------------------------------------------------
# Main extraction logic
# -----------------------------------------------------------------------

def main():
    with open(PREPROCESSED, "r", encoding="utf-8") as f:
        preprocessed = json.load(f)

    messages = preprocessed["messages"]
    msg_by_index = {m["index"]: m for m in messages}

    # Build events
    events = []
    for edef in EVENT_DEFS:
        start, end = edef["msgs"]
        exchanges = []
        for idx in range(start, end + 1):
            if idx in msg_by_index:
                m = msg_by_index[idx]
                exchanges.append({
                    "role": m["role"],
                    "text": m["text"],
                })

        event = {
            "date": edef["date"],
            "type": edef["type"],
            "summary": edef["summary"],
            "characters": edef["characters"],
            "factions_affected": edef["factions_affected"],
            "location": edef["location"],
            "tags": edef["tags"],
            "status": "resolved",
            "exchanges": exchanges,
        }
        if "end_date" in edef:
            event["end_date"] = edef["end_date"]
        events.append(event)

    extraction = {
        "chapter": "1.01",
        "book": 1,
        "events": events,
        "new_characters": NEW_CHARACTERS,
        "character_updates": CHARACTER_UPDATES,
        "new_locations": NEW_LOCATIONS,
        "new_factions": NEW_FACTIONS,
        "faction_updates": [],
        "rolls": ROLLS,
        "law_references": [],
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(extraction, f, indent=2, ensure_ascii=False)

    # Print stats
    total_exchanges = sum(len(e["exchanges"]) for e in events)
    print(f"Chapter 1.01 extraction complete:")
    print(f"  Events:          {len(events)}")
    print(f"  Total exchanges: {total_exchanges}")
    print(f"  New characters:  {len(NEW_CHARACTERS)}")
    print(f"  Char updates:    {len(CHARACTER_UPDATES)}")
    print(f"  New locations:   {len(NEW_LOCATIONS)}")
    print(f"  New factions:    {len(NEW_FACTIONS)}")
    print(f"  Rolls:           {len(ROLLS)}")
    print(f"  Written to:      {OUTPUT}")


if __name__ == "__main__":
    main()
