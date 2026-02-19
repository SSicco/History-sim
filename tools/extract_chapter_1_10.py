#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.10.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.10_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.10_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 22),
        "date": "1430-11-08",
        "end_date": "1430-12-20",
        "type": "decision",
        "summary": "Juan courts Isabel of Portugal in the weeks after the Council. Her character is established: plain in appearance but with quiet strength, conventionally pious and dutiful. Juan shows her the banner and sacred relics, and she responds with deep reverence. He promises to build a Portuguese-style chapel in every palace for her comfort. Their relationship is warm but formal — they are betrothed but cannot share a bed until married. Wedding plans begin.",
        "characters": [
            "juan_ii", "isabel_of_portugal"
        ],
        "factions_affected": [],
        "location": "Seville",
        "tags": ["personal", "marriage", "religion"],
    },
    {
        "msgs": (23, 44),
        "date": "1430-12-20",
        "end_date": "1430-12-28",
        "type": "council",
        "summary": "Wedding planning in Seville: date set for February 15, 1431 in Toledo Cathedral. Isabel chooses her Portuguese wedding dress and suggests 'Ubi Caritas' for the choir. The papal legate situation is determined: Cardinal Capranica is already in Toledo — a 62-year-old bureaucratic obstructionist with decent resources but maximum red tape. He will officiate the wedding. Juan organizes the travel party: Fernán, Sir Thomas, and García travel with 50 crusaders; Rodrigo stays in Seville to manage recruitment. Noble recruitment at the wedding is planned: physical trial, spiritual assessment by Hernando, oath before the banner, with 200 maravedís monthly pay. Juan creates a surprise: 62 freshly forged iron clasps for the existing crusaders.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "alvaro_de_luna",
            "fray_hernando", "fernan_alonso_de_robles",
            "corporal_rodrigo", "thomas_beaumont", "sergeant_garcia"
        ],
        "factions_affected": [],
        "location": "Seville",
        "tags": ["planning", "marriage", "crusade"],
    },
    {
        "msgs": (45, 50),
        "date": "1430-12-28",
        "end_date": "1431-01-14",
        "type": "decision",
        "summary": "The royal party travels from Seville to Toledo — a major procession of ~200 people including crusaders, Isabel's Portuguese entourage, and court officials. VERY SUCCESSFUL roll — unusually good winter weather, fast pace, arrives Toledo January 14. Isabel transforms on the journey: riding openly, accepting flowers from villagers, gaining confidence as future queen. The crusaders in white tabards with red crosses become a spectacle along the route. Towns welcome them enthusiastically. Isabel and Juan continue building their relationship during the journey.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "alvaro_de_luna",
            "fray_hernando", "fernan_alonso_de_robles",
            "thomas_beaumont", "sergeant_garcia"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["travel", "roll"],
    },
    {
        "msgs": (51, 70),
        "date": "1431-01-14",
        "end_date": "1431-01-20",
        "type": "diplomacy",
        "summary": "Juan meets Cardinal Domenico Capranica, the papal legate — a thin, meticulous 62-year-old bureaucratic obstructionist. Initial meeting goes well (honeymoon period): Juan shares Diego's meticulous records, acknowledges the importance of proper financial stewardship, and proposes a joint budget system. The Cardinal is pleased and agrees to cooperation. However, the long-term relationship is rolled as 'serious conflict' — the honeymoon will last 2-3 weeks before deteriorating. A bright spot: Álvaro and the legate's administrator Father Tommaso forge an excellent partnership (roll: 77) for detailed budget management, creating a buffer for the coming conflict.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "cardinal_capranica",
            "fray_hernando"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["diplomacy", "crusade", "religion", "roll"],
    },
    {
        "msgs": (71, 86),
        "date": "1431-01-20",
        "end_date": "1431-02-10",
        "type": "council",
        "summary": "Juan and Álvaro plan the 1431 crusade campaign in detail. The western army (12,000 strong) will include 1,000 crown troops, 1,500 Military Order soldiers, ~600 sworn crusaders, and ~8,900 noble levies. A separate eastern force of cavalry raiders (10 groups of 300 each, drawn from all three categories) will conduct flanking operations. Budget is meticulously calculated using historical estimates: total annual cost approximately 250-300 million maravedís. The campaign season runs from spring through late autumn, with specific objectives to be determined based on frontier reconnaissance.",
        "characters": [
            "juan_ii", "alvaro_de_luna"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["military", "planning", "crusade", "budget"],
    },
]

