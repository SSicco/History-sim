#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.15.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.15_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.15_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 8),
        "date": "1431-03-25",
        "type": "military",
        "summary": "Intelligence rolls for what Sultan Muhammad IX knows and his strategic response. Roll 41: Partial Intelligence — Sultan knows major crusade launching early April, large eastern army (~20,000) at Jaen, smaller western force at Seville. Does NOT know true western force size, naval component, two-army coordination, or specific targets. Roll 44: Mobile Defense with Raiding — main army (18,000) positioned centrally to respond rapidly, 2,500-3,000 light cavalry for constant raiding, avoids pitched battles, targets supply lines. Full army assembly at Jaen: 23,147 troops mustered. Six cavalry screening columns of 500 each deployed into the frontier. Juan appears in full white armor. Army waits for scout reports.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "garcia_fernandez_de_baeza",
            "rodrigo_de_narvaez", "pedro_manrique_de_lara", "alvar_perez_de_guzman",
            "juan_de_luna", "sancho_de_rojas"
        ],
        "factions_affected": [],
        "location": "Jaen",
        "tags": ["military", "intelligence", "roll", "assembly", "cavalry"],
    },
    {
        "msgs": (9, 14),
        "date": "1431-03-29",
        "type": "military",
        "summary": "Cavalry scouts return over several days (March 25-29) with intelligence on Granadan frontier fortresses: Alcala la Real (800-1,000 garrison), Moclin (700-800), Illora (1,000), Cambil (500-600), Guadix (600), various smaller forts (100-300 each). Sultan's main army (~17,000-18,000) positioned centrally between Loja and Granada. War council debates central approach (direct toward Granada, forces early confrontation) vs eastern approach (less defended but slower, through mountains). Central approach chosen — better terrain for heavy army, forces Sultan to react, exploits siege artillery advantage.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "garcia_fernandez_de_baeza",
            "rodrigo_de_narvaez", "alvar_perez_de_guzman"
        ],
        "factions_affected": [],
        "location": "Jaen",
        "tags": ["military", "intelligence", "war_council", "strategy"],
    },
    {
        "msgs": (15, 24),
        "date": "1431-03-29",
        "type": "military",
        "summary": "Juan proposes concentrated bombardment without full encirclement, keeping the main army concentrated and mobile. Inspired by Caesar (Alesia/Gergovia), proposes Roman-style fieldworks to protect bombardment position. Council discusses hiring carpenters and woodcutters, bringing timber, constructing proper defenses. Juan decides target: Alcala la Real. Orders: hire civilian workers, army marches at dawn March 30, message to Rodrigo Manrique — western army waits until Sultan commits. Queen Isabel remains in Jaen. Cavalry reorganized: 2,000 recalled for close screening, 1,000 given operational freedom. Relics stay at Jaen; the white banner marches with the army.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "pietro_calabrese",
            "isabel_of_portugal", "rodrigo_manrique"
        ],
        "factions_affected": [],
        "location": "Jaen",
        "tags": ["military", "strategy", "artillery", "fieldworks", "logistics"],
    },
    {
        "msgs": (25, 32),
        "date": "1431-03-30",
        "end_date": "1431-03-31",
        "type": "military",
        "summary": "Three intelligence rolls. Roll 49: Sultan detects army within 24 hours, gets complete composition including bombards and civilian workers. Roll 44: Sultan's response — rapid relief forced march with 16,000 troops (strips western defense to 2,000), covers 40 miles in 2 days. Roll 51: Castilian cavalry detection — good warning, 48-60 hours notice, accurate count. Army departs Jaen dawn March 30, arrives Alcala la Real after 1.5 days. Camp 3 miles north of fortress. Late March 31: scout Miguel de Baeza reports Sultan's entire field army (16,000-17,000) on forced march, arriving in ~48 hours.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "juan_de_luna",
            "garcia_fernandez_de_baeza"
        ],
        "factions_affected": [],
        "location": "Alcala la Real",
        "tags": ["military", "intelligence", "march", "roll", "scouts"],
    },
    {
        "msgs": (33, 66),
        "date": "1431-03-31",
        "type": "military",
        "summary": "Emergency war council at Alcala la Real. Sultan arriving in 48 hours. Key decisions: (1) Deception — one bombard visible as bait, four hidden. (2) Command structure — Enrique commands siege works (5,000) as anvil; Garcia Fernandez First Battle (5,000); Padilla Second Battle (5,000, overall infantry); Narvaez Third Battle (5,000); Juan commands heavy cavalry (4,000) as hammer. (3) Insight: destroying Sultan's ~10,000 infantry renders his cavalry mere raiders — campaign-decisive. (4) Discipline: no individual charges, cavalry pursues only broken infantry. Plans for Sultan attacking (Enrique holds, Juan hammers) and Sultan refusing (advance to cut supply lines).",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "infante_enrique_de_aragon",
            "garcia_fernandez_de_baeza", "rodrigo_de_narvaez", "pietro_calabrese",
            "fernan_alonso_de_robles"
        ],
        "factions_affected": [],
        "location": "Alcala la Real",
        "tags": ["military", "war_council", "battle_planning", "command", "strategy"],
    },
    {
        "msgs": (67, 72),
        "date": "1431-03-31",
        "type": "narrative",
        "summary": "Courier sent to Seville: 'Sultan's field army engaged at Alcala la Real. Launch western operations immediately.' Sultan stripped western defenses to 2,000, creating the exact vulnerability the two-army strategy targeted. Evening: Juan rides through camp in white armor (no helmet), stops to address troops. Effect is electric — 'DIOS Y CASTILLA!' sweeps through 23,000 men. Juan prays with weapons at hand. Eve of battle.",
        "characters": [
            "juan_ii", "fray_hernando", "fernan_alonso_de_robles"
        ],
        "factions_affected": [],
        "location": "Alcala la Real",
        "tags": ["narrative", "morale", "signal", "prayer", "eve_of_battle"],
    },
]

