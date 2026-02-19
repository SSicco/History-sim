#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.11.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.11_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.11_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 24),
        "date": "1431-01-17",
        "end_date": "1431-01-28",
        "type": "council",
        "summary": "The crusade oversight committee meets in Toledo's Royal Alcázar. Cardinal Capranica, the Archbishop of Toledo, Álvaro de Luna, and Father Tommaso present the 47-page campaign budget (143,171 florins for 8-month campaign, April-November 1431). The budget is unanimously approved. Discussion follows on crusade taxation: 5% noble tax with 2,000 maravedí personal service exemption, 10% church property tax with hardship provisions. Joint assessment teams agreed (43 crown assessors paired with ecclesiastical observers). Capranica invited to officiate the February 15 wedding — accepts with genuine pleasure. Juan commissions a commemorative painting by an Italian or Flemish master for next winter. Papal letters to foreign kingdoms held until after first campaign season to announce victories rather than mere proclamations.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "cardinal_capranica",
            "archbishop_cerezuela", "tommaso_parentucelli"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["budget", "crusade", "taxation", "planning", "marriage"],
    },
    {
        "msgs": (25, 50),
        "date": "1431-01-24",
        "type": "crisis",
        "summary": "CRISIS: Cardinal Capranica demands Isabel dismiss her three Portuguese ladies-in-waiting (Dona Beatriz, Dona Inês, Dona Catarina) and replace them with Spanish women he has selected from Toledo families. Massive overreach — the papal bull grants no authority over the royal household. Isabel comes to Juan in distress. Juan convenes Álvaro, Fray Hernando, the Portuguese ladies, and trusted guards. Hernando confirms the ladies are devout Catholics with no spiritual failings. The group concludes Capranica's real motive is control: placing families in his debt and gaining indirect influence over the Queen. Juan's strategy: passive resistance — ignore the demand (Capranica never formally approached Juan), post guards under Rodrigo Sánchez with crown protection letter, act innocent if challenged. Leave Capranica a face-saving exit to claim it was a misunderstanding. Roll: 98 (Breaking Point) — triggered the crisis.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "cardinal_capranica",
            "fray_hernando", "alvaro_de_luna", "dona_beatriz"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["crisis", "politics", "personal", "religion", "roll"],
    },
    {
        "msgs": (51, 56),
        "date": "1431-01-27",
        "type": "diplomacy",
        "summary": "At a formal dinner hosted by the Archbishop for Toledo's noble families, Capranica makes pointed public comments about 'foreign influences' and the importance of Spanish tradition — clear indirect reference to Isabel's Portuguese attendants. Juan responds with a masterful speech: praises Isabel's piety, confesses he initially worried about their traditions conflicting, testifies to her genuine devotion and their shared faith, publicly announces commissioning a Portuguese-style chapel for her comfort. Raises toast to Isabel, rallying the entire room. Capranica forced into graceful retreat, acknowledging 'excessive caution.' The Portuguese ladies' position is publicly secured. Roll: 83 (Public Pressure) — determined Capranica's approach.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "cardinal_capranica",
            "alvaro_de_luna", "don_fadrique", "dona_beatriz"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["diplomacy", "personal", "marriage", "religion", "roll"],
    },
    {
        "msgs": (57, 62),
        "date": "1431-01-28",
        "type": "diplomacy",
        "summary": "Juan visits Capranica the morning after the dinner with a welcome gift: a rare 12th-century illuminated Decretum Gratiani manuscript from Bologna's original school of canon law. Capranica is genuinely astonished and deeply moved — the scholarly gift shows understanding of him as a person, not just his position. He apologizes sincerely for overstepping on the Portuguese ladies matter, admitting he confuses guidance with control. Juan responds with grace, stressing their partnership and his open door. The relationship emerges stronger: Capranica now loyal from genuine respect rather than obligation. He promises to write the Pope praising Juan's wisdom.",
        "characters": [
            "juan_ii", "cardinal_capranica", "alvaro_de_luna"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["diplomacy", "personal", "religion"],
    },
    {
        "msgs": (63, 70),
        "date": "1431-01-28",
        "end_date": "1431-02-14",
        "type": "decision",
        "summary": "Strategic assessment of noble response to upcoming crusade taxation. Roll: 45 (Quiet Compliance with Grumbling) — nobles accept the tax but complain privately. They'll comply with assessments but won't be happy; some minor foot-dragging on records expected but nothing organized. The oversight committee will need firmness but won't face serious resistance. In the 18 days before the wedding, Toledo fills with arriving noble families, assessment teams are finalized, the Portuguese chapel remodeling begins, crusader numbers approach 200, and a few great houses (Mendoza, Guzmán) request private audiences seeking 'clarity' on tax details.",
        "characters": [
            "juan_ii", "alvaro_de_luna"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["taxation", "politics", "planning", "roll"],
    },
]

NEW_CHARACTERS = [
    {
        "id": "tommaso_parentucelli",
        "name": "Father Tommaso Parentucelli",
        "aliases": ["tommaso_parentucelli", "parentucelli", "father_tommaso"],
        "title": "Papal Administrator to the Legate",
        "born": "1391-00-00",
        "status": ["active"],
        "category": ["papal_court"],
        "location": "Toledo",
        "current_task": "Serving as Cardinal Capranica's administrator; developed outstanding working relationship with Álvaro on crusade budget management; prepared formal budget documents and assessment team letters of authority",
        "personality": ["practical", "efficient", "ink_stained", "detail_oriented"],
        "interests": ["administration", "financial management", "documentation", "logistics"],
        "speech_style": "Practical and matter-of-fact; speaks up when he has useful information; ever-present writing materials",
        "core_characteristics": "Italian priest serving as Cardinal Capranica's administrator, approximately 40 years old. Practical-minded and focused on results rather than procedure, contrasting with his Cardinal's obsessive formality. His excellent working relationship with Álvaro de Luna (roll: 77) created the comprehensive 47-page campaign budget and provides a functional channel between crown and legate even when leaders clash. Always has writing materials at hand.",
        "faction_ids": [],
        "appearance": {
            "build": "average",
            "age_appearance": "about 40",
            "distinguishing_features": "ink-stained hands",
        },
    },
    {
        "id": "dona_beatriz",
        "name": "Doña Beatriz",
        "aliases": ["dona_beatriz", "beatriz", "beatriz_portugal"],
        "title": "Lady-in-Waiting to Queen Isabel",
        "born": "1391-00-00",
        "status": ["active"],
        "category": ["household"],
        "location": "Toledo",
        "current_task": "Serving as senior lady-in-waiting to Queen Isabel; under crown protection after Cardinal Capranica's attempt to dismiss the Portuguese attendants",
        "personality": ["dignified", "composed", "loyal", "devout"],
        "interests": ["faith", "Portuguese devotions", "service to the Queen"],
        "speech_style": "Quiet and dignified; speaks with careful courtesy; emotional when her loyalty and faith are questioned",
        "core_characteristics": "Approximately 40 years old, from an old Portuguese noble house. Senior among Isabel's three Portuguese ladies-in-waiting who sailed with her from Portugal. Deeply devout Catholic who follows the Roman breviary with Portuguese traditional devotions (Our Lady of the Conception, feast of Saint Vincent). Her composure and dignity helped defuse the Cardinal's challenge to the Portuguese attendants' presence at court.",
        "faction_ids": ["royal_court"],
        "appearance": {
            "age_appearance": "about 40",
            "bearing": "dignified noble bearing",
        },
    },
    {
        "id": "don_fadrique",
        "name": "Don Fadrique",
        "aliases": ["don_fadrique"],
        "title": "Head of the Toledo Family",
        "born": "1380-00-00",
        "status": ["active"],
        "category": ["nobility"],
        "location": "Toledo",
        "current_task": "Attending court in Toledo for the royal wedding; supported Isabel publicly at the Archbishop's dinner",
        "personality": ["supportive", "shrewd"],
        "interests": ["Toledo politics", "court affairs"],
        "speech_style": "Direct and supportive; speaks up at key moments",
        "core_characteristics": "Head of the powerful Toledo family. Publicly supported Isabel at the Archbishop's dinner, declaring 'Castile is blessed in its Queen!' Appears to be aligned with the crown's interests.",
        "faction_ids": [],
        "appearance": {},
    },
]

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "In Toledo preparing for February 15 wedding; budget approved; managing Cardinal Capranica relationship; crusade taxation framework established",
        "location": "Toledo",
    },
    {
        "id": "isabel_of_portugal",
        "current_task": "In Toledo preparing for wedding; Portuguese ladies retained under crown protection; growing confidence; publicly embraced by Toledo nobility",
        "location": "Toledo",
    },
    {
        "id": "cardinal_capranica",
        "current_task": "Preparing to officiate royal wedding February 15; relationship with Juan tested but restored after Portuguese ladies overreach; loyal from genuine respect",
        "personality": {"add": ["chastened"]},
        "location": "Toledo",
    },
    {
        "id": "alvaro_de_luna",
        "current_task": "Finalizing assessment teams and letters of authority for crusade taxation; managing wedding logistics and noble arrivals",
        "location": "Toledo",
    },
    {
        "id": "archbishop_cerezuela",
        "current_task": "Serving on crusade oversight committee; hosted dinner for Toledo nobility; supporting crown-legate relations",
        "location": "Toledo",
    },
]

