#!/usr/bin/env python3
"""One-shot extraction script for Chapter 1.22."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.22_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.22_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 18),
        "date": "1431-07-10",
        "type": "military",
        "summary": "Western campaign launched. Master of Santiago appointed to lead 10,000 troops (7,000 infantry, 3,000 cavalry, 1,500 Military Order core) with all 5 bombards and 6 galleys westward. Full autonomy, reports to Juan. Calabrese goes with guns. Departs dawn July 10. Juan orders defensive posture: Estuniga commands Malaga, Rodrigo intensifies reconnaissance. Granada's response: Roll 86 — Sultan's Grand Strategy: Major Foreign Aid Appeal to Morocco. Roll 52 — Moroccan Aid: Modest Success — 2,500 troops arriving November, 120,000 gold dinars arriving September. Roll 57 — Sultan's Operational Strategy: Active Harassment Campaign — 1,500-2,500 light cavalry raiders deployed for systematic hit-and-run.",
        "characters": [
            "juan_ii", "alvaro_de_estuniga", "fadrique_enriquez",
            "pietro_calabrese", "rodrigo_de_perea"
        ],
        "factions_affected": ["royal_court"],
        "location": "Malaga",
        "tags": ["military", "command", "western_campaign", "granada_response", "roll"],
    },
    {
        "msgs": (19, 32),
        "date": "1431-07-26",
        "end_date": "1431-08-23",
        "type": "military",
        "summary": "Master of Santiago's first month: Roll 17 — Modest Progress with Difficulties. Marbella falls July 26 after fierce resistance (180 dead, 240 wounded). Supply convoy ambushed. Estepona under siege August 5, falls August 11 (85 dead, 120 wounded). Granada raiders continuously harass. 2 major + 3 minor fortresses taken, ~280 dead, 380 wounded. Behind schedule. Juan forms 3,000-cavalry counter-raiding force under Infante Enrique with scouts, ~40 Gibralfaro Muslim soldiers as intelligence assets, funds for informants. Orders: 'Be like a wolf, show no mercy.' Roll 6 — CAMPAIGN FAILURE. Enrique ambushed August 23 in hills west of Loja. 187 dead, 143 wounded. Enrique wounded (arrow in shoulder). Arabic-speaking scouts and informants killed or captured — intelligence network destroyed. Raiders emboldened, attacks INCREASE.",
        "characters": [
            "juan_ii", "infante_enrique_de_aragon", "rodrigo_de_perea"
        ],
        "factions_affected": [],
        "location": "Malaga",
        "tags": ["military", "western_campaign", "counter_raiding", "failure", "roll"],
    },
    {
        "msgs": (33, 68),
        "date": "1431-08-12",
        "end_date": "1431-08-25",
        "type": "personal",
        "summary": "Juan rides to Jaen, arrives August 12. Reunion with Queen Isabel — pregnant (~4-5 months, quickening felt 3 days prior). Emotional reunion. Juan tells her about the campaign. Discussion of converts and Moorish soldiers. Juan discusses vision of uniting all Iberian crowns (Castile, Aragon, Portugal, Navarre). Gift of carved Virgin Mary. Discussion of Isabel's Portuguese family (grandfather King Joao I, father Prince Duarte, siblings). Administrative actions: writes to Alvaro de Luna (Constable, in Toledo) ordering Cortes summoned to Jaen in November for land distribution and noble tax reform. Letters requesting crusade contributions from other Christian nations. Peaceful days August 13-25.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "alvaro_de_luna"
        ],
        "factions_affected": [],
        "location": "Jaen",
        "tags": ["personal", "pregnancy", "politics", "reform", "iberian_union"],
    },
    {
        "msgs": (69, 86),
        "date": "1431-08-25",
        "type": "military",
        "summary": "August 25: Urgent dispatch from Don Rodrigo. Enrique ambushed August 23 in hills west of Loja. 187 dead, 143 wounded. Enrique wounded (arrow in shoulder, survivable). Intelligence network destroyed — Arabic-speaking scouts killed or captured. Raiders emboldened, attacks increasing. Enrique requests Juan's direct intervention. Emotional farewell with Isabel — she decides to leave immediately for Toledo for safety and the birth (due January/February 1432). Juan prepares to ride south to the front. Chapter ends with Juan called back to war.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "infante_enrique_de_aragon",
            "rodrigo_de_perea"
        ],
        "factions_affected": [],
        "location": "Jaen",
        "tags": ["military", "crisis", "farewell", "personal"],
    },
]

NEW_CHARACTERS = []

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "Riding south from Jaen to salvage counter-raiding crisis after Enrique's catastrophic failure (roll 6). Isabel departing for Toledo. Cortes summoned for November. Campaign winning but bleeding — victories offset by guerrilla disruption, counter-raiding failure, Moroccan reinforcements coming November.",
        "location": "En route from Jaen to front",
    },
    {
        "id": "infante_enrique_de_aragon",
        "current_task": "Wounded (arrow in shoulder, survivable) from ambush August 23. Counter-raiding campaign catastrophically failed (roll 6). 330 casualties. Intelligence network destroyed. Requesting Juan's direct intervention.",
        "location": "Loja area",
    },
    {
        "id": "isabel_of_portugal",
        "current_task": "Departing Jaen for Toledo. Pregnant (~4-5 months, quickening felt). Due January/February 1432. Emotional farewell with Juan.",
        "location": "En route to Toledo",
    },
    {
        "id": "alvaro_de_luna",
        "current_task": "Constable, managing kingdom from Toledo. Ordered to summon Cortes to Jaen in November for land distribution and noble tax reform. Drafting foreign aid letters.",
        "location": "Toledo",
    },
    {
        "id": "alvaro_de_estuniga",
        "current_task": "Commands defensive forces at Malaga. Maintaining garrison and supply operations while Master of Santiago campaigns westward.",
        "location": "Malaga",
    },
    {
        "id": "pietro_calabrese",
        "current_task": "With Master of Santiago's western army, operating 5 bombards. Took Marbella and Estepona. Continuing coastal advance.",
        "location": "Western coast",
    },
]

NEW_LOCATIONS = [
    {
        "location_id": "marbella",
        "name": "Marbella",
        "region": "Granada coast",
        "description": "Coastal fortress west of Malaga. Taken July 26 after fierce resistance (180 dead, 240 wounded). Part of western coastal advance.",
        "sub_locations": [],
    },
    {
        "location_id": "estepona",
        "name": "Estepona",
        "region": "Granada coast",
        "description": "Coastal fortress further west, taken August 11 (85 dead, 120 wounded). Western army continuing advance toward Gibraltar.",
        "sub_locations": [],
    },
]

NEW_FACTIONS = []
FACTION_UPDATES = [
    {
        "faction_id": "royal_court",
        "description": "Campaign winning but grinding. Western army took Marbella + Estepona (roll 17 — modest progress, 660 casualties). Counter-raiding catastrophe (roll 6 — Enrique wounded, 330 casualties, intelligence network destroyed). Granada's active harassment with 1,500-2,500 raiders. Morocco committing 2,500 troops (November) + 120k dinars (September). Juan called back from Jaen to the front. Isabel departing for Toledo. Cortes summoned November.",
    },
]

ROLLS = [
    {
        "event_index": 0,
        "title": "Sultan's Grand Strategy",
        "context": "Sultan's response to losing Malaga — his second city and vital port. What does he do?",
        "roll_type": "diplomacy",
        "date": "1431-07-15",
        "rolled": 86,
        "outcome_range": "81-93",
        "outcome_label": "Major Foreign Aid Appeal",
        "outcome_detail": "Sultan sends desperate embassy to Morocco requesting massive military intervention. Also appeals to broader Muslim world.",
        "evaluation": "High roll giving Sultan a strong diplomatic play. Sets up Moroccan reinforcement as future complication.",
        "success_factors": ["Islamic solidarity", "Morocco's interest in Iberian affairs"],
        "failure_factors": ["Distance and logistics", "Morocco has own problems"],
    },
    {
        "event_index": 0,
        "title": "Moroccan Aid Response",
        "context": "Sultan's desperate appeal to Morocco for military aid after losing Malaga.",
        "roll_type": "diplomacy",
        "date": "1431-08-01",
        "rolled": 52,
        "outcome_range": "39-63",
        "outcome_label": "Modest Success",
        "outcome_detail": "Morocco commits 2,500 troops arriving November, plus 120,000 gold dinars arriving September. Meaningful but not overwhelming support.",
        "evaluation": "Moderate result. Enough to sustain Granada through winter but not enough to change strategic balance.",
        "success_factors": ["Islamic obligation", "Moroccan military capacity"],
        "failure_factors": ["Slow arrival timeline", "Limited numbers"],
    },
    {
        "event_index": 0,
        "title": "Sultan's Operational Strategy",
        "context": "While waiting for Moroccan reinforcements (November), what does Sultan do with remaining forces?",
        "roll_type": "military",
        "date": "1431-07-20",
        "rolled": 57,
        "outcome_range": "46-65",
        "outcome_label": "Active Harassment Campaign",
        "outcome_detail": "Sultan deploys 1,500-2,500 light cavalry raiders for systematic hit-and-run attacks on Castilian supply lines, foraging parties, and messengers.",
        "evaluation": "Smart asymmetric strategy. Cannot win battles but can bleed Castilian operations and delay the advance.",
        "success_factors": ["Light cavalry mobility", "Terrain knowledge", "Castilian supply line exposure"],
        "failure_factors": ["Unsustainable attrition", "Cannot prevent sieges"],
    },
    {
        "event_index": 1,
        "title": "Master of Santiago's First 30 Days",
        "context": "10,000 troops with 5 bombards advancing west along coast from Malaga. Taking fortresses.",
        "roll_type": "military",
        "date": "1431-08-11",
        "rolled": 17,
        "outcome_range": "11-25",
        "outcome_label": "Modest Progress with Difficulties",
        "outcome_detail": "Marbella falls July 26 (fierce, 180 dead, 240 wounded). Estepona falls August 11 (85 dead, 120 wounded). 2 major + 3 minor fortresses. Total ~280 dead, 380 wounded. Behind schedule. Raiders continuously harass supply lines.",
        "evaluation": "Below expectations. Coastal advance is working but at higher cost than hoped. Raiders a persistent problem.",
        "success_factors": ["Bombards available", "Experienced troops", "Naval support"],
        "failure_factors": ["Fierce resistance", "Raider harassment", "Casualties mounting"],
    },
    {
        "event_index": 1,
        "title": "Enrique's Counter-Raiding Campaign",
        "context": "3,000 cavalry force with scouts, Gibralfaro soldiers, and informant funds deployed to destroy guerrilla raiders.",
        "roll_type": "military",
        "date": "1431-08-23",
        "rolled": 6,
        "outcome_range": "01-10",
        "outcome_label": "Campaign Failure",
        "outcome_detail": "Enrique's force ambushed August 23 in hills west of Loja. 187 dead, 143 wounded (330 total). Enrique himself wounded (arrow in shoulder). Arabic-speaking scouts and informants killed or captured — entire intelligence network destroyed. Raiders emboldened, attacks INCREASE instead of decrease.",
        "evaluation": "Near-worst possible outcome. Campaign failure on every level — tactical, operational, intelligence. Sets back counter-guerrilla efforts severely.",
        "success_factors": [],
        "failure_factors": ["Ambush in unfamiliar terrain", "Intelligence failure", "Guerrilla expertise", "Enrique's inexperience with asymmetric warfare"],
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
    extraction = {"chapter": "1.22", "book": 1, "events": events, "new_characters": NEW_CHARACTERS,
                  "character_updates": CHARACTER_UPDATES, "new_locations": NEW_LOCATIONS,
                  "new_factions": NEW_FACTIONS, "faction_updates": FACTION_UPDATES,
                  "rolls": ROLLS, "law_references": LAW_REFERENCES}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(extraction, f, indent=2, ensure_ascii=False)
    total_exchanges = sum(len(e["exchanges"]) for e in events)
    print(f"Chapter 1.22: {len(events)} events, {total_exchanges} exchanges, {len(NEW_CHARACTERS)} new chars, {len(ROLLS)} rolls")

if __name__ == "__main__":
    main()