NEW_CHARACTERS = [
    {
        "id": "garcia_fernandez_de_baeza",
        "name": "Don García Fernández de Baeza",
        "aliases": ["garcia_fernandez_de_baeza", "don_garcia"],
        "title": "Cavalry Commander / Commander of the First Battle",
        "born": "1393-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Alcala la Real",
        "current_task": "Commanding the First Battle (Vanguard, 5,000 troops); veteran of 20 frontier campaigns; preparing for battle against Sultan's relief force",
        "personality": ["aggressive", "experienced", "bold", "decisive"],
        "interests": ["frontier warfare", "cavalry tactics", "combat"],
        "speech_style": "Direct, aggressive, speaks from two decades of frontier experience. Cuts to tactical reality quickly.",
        "core_characteristics": "Age 38. Veteran of 20 frontier campaigns. Lean build, scarred face. Named commander of the First Battle (Vanguard, 5,000 troops). Aggressive tactician who favors bold action.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "late 30s",
            "build": "lean",
            "hair": "dark",
            "distinguishing_features": "scarred face from decades of frontier fighting",
        },
    },
    {
        "id": "rodrigo_de_narvaez",
        "name": "Don Rodrigo de Narváez",
        "aliases": ["rodrigo_de_narvaez", "narvaez"],
        "title": "Cavalry Commander / Commander of the Third Battle",
        "born": "1389-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Alcala la Real",
        "current_task": "Commanding the Third Battle (Rear Guard, 5,000 troops); preparing for battle against Sultan's relief force",
        "personality": ["cautious", "methodical", "experienced", "steady"],
        "interests": ["frontier defense", "military discipline", "reconnaissance"],
        "speech_style": "Measured, careful, methodical. Considers before speaking.",
        "core_characteristics": "Age 42. Minor nobility of the Antequera frontier. Cautious and methodical — steady counterpart to Garcia Fernandez's aggression. Commander of the Third Battle (Rear Guard, 5,000 troops).",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "early 40s",
            "build": "solid",
            "distinguishing_features": "weathered frontier veteran's bearing",
        },
    },
    {
        "id": "pedro_manrique_de_lara",
        "name": "Don Pedro Manrique de Lara",
        "aliases": ["pedro_manrique_de_lara"],
        "title": "Cavalry Column Commander",
        "born": "1402-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Alcala la Real",
        "current_task": "Commanding one of six cavalry screening columns; younger cousin of Rodrigo Manrique",
        "personality": ["eager", "ambitious", "energetic", "loyal"],
        "interests": ["cavalry warfare", "proving himself", "family honor"],
        "speech_style": "Energetic, sometimes overeager. Respectful of seniors but wants to distinguish himself.",
        "core_characteristics": "Age 29. Younger cousin of Rodrigo Manrique (western army commander). Eager to prove himself worthy of the Manrique name.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "late 20s",
            "build": "athletic",
            "distinguishing_features": "bears family resemblance to Rodrigo Manrique",
        },
    },
    {
        "id": "alvar_perez_de_guzman",
        "name": "Don Álvar Pérez de Guzmán",
        "aliases": ["alvar_perez_de_guzman", "alvar_perez"],
        "title": "Cavalry Column Commander",
        "born": "1396-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Alcala la Real",
        "current_task": "Commanding cavalry screening column; providing intelligence analysis with Arabic language skills and deep understanding of Moorish tactics",
        "personality": ["intelligent", "analytical", "culturally_aware", "pragmatic"],
        "interests": ["Arabic culture", "Moorish military tactics", "frontier diplomacy"],
        "speech_style": "Thoughtful and analytical. Peppers conversation with Arabic terms. Nuanced understanding of the enemy.",
        "core_characteristics": "Age 35. Seville frontier nobility. Speaks Arabic fluently, understands Moorish tactics and culture. Invaluable intelligence asset.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "mid 30s",
            "build": "average",
            "distinguishing_features": "dark complexion from years on the southern frontier",
        },
    },
    {
        "id": "juan_de_luna",
        "name": "Don Juan de Luna",
        "aliases": ["juan_de_luna"],
        "title": "Cavalry Column Commander / Deep Reconnaissance Specialist",
        "born": "1398-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Alcala la Real",
        "current_task": "Commanding deep reconnaissance cavalry column; his scouts detected Sultan's forced march, providing critical 48-hour warning; no relation to Álvaro de Luna",
        "personality": ["quiet", "observant", "resourceful", "independent"],
        "interests": ["deep reconnaissance", "scouting", "frontier survival"],
        "speech_style": "Quiet, precise, economical with words. Reports facts without embellishment.",
        "core_characteristics": "Age 33. Murcia frontier specialist. Deep reconnaissance expert — his scouts provided the critical warning about the Sultan's forced march. No relation to Álvaro de Luna.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "early 30s",
            "build": "wiry",
            "distinguishing_features": "quiet bearing of a man accustomed to operating behind enemy lines",
        },
    },
    {
        "id": "sancho_de_rojas",
        "name": "Don Sancho de Rojas",
        "aliases": ["sancho_de_rojas"],
        "title": "Cavalry Column Commander / Reserve",
        "born": "1391-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Alcala la Real",
        "current_task": "Commanding reserve cavalry column; Calatrava Order veteran",
        "personality": ["disciplined", "reliable", "devout", "steady"],
        "interests": ["Calatrava Order traditions", "military discipline", "faith"],
        "speech_style": "Formal, military, disciplined. Structured cadence of a Military Order veteran.",
        "core_characteristics": "Age 40. Calatrava Order veteran. Commands reserve cavalry column. Disciplined and reliable.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "about 40",
            "build": "solid",
            "distinguishing_features": "bears the red cross of Calatrava",
        },
    },
]

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "Personally commanding 4,000 heavy cavalry as hammer at Alcala la Real; Sultan's 16,000 relief army arriving in 48 hours; battle plan set; rode through camp in white armor inspiring troops; praying on eve of battle",
        "location": "Alcala la Real",
    },
    {
        "id": "pedro_gonzalez_de_padilla",
        "current_task": "Commands Second Battle (5,000) and overall infantry coordination at Alcala la Real; preparing for decisive battle against Sultan's relief force",
        "location": "Alcala la Real",
    },
    {
        "id": "infante_enrique_de_aragon",
        "current_task": "Commands siege works (5,000 — crusaders, Military Orders, professionals) as defensive anvil; most demanding independent command; significant redemption — entrusted with where battle will be won or lost",
        "location": "Alcala la Real",
    },
    {
        "id": "pietro_calabrese",
        "current_task": "Commands 5 bombards at Alcala la Real; deception plan: 1 visible as bait, 4 hidden; preparing for Sultan's arrival",
        "location": "Alcala la Real",
    },
    {
        "id": "fernan_alonso_de_robles",
        "current_task": "Commands crusaders/Guardian Company within Enrique's siege works (5,000 troops); preparing to hold the anvil",
        "location": "Alcala la Real",
    },
    {
        "id": "isabel_of_portugal",
        "current_task": "Remaining at Jaen fortress; unusually fatigued (early pregnancy, unaware); Catarina attending her",
        "location": "Jaen",
    },
]

