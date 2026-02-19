#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.14.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.14_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.14_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 24),
        "date": "1431-02-22",
        "type": "military",
        "summary": "One week after wedding. Isabel relationship roll: 31 (Comfortable and Dutiful) — genuine fondness growing, feels safe and content, not fiery passion but steady warmth. Pregnancy roll: 52 (Early March Conception — will conceive ~4 weeks from now). Juan inspects crusader encampment outside Toledo: 267 sworn crusaders in Toledo (50 original + 217 new recruits), 101 in Seville, 368 total. Captain García Fernández reports 53 new arrivals this week, projecting 400 by month's end. Juan orders force division: Seville crusaders to western army under Rodrigo, Toledo crusaders to eastern army under banner. Emphasizes quality over quantity — only combat-ready men march in April, rest continue training and join in waves. Inspects artillery: Master Gunner Pietro Calabrese (Italian from Milan) commands 5 medium bombards with 30 crew. Juan redirects artillery from western to eastern army. Pietro needs extra oxen, infantry protection, weather-proof powder transport. Departure for Jaen: March 5-10, arrival by month's end.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "garcia_fernandez",
            "pietro_calabrese", "fray_hernando"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["military", "inspection", "artillery", "crusade", "personal", "roll"],
    },
    {
        "msgs": (25, 34),
        "date": "1431-02-22",
        "type": "diplomacy",
        "summary": "Meeting with Álvaro at the Alcázar. Rodrigo Manrique reports from Seville: 101 original crusaders in excellent shape, 27 new recruits accepted (of 43 applicants), total 128 in Seville, projecting 150-170 by April. Juan orders formal noble levy summons sent immediately with assembly deadline March 25 at staging areas — no staggered arrivals. Force targets confirmed: 12,000 western army (Seville), 23,000 eastern army (Jaen). 43 trained tax assessors deployed with dual mission: audit army spending and assess noble estate revenues. Treasury: 390,000 florins available. Juan announces travel plans: leave Toledo early March for Jaen with Isabel, brief visit to Seville, then return. Isabel stays with army until pregnancy confirmed, then returns to Toledo.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "rodrigo_manrique"
        ],
        "factions_affected": ["royal_court"],
        "location": "Toledo",
        "tags": ["diplomacy", "logistics", "planning", "taxation"],
    },
    {
        "msgs": (35, 40),
        "date": "1431-02-22",
        "type": "personal",
        "summary": "Afternoon with Isabel. They inspect the completed Portuguese chapel — Portuguese heraldry, saints, blue-and-white color scheme, private devotional shrine. Juan prays a deeply personal, vulnerable prayer: asks God's blessing on their marriage, the crusade, Isabel's comfort in a foreign land, and for children. Isabel is profoundly moved and prays her own response, then opens up about struggling to express emotions she was never taught to articulate. The shared vulnerability deepens their emotional connection significantly — moving beyond duty toward genuine intimacy of the heart.",
        "characters": [
            "juan_ii", "isabel_of_portugal"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["personal", "marriage", "religion", "emotional"],
    },
    {
        "msgs": (41, 48),
        "date": "1431-03-02",
        "end_date": "1431-03-07",
        "type": "personal",
        "summary": "Final weeks in Toledo: Juan trains daily in armor, building endurance to 6 hours in full harness. March 2: departure for Jaen. Roll: 99 (Exceptional Journey with Notable Event). Roll: 92 (The Letter from Portugal). Six-day journey through La Mancha and hill country. Isabel insists on riding horseback instead of wagon, proves herself a competent rider. Day 5: courier delivers letter from Isabel's mother, the Queen of Portugal. The Queen Mother reveals her own arranged marriage started cold but became deep love over 20 years. Advice: 'Do not hide yourself from Juan. Show him your true self. Love grows like a garden — plant seeds now.' Isabel reads the letter aloud to Juan, breaks down crying, and confesses all her hidden fears — fear of failing as queen, fear of not giving him a son, fear he deserved someone better. She asks him to know the 'real' Isabel. The moment fundamentally transforms their relationship from comfortable duty to genuine emotional partnership. Isabel conceived during this journey (early March, per pregnancy roll). Neither knows yet. Arrival at Jaen March 7.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "dona_beatriz",
            "alvaro_de_luna"
        ],
        "factions_affected": [],
        "location": "Jaen",
        "tags": ["personal", "journey", "marriage", "emotional", "roll"],
    },
    {
        "msgs": (49, 56),
        "date": "1431-03-07",
        "type": "military",
        "summary": "Eastern army briefing at Jaen with Don Pedro González de Padilla (Master of Calatrava). Status: ~3,000 troops present, full 23,000 expected by March 25. Military Orders committed: Calatrava 1,500 knights, Santiago 2,000, Alcántara 1,000. Four supply depots operational at Ciudad Real, Úbeda, Baeza, and Jaen. Intelligence: Granada concentrating forces westward and near Granada city, unaware of eastern offensive's full scale. 3,000 cavalry organized into six raiding columns of 500 each. Six surgeons contracted with field hospitals at each depot. Pietro's 5 bombards arriving late March. Strategy: drive toward Granada city, take fortresses to secure supply corridor, stay flexible. Pedro estimates 90-150 miles through mountains, 12+ significant fortresses; in 8 months could take 3-4 major positions pushing 40-60 miles deeper. Juan grants Pedro full command authority in his absence with formal letter. Infante Enrique must obey or face consequences. Pedro raises concern about Granada calling Ottoman/North African aid.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "alvaro_de_luna"
        ],
        "factions_affected": ["royal_court"],
        "location": "Jaen",
        "tags": ["military", "strategy", "briefing", "command"],
    },
    {
        "msgs": (57, 78),
        "date": "1431-03-08",
        "end_date": "1431-03-14",
        "type": "military",
        "summary": "Juan decides to ride to Seville for western army inspection, invites Isabel. Roll: 40 (Duty-Bound Single Volunteer) — Dona Catarina (age 23) volunteers to accompany Isabel out of duty; Dona Beatriz (54) physically unable, Maria and Ana decline as inadequate riders. Traveling party: 13 riders. Roll: 44 (Adequate Journey) — four-day ride March 8-11, first day hard but bodies adapt, workmanlike routine by day three, Catarina reveals dry humor. Arrival in Seville. Rodrigo Manrique briefs: ~1,800 troops present, 12,000 expected by March 25. Naval force: 12 Genoese combat galleys (38,400 florins), 10 transports (12,000 florins), 8 Portuguese dowry galleys — 30 ships total. 127 crusaders (projecting 160-170 by April). Coastal supply caches pre-positioned. Intelligence: Granada reinforcing western fortresses but doesn't realize full naval invasion planned. Meeting with Infante Juan de Aragon — profoundly transformed from proud rebel prince to humble, cooperative subordinate. Wearing simple crusader tabard. Juan calls him 'cousin,' officially designates him as part of Rodrigo's command. The Infante brings diplomatic skill, logistics experience, speaks Genoese dialect. Rodrigo establishes 'You follow my orders' — Infante accepts fully. Hour-long planning session proves command structure works.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "dona_catarina",
            "rodrigo_manrique", "infante_juan_de_aragon",
            "dona_beatriz", "enrique_enriquez"
        ],
        "factions_affected": ["royal_court"],
        "location": "Seville",
        "tags": ["military", "naval", "journey", "command", "roll"],
    },
    {
        "msgs": (79, 84),
        "date": "1431-03-12",
        "end_date": "1431-03-18",
        "type": "narrative",
        "summary": "Days in Seville (March 12-14): audiences with western nobles, visiting crusaders, dining with Genoese captains (Infante Juan invaluable as translator), meeting merchants. Personal time with Isabel: walking Alcázar gardens, evening prayers, exploring Seville's cathedral. Notable: Isabel's hand unconsciously moves to her belly during prayers — around time of conception but neither knows yet. Return journey to Jaen (March 15-18): four days, notably easier than westward trip. Both women more confident riders. Isabel suggests pushing the pace. Catarina opening up, becoming companion rather than servant. Arrive in good condition. Staging area has grown to 8,000-10,000 troops with more arriving daily. Seven days until March 25 assembly deadline. Campaign launch approximately two weeks away.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "dona_catarina",
            "infante_juan_de_aragon", "rodrigo_manrique"
        ],
        "factions_affected": [],
        "location": "Jaen",
        "tags": ["narrative", "journey", "preparation", "campaign"],
    },
]

