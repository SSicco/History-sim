#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.17.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.17_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.17_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 18),
        "date": "1431-04-02",
        "type": "military",
        "summary": "Post-battle consolidation at Alcala la Real. Juan speaks with Enrique — siege works held with only ~30 casualties. Strategic discussion: Juan rejects mad dash toward Granada, opts for methodical fortress-by-fortress advance. Next target: Illora (12 miles NW, on road to Granada). Army split: Master of Calatrava takes 15,000 with bombards to besiege Illora at dawn; Enrique commands 5,000 reserve at Alcala. Juan and Alvaro will ride back to Jaen to coordinate all three armies (eastern siege, Alcala reserve, western coastal). Juan visits wounded Martín de Oviedo — fevered, barely conscious. Martin asks Juan to look after his daughters Maria (14) and Isabel (12) in Toledo. Juan promises.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "infante_enrique_de_aragon",
            "pedro_gonzalez_de_padilla", "martin_de_oviedo", "fray_hernando",
            "yusuf_ibn_rashid"
        ],
        "factions_affected": ["royal_court"],
        "location": "Alcala la Real",
        "tags": ["military", "strategy", "consolidation", "personal", "command"],
    },
    {
        "msgs": (19, 30),
        "date": "1431-04-02",
        "end_date": "1431-04-04",
        "type": "narrative",
        "summary": "Martín de Oviedo's survival roll: player rolled 83 (Strong Recovery) but deliberately chose to override with 5 (Death) for narrative drama. Martin will die within 3-4 days as infection overwhelms him. Last words to Juan: 'The blow was worth it. You'll be a great king. Tell my daughters their father died doing his duty. That he loved them.' Journey to Jaen: Roll 11 (Minor Incident). Sub-roll 81 (Bridge Out) — stone bridge collapsed from spring rains, 4-hour detour through ford. Juan and Alvaro arrive at Jaen mid-afternoon April 4.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "martin_de_oviedo"
        ],
        "factions_affected": [],
        "location": "Jaen",
        "tags": ["narrative", "death", "journey", "roll", "personal"],
    },
    {
        "msgs": (31, 38),
        "date": "1431-04-04",
        "type": "personal",
        "summary": "Reunion with Isabel at Jaen. She has been terrified during Juan's absence. Isabel reveals she may be pregnant — missed her courses for over a month since early March journey to Jaen. Could be stress but she is hopeful. Juan tells her it is 'everything we have hoped for.' They are intimate. Isabel mentions she will need to return to Toledo for safety when pregnancy confirmed but wants to stay at Jaen as long as possible. Juan tells Alvaro privately — Alvaro understands the immense political significance of an heir securing the succession.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "alvaro_de_luna"
        ],
        "factions_affected": [],
        "location": "Jaen",
        "tags": ["personal", "pregnancy", "marriage", "succession"],
    },
    {
        "msgs": (39, 44),
        "date": "1431-04-04",
        "end_date": "1431-04-07",
        "type": "military",
        "summary": "Western army dispatches from Alvaro de Estuniga. Roll 26: Moderate Success — One Major Objective. Fleet landed April 2 east of Velez-Malaga without opposition. Coastal defenses undermanned (~200). Beachhead: 23 dead, 41 wounded. Town fell within hours; garrison withdrew to citadel (400-500 defenders). By April 6, citadel surrendered after bombardment opened two breaches. Commander Muhammad al-Badisi requested terms: safe passage with personal weapons. Final casualties: 58 dead, 94 wounded. Military government established over town population (~2,000). Estuniga requests orders: press toward Malaga (major siege), consolidate Velez-Malaga, or sweep east along coast.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "alvaro_de_estuniga",
            "muhammad_al_badisi"
        ],
        "factions_affected": [],
        "location": "Jaen",
        "tags": ["military", "western_army", "naval", "siege", "roll"],
    },
    {
        "msgs": (45, 70),
        "date": "1431-04-03",
        "end_date": "1431-07-15",
        "type": "military",
        "summary": "Granada's response to catastrophe — multiple d100 rolls. Roll 27: Severe Crisis, Paralysis — court tears itself apart for 5 days, no decisions. Roll 82: Sultan's strategy — diplomatic offensive, four embassies to Aragon, Portugal, Navarre, Morocco. Roll 19: Diplomatic failure — all Christian powers politely refuse. Roll 19: Guerrilla campaign launched — Commander Yahya ibn Malik gathers ~800 light cavalry. Roll 53: Moderate guerrilla success — 180-200 Castilians killed, 7 supply convoys ambushed, 8-10 messengers killed, Illora siege delayed 2-3 weeks. Roll 68: Moderate Muslim support — Morocco commits 2,000-2,500 troops, 60-80k dinars from various sources. Roll 43: Mercenary recruitment — 3,000-4,000 hired at 140-170k dinars. Granada rebuilds to ~14,000 by mid-July (vs Castile ~33,000). Still outnumbered 2.4:1 but functional army again.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "yahya_ibn_malik"
        ],
        "factions_affected": ["royal_court"],
        "location": "Jaen",
        "tags": ["military", "diplomacy", "guerrilla", "intelligence", "roll"],
    },
    {
        "msgs": (71, 90),
        "date": "1431-04-10",
        "type": "political",
        "summary": "Landmark strategic discussion with Alvaro de Luna at Jaen. Topics: (1) Crusade going 'too well' — Juan worried emergency powers will end too quickly before reforms are implemented. Alvaro reassures: guerrilla resistance means longer campaign. (2) Taxation revolution: current noble rate effectively 1-2% based on 119-year-old assessments. Proposed: update to actual values (Phase 1, 1432), rationalize rates to 3-4% (Phase 2, 1433), raise to 5-6% (Phase 3, 1434+). New Granada estates at 3-4% as model. Final concept: 7-8% base rate with service credits (500 maravedis/month personal service, 2,000/100 men, max 50% reduction). (3) Land-to-naval power transformation — with Reconquista ending, noble military leverage obsolete. Naval power inherently centralized. Professional standing army of 5,000-8,000 replaces feudal levies. (4) The Perpetual Crusade Fund: nobles pay 8% into earmarked expansion fund for Africa, Canaries, Atlantic. Only active levy service grants exemption. Self-reinforcing cycle of expansion and glory. Increases permanent royal revenue by 6-8 million maravedis annually. Introduce at informal 'Council of Victory' after 1431 campaign, formalize at Cortes 1432.",
        "characters": [
            "juan_ii", "alvaro_de_luna"
        ],
        "factions_affected": ["royal_court"],
        "location": "Jaen",
        "tags": ["political", "taxation", "reform", "naval", "strategy"],
    },
    {
        "msgs": (91, 98),
        "date": "1431-04-10",
        "type": "diplomacy",
        "summary": "Letter to Pope Martin V and embassy to Rome. Official letter reports: Battle of Alcala (Sultan's army destroyed), fortress surrender with mass conversions, Velez-Malaga taken, multiple fortresses under siege. Personal letter from Juan pledges perpetual crusading beyond Granada — Africa, Ottomans, heresy — positioning himself as Christendom's preeminent secular champion. Asks Pope's blessing for Isabel. Embassy: Fray Hernando travels to Rome with Ahmad al-Zarqali — the converted qadi is living proof of the crusade's spiritual victories, a Muslim scholar who chose baptism freely after witnessing divine judgment. Will testify before Pope and cardinals. Alvaro notes: 'Artists will paint it. Chroniclers will write about it.'",
        "characters": [
            "juan_ii", "alvaro_de_luna", "fray_hernando", "ahmad_al_zarqali"
        ],
        "factions_affected": [],
        "location": "Jaen",
        "tags": ["diplomacy", "papal", "embassy", "religion", "propaganda"],
    },
]