NEW_LOCATIONS = [
    {
        "location_id": "alcala_la_real",
        "name": "Alcala la Real",
        "region": "Granada frontier",
        "description": "Major Granadan frontier fortress on the road south from Jaen toward Granada. First target of the eastern crusade army. Garrison 800-1,000. Site of imminent decisive battle.",
        "sub_locations": [
            "Fortress of Alcala la Real",
            "Castilian Camp (3 miles north)",
            "Siege Works / Bombardment Position"
        ],
    },
]

NEW_FACTIONS = []
FACTION_UPDATES = [
    {
        "faction_id": "royal_court",
        "description": "Campaign active. Eastern army (23,147) at Alcala la Real. Sultan's relief force (16,000) arriving in 48 hours. Signal sent to western army — Sultan stripped western defenses to 2,000. Both jaws of the two-army trap closing simultaneously.",
    },
]

ROLLS = [
    {
        "event_index": 0,
        "title": "Sultan's Intelligence on the Crusade",
        "context": "What does Sultan Muhammad IX know about the coming crusade?",
        "roll_type": "intelligence",
        "date": "1431-03-25",
        "rolled": 41,
        "outcome_range": "26-50",
        "outcome_label": "Partial Intelligence",
        "outcome_detail": "Sultan knows: major crusade launching early April, large eastern army (~20,000) at Jaen, smaller western force at Seville. Does NOT know: true western force size, naval component, two-army coordination, or specific targets.",
        "evaluation": "Middle-range result. Enough to prepare defensively but not to anticipate the full two-army threat.",
        "success_factors": ["Public papal bull", "Active frontier informants"],
        "failure_factors": ["Two-army coordination secret", "Naval preparations disguised"],
    },
    {
        "event_index": 0,
        "title": "Sultan's Strategic Response",
        "context": "Given partial intelligence, how does the Sultan position his ~18,000 field troops?",
        "roll_type": "military",
        "date": "1431-03-25",
        "rolled": 44,
        "outcome_range": "36-50",
        "outcome_label": "Mobile Defense with Raiding",
        "outcome_detail": "Main army positioned centrally between Loja and Granada. 2,500-3,000 light cavalry for raiding. Avoid pitched battles, fight from prepared positions. Western defense: 6,000-8,000 troops.",
        "evaluation": "Competent defense playing to Moorish strengths, but central positioning means Sultan must commit when attack comes.",
        "success_factors": ["Sound doctrine", "Terrain advantage", "Cavalry superiority"],
        "failure_factors": ["Cannot defend both fronts", "Underestimates western threat"],
    },
    {
        "event_index": 3,
        "title": "Sultan's Detection of Army Movement",
        "context": "23,147 troops depart Jaen March 30. How quickly does Sultan learn?",
        "roll_type": "intelligence",
        "date": "1431-03-30",
        "rolled": 49,
        "outcome_range": "46-65",
        "outcome_label": "Rapid and Detailed",
        "outcome_detail": "Sultan learns within 24 hours. Gets complete composition, bombard confirmation, civilian workers (implying fieldworks), estimated arrival time.",
        "evaluation": "Good for Sultan but triggers reactive commitment east — plays into two-army trap.",
        "success_factors": ["Excellent spy network", "Army of 23,000 impossible to hide"],
        "failure_factors": ["Speed forces reactive posture"],
    },
    {
        "event_index": 3,
        "title": "Sultan's Military Response",
        "context": "Sultan knows Juan marches on Alcala la Real with 23,000+ and bombards. What does he do?",
        "roll_type": "military",
        "date": "1431-03-30",
        "rolled": 44,
        "outcome_range": "39-58",
        "outcome_label": "Rapid Relief — Catch Them Building",
        "outcome_detail": "Mobilizes within 24 hours. Forced march with 16,000 (strips western defense to 2,000). 40 miles in 2 days. Arrive Day 3-4 to catch fieldworks incomplete.",
        "evaluation": "Aggressive but plays directly into two-army trap. Strips western defenses critically.",
        "success_factors": ["Aggressive action to prevent siege"],
        "failure_factors": ["Strips western defenses", "Exhausts troops", "Plays into trap"],
    },
    {
        "event_index": 3,
        "title": "Castilian Cavalry Detection",
        "context": "1,000 cavalry with operational freedom (Juan de Luna's specialty). How well do they detect Sultan's march?",
        "roll_type": "military",
        "date": "1431-03-30",
        "rolled": 51,
        "outcome_range": "51-70",
        "outcome_label": "Good Warning",
        "outcome_detail": "Scouts report within 12 hours. Accurate count (~17,000), forced march pace, composition, route. 48-60 hours warning for Juan.",
        "evaluation": "Solid result giving adequate preparation time for battle plan.",
        "success_factors": ["Dedicated recon column", "Juan de Luna's expertise"],
        "failure_factors": ["12-hour delay reduces prep time slightly"],
    },
]

LAW_REFERENCES = []

def main():
    with open(PREPROCESSED, "r", encoding="utf-8") as f:
        preprocessed = json.load(f)

    messages = preprocessed["messages"]
    msg_by_index = {m["index"]: m for m in messages}

    events = []
    for edef in EVENT_DEFS:
        start, end = edef["msgs"]
        exchanges = []
        for idx in range(start, end + 1):
            if idx in msg_by_index:
                m = msg_by_index[idx]
                exchanges.append({"role": m["role"], "text": m["text"]})
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
        "chapter": "1.15",
        "book": 1,
        "events": events,
        "new_characters": NEW_CHARACTERS,
        "character_updates": CHARACTER_UPDATES,
        "new_locations": NEW_LOCATIONS,
        "new_factions": NEW_FACTIONS,
        "faction_updates": FACTION_UPDATES,
        "rolls": ROLLS,
        "law_references": LAW_REFERENCES,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(extraction, f, indent=2, ensure_ascii=False)

    total_exchanges = sum(len(e["exchanges"]) for e in events)
    print(f"Chapter 1.15 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  New locations:     {len(NEW_LOCATIONS)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Written to:        {OUTPUT}")

if __name__ == "__main__":
    main()
