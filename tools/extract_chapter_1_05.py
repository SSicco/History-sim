#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.05.

Reads tools/preprocessed/chapter_1.05_preprocessed.json and produces
tools/extractions/chapter_1.05_extracted.json.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.05_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.05_extracted.json"

# -----------------------------------------------------------------------
# Event definitions
# -----------------------------------------------------------------------

EVENT_DEFS = [
    {
        "msgs": (1, 14),
        "date": "1430-08-10",
        "end_date": "1430-08-18",
        "type": "decision",
        "summary": "Juan gives Fray Hernando an expanded role: build a tradition of confession and spiritual assessment for the crusade, recruit chaplains, and evaluate the character of recruits without breaking the confessional seal. Hernando accepts. The party then travels from Florence to Pisa and takes ship (the Sant'Angelo, Captain Grimaldi) across the Mediterranean to Barcelona. Success roll — the journey takes 9 days with one tense encounter with a pirate galley that decides to break off. They arrive safely on August 18.",
        "characters": [
            "juan_ii", "fray_hernando", "fernan_alonso_de_robles",
            "thomas_beaumont", "sergeant_garcia", "corporal_rodrigo"
        ],
        "factions_affected": [],
        "location": "Barcelona",
        "tags": ["travel", "religion", "planning", "roll"],
    },
    {
        "msgs": (15, 32),
        "date": "1430-08-18",
        "end_date": "1430-08-20",
        "type": "diplomacy",
        "summary": "Juan arrives in Barcelona and is greeted by Pere de Cardona, Royal Chamberlain. He immediately arranges to meet his sister Queen María of Aragon (née María de Trastámara), whom he hasn't seen in years. Their reunion is emotional and warm (roll: 5/affectionate). Juan tells her everything — the pilgrimage, Rome, the papal audience, the crusade bull. María provides critical intelligence about the Infantes' failed revolt and the state of Castile. She explains her limited authority in Aragon (manages court but the Consell Reial holds real power) and advises a multi-week campaign in Barcelona: display relics at the cathedral, meet with the Archbishop of Zaragoza and Consell Reial members, and write to Alfonso V.",
        "characters": [
            "juan_ii", "maria_of_aragon"
        ],
        "factions_affected": [],
        "location": "Barcelona",
        "tags": ["diplomacy", "family", "intelligence"],
    },
    {
        "msgs": (33, 44),
        "date": "1430-08-19",
        "type": "decision",
        "summary": "Learning of the Infantes' rebellion, Juan orders Captain Fernán to ride to Castile with sealed letters demanding Álvaro de Luna arrest the Infantes for treason. María objects — these are her husband's brothers, and cornering them could force Alfonso to choose sides. Juan is adamant. Fray Hernando challenges Juan's phrasing ('my mind is as clear as when I left for Rome'), warning against linking divine guidance to political arrests. Juan accepts the revision. Fernán departs with Martín and Felipe, transferring command to Corporal Rodrigo. Juan shows María the relics and banner, and four Italian crusaders from the Florence speech arrive: Marco Tornesi (soldier), Pietro Aldobrandini (merchant's son), Giovanni Rossi (blacksmith), and Andrea Vescovi (farmer's son).",
        "characters": [
            "juan_ii", "fernan_alonso_de_robles", "maria_of_aragon",
            "fray_hernando", "corporal_rodrigo", "marco_tornesi",
            "alvaro_de_luna"
        ],
        "factions_affected": ["royal_court"],
        "location": "Barcelona",
        "tags": ["politics", "military", "crusade"],
    },
    {
        "msgs": (45, 64),
        "date": "1430-08-19",
        "end_date": "1430-08-20",
        "type": "council",
        "summary": "Juan drafts the arrest letter to Álvaro with Hernando's help, softening language about divine certainty. He then formally accepts the four Italian crusaders in a dawn ceremony before the banner and relics — tapping each with his father's sword and allowing them to touch the reliquaries once. The oath includes unprecedented provisions: no rape, no forced conversion, protect surrendered Muslims with their lives. Juan reorganizes his force: Rodrigo as captain, García as senior sergeant, and establishes rotating banner guard pairs. He plans to recruit promising soldiers and tasks Fray Hernando with assessing all recruits spiritually.",
        "characters": [
            "juan_ii", "fray_hernando", "corporal_rodrigo",
            "sergeant_garcia", "thomas_beaumont", "marco_tornesi"
        ],
        "factions_affected": [],
        "location": "Barcelona",
        "tags": ["crusade", "ceremony", "military", "religion"],
    },
    {
        "msgs": (65, 78),
        "date": "1430-08-20",
        "end_date": "1430-08-27",
        "type": "diplomacy",
        "summary": "The Barcelona cathedral campaign is a great success. Over a week, massive crowds come to see the True Cross and Saint James bone. Recruitment system established: physical assessment by Rodrigo and Sir Thomas, spiritual assessment by Fray Hernando. By August 27: 82,000 florins raised (including 20,000 from converso merchant Rodrigo Ruiz, 8,000 from shipping magnate Lorenzo Medina), 62 crusaders recruited and training. The Archbishop of Zaragoza endorses the crusade and argues before the Consell Reial for Aragonese support. The Consell grants safe passage, allows recruitment, and provides 3 ships for transport to Seville. At a dinner hosted by María, Juan meets Isabel Ruiz, the 17-year-old converso merchant's daughter who challenges him about protecting Muslims — and falls deeply in love.",
        "characters": [
            "juan_ii", "fray_hernando", "corporal_rodrigo",
            "thomas_beaumont", "sergeant_garcia", "marco_tornesi",
            "maria_of_aragon", "isabel_ruiz", "cosimo_de_medici"
        ],
        "factions_affected": [],
        "location": "Barcelona",
        "tags": ["crusade", "diplomacy", "recruitment", "romance", "roll"],
    },
    {
        "msgs": (79, 110),
        "date": "1430-08-28",
        "end_date": "1430-08-29",
        "type": "decision",
        "summary": "Juan is consumed by love for Isabel. His sister María arranges a tea meeting with Isabel and her mother, but Juan misreads Isabel's careful distance as rejection. María explains the reality: Isabel is a converso — she cannot have an affair with a king; it would mark her as a harlot. Juan realizes the only way to pursue her is marriage, which would be politically explosive. He experiences a crisis of certainty: his 'absolute certainty' about Isabel was wrong, leading him to question whether his other certainties (Rome, arrest orders) might also be wrong. In an honest conversation with Fray Hernando, Juan admits disappointment and shame, and asks Hernando to challenge him whenever that feeling of certainty strikes. He lets the arrest orders stand but with new humility.",
        "characters": [
            "juan_ii", "maria_of_aragon", "isabel_ruiz", "fray_hernando"
        ],
        "factions_affected": [],
        "location": "Barcelona",
        "tags": ["romance", "personal", "religion", "introspection"],
    },
    {
        "msgs": (111, 144),
        "date": "1430-08-29",
        "end_date": "1430-09-08",
        "type": "council",
        "summary": "Juan organizes his growing crusade force. He designs uniforms: white tabards with red cross on front and back, and iron clasps reading 'Granada' — silver for officers, gold for the inner circle. He meets eight promising recruits and holds a council to discuss practical matters: pay (200 maravedís per soldier per month), treatment of Muslim prisoners, and the crusade's rules of conduct. He announces the pay publicly, and the 62 crusaders cheer. Juan plans to depart Barcelona in three weeks with three ships provided by the Aragonese Consell Reial, sending Diego ahead to Seville to prepare for their arrival.",
        "characters": [
            "juan_ii", "corporal_rodrigo", "fray_hernando",
            "thomas_beaumont", "sergeant_garcia", "marco_tornesi"
        ],
        "factions_affected": [],
        "location": "Barcelona",
        "tags": ["military", "planning", "crusade", "organization"],
    },
]

