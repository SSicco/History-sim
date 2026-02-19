#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.07.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.07_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.07_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 6),
        "date": "1430-09-28",
        "type": "council",
        "summary": "Juan addresses Seville's assembled nobles demanding the Infantes surrender for trial, presenting evidence of rebellion and displaying the papal bull. FAILURE roll (not catastrophic) — the nobles remain divided. About 30% rally behind Juan, but the nobility is cautious: many distrust Álvaro de Luna, fear civil war, and see the arrest demand as heavy-handed. The Infantes' supporters stand firm. Juan is crushed by the lukewarm reception of what he believed was an overwhelming case.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "fray_hernando"
        ],
        "factions_affected": ["royal_court", "aragonese_faction"],
        "location": "Seville",
        "tags": ["politics", "speech", "roll"],
    },
    {
        "msgs": (7, 28),
        "date": "1430-09-28",
        "end_date": "1430-09-29",
        "type": "council",
        "summary": "Stung by the failed noble address, Juan and Álvaro strategize late into the night. They decide on three major moves: (1) pursue a Portuguese marriage for Juan — a naval power with no stake in the Aragonese dispute; (2) send a letter to Alfonso V of Aragon offering safe conduct for the Infantes to attend the November Royal Council, support for Alfonso's Italian ambitions, and a hint at future meeting; (3) publicly announce the safe conduct to shift narrative from 'tyrannical arrest' to 'fair trial.' The letter to Alfonso is drafted that night, including papal backing references, and dispatched by fastest ship the next morning with gifts (sword, Castilian war horse).",
        "characters": [
            "juan_ii", "alvaro_de_luna", "alfonso_v"
        ],
        "factions_affected": [],
        "location": "Seville",
        "tags": ["strategy", "diplomacy", "marriage"],
    },
    {
        "msgs": (29, 64),
        "date": "1430-09-29",
        "end_date": "1430-10-01",
        "type": "decision",
        "summary": "Juan organizes crusade logistics in Seville: reviews the three levels of clasps (iron, silver, gold — all reading 'Granada'), commissions 100 more, and establishes a learned crusader rank for chaplains and educated soldiers. He discusses banner display security with Rodrigo and plans a major public speech at the Plaza de San Francisco for October 2. In a deep confession with Fray Hernando, Juan confesses about Isabel — his pride in writing the poem, the selfishness of burdening her with his feelings, and the pain of letting go. He also confesses fear about his political marriage to a Portuguese princess and disappointment in the nobility. Hernando reminds him that the growth shown in burning the poem and recognizing his mistakes is itself grace.",
        "characters": [
            "juan_ii", "fray_hernando", "corporal_rodrigo",
            "thomas_beaumont", "sergeant_garcia"
        ],
        "factions_affected": [],
        "location": "Seville",
        "tags": ["crusade", "religion", "personal", "organization"],
    },
    {
        "msgs": (65, 76),
        "date": "1430-10-02",
        "type": "diplomacy",
        "summary": "Juan's crusaders pass a spiritual assessment (success roll — genuine faith, not adventure-seekers). On October 2, Juan addresses 8,000-10,000 people at the Plaza de San Francisco in Seville with the banner and relics on display. His speech covers the papal mandate, the Infantes' rebellion, the offer of safe conduct, and the crusade vision. SUCCESS roll — the speech lands well: the common people and middle class rally, donations flow, and the crusade narrative gains traction in Seville. Not the overwhelming triumph of Florence, but a solid political win that strengthens Juan's position heading into the November Council.",
        "characters": [
            "juan_ii", "fray_hernando", "corporal_rodrigo",
            "thomas_beaumont", "sergeant_garcia", "marco_tornesi"
        ],
        "factions_affected": [],
        "location": "Seville, Plaza de San Francisco",
        "tags": ["speech", "crusade", "diplomacy", "roll"],
    },
    {
        "msgs": (77, 100),
        "date": "1430-10-08",
        "end_date": "1430-10-25",
        "type": "diplomacy",
        "summary": "Three diplomatic responses arrive in rapid succession. The Infantes accept safe conduct and will attend the November Council (simple acceptance, no conditions). Alfonso V of Aragon responds cautiously — interested in the Italian support offer, requests the Infantes be treated fairly, doesn't commit to alliance but doesn't threaten war either. Portugal enthusiastically accepts the marriage proposal — Princess Isabel of Portugal will marry Juan, with a large dowry including 100,000 gold crusados, Madeira trade rights, and mutual defense treaty. Captain Fernán returns from his intelligence mission in Castile with detailed reports on Infantes' military positions and noble alignments.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "fernan_alonso_de_robles",
            "infante_juan_de_aragon", "infante_enrique_de_aragon",
            "alfonso_v", "corporal_rodrigo"
        ],
        "factions_affected": [],
        "location": "Seville",
        "tags": ["diplomacy", "marriage", "politics"],
    },
    {
        "msgs": (101, 110),
        "date": "1430-10-25",
        "end_date": "1430-10-31",
        "type": "council",
        "summary": "Juan and Álvaro finalize the November 8 Royal Council agenda: (1) Welcome and framing; (2) Announce Portuguese betrothal with proof; (3) Describe warm Aragonese relations and Barcelona welcome; (4) Present evidence of the Infantes' rebellion with witnesses; (5) Offer the Infantes a chance to respond; (6) After the Council, a public ceremony outside where crusaders stand under the banner and Juan personally distributes clasps. The format is designed to show strength, legitimacy, and international support before delivering the hammer blow of treason charges.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "thomas_beaumont",
            "corporal_rodrigo", "fernan_alonso_de_robles",
            "sergeant_garcia"
        ],
        "factions_affected": [],
        "location": "Seville",
        "tags": ["planning", "politics", "council"],
    },
]

