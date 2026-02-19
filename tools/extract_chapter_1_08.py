#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.08.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.08_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.08_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 4),
        "date": "1430-11-07",
        "type": "diplomacy",
        "summary": "Juan meets the Infantes de Aragón the evening before the Royal Council. Both princes arrived November 7 with modest retinues under safe conduct. Juan is polite but deliberately brief — checking their accommodations, asking about their journey, but refusing to discuss substantive matters. Infante Juan is tightly controlled, Infante Enrique more subdued. Juan keeps the meeting to under five minutes.",
        "characters": [
            "juan_ii", "infante_juan_de_aragon", "infante_enrique_de_aragon"
        ],
        "factions_affected": [],
        "location": "Seville, Alcázar",
        "tags": ["politics", "diplomacy"],
    },
    {
        "msgs": (5, 20),
        "date": "1430-11-08",
        "type": "council",
        "summary": "The Royal Council of Seville — Juan's masterpiece of political theater. He opens by announcing the Portuguese betrothal (SUCCESS roll — nobles impressed), then describes Barcelona's warm welcome and Aragonese diplomatic relations (SUCCESS), then presents the papal bull with the Archbishop of Toledo's endorsement (SUCCESS — nobles pledge their arms to the crusade). Finally, Juan frames the Infantes' rebellion as an obstacle to the sacred crusade (GREAT SUCCESS — seamless transition, Álvaro's evidence is devastating, twelve witnesses testify, the case is overwhelming). Through four successive successful rolls, Juan transforms from a young king defending his throne into the divinely mandated leader of a holy crusade, making opposition to him opposition to God.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "fray_hernando",
            "archbishop_cerezuela", "infante_juan_de_aragon",
            "infante_enrique_de_aragon"
        ],
        "factions_affected": ["royal_court", "aragonese_faction"],
        "location": "Seville, Alcázar",
        "tags": ["politics", "council", "crusade", "roll"],
    },
    {
        "msgs": (21, 28),
        "date": "1430-11-08",
        "type": "council",
        "summary": "The Infantes' defense achieves a GREAT SUCCESS of its own — not by contesting the evidence, but by completely submitting. Infante Enrique weeps and begs forgiveness. Infante Juan, breaking from his script, drops to his knees and offers to renounce all claims, titles, and lands in exchange for joining the crusade as a common soldier. Juan seizes the moment brilliantly, drawing a parallel between his own renunciation before the Pope and the Infantes' submission. The Council finds the Infantes guilty of rebellion but Juan exercises mercy: no formal punishment due to safe conduct, but they must renounce all Castilian titles and serve the crusade to earn redemption. The nobles cheer.",
        "characters": [
            "juan_ii", "infante_juan_de_aragon", "infante_enrique_de_aragon",
            "alvaro_de_luna"
        ],
        "factions_affected": ["royal_court", "aragonese_faction"],
        "location": "Seville, Alcázar",
        "tags": ["politics", "council", "justice", "mercy", "roll"],
    },
    {
        "msgs": (29, 38),
        "date": "1430-11-08",
        "type": "council",
        "summary": "After the Council, Juan leads everyone outside for the crusader clasp ceremony. Before the banner with sacred relics, Juan personally distributes clasps — starting with himself, then his commanders (Sir Thomas, Rodrigo, Fernán, García), chaplains, and common crusaders. He gives the Infantes time to consider their commitment rather than rushing them into the oath — honoring both the safe conduct and testing their sincerity. The Archbishop of Toledo asks to help assess the Infantes' readiness, but Juan assigns this to Fray Hernando specifically, maintaining his own institutional independence. Diego is ordered to draft formal documents for the Infantes' title renunciation.",
        "characters": [
            "juan_ii", "thomas_beaumont", "corporal_rodrigo",
            "fernan_alonso_de_robles", "sergeant_garcia",
            "fray_hernando", "archbishop_cerezuela",
            "infante_juan_de_aragon", "infante_enrique_de_aragon"
        ],
        "factions_affected": [],
        "location": "Seville, Alcázar",
        "tags": ["crusade", "ceremony", "politics"],
    },
    {
        "msgs": (39, 50),
        "date": "1430-11-08",
        "type": "council",
        "summary": "In private with Álvaro, Juan reveals his long-term strategy: use the Infantes' renunciation to eliminate their entire line from Aragonese succession, eventually pressing his own claim to unite Castile and Aragon under one crown. He plans to achieve this through glory and diplomacy rather than assassination or war. Key complication: Infante Juan has a son, Carlos, Prince of Viana, whose claims through his mother's Navarrese line would survive his father's renunciation. Juan acknowledges this must be handled carefully and decides to invite Carlos to Seville. Álvaro is both impressed and slightly alarmed by Juan's dynastic ambition.",
        "characters": [
            "juan_ii", "alvaro_de_luna"
        ],
        "factions_affected": [],
        "location": "Seville",
        "tags": ["strategy", "dynasty", "succession"],
    },
]

NEW_CHARACTERS = []

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "Won the Royal Council decisively; Infantes found guilty and submitting to crusade; Portuguese marriage secured; long-term plan to unite Castile and Aragon",
        "personality": {"add": ["master_politician"]},
    },
    {
        "id": "infante_juan_de_aragon",
        "current_task": "Found guilty of rebellion; renounced all Castilian claims and titles; committed to joining crusade as common soldier; awaiting Fray Hernando's spiritual assessment",
        "personality": {"add": ["humbled", "penitent"]},
        "location": "Seville",
    },
    {
        "id": "infante_enrique_de_aragon",
        "current_task": "Found guilty of rebellion; renounced claims and titles; committed to joining crusade; wept during submission",
        "personality": {"add": ["penitent"]},
        "location": "Seville",
    },
    {
        "id": "alvaro_de_luna",
        "current_task": "Presented devastating evidence at the Council; impressed and slightly alarmed by Juan's long-term dynastic ambitions for Aragon",
    },
]