NEW_CHARACTERS = [
    {
        "id": "alvaro_de_estuniga",
        "name": "Álvaro de Estúñiga",
        "aliases": ["alvaro_de_estuniga", "estuniga"],
        "title": "Commander of the Western Crusade Army",
        "born": "1390-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Velez-Malaga",
        "current_task": "Commanding western army (12,000 troops + 30 ships) after taking Velez-Malaga; citadel surrendered April 6; military government established; awaiting orders on next objective (Malaga, consolidation, or eastward sweep)",
        "personality": ["competent", "methodical", "professional"],
        "interests": ["military command", "naval operations", "siege warfare"],
        "speech_style": "Professional military dispatches. Clear, organized reporting.",
        "core_characteristics": "Commander of the western crusade army operating from Velez-Malaga. Successfully conducted amphibious landing and took the first major coastal objective. Reports via dispatches to Juan at Jaen. Awaiting further orders.",
        "faction_ids": [],
        "appearance": {},
    },
    {
        "id": "yahya_ibn_malik",
        "name": "Yahya ibn Malik",
        "aliases": ["yahya_ibn_malik", "yahya"],
        "title": "Granadan Guerrilla Commander",
        "born": "1386-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Granada frontier",
        "current_task": "Leading guerrilla cavalry campaign (~800 riders) against Castilian supply lines; causing real disruption — 180-200 Castilians killed, supply convoys ambushed, messengers killed, Illora siege delayed 2-3 weeks",
        "personality": ["cunning", "resourceful", "tenacious", "bitter"],
        "interests": ["guerrilla warfare", "cavalry tactics", "frontier survival"],
        "speech_style": "Sharp, bitter, practical. Speaks with the urgency of a man fighting a losing war with whatever means remain.",
        "core_characteristics": "Grizzled Granadan cavalry commander who barely escaped the Battle of Alcala la Real. While the Sultan's court was paralyzed by infighting, Yahya organized ~800 surviving light cavalry into guerrilla raiding parties of 10-50 riders. His campaign causes genuine disruption: supply lines hit, messengers killed, siege delayed. The smart play for an outnumbered defender.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "mid 40s",
            "build": "lean",
            "distinguishing_features": "grizzled veteran; barely escaped Alcala",
        },
    },
]

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "At Jaen coordinating three armies: eastern siege of Illora (15,000), Alcala reserve (5,000), western army at Velez-Malaga (12,000). Isabel likely pregnant. Conceiving grand taxation reform (7-8% + service credits) and Perpetual Crusade Fund (8% for expansion). Embassy to Rome being prepared. Letters sent to Pope Martin V. Martin de Oviedo's daughters now his responsibility.",
        "location": "Jaen",
    },
    {
        "id": "alvaro_de_luna",
        "current_task": "At Jaen as chief advisor; riding with Juan from Alcala; developing taxation reform plan and Perpetual Crusade Fund concept; coordinating three-army operations; stunned by Juan's naval power transformation insight",
        "location": "Jaen",
    },
    {
        "id": "infante_enrique_de_aragon",
        "current_task": "Commands 5,000 reserve troops at Alcala la Real; resting, tending wounded, securing area; ready to move on orders, possibly to reinforce western army",
        "location": "Alcala la Real",
    },
    {
        "id": "pedro_gonzalez_de_padilla",
        "current_task": "Leading 15,000 troops with bombards to besiege Illora (12 miles NW of Alcala la Real, on road to Granada); departing at dawn April 3",
        "location": "Illora",
    },
    {
        "id": "isabel_of_portugal",
        "current_task": "At Jaen; likely pregnant (missed courses for over a month since early March); terrified during Juan's absence at battle; will need to return to Toledo when pregnancy confirmed but wants to stay",
        "location": "Jaen",
    },
    {
        "id": "martin_de_oviedo",
        "status": ["deceased"],
        "current_task": "Died 3-4 days after the Battle of Alcala la Real from infection of neck/shoulder wound. Last words asked Juan to care for his daughters Maria (14) and Isabel (12) in Toledo. 'The blow was worth it. You'll be a great king.'",
        "location": "Alcala la Real",
    },
    {
        "id": "fray_hernando",
        "current_task": "Selected to lead embassy to Rome together with Ahmad al-Zarqali; will present the crusade's military and spiritual victories to Pope Martin V; also overseeing converts' instruction at Alcala before departure",
        "location": "Alcala la Real",
    },
    {
        "id": "ahmad_al_zarqali",
        "current_task": "Selected to accompany Fray Hernando to Rome as living proof of the crusade's spiritual victories — a Muslim scholar who chose baptism freely. Will testify before Pope and cardinals. Traveling with Fray Hernando for weeks, discussing theology",
        "location": "Alcala la Real",
    },
]