NEW_CHARACTERS = []

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "Preparing for November 8 Royal Council; Portuguese marriage secured; Infantes accepted safe conduct; planning trial and crusade ceremony",
        "personality": {"add": ["humbled_by_failure"]},
    },
    {
        "id": "alvaro_de_luna",
        "current_task": "Co-planning the Royal Council with Juan; managing safe conduct logistics; preparing evidence against the Infantes",
    },
    {
        "id": "fernan_alonso_de_robles",
        "current_task": "Returned from intelligence mission in Castile with detailed reports on Infantes' positions and noble alignments",
        "location": "Seville",
    },
    {
        "id": "alfonso_v",
        "current_task": "Responded cautiously to Juan's overture; interested in Italian campaign support; watching the Council outcome before committing",
    },
]

NEW_LOCATIONS = []
NEW_FACTIONS = []
FACTION_UPDATES = []

ROLLS = [
    {
        "event_index": 0,
        "title": "Noble Address on Infantes' Rebellion",
        "context": "Juan addresses Seville's nobles, presenting evidence of rebellion and the papal bull, demanding the Infantes surrender for trial.",
        "roll_type": "persuasion",
        "date": "1430-09-28",
        "rolled": None,
        "outcome_range": "failure",
        "outcome_label": "Failure (Not Catastrophic)",
        "outcome_detail": "Nobles remain divided. About 30% rally behind Juan, but the majority are cautious — distrustful of Álvaro, fearing civil war, and seeing the arrest demand as heavy-handed. The papal bull impresses but doesn't override political calculation.",
        "evaluation": "The speech was well-constructed but the political landscape was against success. Many nobles resent Álvaro de Luna's influence and fear being drawn into a civil war between the crown and Aragon.",
        "success_factors": [
            "Papal bull as evidence of divine mandate",
            "Clear evidence of Infantes' rebellion",
            "Juan's growing reputation",
        ],
        "failure_factors": [
            "Noble distrust of Álvaro de Luna",
            "Fear of civil war with Aragon",
            "Arrest demand seen as heavy-handed",
            "50% of nobility neutral and cautious",
        ],
    },
    {
        "event_index": 3,
        "title": "Crusader Spiritual Assessment",
        "context": "Juan assesses whether his 62 crusaders have maintained genuine spiritual commitment through their selective recruitment and Fray Hernando's spiritual formation.",
        "roll_type": "intrigue",
        "date": "1430-10-01",
        "rolled": None,
        "outcome_range": "success",
        "outcome_label": "Success",
        "outcome_detail": "The crusaders show genuine faith and commitment. Daily confession, group prayer, and careful vetting have created a core of believers rather than mercenaries. Not all are saints, but their sincerity is real.",
        "evaluation": "Fray Hernando's spiritual formation program and the two-stage recruitment process (physical by Rodrigo, spiritual by Hernando) created a genuine core.",
        "success_factors": [
            "Selective recruitment process",
            "Fray Hernando's daily spiritual formation",
            "Strong group cohesion from shared journey",
        ],
        "failure_factors": [],
    },
    {
        "event_index": 3,
        "title": "Seville Plaza Speech",
        "context": "Juan addresses 8,000-10,000 people at the Plaza de San Francisco with the banner and relics, covering the papal mandate, Infantes' rebellion, safe conduct offer, and crusade vision.",
        "roll_type": "persuasion",
        "date": "1430-10-02",
        "rolled": None,
        "outcome_range": "success",
        "outcome_label": "Success",
        "outcome_detail": "Solid political win. Common people and middle class rally, donations flow, crusade narrative gains traction. Not the overwhelming triumph of Florence but a meaningful advance in Juan's home territory. The safe conduct offer is perceived positively as showing fairness.",
        "evaluation": "After the noble address failure, this public speech to the broader population proved more effective. Common people respond to the crusade message more readily than cautious nobles.",
        "success_factors": [
            "Strong message and relics on display",
            "Home territory (Seville)",
            "Safe conduct narrative showing fairness",
            "Common people more responsive than nobles",
        ],
        "failure_factors": [
            "Recent noble address failure dampened expectations",
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
        "chapter": "1.07",
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
    print(f"Chapter 1.07 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Written to:        {OUTPUT}")

if __name__ == "__main__":
    main()
