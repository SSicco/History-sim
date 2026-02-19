#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.09.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.09_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.09_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 14),
        "date": "1430-11-09",
        "end_date": "1430-11-12",
        "type": "council",
        "summary": "The Infantes honor their oaths completely (roll: 32 — full compliance). They arrive at dawn on November 9 for Fray Hernando's spiritual examination. Hernando assesses Enrique as genuinely committed with a warrior's soul seeking redemption, and Juan as more intellectual but sincere enough. Both send orders for their household troops (~3,600 men) to muster at Seville. Juan II accepts them as crusaders and offers to make them commanders, but declines their proposal for direct command of their levies. Individual soldiers may join voluntarily. About 800 from the Infantes' households eventually join as crusaders.",
        "characters": [
            "juan_ii", "infante_juan_de_aragon", "infante_enrique_de_aragon",
            "fray_hernando", "alvaro_de_luna"
        ],
        "factions_affected": ["royal_court"],
        "location": "Seville",
        "tags": ["politics", "crusade", "recruitment", "roll"],
    },
    {
        "msgs": (15, 32),
        "date": "1430-11-12",
        "type": "council",
        "summary": "Before the banner with the True Cross, the Infantes swear sacred oaths renouncing all claims to Aragon's throne for themselves and their descendants forever. Critical moment: Infante Juan asks about his 9-year-old son Carlos, King of Navarre. Juan II clarifies that Carlos keeps Navarre (a father cannot give away what belongs to his son) but Aragonese claims are renounced. Juan II kneels before the True Cross and swears to protect Carlos as if he were his own son. Both Infantes touch the sacred relics — Enrique trembles and weeps, feeling 'everything'; Juan breaks down completely, sobbing 'forgive me.' Juan II pins commander clasps (bronze with silver inlay) to both. Their transformation seems genuine.",
        "characters": [
            "juan_ii", "infante_juan_de_aragon", "infante_enrique_de_aragon",
            "fray_hernando"
        ],
        "factions_affected": [],
        "location": "Seville",
        "tags": ["crusade", "ceremony", "succession", "religion"],
    },
    {
        "msgs": (33, 42),
        "date": "1430-11-13",
        "type": "diplomacy",
        "summary": "Álvaro recognizes the political earthquake: Alfonso V has no heir, his brothers' renunciation throws Aragonese succession into chaos, and Castile benefits enormously. Juan sends a letter campaign to Alfonso: a warm familial letter from Juan, complete testimonies from Fray Hernando and witnesses, the Infantes' own letters explaining their choice, and a personal note to sister María mentioning his upcoming marriage. Letters dispatched November 13 by multiple routes, expected to reach Naples by late November.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "alfonso_v", "maria_of_aragon"
        ],
        "factions_affected": [],
        "location": "Seville",
        "tags": ["diplomacy", "succession", "strategy"],
    },
    {
        "msgs": (43, 50),
        "date": "1430-12-14",
        "type": "diplomacy",
        "summary": "Princess Isabel of Portugal (age 15) arrives in Seville aboard eight Portuguese galleys. Juan meets her with complete honesty about what she's entering: near civil war, crusade lasting approximately ten years, a kingdom constantly at war. Isabel is initially overwhelmed — her father hadn't fully explained. Juan kneels before her, promising she'll be a real partner, not just a 'pretty face and a womb.' She reveals her love of reading (history, philosophy, theology) and desire to be useful. GREAT SUCCESS roll — Isabel transforms from terrified and defensive to genuinely hopeful, asking excited questions about books and the city. She gives a public speech in carefully learned Castilian. The foundation of a real partnership is established.",
        "characters": [
            "juan_ii", "isabel_of_portugal"
        ],
        "factions_affected": [],
        "location": "Seville",
        "tags": ["marriage", "diplomacy", "personal"],
    },
    {
        "msgs": (51, 58),
        "date": "1430-12-18",
        "type": "diplomacy",
        "summary": "Alfonso V's response arrives while Juan is showing Isabel the palace library. SUCCESS roll for maintaining good relations — Alfonso's letter is cold but not hostile. He acknowledges the Infantes deserved punishment, doesn't question the validity of sacred oaths, but notes the succession implications are 'remarkably convenient' for Castile. He withdraws active crusade support to focus on Naples and his own succession, but maintains formal diplomatic relations through María. No war threats, no diplomatic break. Isabel perceptively notes Alfonso handled it skillfully — accepting reality while signaling he's watching. The Aragonese relationship has cooled but not broken.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "isabel_of_portugal", "alfonso_v"
        ],
        "factions_affected": [],
        "location": "Seville",
        "tags": ["diplomacy", "succession", "roll"],
    },
]