NEW_CHARACTERS = [
    {
        "id": "cardinal_capranica",
        "name": "Cardinal Domenico Capranica",
        "aliases": ["cardinal_capranica", "capranica"],
        "title": "Cardinal and Papal Legate to the Crusade",
        "born": "1369-00-00",
        "status": ["active"],
        "category": ["religious"],
        "location": "Toledo",
        "current_task": "Serving as papal legate to Juan II's crusade; initial cooperation on budget management but long-term serious conflict predicted",
        "personality": ["meticulous", "bureaucratic", "obstructionist", "detail_oriented"],
        "interests": ["proper procedure", "financial accountability", "papal authority", "documentation"],
        "speech_style": "Formal, precise, insistent on proper procedure; thin voice that carries surprisingly well",
        "core_characteristics": "62-year-old Italian cardinal appointed as papal legate to the crusade. Bureaucratic obstructionist with decent resources but maximum red tape — every decision requires documentation in triplicate. Initial meeting with Juan went well (honeymoon period), but long-term relationship will be seriously conflicted. His administrator Father Tommaso works excellently with Álvaro de Luna on budget management.",
        "faction_ids": [],
        "appearance": {
            "build": "thin",
            "age_appearance": "early 60s",
        },
    },
]

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "In Toledo preparing for February 15 wedding and spring crusade campaign; working with Cardinal Capranica on crusade finances",
        "location": "Toledo",
    },
    {
        "id": "isabel_of_portugal",
        "current_task": "In Toledo preparing for February 15 wedding; growing in confidence as future queen; gained popularity on the journey from Seville",
        "personality": {"add": ["growing_confidence"]},
        "location": "Toledo",
    },
    {
        "id": "alvaro_de_luna",
        "current_task": "Planning crusade budget and military campaign with excellent partnership with Father Tommaso (legate's administrator)",
        "location": "Toledo",
    },
    {
        "id": "corporal_rodrigo",
        "current_task": "Left in command of Seville operations; managing ongoing crusade recruitment while the court is in Toledo",
        "location": "Seville",
    },
]

NEW_LOCATIONS = []
NEW_FACTIONS = []
FACTION_UPDATES = []

ROLLS = [
    {
        "event_index": 2,
        "title": "Journey from Seville to Toledo",
        "context": "Royal procession of ~200 people travels from Seville to Toledo in late December/early January winter conditions.",
        "roll_type": "travel",
        "date": "1431-01-14",
        "rolled": 76,
        "outcome_range": "critical_success",
        "outcome_label": "Very Successful",
        "outcome_detail": "Unusually good winter weather. Fast pace, arriving Toledo January 14. Isabel transforms on the journey — riding openly, accepting flowers, gaining confidence. Towns welcome the crusade procession enthusiastically.",
        "evaluation": "Lucky weather and good logistics. The visual spectacle of white-tabarded crusaders became a publicity event along the entire route.",
        "success_factors": ["Unusually mild winter weather", "Well-organized procession", "Popular enthusiasm along the route"],
        "failure_factors": [],
    },
    {
        "event_index": 3,
        "title": "Initial Meeting with Cardinal Capranica",
        "context": "Juan II meets the papal legate, Cardinal Capranica, for the first time in Toledo. Initial honeymoon period.",
        "roll_type": "diplomacy",
        "date": "1431-01-14",
        "rolled": None,
        "outcome_range": "success",
        "outcome_label": "Honeymoon Success",
        "outcome_detail": "Initial meeting goes well. Cardinal pleased by Juan's meticulous records and willingness to establish proper financial oversight. However, long-term relationship rolled as 'serious conflict' — deterioration expected after 2-3 weeks.",
        "evaluation": "Juan's approach of acknowledging the Cardinal's authority while maintaining his own discretion worked in the short term. The fundamental conflict over control vs. flexibility will emerge later.",
        "success_factors": ["Juan's meticulous records (Diego's work)", "Willingness to cooperate on budgets", "Shared language of proper stewardship"],
        "failure_factors": ["Cardinal's fundamentally obstructionist nature", "Different priorities (control vs. flexibility)"],
    },
    {
        "event_index": 3,
        "title": "Álvaro-Tommaso Budget Partnership",
        "context": "Álvaro de Luna and Father Tommaso (legate's administrator) work together on detailed crusade budget management.",
        "roll_type": "diplomacy",
        "date": "1431-01-20",
        "rolled": 77,
        "outcome_range": "critical_success",
        "outcome_label": "Excellent Partnership",
        "outcome_detail": "Álvaro and Father Tommaso develop an outstanding working relationship. Their complementary skills (Álvaro's practical knowledge, Tommaso's administrative rigor) produce a comprehensive and realistic crusade budget. This partnership provides a critical buffer for the coming Juan-Capranica conflict.",
        "evaluation": "A fortunate pairing. The administrator's practical focus contrasts with his Cardinal's obstructionism, creating a functional channel even when the leaders clash.",
        "success_factors": ["Complementary skills", "Shared focus on practical outcomes", "Both experienced administrators"],
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
        "chapter": "1.10",
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
    print(f"Chapter 1.10 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Written to:        {OUTPUT}")

if __name__ == "__main__":
    main()