NEW_LOCATIONS = []
NEW_FACTIONS = []
FACTION_UPDATES = [
    {
        "faction_id": "royal_court",
        "member_ids": {"add": ["dona_beatriz", "tommaso_parentucelli"]},
        "description": "The royal court in Toledo now includes Cardinal Capranica's administrator Tommaso (working closely with Álvaro), and Isabel's Portuguese ladies-in-waiting under crown protection. Budget approved, taxation framework established, wedding preparations underway. Noble response to taxation expected to be compliant if grumbling.",
    },
]

ROLLS = [
    {
        "event_index": 1,
        "title": "End of Honeymoon with Cardinal Capranica",
        "context": "After weeks of productive cooperation, what event causes the inevitable tension between Juan II and Cardinal Capranica?",
        "roll_type": "chaos",
        "date": "1431-01-24",
        "rolled": 98,
        "outcome_range": "critical_failure",
        "outcome_label": "Breaking Point — Portuguese Ladies Dismissal",
        "outcome_detail": "Capranica demands Isabel dismiss her Portuguese ladies-in-waiting (Dona Beatriz, Dona Inês, Dona Catarina) and replace them with Spanish women he has selected. Massive overreach into royal household management — the papal bull grants no such authority. Creates serious crisis requiring careful diplomatic handling.",
        "evaluation": "Near-worst possible outcome. Capranica's overreach threatened both the Portuguese alliance and Isabel's personal wellbeing. However, Juan's established good relationship moderated the damage — what could have been a catastrophic break instead became a manageable crisis.",
        "success_factors": [],
        "failure_factors": ["Capranica's controlling nature", "Ambition to expand legatine authority", "Desire to place allies in Queen's household"],
    },
    {
        "event_index": 2,
        "title": "Cardinal's Response to Portuguese Ladies Resolution",
        "context": "After Juan blocks Capranica's demand through passive resistance and guard protection, how does the Cardinal react?",
        "roll_type": "diplomacy",
        "date": "1431-01-27",
        "rolled": 83,
        "outcome_range": "failure",
        "outcome_label": "Public Pressure at Dinner",
        "outcome_detail": "Capranica makes pointed public comments at a formal dinner about 'foreign influences' and Spanish tradition, clearly targeting the Portuguese attendants. Never names them directly but the implication is unmistakable. Forces Juan to respond publicly. Juan turns the moment into a triumphant speech praising Isabel's piety and announcing a Portuguese chapel commission.",
        "evaluation": "Capranica escalated to public pressure rather than accepting the situation privately. This backfired — Juan's masterful speech rallied the room behind Isabel and forced Capranica into a graceful retreat. The public nature of the resolution actually strengthened Juan's position.",
        "success_factors": [],
        "failure_factors": ["Capranica's wounded pride", "Unwillingness to accept private defeat", "Underestimation of Juan's public speaking ability"],
    },
    {
        "event_index": 0,
        "title": "Noble Response to Crusade Taxation",
        "context": "Castilian nobility learns that specific crusade taxation details (5% noble tax, 10% church tax) will be announced at the wedding. How do they respond in the weeks before the announcement?",
        "roll_type": "chaos",
        "date": "1431-01-28",
        "rolled": 45,
        "outcome_range": "mixed",
        "outcome_label": "Quiet Compliance with Grumbling",
        "outcome_detail": "Nobles accept the tax is happening but complain privately to each other. They'll comply with assessments but won't be happy. Some minor foot-dragging on producing records expected, but nothing organized. The oversight committee will need to be firm but won't face serious resistance. A few great houses (Mendoza, Guzmán) request private audiences seeking 'clarity' on tax details.",
        "evaluation": "Best realistic outcome given the unprecedented nature of direct crown taxation backed by papal authority. The combination of papal backing, popular crusade enthusiasm, absence of Infantes as opposition leaders, and personal service exemption all work to prevent organized resistance.",
        "success_factors": ["Papal authority behind taxation", "Popular crusade enthusiasm", "No opposition leader (Infantes eliminated)", "Personal service exemption offers honorable alternative"],
        "failure_factors": ["Sets precedent for crown taxation", "Assessment process threatening to nobles used to controlling own reporting"],
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
        "chapter": "1.11",
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
    print(f"Chapter 1.11 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Written to:        {OUTPUT}")

if __name__ == "__main__":
    main()