NEW_CHARACTERS = [
    {
        "id": "pietro_calabrese",
        "name": "Master Pietro Calabrese",
        "aliases": ["pietro_calabrese", "pietro", "master_pietro"],
        "title": "Master Gunner",
        "born": "1381-00-00",
        "status": ["active"],
        "category": ["military", "artisan"],
        "location": "Toledo",
        "current_task": "Commanding 5 medium bombards with 30 gunners; preparing to march from Toledo to Jaen by March 5-10 for eastern army campaign; reassigned from western to eastern army",
        "personality": ["blunt", "professional", "demanding", "experienced"],
        "interests": ["artillery", "siege warfare", "gunpowder weapons", "engineering"],
        "speech_style": "Heavily accented Castilian (Italian native); blunt and direct; speaks with professional authority about his craft; does not mince words about tactical reality",
        "core_characteristics": "Italian master gunner from Milan, hired at considerable expense. Approximately 50 years old with burn scars on forearms from decades of work with powder. Missing several teeth, squinting eyes from years of bright flashes. Commands 5 medium bombards (50-pound stone balls, 300-400 yard range) with crews of 6 each plus 2 assistant master gunners. Demands: extra oxen (10 per gun), guaranteed infantry protection, weather-protected powder transport, good reconnaissance, and authority to refuse tactically unsound operations. Quote: 'Use us well, and we win you fortresses. Use us badly, and you lose everything.'",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "about 50",
            "build": "stocky",
            "hair": "grey",
            "distinguishing_features": "burn scars on forearms; missing teeth; squinting eyes from powder flashes",
        },
    },
    {
        "id": "dona_catarina",
        "name": "Dona Catarina",
        "aliases": ["dona_catarina", "catarina"],
        "title": "Portuguese Lady-in-Waiting to Queen Isabel",
        "born": "1408-00-00",
        "status": ["active"],
        "category": ["court"],
        "location": "Jaen",
        "current_task": "Accompanying Queen Isabel on horseback journeys between Jaen and Seville; evolving from dutiful attendant to genuine companion; the only lady-in-waiting physically capable of riding with the army",
        "personality": ["dutiful", "reserved", "competent", "dry_humor"],
        "interests": ["horsemanship", "service to Isabel", "quiet observation"],
        "speech_style": "Reserved and formal initially; gradually reveals dry, understated humor when relaxed; practical rather than courtly",
        "core_characteristics": "Portuguese lady-in-waiting to Queen Isabel, age 23. Dark-haired, slender, more athletic build than the other ladies. Competent rider (grew up near the Portuguese coast). Volunteered out of obligation rather than enthusiasm to accompany Isabel on the hard ride to Seville when Dona Beatriz was physically unable and the younger ladies were inadequate riders. Over the journey, her relationship with Isabel evolved from servant to companion. Her dry humor emerged as she grew more comfortable with the informal military travel.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "about 23",
            "build": "slender and athletic",
            "hair": "dark",
            "distinguishing_features": "athletic build unusual among court ladies",
        },
    },
]

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "At Jaen staging area with Isabel; eastern army assembling (8,000-10,000 troops, 23,000 expected by March 25); western army inspected in Seville; campaign launch ~2 weeks away; training daily in armor (6-hour endurance achieved)",
        "location": "Jaen",
    },
    {
        "id": "isabel_of_portugal",
        "title": "Queen of Castile",
        "current_task": "Traveling with the army; conceived in early March (unaware yet); relationship with Juan transformed after reading mother's letter — moved from comfortable duty to genuine emotional partnership; riding horseback competently; will return to Toledo when pregnancy confirmed",
        "location": "Jaen",
    },
    {
        "id": "alvaro_de_luna",
        "current_task": "Coordinating campaign launch logistics; noble levy summons issued (March 25 deadline); 43 tax assessors deployed; managing correspondence between Toledo, Jaen, and Seville staging areas",
        "location": "Jaen",
    },
    {
        "id": "garcia_fernandez",
        "current_task": "Promoted to crusader training commander in Toledo; preparing 300+ combat-ready crusaders for April march; screening new recruits with Fray Hernando; managing training pipeline with waves joining later",
        "location": "Toledo",
    },
    {
        "id": "pedro_gonzalez_de_padilla",
        "current_task": "Granted full command authority over eastern army (23,000) in Juan's absence; formal letter issued; managing assembly at Jaen staging area (8,000-10,000 troops present); coordinating supply depots, cavalry columns, and field hospitals; authorized to command Infante Enrique",
        "location": "Jaen",
    },
    {
        "id": "infante_juan_de_aragon",
        "current_task": "Formally appointed senior advisor to Rodrigo Manrique's western army command; profoundly transformed — wearing simple crusader tabard, fully cooperative, accepts subordinate role; brings diplomatic skill, logistics experience, and Genoese dialect to amphibious operations",
        "personality": {"remove": ["ambitious"], "add": ["humbled", "cooperative"]},
        "location": "Seville",
    },
    {
        "id": "rodrigo_manrique",
        "current_task": "Commanding western army (12,000 expected by March 25) at Seville; 30 ships assembled (12 Genoese galleys, 10 transports, 8 Portuguese dowry galleys); 127 crusaders; coastal supply caches pre-positioned; Infante Juan de Aragon accepted as subordinate advisor; needs 3-5 days after signal to finalize embarkation",
        "location": "Seville",
    },
    {
        "id": "dona_beatriz",
        "current_task": "Senior lady-in-waiting to Queen Isabel; physically unable to ride horseback on hard journeys (age ~54); remained at Jaen while Isabel traveled to Seville with Dona Catarina",
        "location": "Jaen",
    },
]