NEW_LOCATIONS = [
    {
        "location_id": "illora",
        "name": "Illora",
        "region": "Granada frontier",
        "description": "Granadan fortress 12 miles northwest of Alcala la Real, directly on the road to Granada city. Second target of the eastern crusade army's advance. Under siege by 15,000 Castilian troops with bombards under the Master of Calatrava. Siege delayed 2-3 weeks by guerrilla raids on supply lines.",
        "sub_locations": ["Fortress of Illora", "Siege Camp"],
    },
    {
        "location_id": "velez_malaga",
        "name": "Vélez-Málaga",
        "region": "Granada coast",
        "description": "Fortified coastal town east of Malaga taken by the western crusade army on April 2-6, 1431. First major coastal objective secured. Amphibious landing met minimal opposition. Citadel surrendered after 4 days of bombardment. Town population ~2,000 under Castilian military government. Strategic base for further coastal operations.",
        "sub_locations": ["Town", "Citadel", "Harbor/Beachhead"],
    },
]

NEW_FACTIONS = []
FACTION_UPDATES = [
    {
        "faction_id": "royal_court",
        "description": "Three-army coordination from Jaen. Eastern army (15,000) besieging Illora under Master of Calatrava. Reserve (5,000) at Alcala under Enrique. Western army (12,000) holds Velez-Malaga. Granada rebuilding army to ~14,000 by mid-July through Moroccan and mercenary support. Guerrilla raids causing real disruption. Grand taxation reform and Perpetual Crusade Fund being conceptualized. Embassy to Rome with converted qadi being prepared. Isabel likely pregnant.",
    },
]

