#!/usr/bin/env python3
"""One-shot extraction script for Chapter 1.21."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.21_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.21_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 20),
        "date": "1431-07-09",
        "type": "military",
        "summary": "Assault and Fall of Malaga. After ~3 weeks of bombardment, two major breaches opened (40ft and 30ft). Dawn assault July 9: Primary breach — 50 defenders overwhelmed, 8 Castilian dead. Secondary breach — 20 defenders flee, 2 Castilian dead. Both breaches taken in 10 minutes. Crusader force drives for the Alcazaba. White flags appear on Alcazaba battlements at 6:27 AM. Qaid Ibrahim al-Najjar emerges unarmed with 20 officers and 600 garrison troops. Surrenders formally, acknowledging Juan's mercy. Juan grants safe conduct — lives preserved but possessions forfeit (city refused surrender before assault). City gates opened, 8,000-10,000 civilians flee. Message sent to Gibralfaro fortress: surrender now or surrender later as prisoners.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "fadrique_enriquez",
            "infante_enrique_de_aragon", "pietro_calabrese", "fernan_alonso_de_robles",
            "qaid_ibrahim_al_najjar"
        ],
        "factions_affected": ["royal_court"],
        "location": "Malaga",
        "tags": ["military", "assault", "siege", "surrender", "city"],
    },
    {
        "msgs": (21, 40),
        "date": "1431-07-09",
        "type": "diplomacy",
        "summary": "Gibralfaro fortress response. Roll 97: Surrender with Offer of Service — historic result. Captain Yusuf ibn Hassan not only surrenders 298 men but offers 50-80 professional soldiers willing to serve as garrison troops for Castile. Juan's commanders debate: Alvaro sees opportunity, Master of Calatrava skeptical, Admiral notes Mediterranean precedent. Juan accepts, spreading Moorish soldiers across garrisons with Castilian majority oversight. ~50 integrated. Unprecedented: enemy professionals volunteering for service. By 11 AM, Gibralfaro surrendered. Malaga falls in a stunningly swift assault — only 15 Castilian casualties in the actual breach assault.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "fadrique_enriquez",
            "alvaro_de_estuniga", "yusuf_ibn_hassan"
        ],
        "factions_affected": [],
        "location": "Malaga",
        "tags": ["diplomacy", "surrender", "service", "integration", "roll"],
    },
    {
        "msgs": (41, 60),
        "date": "1431-07-09",
        "end_date": "1431-07-10",
        "type": "military",
        "summary": "Strategic planning after Malaga's fall. War council assesses position. Four options: (1) Press toward Granada city, (2) Consolidate coast westward, (3) Clear eastern fortresses, (4) Raid and devastate. Current forces: ~30,000 troops, ~7,000 committed to garrisons, 23,000 mobile. 8-10 weeks of campaign weather remain. Juan chooses Option 2: consolidate the western coast from Malaga toward Gibraltar. Take Marbella, Estepona, and coastal forts. Strategic logic: Granada city isolated, cannot reinforce westward. Garrisons at Loja and Malaga bottle up Granada. Coast secured gives naval dominance.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "alvaro_de_estuniga",
            "fadrique_enriquez", "infante_enrique_de_aragon", "rodrigo_de_perea"
        ],
        "factions_affected": ["royal_court"],
        "location": "Malaga",
        "tags": ["military", "strategy", "war_council", "consolidation"],
    },
]

NEW_CHARACTERS = [
    {
        "id": "qaid_ibrahim_al_najjar",
        "name": "Qaid Ibrahim al-Najjar",
        "aliases": ["qaid_ibrahim_al_najjar", "qaid_ibrahim"],
        "title": "Former Commander of Malaga Alcazaba",
        "born": "1385-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Malaga",
        "current_task": "Surrendered Alcazaba garrison (600 men) after Malaga breached. Acknowledged Juan's mercy. Lives preserved but possessions forfeit per laws of siege.",
        "personality": ["professional", "pragmatic", "honorable"],
        "interests": ["military command", "fortress defense"],
        "speech_style": "Dignified, professional. Accepts defeat with grace.",
        "core_characteristics": "Professional garrison commander of Malaga's Alcazaba. Surrendered within 30 minutes of breaches being stormed, recognizing hopelessness. Cited Juan's honorable treatment of previous garrisons.",
        "faction_ids": [],
        "appearance": {},
    },
    {
        "id": "yusuf_ibn_hassan",
        "name": "Captain Yusuf ibn Hassan",
        "aliases": ["yusuf_ibn_hassan", "captain_yusuf"],
        "title": "Former Commander of Gibralfaro Fortress / Castilian Garrison Soldier",
        "born": "1390-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Malaga",
        "current_task": "Surrendered Gibralfaro garrison (298 men) and offered 50-80 professional soldiers for Castilian service. Speaks Castilian from frontier trading. Soldiers being integrated across garrisons with Castilian majority oversight.",
        "personality": ["pragmatic", "professional", "resourceful", "opportunistic"],
        "interests": ["military service", "survival", "professional soldiering"],
        "speech_style": "Speaks Castilian from frontier trading. Direct, professional. Career soldier looking for the next employer.",
        "core_characteristics": "Age early 40s. Career military man who commands professional soldiers. Surrendered Gibralfaro and made the unprecedented offer of service — his men are professionals who fight for whoever pays well and treats them fairly. Mediterranean tradition of military service transcending religious lines.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "early 40s",
            "build": "military",
            "distinguishing_features": "career soldier's bearing; speaks Castilian",
        },
    },
]

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "Malaga taken July 9 — Granada's second city and vital port. Stunningly swift assault (15 casualties). Gibralfaro surrendered with offer of service (roll 97). Chose western consolidation strategy — take coast toward Gibraltar. ~23,000 mobile troops. Command post at Malaga Alcazaba.",
        "location": "Malaga",
    },
    {
        "id": "fadrique_enriquez",
        "current_task": "Naval blockade secured Malaga harbor. Captured 8 merchant vessels. Supporting coastal operations.",
        "location": "Malaga",
    },
]

NEW_LOCATIONS = []
NEW_FACTIONS = []
FACTION_UPDATES = [
    {
        "faction_id": "royal_court",
        "description": "Malaga falls July 9 — Granada's second city taken in swift assault (15 casualties). Gibralfaro surrenders with unprecedented offer of military service (roll 97). ~50 Moorish soldiers integrated into garrisons. Western consolidation strategy chosen: take coast toward Gibraltar. Castile holds 7 major positions with ~34,000 troops deployed. Granada increasingly isolated.",
    },
]

ROLLS = [
    {
        "event_index": 1,
        "title": "Gibralfaro Garrison Response",
        "context": "Alcazaba already surrendered. City falling. Gibralfaro fortress (298 men) sent message: surrender now or later as prisoners.",
        "roll_type": "diplomacy",
        "date": "1431-07-09",
        "rolled": 97,
        "outcome_range": "95-100",
        "outcome_label": "Surrender with Offer of Service",
        "outcome_detail": "Captain Yusuf ibn Hassan not only surrenders 298 men but offers 50-80 professional soldiers for Castilian garrison service. Unprecedented — enemy professionals volunteering for service. Mediterranean tradition of military service transcending religious lines.",
        "evaluation": "Near-maximum roll. Historic result. Creates precedent for enemy integration and signals Granada's military cohesion is breaking down.",
        "success_factors": ["City already falling", "Hopeless situation", "Professional soldiers seeking employment", "Juan's reputation for mercy"],
        "failure_factors": [],
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
        event = {"date": edef["date"], "type": edef["type"], "summary": edef["summary"],
                 "characters": edef["characters"], "factions_affected": edef["factions_affected"],
                 "location": edef["location"], "tags": edef["tags"], "status": "resolved", "exchanges": exchanges}
        if "end_date" in edef:
            event["end_date"] = edef["end_date"]
        events.append(event)
    extraction = {"chapter": "1.21", "book": 1, "events": events, "new_characters": NEW_CHARACTERS,
                  "character_updates": CHARACTER_UPDATES, "new_locations": NEW_LOCATIONS,
                  "new_factions": NEW_FACTIONS, "faction_updates": FACTION_UPDATES,
                  "rolls": ROLLS, "law_references": LAW_REFERENCES}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(extraction, f, indent=2, ensure_ascii=False)
    total_exchanges = sum(len(e["exchanges"]) for e in events)
    print(f"Chapter 1.21: {len(events)} events, {total_exchanges} exchanges, {len(NEW_CHARACTERS)} new chars, {len(ROLLS)} rolls")

if __name__ == "__main__":
    main()