NEW_CHARACTERS = [
    {
        "id": "isabel_of_portugal",
        "name": "Princess Isabel of Portugal",
        "aliases": ["isabel_of_portugal", "princess_isabel", "isabel_de_portugal"],
        "title": "Princess of Portugal",
        "born": "1415-00-00",
        "status": ["active"],
        "category": ["royal_family"],
        "location": "Seville",
        "current_task": "Betrothed to Juan II; arrived in Seville from Portugal; building partnership with Juan; wedding planned for late January/early February 1431",
        "personality": ["intelligent", "bookish", "brave", "perceptive", "reserved_initially"],
        "interests": ["reading", "history", "philosophy", "theology", "governance"],
        "speech_style": "Careful and measured, with growing confidence; speaks learned Castilian; reveals intelligence in questions rather than statements",
        "core_characteristics": "15-year-old Portuguese princess, Juan II's betrothed. Dark hair, brown eyes, pale with freckles. Father allowed her to read in his library (history, philosophy, theology) though her confessor disapproved. Initially terrified by the reality of what she was marrying into (decade-long crusade, near civil war), but transformed when Juan was completely honest and treated her as a partner. Showed political acumen in analyzing Alfonso's letter. Dreams of being useful and intellectually engaged, not merely decorative.",
        "faction_ids": ["royal_court"],
        "appearance": {
            "hair": "dark",
            "eyes": "brown",
            "skin": "pale with freckles",
            "age_appearance": "fifteen",
        },
    },
]

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "Betrothed to Princess Isabel of Portugal; Infantes transformed into crusader commanders; 340+ crusaders assembled; preparing for wedding and spring campaign",
        "location": "Seville",
    },
    {
        "id": "infante_juan_de_aragon",
        "current_task": "Accepted as crusader commander; renounced all Aragonese succession claims for himself and descendants; experienced profound spiritual transformation before the relics; son Carlos protected by Juan II's oath",
        "personality": {"add": ["spiritually_transformed"]},
    },
    {
        "id": "infante_enrique_de_aragon",
        "current_task": "Accepted as crusader commander; renounced all Aragonese succession claims; experienced intense spiritual moment touching the True Cross",
    },
    {
        "id": "alfonso_v",
        "current_task": "Responded coldly to brothers' renunciation; withdrew active crusade support; focused on Naples; maintaining formal but cooled relations with Castile",
    },
]

NEW_LOCATIONS = []
NEW_FACTIONS = []
FACTION_UPDATES = [
    {
        "faction_id": "royal_court",
        "member_ids": {"add": ["isabel_of_portugal", "infante_juan_de_aragon", "infante_enrique_de_aragon"]},
        "description": "The royal court now includes Princess Isabel of Portugal (betrothed), the former Infantes as crusader commanders, and a growing force of 340+ sworn crusaders. The Portuguese alliance is secured through marriage. Aragonese support withdrawn but relations not hostile.",
    },
]

ROLLS = [
    {
        "event_index": 0,
        "title": "Infantes' Decision After Council",
        "context": "After publicly confessing rebellion and offering to join the crusade, the Infantes must decide whether to honor their oaths.",
        "roll_type": "chaos",
        "date": "1430-11-09",
        "rolled": 32,
        "outcome_range": "success",
        "outcome_label": "Honor Oaths Completely",
        "outcome_detail": "The Infantes arrive at dawn for spiritual examination, present themselves without armed retinue, dressed simply. They send formal orders for their household troops to muster at Seville under Juan II's command. About 800 soldiers join as individual crusaders.",
        "evaluation": "50% probability of full compliance. The sacred oath before the True Cross and the political calculus (nowhere else to go) combined to produce genuine commitment.",
        "success_factors": ["Sacred oath binding", "Political reality (no alternatives)", "Genuine spiritual impact of relics"],
        "failure_factors": [],
    },
    {
        "event_index": 3,
        "title": "Building Partnership with Princess Isabel",
        "context": "Juan II meets his Portuguese betrothed and attempts to build a genuine partnership through complete honesty about the challenges ahead.",
        "roll_type": "persuasion",
        "date": "1430-12-14",
        "rolled": None,
        "outcome_range": "critical_success",
        "outcome_label": "Great Success",
        "outcome_detail": "Isabel transforms from terrified and defensive to genuinely hopeful. She reveals her love of learning and desire to be useful. Juan's honesty and his act of kneeling before her (unprecedented for a king to his bride) creates a genuine emotional connection. She gives a confident public speech in Castilian. Their Portuguese and Castilian escorts are visibly shocked by the transformation.",
        "evaluation": "Juan's approach of radical honesty — the same approach that worked with the Pope — proved effective again. Treating Isabel as an intellectual partner rather than a political asset struck exactly the right note.",
        "success_factors": [
            "Complete honesty about challenges",
            "Kneeling before her (unprecedented vulnerability)",
            "Treating her as intellectual partner",
            "Offering books and education",
        ],
        "failure_factors": [],
    },
    {
        "event_index": 4,
        "title": "Alfonso V's Response to Brothers' Renunciation",
        "context": "Alfonso V receives news that his brothers have renounced all Aragonese succession claims before sacred relics, throwing Aragon's succession into chaos.",
        "roll_type": "diplomacy",
        "date": "1430-12-18",
        "rolled": None,
        "outcome_range": "success",
        "outcome_label": "Success",
        "outcome_detail": "Alfonso accepts with cold wariness. He acknowledges the Infantes deserved punishment, doesn't challenge sacred oaths, but notes outcomes are 'remarkably convenient' for Castile. Withdraws active crusade support to focus on Naples. Maintains formal relations through María. No war threats or diplomatic break.",
        "evaluation": "Best realistic outcome given the magnitude of the succession shift. Alfonso is too focused on Naples to risk war with a papally-backed crusader king.",
        "success_factors": [
            "Complete transparency about oaths",
            "Sacred context prevents challenging legitimacy",
            "Alfonso focused on Italian ambitions",
            "María serving as diplomatic bridge",
        ],
        "failure_factors": [
            "Succession implications deeply concerning to Alfonso",
            "Cold tone signals lasting damage to relationship",
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
        "chapter": "1.09",
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
    print(f"Chapter 1.09 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Written to:        {OUTPUT}")

if __name__ == "__main__":
    main()