NEW_LOCATIONS = [
    {
        "location_id": "jaen",
        "name": "Jaen",
        "region": "Castile",
        "description": "Frontier city in southern Castile, staging area for the eastern crusade army. Fortress city commanding the mountain passes into Granada. Supply depots established at Jaen and satellite positions at Ciudad Real, Ubeda, and Baeza.",
        "sub_locations": [
            "Fortress of Jaen",
            "Eastern Army Staging Area",
            "Supply Depot"
        ],
    },
]

NEW_FACTIONS = []
FACTION_UPDATES = [
    {
        "faction_id": "royal_court",
        "description": "Campaign launch imminent. Two armies assembling: eastern (23,000 at Jaen under Master of Calatrava) and western (12,000 at Seville under Rodrigo Manrique with Infante Juan as advisor). Noble levy summons issued with March 25 deadline. 43 tax assessors deployed. Treasury: 390,000 florins. 5 bombards assigned to eastern army. Both Infantes formally serving — Juan transformed and cooperative, Enrique subdued but compliant.",
    },
]

ROLLS = [
    {
        "event_index": 0,
        "title": "Isabel's Emotional Response to Married Life",
        "context": "Isabel of Portugal (age 15) and Juan II (age 18) have been married one week. Juan has been considerate and gentle. Isabel had developing feelings before the wedding (shared faith, evening prayers, garden moment). She is conventionally pious, dutiful, sheltered, plain (rolled 41 appearance). How does she respond emotionally to the intimate aspects of marriage?",
        "roll_type": "social",
        "date": "1431-02-22",
        "rolled": 31,
        "outcome_range": "31-50",
        "outcome_label": "Comfortable and Dutiful",
        "outcome_detail": "Isabel has adjusted well to married life. Physical intimacy is no longer strange or uncomfortable. She fulfills her duties willingly and finds comfort in Juan's affection. Not overwhelming passion, but genuine growing fondness — steady warmth and trust. She feels safe with him, appreciates his gentleness. A solid foundation for their relationship. She tells him: 'I am content. More than content. You have been so kind to me.'",
        "evaluation": "Middle-range result reflecting a realistic arranged marriage. Not the fairy-tale love story, but a functional, warm partnership with room to grow. Consistent with Isabel's dutiful nature and sheltered upbringing.",
        "success_factors": ["Juan's consistent gentleness", "Shared faith foundation", "Pre-wedding emotional connection"],
        "failure_factors": ["Isabel's sheltered upbringing limits emotional expression", "Duty-oriented processing of feelings"],
    },
    {
        "event_index": 0,
        "title": "Isabel's Pregnancy Timeline",
        "context": "Both very young and healthy (15 and 18), frequent intimacy, good nutrition. Historical parallels suggest first pregnancy often within 3-6 months for healthy young royal couples. Stress of new marriage and country could delay slightly.",
        "roll_type": "personal",
        "date": "1431-02-22",
        "rolled": 52,
        "outcome_range": "36-60",
        "outcome_label": "Early March Conception",
        "outcome_detail": "Isabel conceives in early March, about 4-5 weeks after the wedding. By April she misses her first period; by May she's missed two and experiencing clear symptoms: nausea, fatigue, breast changes. She tells Juan in late April/early May, around 8-10 weeks pregnant. Confirmed pregnancy well before crusade departure.",
        "evaluation": "Historically typical timing. Neither too fast nor delayed. Provides clear narrative beat — pregnancy confirmed as campaign is underway.",
        "success_factors": ["Youth and health of both partners", "Frequent intimacy", "Good nutrition"],
        "failure_factors": [],
    },
    {
        "event_index": 3,
        "title": "Toledo to Jaen Journey",
        "context": "Six-day journey from Toledo to Jaen (March 2-7, 1431). Juan travels with Isabel, Alvaro, household guard, and attendants. Isabel has never traveled this far from a palace/convent. Route passes through La Mancha plains and hill country into frontier territory.",
        "roll_type": "travel",
        "date": "1431-03-02",
        "rolled": 99,
        "outcome_range": "96-100",
        "outcome_label": "Exceptional Journey with Notable Event",
        "outcome_detail": "The journey exceeds all expectations. Isabel insists on riding horseback instead of the wagon, proving herself a competent and determined rider. The open road brings out strength neither knew she had. A transformative event occurs during the journey that fundamentally alters the relationship between Juan and Isabel.",
        "evaluation": "Near-perfect roll creating a pivotal narrative moment. The journey itself becomes a crucible for character development.",
        "success_factors": ["Good weather", "Well-planned route", "Isabel's hidden courage", "Privacy of the road"],
        "failure_factors": [],
    },
    {
        "event_index": 3,
        "title": "Transformative Event During Journey",
        "context": "Sub-roll to determine what notable event occurs during the exceptional journey (roll 99). Options ranged from battlefield discovery to bandit encounter to natural wonder to a significant letter.",
        "roll_type": "narrative",
        "date": "1431-03-06",
        "rolled": 92,
        "outcome_range": "86-95",
        "outcome_label": "The Letter from Portugal",
        "outcome_detail": "A courier delivers a letter from Isabel's mother, the Queen of Portugal. The Queen Mother reveals her own arranged marriage started cold but became deep love over 20 years. Her advice: 'Do not hide yourself from Juan. Show him your true self. Love grows like a garden — plant seeds now.' Isabel reads the letter aloud to Juan, breaks down crying, and confesses all her hidden fears: fear of failing as queen, fear of not giving him a son, fear he deserved someone better. She asks him to know the real Isabel, not just the dutiful surface. The moment fundamentally transforms their relationship.",
        "evaluation": "Powerful narrative result. The Queen Mother's letter serves as catalyst for Isabel to shed her protective shell of duty and show genuine vulnerability. Combined with the exceptional journey roll, this creates a pivotal relationship moment.",
        "success_factors": ["Privacy of the road (no court observers)", "Isabel's growing trust", "Mother's wisdom from lived experience"],
        "failure_factors": [],
    },
    {
        "event_index": 5,
        "title": "Portuguese Ladies' Response to Seville Ride",
        "context": "Juan invites Isabel to ride horseback to Seville (fast 4-day journey, no wagon). Isabel needs at least one lady-in-waiting. Four candidates: Dona Beatriz (54, senior, too old), Catarina (23, competent rider), Maria (19, poor rider), Ana (early 20s, adequate but not confident).",
        "roll_type": "social",
        "date": "1431-03-08",
        "rolled": 40,
        "outcome_range": "31-50",
        "outcome_label": "Duty-Bound Single Volunteer",
        "outcome_detail": "Dona Catarina (age 23) volunteers out of obligation rather than enthusiasm. She grew up near the Portuguese coast and is a competent rider, the most physically capable of the ladies. Dona Beatriz is physically unable (age 54). Maria and Ana decline as inadequate riders. Catarina approaches it as duty — she does not relish the hard ride but will not let her princess travel without a companion.",
        "evaluation": "Middle-range result. One volunteer, motivated by duty rather than excitement. Creates an interesting dynamic — Catarina and Isabel will bond over the shared ordeal of hard riding.",
        "success_factors": ["Catarina's riding competence", "Sense of duty to Isabel"],
        "failure_factors": ["Other ladies unable or unwilling", "Catarina not initially enthusiastic"],
    },
    {
        "event_index": 5,
        "title": "Jaen to Seville Journey",
        "context": "Four-day horseback ride from Jaen to Seville (March 8-11). Party of 13: Juan, Isabel, Catarina, 6 crusader guards, 4 household guards. Fast pace, sleeping in the field or at waypoints. Isabel's second long ride; Catarina's first hard journey.",
        "roll_type": "travel",
        "date": "1431-03-08",
        "rolled": 44,
        "outcome_range": "31-50",
        "outcome_label": "Adequate Journey — Building Stamina",
        "outcome_detail": "First day is hard on both women — saddle-sore, exhausted, not accustomed to the pace. But bodies adapt by day two. By day three, a workmanlike routine is established. Evening camps provide the better moments — Catarina shows dry humor when relaxed. They arrive in Seville late afternoon on day four, tired and dusty but intact. Not transformative, just successful.",
        "evaluation": "Solid middle result. The journey serves its purpose without drama. Both women prove they can handle hard riding, building confidence for future travel.",
        "success_factors": ["Prior riding experience", "Good weather", "Manageable pace"],
        "failure_factors": ["Physical toll of sustained riding", "Inexperience with military travel"],
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
        "chapter": "1.14",
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
    print(f"Chapter 1.14 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  New locations:     {len(NEW_LOCATIONS)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Written to:        {OUTPUT}")

if __name__ == "__main__":
    main()