NEW_LOCATIONS = []
NEW_FACTIONS = []
FACTION_UPDATES = [
    {
        "faction_id": "aragonese_faction",
        "description": "Effectively dissolved. Both Infantes found guilty of rebellion at the November 8 Royal Council, renounced all Castilian claims and titles, and committed to serving in the crusade as common soldiers. Master of Santiago (Luis de Guzmán) left without a patron. The faction's political power in Castile is broken.",
    },
]

ROLLS = [
    {
        "event_index": 1,
        "title": "Council: Portuguese Betrothal Announcement",
        "context": "Juan opens the Royal Council by announcing his betrothal to Princess Isabel of Portugal.",
        "roll_type": "persuasion",
        "date": "1430-11-08",
        "rolled": None,
        "outcome_range": "success",
        "outcome_label": "Success",
        "outcome_detail": "Nobles impressed by the strategic marriage. Portugal's naval power, wealth, and neutrality make it an excellent choice. Momentum established early.",
        "evaluation": "Strong opening move. The betrothal demonstrates Juan's growing diplomatic network and strategic thinking.",
        "success_factors": ["Excellent match strategically", "Letter from Portuguese king as proof", "Sets positive tone"],
        "failure_factors": [],
    },
    {
        "event_index": 1,
        "title": "Council: Aragonese Relations",
        "context": "Juan describes Barcelona's warm welcome, 82,000 florins raised, and ongoing diplomatic relations with Alfonso V.",
        "roll_type": "persuasion",
        "date": "1430-11-08",
        "rolled": None,
        "outcome_range": "success",
        "outcome_label": "Success",
        "outcome_detail": "Nobles impressed by the Barcelona achievements. The scale of support and Aragonese Consell Reial's backing demonstrates Juan's international standing.",
        "evaluation": "Building momentum. Each success makes the next segment more impactful.",
        "success_factors": ["82,000 florins concrete evidence", "Consell Reial backing", "Building on Portuguese announcement"],
        "failure_factors": [],
    },
    {
        "event_index": 1,
        "title": "Council: Papal Bull Presentation",
        "context": "Juan presents the papal crusade bull with the Archbishop of Toledo's formal endorsement.",
        "roll_type": "persuasion",
        "date": "1430-11-08",
        "rolled": None,
        "outcome_range": "success",
        "outcome_label": "Success",
        "outcome_detail": "The Archbishop's endorsement and the physical presence of the papal bull with its lead seal are powerfully convincing. Nobles pledge their arms to the crusade.",
        "evaluation": "The religious framing transforms the Council from political to sacred. Opposition becomes opposition to God.",
        "success_factors": ["Papal authority", "Archbishop's endorsement", "Accumulated momentum from prior segments"],
        "failure_factors": [],
    },
    {
        "event_index": 1,
        "title": "Council: Rebellion Evidence Against Infantes",
        "context": "Juan transitions to the Infantes' rebellion, framing it as obstacle to the sacred crusade. Álvaro presents evidence with twelve witnesses.",
        "roll_type": "persuasion",
        "date": "1430-11-08",
        "rolled": None,
        "outcome_range": "critical_success",
        "outcome_label": "Great Success",
        "outcome_detail": "Seamless transition from crusade fervor to rebellion charges. The nobles accept the framing completely — opposing the Infantes becomes a matter of faith, not just politics. Twelve witnesses deliver devastating testimony. The case is overwhelming.",
        "evaluation": "The accumulated momentum of three previous successes made this great success possible. By the time evidence was presented, the nobles were already committed to the crusade and saw the Infantes as obstacles to God's work.",
        "success_factors": [
            "Three prior successes building momentum",
            "Framing rebellion as obstacle to crusade",
            "Twelve witnesses with devastating evidence",
            "Álvaro's thorough preparation",
        ],
        "failure_factors": [],
    },
    {
        "event_index": 2,
        "title": "Infantes' Defense at the Council",
        "context": "The Infantes respond to overwhelming evidence of rebellion. Rather than contest the charges, they choose complete submission.",
        "roll_type": "persuasion",
        "date": "1430-11-08",
        "rolled": None,
        "outcome_range": "critical_success",
        "outcome_label": "Great Success",
        "outcome_detail": "The Infantes' surrender exceeds all expectations. Infante Enrique weeps genuinely. Infante Juan breaks from his script and drops to his knees, offering to renounce everything and serve as a common crusader. The nobles are deeply moved. Juan brilliantly draws a parallel to his own renunciation before the Pope, transforming the moment from humiliation into redemption.",
        "evaluation": "Surprising outcome — the Infantes chose the one strategy that could save them. Their complete submission, whether calculated or genuine, gave Juan the opportunity to show mercy and strengthen his position simultaneously.",
        "success_factors": [
            "Complete submission rather than defiance",
            "Genuine emotion (Enrique's tears)",
            "Infante Juan's dramatic renunciation offer",
            "Nobles' emotional readiness after earlier Council sessions",
        ],
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
        "chapter": "1.08",
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
    print(f"Chapter 1.08 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Written to:        {OUTPUT}")

if __name__ == "__main__":
    main()
