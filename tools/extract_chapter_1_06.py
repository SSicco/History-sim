#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.06.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.06_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.06_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 6),
        "date": "1430-09-02",
        "end_date": "1430-09-10",
        "type": "crisis",
        "summary": "Captain Fernán successfully delivers Juan's arrest orders to Álvaro in Valladolid after a 14-day hard ride (success roll). Álvaro publicly summons the Infantes to surrender for trial on September 5, but the arrest attempt FAILS: the Infantes publicly refuse, claiming the orders are forged; they withdraw to separate fortified positions; a three-day standoff at Arévalo ends with Álvaro withdrawing. The Infantes had been intercepting correspondence and were prepared. Alfonso V of Aragon threatens war if his brothers are harmed. The Infantes remain free and defiant but exposed as refusing royal justice, with ~5,000 troops and support from the Master of Santiago.",
        "characters": [
            "fernan_alonso_de_robles", "alvaro_de_luna",
            "infante_juan_de_aragon", "infante_enrique_de_aragon",
            "luis_de_guzman"
        ],
        "factions_affected": ["royal_court", "aragonese_faction"],
        "location": "Castile",
        "tags": ["crisis", "politics", "military", "roll"],
    },
    {
        "msgs": (7, 16),
        "date": "1430-09-12",
        "end_date": "1430-09-17",
        "type": "decision",
        "summary": "In Barcelona, Juan discusses Castilian and Aragonese succession with his companions. He writes a poem expressing spiritual love for Isabel Ruiz, but when María challenges him — pointing out that burdening Isabel with knowledge of impossible love would be selfish — Juan burns the poem. He embraces María and weeps, genuinely letting go of his feelings for the first time. This marks his first real sacrifice of personal desire for another's wellbeing.",
        "characters": [
            "juan_ii", "maria_of_aragon", "isabel_ruiz"
        ],
        "factions_affected": [],
        "location": "Barcelona",
        "tags": ["personal", "romance", "family", "sacrifice"],
    },
    {
        "msgs": (17, 20),
        "date": "1430-09-18",
        "end_date": "1430-09-28",
        "type": "decision",
        "summary": "Juan departs Barcelona with three galleys (Santa Eulalia, Sant Jordi, Mare de Déu) carrying 62 crusaders, relics, banner, and treasury. Success roll — the 10-day voyage includes several tense moments: bluffing past Valencia's inspection with threats of excommunication, a corsair encounter where pirates retreat upon seeing the armed formation, and Moroccan war galleys shadowing them through the Strait of Gibraltar. All arrive safely in Seville on September 28.",
        "characters": [
            "juan_ii", "fray_hernando", "corporal_rodrigo",
            "thomas_beaumont", "sergeant_garcia", "marco_tornesi"
        ],
        "factions_affected": [],
        "location": "Seville",
        "tags": ["travel", "military", "roll"],
    },
    {
        "msgs": (21, 32),
        "date": "1430-09-28",
        "type": "council",
        "summary": "In the Torre del Oro, Álvaro briefs Juan on the state of the kingdom: the papal bull is legend (half of Castile thinks Juan a living saint), but the Infantes refused arrest and control ~5,000 troops with 8 noble houses. About 30% of nobility supports the crown, 20% the Infantes, 50% neutral. Juan discusses options including execution — Álvaro warns this would mean war with Aragon and horror among European courts. They agree to focus on stabilizing the realm first, confirming arrest orders publicly, and dealing with the Granadan delegation.",
        "characters": [
            "juan_ii", "alvaro_de_luna"
        ],
        "factions_affected": [],
        "location": "Seville, Torre del Oro",
        "tags": ["politics", "strategy", "council"],
    },
    {
        "msgs": (33, 38),
        "date": "1430-09-28",
        "type": "diplomacy",
        "summary": "Juan receives the Granadan delegation in the Alcázar throne room with the papal bull and sacred banner on full display. Ambassador Abu Abdullah al-Zaghal offers doubled tribute, trade privileges, release of Christian captives, and limited missionary access. Juan walks from his throne to shake al-Zaghal's hand — shocking the court — but firmly refuses the offer, citing the papal mandate as non-negotiable. He offers conversion as the only alternative. Al-Zaghal respectfully declines, warning that Granada now commands 20,000 soldiers with Maghrebi warriors, Egyptian gold, and Ottoman cannon. He departs noting that Juan's promise to protect surrendered Muslims is 'unexpected and will be remembered.' The diplomatic option is closed; war is inevitable.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "fray_hernando",
            "thomas_beaumont", "corporal_rodrigo", "sergeant_garcia",
            "abu_al_zaghal"
        ],
        "factions_affected": [],
        "location": "Seville, Alcázar",
        "tags": ["diplomacy", "crusade", "granada", "war"],
    },
]