# -----------------------------------------------------------------------
# New characters
# -----------------------------------------------------------------------

NEW_CHARACTERS = [
    {
        "id": "maria_of_aragon",
        "name": "Queen María of Aragon",
        "aliases": ["maria_of_aragon", "maria_of_castile", "queen_maria", "maria_trastamara"],
        "title": "Queen of Aragon",
        "born": "1396-00-00",
        "status": ["active"],
        "category": ["royal_family"],
        "location": "Barcelona",
        "current_task": "Managing the Aragonese court in Alfonso V's absence; supporting her brother Juan II's crusade from Barcelona",
        "personality": ["warm", "intelligent", "cautious", "lonely"],
        "interests": ["family", "governance", "diplomacy"],
        "speech_style": "Warm and sisterly with Juan, but measured when discussing politics; carries the weight of years alone",
        "core_characteristics": "Juan II's older sister, married to Alfonso V of Aragon since 1415. Age ~34 in 1430. Has no children. Left Castile at 19, only seen Juan twice since. Alfonso is focused on Italian ambitions (Naples), leaving her isolated in Barcelona. Manages court and receives ambassadors but real power rests with the Consell Reial. Provides Juan critical intelligence about the Infantes' revolt. Warns about the political complications of his decisions. Arranges social events that introduce Juan to Barcelona's elite.",
        "faction_ids": ["royal_court"],
        "appearance": {
            "hair": "dark",
            "eyes": "warm brown (similar to Juan's)",
        },
    },
    {
        "id": "isabel_ruiz",
        "name": "Isabel Ruiz",
        "aliases": ["isabel_ruiz", "isabel"],
        "title": "",
        "born": "1413-00-00",
        "status": ["active"],
        "category": ["economic"],
        "location": "Barcelona",
        "current_task": "Daughter of converso merchant Rodrigo Ruiz; met Juan II at María's dinner and challenged him about protecting Muslims",
        "personality": ["bold", "questioning", "genuine", "intelligent", "slightly_awkward"],
        "interests": ["justice", "faith", "learning"],
        "speech_style": "Direct and questioning, sometimes bold enough to embarrass her parents; speaks from genuine conviction rather than court training",
        "core_characteristics": "17-year-old daughter of converso cloth merchant Rodrigo Ruiz. Auburn hair, green eyes, freckled. Her grandfather was born Jewish and converted. Family wealthy from trade but always watched and judged. She challenged Juan directly about his promise to protect Muslims who surrender. Juan fell deeply in love with her at first sight, but a relationship proved impossible — as a converso, any affair would mark her as a harlot. Juan's crisis of certainty about his feelings for her led to important self-reflection.",
        "faction_ids": [],
        "appearance": {
            "hair": "auburn",
            "eyes": "bright green",
            "skin": "pale with freckles",
            "age_appearance": "seventeen",
        },
    },
    {
        "id": "marco_tornesi",
        "name": "Marco Tornesi",
        "aliases": ["marco_tornesi", "marco"],
        "title": "Crusader",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Barcelona",
        "current_task": "First Italian crusader; serving as training sergeant for new recruits; accepted into the crusade in the dawn oath ceremony",
        "personality": ["experienced", "humble", "seeking_redemption"],
        "interests": ["combat", "soldiering", "redemption"],
        "speech_style": "Lean, practical soldier's speech; carries shame from mercenary past",
        "core_characteristics": "Former mercenary (~30 years old), lean and weather-beaten. First of four Italians to ride from Florence to Barcelona after Juan's speech. Former soldier for Milan and Genoa, now seeking redemption through the crusade. Proved excellent as training sergeant. Only one of the four with genuine combat experience. Some Castilian. Accepted in the dawn oath ceremony before the banner and relics.",
        "faction_ids": ["royal_court"],
        "appearance": {
            "build": "lean",
            "age_appearance": "around thirty",
            "distinguishing_features": "weather-beaten face",
        },
    },
]