ROLLS = [
    {
        "event_index": 1,
        "title": "Martín de Oviedo Survival",
        "context": "Guardian knight with deep neck/shoulder wound from Moroccan mamluk blade. Fever already present. Medieval infection mortality high. Strong will to live, immediate wound care, veteran constitution.",
        "roll_type": "personal",
        "date": "1431-04-02",
        "rolled": 5,
        "outcome_range": "01-15",
        "outcome_label": "Death",
        "outcome_detail": "Player actually rolled 83 (Strong Recovery) but deliberately chose to override with 5 for narrative drama. Martin dies within 3-4 days as infection overwhelms him. Last words ask Juan to care for daughters Maria (14) and Isabel (12). 'The blow was worth it. You'll be a great king.'",
        "evaluation": "Player-chosen narrative result. The actual roll of 83 would have meant recovery, but death was deemed more dramatically appropriate.",
        "success_factors": [],
        "failure_factors": ["Deep wound in vulnerable area", "Fever present", "Medieval medical limitations"],
    },
    {
        "event_index": 1,
        "title": "Journey Alcala to Jaen",
        "context": "Juan and Alvaro ride north to Jaen with ~20 riders. 20-mile journey through frontier territory. Spring weather.",
        "roll_type": "travel",
        "date": "1431-04-02",
        "rolled": 11,
        "outcome_range": "09-15",
        "outcome_label": "Minor Incident",
        "outcome_detail": "Sub-roll 81: Bridge Out. Stone bridge over swollen stream collapsed from spring rains. Village headman directs to ford 3 miles upstream. 4-hour detour. Water up to horses' bellies. Push through the night. Arrive Jaen mid-afternoon April 4.",
        "evaluation": "Minor inconvenience, no danger. Realistic spring travel complication.",
        "success_factors": ["Local knowledge of alternate crossing"],
        "failure_factors": ["Spring rains", "Bridge infrastructure"],
    },
    {
        "event_index": 3,
        "title": "Western Army Operations — First Week",
        "context": "Western army (12,000 troops + 30 ships) launches amphibious operations against Granada's coast. Sultan stripped western defenses to 2,000. Targets the coast east of Malaga.",
        "roll_type": "military",
        "date": "1431-04-02",
        "rolled": 26,
        "outcome_range": "17-28",
        "outcome_label": "Moderate Success — One Major Objective",
        "outcome_detail": "Fleet lands April 2 near Velez-Malaga. Minimal opposition (~200 defenders). Beachhead: 23 dead, 41 wounded. Town falls quickly; garrison (400-500) withdraws to citadel. By April 6, citadel surrenders after bombardment. Total: 58 dead, 94 wounded. Military government established.",
        "evaluation": "Solid but not spectacular. One major town taken with moderate casualties. Western front functional but not dominant.",
        "success_factors": ["Sultan stripped defenses", "Naval superiority", "Surprise"],
        "failure_factors": ["Moderate casualties", "Single objective only"],
    },
    {
        "event_index": 4,
        "title": "Granada's Internal Response to Catastrophe",
        "context": "News of Alcala disaster reaches Granada. Fewer than 3,000 of 16,000 return. Court reaction.",
        "roll_type": "political",
        "date": "1431-04-03",
        "rolled": 27,
        "outcome_range": "23-35",
        "outcome_label": "Severe Crisis — Paralysis",
        "outcome_detail": "Court tears itself apart for 5 days. Qadi of Granada (lost two sons) screams accusations. Commanders blame each other. Imams debate if God abandoned Granada. Mass conversions at Alcala create theological crisis. No decisions, no orders. Sultan barely imposes his will.",
        "evaluation": "Bad for Granada. Five days of paralysis while Castilians advance. Institutional collapse at worst possible time.",
        "success_factors": [],
        "failure_factors": ["Catastrophic military defeat", "Mass conversions", "Court infighting"],
    },
    {
        "event_index": 4,
        "title": "Sultan's Strategic Response",
        "context": "After 5 days of paralysis, Sultan Muhammad IX tries to act. What strategy does he adopt?",
        "roll_type": "diplomacy",
        "date": "1431-04-08",
        "rolled": 82,
        "outcome_range": "79-87",
        "outcome_label": "Diplomatic Offensive — Exploit Christian Divisions",
        "outcome_detail": "Four embassies dispatched: to Aragon (territorial concessions + 20,000 gold), Portugal (family ties through Isabel), Navarre (rivalry with Castile), Morocco (vassalage offered, Islamic obligation). Attempting to break Castilian momentum through diplomacy.",
        "evaluation": "Shrewd diplomatic thinking but from position of extreme weakness.",
        "success_factors": ["Multiple simultaneous approaches", "Playing on real rivalries"],
        "failure_factors": ["Extreme weakness", "Papal crusade backing", "Family ties favor Castile"],
    },
    {
        "event_index": 4,
        "title": "Diplomatic Success",
        "context": "Granada's four embassies reach Christian powers and Morocco. Will any respond favorably?",
        "roll_type": "diplomacy",
        "date": "1431-04-15",
        "rolled": 19,
        "outcome_range": "13-28",
        "outcome_label": "Minimal Response — Polite Refusals",
        "outcome_detail": "Aragon: 'Cannot interfere in Papal crusade.' Portugal: 'Will not undermine son-in-law's holy mission.' Navarre: 'No strategic interest.' Morocco: no response yet. Complete diplomatic failure — Granada stands alone.",
        "evaluation": "Low roll compounding Granada's problems. No Christian power willing to oppose a Papal crusade. Morocco is the only hope.",
        "success_factors": [],
        "failure_factors": ["Papal crusade legitimacy", "Family ties favor Castile", "No strategic incentive"],
    },
    {
        "event_index": 4,
        "title": "Granada's Broader Military Response",
        "context": "While court is paralyzed, what do surviving military commanders do on their own initiative?",
        "roll_type": "military",
        "date": "1431-04-10",
        "rolled": 19,
        "outcome_range": "19-30",
        "outcome_label": "Guerrilla Campaign Launched",
        "outcome_detail": "Commander Yahya ibn Malik gathers ~800 surviving light cavalry — Moroccan survivors, Granadan professionals, rearguard veterans. Splits into raiding parties of 10-50 targeting supply lines, foraging parties, messengers, isolated detachments.",
        "evaluation": "Smart response from surviving field commanders. Guerrilla warfare is the right strategy for an outnumbered defender.",
        "success_factors": ["Experienced cavalry survivors", "Knowledge of terrain", "Castilian supply line vulnerability"],
        "failure_factors": ["Limited numbers", "No infantry support", "Attrition unsustainable"],
    },
    {
        "event_index": 4,
        "title": "Guerrilla Campaign Effectiveness",
        "context": "Yahya ibn Malik's ~800 guerrilla cavalry operating against Castilian supply lines, foraging parties, and messengers. Two-week assessment.",
        "roll_type": "military",
        "date": "1431-04-25",
        "rolled": 53,
        "outcome_range": "39-54",
        "outcome_label": "Moderate Success — Real Disruption",
        "outcome_detail": "Week 1: tentative raids. Week 2: major convoy ambushed (28 killed), 6 messengers intercepted, night raid on Illora siege camp (30 casualties). Total: 180-200 Castilians killed, ~100 wounded. 7 convoys ambushed, 3 destroyed. Illora siege delayed 2-3 weeks. Granada lost 140 cavalry. Roads no longer safe.",
        "evaluation": "Surprisingly effective. Cannot change the strategic balance but makes the crusade significantly more costly and slower.",
        "success_factors": ["Terrain knowledge", "Light cavalry mobility", "Castilian overextension"],
        "failure_factors": ["Unsustainable attrition (140 of 800)", "Cannot prevent sieges, only delay"],
    },
    {
        "event_index": 4,
        "title": "Combined Muslim Foreign Support",
        "context": "Granada appeals to Muslim world — Morocco, Mamluks, Tunisia, other powers. What support arrives?",
        "roll_type": "diplomacy",
        "date": "1431-05-15",
        "rolled": 68,
        "outcome_range": "64-77",
        "outcome_label": "Moderate Support — Moroccan Commitment",
        "outcome_detail": "Morocco commits 2,000-2,500 professional troops in waves (first 800 arriving in 6-7 weeks). Financial aid: 60-80k dinars. Mamluks send weapons, armor, supplies, advisors. Tunisia sends 3-5 ships. Meaningful but not war-changing support.",
        "evaluation": "Moderate result. Enough to rebuild a functional army but not enough to challenge Castilian superiority directly.",
        "success_factors": ["Islamic solidarity", "Moroccan military capability"],
        "failure_factors": ["Distance", "Other commitments", "Castilian naval presence"],
    },
    {
        "event_index": 4,
        "title": "Mercenary Recruitment",
        "context": "Sultan spends 150-200k dinars on mercenary recruitment. Who answers the call?",
        "roll_type": "military",
        "date": "1431-05-15",
        "rolled": 43,
        "outcome_range": "36-50",
        "outcome_label": "Moderate Success — Decent Force",
        "outcome_detail": "3,000-4,000 mercenaries: 45% North African veterans, 30% Muslim volunteers, 25% Mediterranean professionals. Cost: 140-170k dinars. Average to good quality. Arrive in waves through mid-July. Full force assembled ~mid-July.",
        "evaluation": "Moderate result. Decent numbers but quality mixed. Combined with Moroccan troops, gives Granada ~14,000 by July.",
        "success_factors": ["Substantial funding", "Jihad motivation for volunteers"],
        "failure_factors": ["Quality variable", "Slow arrival", "Expensive"],
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
        "chapter": "1.17",
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
    print(f"Chapter 1.17 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  New locations:     {len(NEW_LOCATIONS)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Written to:        {OUTPUT}")

if __name__ == "__main__":
    main()