NEW_CHARACTERS = [
    {
        "id": "abu_al_zaghal",
        "name": "Abu Abdullah al-Zaghal",
        "aliases": ["abu_al_zaghal", "al_zaghal"],
        "title": "Ambassador of Granada",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["foreign_ruler"],
        "location": "Granada",
        "current_task": "Returned from failed diplomatic mission to Seville; reported Juan II's rejection of peace terms and the scale of the crusade preparations",
        "personality": ["intelligent", "dignified", "eloquent", "pragmatic"],
        "interests": ["diplomacy", "Granada's survival"],
        "speech_style": "Fluent Castilian; formal but direct, capable of carrying both threat and respect in the same sentence",
        "core_characteristics": "Skilled Granadan diplomat, ~50 years old, gray beard. Led 12-person embassy to Seville with gifts worth ~20,000 dinars. Offered generous peace terms (doubled tribute, captive release, trade privileges, limited missionaries). When refused, warned Juan of Granada's unprecedented military support. Noted Juan's courtesy in walking from his throne to shake a Muslim's hand — called it 'unexpected and remembered.'",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "around fifty",
            "distinguishing_features": "intelligent dark eyes, carefully groomed gray beard",
        },
    },
]

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "Arrived in Seville with 62 crusaders; refused Granadan peace terms; preparing for the Royal Council and addressing the Infantes' rebellion",
        "location": "Seville",
    },
    {
        "id": "alvaro_de_luna",
        "current_task": "Failed to arrest the Infantes; briefed Juan on the state of the kingdom; preparing for the November Royal Council",
        "location": "Seville",
    },
    {
        "id": "fernan_alonso_de_robles",
        "current_task": "Successfully delivered arrest orders to Álvaro; now in Castile",
        "location": "Valladolid",
    },
    {
        "id": "infante_juan_de_aragon",
        "current_task": "Refused royal summons to surrender; fortified in Arévalo with ~5,000 troops; claiming arrest orders were forged by Álvaro",
        "location": "Arévalo",
    },
    {
        "id": "muhammad_ix",
        "current_task": "Diplomatic mission to Seville failed; peace terms rejected; preparing for war with unprecedented Muslim world support",
    },
]

NEW_LOCATIONS = [
    {
        "location_id": "seville",
        "name": "Seville",
        "region": "Castile",
        "description": "Major city in southern Castile. The Alcázar serves as the royal palace. Torre del Oro used for sensitive conferences. Site of Juan II's arrival with crusaders, his strategic briefing with Álvaro, and the formal rejection of Granada's peace offer. The Royal Council is scheduled here for November 8.",
        "sub_locations": ["Alcázar", "Torre del Oro"],
    },
]

NEW_FACTIONS = []

FACTION_UPDATES = []

ROLLS = [
    {
        "event_index": 0,
        "title": "Captain Fernán's Mission Delivery",
        "context": "Captain Fernán rides from Barcelona to Valladolid with royal arrest orders for the Infantes.",
        "roll_type": "travel",
        "date": "1430-09-02",
        "rolled": None,
        "outcome_range": "success",
        "outcome_label": "Success",
        "outcome_detail": "Fernán and two guards arrive in Valladolid after 14 days of hard riding. Orders delivered to Álvaro intact.",
        "evaluation": "Three experienced riders on a well-known route. The main risk was Navarrese interception, which didn't materialize.",
        "success_factors": ["Experienced riders", "Known route", "Consell Reial safe passage"],
        "failure_factors": [],
    },
    {
        "event_index": 0,
        "title": "Arrest of the Infantes",
        "context": "Álvaro attempts to execute Juan's orders to arrest the Infantes for rebellion.",
        "roll_type": "intrigue",
        "date": "1430-09-10",
        "rolled": None,
        "outcome_range": "failure",
        "outcome_label": "Failure",
        "outcome_detail": "The Infantes were prepared — they'd been intercepting correspondence and knew the orders were coming. They publicly refused, withdrew to fortified positions, and Alfonso V threatened war. A three-day standoff at Arévalo ended with Álvaro withdrawing. The Infantes remain free but are now exposed as refusing royal justice.",
        "evaluation": "The intercepted correspondence gave the Infantes warning. Without sufficient military force and with Alfonso V's threat looming, Álvaro couldn't force the issue.",
        "success_factors": [],
        "failure_factors": [
            "Infantes intercepted correspondence and were forewarned",
            "Insufficient royal military force for siege",
            "Alfonso V's threat of war from Aragon",
            "Infantes' fortified positions",
            "Political risk of open civil war",
        ],
    },
    {
        "event_index": 2,
        "title": "Voyage from Barcelona to Seville",
        "context": "Three galleys carry Juan, 62 crusaders, relics, and treasury from Barcelona around the Iberian coast to Seville.",
        "roll_type": "travel",
        "date": "1430-09-28",
        "rolled": None,
        "outcome_range": "success",
        "outcome_label": "Success",
        "outcome_detail": "Ten-day voyage completed with all cargo intact. Several tense encounters: bluffed past Valencia's inspection, corsairs retreated from armed formation, Moroccan galleys shadowed through Strait of Gibraltar but didn't attack.",
        "evaluation": "Three-ship formation provided security. Tense moments managed through combination of bluffing, arms display, and good seamanship.",
        "success_factors": [
            "Three-ship convoy formation",
            "Experienced Catalan captains",
            "Armed crusaders visible on deck",
            "Papal authority used to bluff Valencia",
        ],
        "failure_factors": [
            "Corsair presence near Cartagena",
            "Moroccan galleys in Strait of Gibraltar",
            "Valencia's attempted inspection",
        ],
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
        "chapter": "1.06",
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
    print(f"Chapter 1.06 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  New locations:     {len(NEW_LOCATIONS)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Written to:        {OUTPUT}")

if __name__ == "__main__":
    main()