# -----------------------------------------------------------------------
# Character updates
# -----------------------------------------------------------------------

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "Organizing the crusade force in Barcelona (82K florins, 62 crusaders); experienced crisis of certainty over Isabel; preparing to sail to Seville",
        "personality": {"add": ["infatuated", "self_questioning"]},
        "location": "Barcelona",
    },
    {
        "id": "fray_hernando",
        "current_task": "Expanded role as spiritual director of the crusade; assessing all recruits; challenged Juan on certainty and humility",
        "location": "Barcelona",
    },
    {
        "id": "fernan_alonso_de_robles",
        "current_task": "Dispatched to Castile with royal orders for Álvaro to arrest the Infantes; riding with Martín and Felipe",
        "location": "Road to Castile",
    },
    {
        "id": "corporal_rodrigo",
        "current_task": "Promoted to captain of Juan's guard (replacing Fernán); organizing crusader training and banner security",
        "location": "Barcelona",
    },
    {
        "id": "sergeant_garcia",
        "current_task": "Senior sergeant under Captain Rodrigo; training crusaders in sword work",
        "location": "Barcelona",
    },
    {
        "id": "thomas_beaumont",
        "current_task": "Military advisor to Juan's force; helping assess and train crusader recruits",
        "location": "Barcelona",
    },
]

# -----------------------------------------------------------------------
# New locations
# -----------------------------------------------------------------------

NEW_LOCATIONS = [
    {
        "location_id": "barcelona",
        "name": "Barcelona",
        "region": "Aragon",
        "description": "Major port city in the Crown of Aragon. Queen María manages the court in Alfonso V's absence. Site of Juan II's major crusade recruitment campaign — cathedral relic displays, 82,000 florins raised, 62 crusaders enrolled. The Consell Reial meets here and granted Aragonese support for the crusade.",
        "sub_locations": ["Barcelona Cathedral", "Palau Reial Menor", "Palau Reial Major"],
    },
]

# -----------------------------------------------------------------------
# Factions
# -----------------------------------------------------------------------

NEW_FACTIONS = []

FACTION_UPDATES = [
    {
        "faction_id": "royal_court",
        "member_ids": {"add": ["maria_of_aragon", "marco_tornesi"]},
    },
]

# -----------------------------------------------------------------------
# Rolls
# -----------------------------------------------------------------------

ROLLS = [
    {
        "event_index": 0,  # Journey to Barcelona
        "title": "Journey from Florence to Barcelona",
        "context": "Juan's party travels overland to Pisa and takes ship across the Mediterranean to Barcelona, carrying the crusade bull, relics, and treasury.",
        "roll_type": "travel",
        "date": "1430-08-18",
        "rolled": None,
        "outcome_range": "success",
        "outcome_label": "Success",
        "outcome_detail": "Nine-day journey completed safely. One tense encounter with a pirate galley that broke off when the Sant'Angelo proved too well-armed. All cargo and passengers arrived intact.",
        "evaluation": "Well-organized party with experienced crew. Captain Grimaldi's decision to avoid the Balearics added time but reduced risk.",
        "success_factors": [
            "Experienced ship captain (Grimaldi)",
            "Well-armed escort",
            "Good weather",
            "Avoiding pirate-heavy Balearic waters",
        ],
        "failure_factors": [
            "Pirate encounter (resolved)",
            "Juan's health issues continuing",
        ],
    },
    {
        "event_index": 4,  # Barcelona Cathedral Campaign
        "title": "Barcelona Cathedral Relic Display & Recruitment",
        "context": "Juan displays the True Cross and Saint James relics at Barcelona Cathedral for a week, with systematic recruitment and fundraising.",
        "roll_type": "persuasion",
        "date": "1430-08-27",
        "rolled": None,
        "outcome_range": "critical_success",
        "outcome_label": "Great Success",
        "outcome_detail": "Overwhelming response over a week: 82,000 florins raised (including 20,000 from converso merchant Ruiz, 8,000 from shipping magnate Medina), 62 crusaders recruited and training. Archbishop of Zaragoza endorses the crusade and secures Consell Reial support including 3 ships for transport. Barcelona's elite pledge financial and logistical support. The crusade gains institutional Aragonese backing.",
        "evaluation": "The combination of sacred relics, papal authority, Juan's growing reputation from Rome and Florence, and María's social networking created a perfect environment for recruitment and fundraising.",
        "success_factors": [
            "Sacred relics (True Cross, Santiago bone) as draws",
            "Papal authority backing the crusade",
            "Juan's reputation from Rome and Florence",
            "María's social network and hosting",
            "Archbishop of Zaragoza's endorsement",
            "Systematic recruitment process",
        ],
        "failure_factors": [],
    },
]

# -----------------------------------------------------------------------
# Law references
# -----------------------------------------------------------------------

LAW_REFERENCES = []

# -----------------------------------------------------------------------
# Main extraction logic
# -----------------------------------------------------------------------

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
        "chapter": "1.05",
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
    print(f"Chapter 1.05 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  New locations:     {len(NEW_LOCATIONS)}")
    print(f"  Faction updates:   {len(FACTION_UPDATES)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Written to:        {OUTPUT}")


if __name__ == "__main__":
    main()
