#!/usr/bin/env python3
"""One-shot extraction script for Chapter 1.19."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.19_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.19_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 14),
        "date": "1431-05-10",
        "type": "military",
        "summary": "Battle at Granada's Gates (La Higueruela). Juan rides with 300 elite cavalry to challenge Sultan, removes helmet. Sultan appears, shouts insults, launches full sortie. Roll 48: Full Sortie As Planned — 2,500-3,000 troops pour through the western gate. Roll 49: Adequate Execution of counter-trap — escort retreats to rally point, hidden infantry emerges (both groups, some timing issues), light cavalry responds. Escort takes 15 dead, ~25 wounded. Defensive line holds under pressure. Roll 70: Decisive Victory — trap springs well. Defensive line dominates, phased reinforcements create killing zones. Don Fadrique's 1,500 heavy cavalry delivers devastating hammer blow. Moorish formation fragments. Moroccan veterans (~250) retreat to gates in fighting square. Battle lasts ~12 minutes. Castilian casualties: 60-120 killed, 90-160 wounded. Moorish losses: 2,000-2,600 killed/wounded/captured incl. ~580 prisoners. Sultan's sortie force shattered.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "fadrique_enriquez",
            "fernan_alonso_de_robles", "rodrigo_de_perea",
            "garcia_lopez_de_padilla"
        ],
        "factions_affected": ["royal_court"],
        "location": "Granada",
        "tags": ["military", "battle", "counter_trap", "cavalry", "roll"],
    },
    {
        "msgs": (15, 26),
        "date": "1431-05-10",
        "end_date": "1431-05-20",
        "type": "military",
        "summary": "Battle aftermath and Vega devastation. Sultan watches from Alhambra as sortie force destroyed. Juan rides past the gates in triumph. Army systematically devastates Granada's Vega (fertile plain) on May 11 — crops burned, irrigation destroyed, orchards cut, mills demolished. Economic warfare to weaken Granada. Western army report: Roll 39 — Modest Success. Western army took TWO coastal positions (Velez-Malaga + Nerja) but progress slower than hoped without artillery. 163 dead, 254 wounded. 8,700 combat-effective. Strategic discussion: Juan decides to march to Loja, take it with bombards, then link up with western army to combine on Malaga. Messages sent to western army and Jaen for artillery.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "fadrique_enriquez",
            "alvaro_de_estuniga"
        ],
        "factions_affected": [],
        "location": "Granada",
        "tags": ["military", "devastation", "vega", "western_army", "strategy", "roll"],
    },
    {
        "msgs": (27, 42),
        "date": "1431-05-20",
        "end_date": "1431-05-29",
        "type": "military",
        "summary": "Wait for artillery at Alcala (May 21-25), bombards arrive from Jaen. War council plans Loja operation: Phase 1 march (2 days), Phase 2 investment (2-3 days), Phase 3 bombardment (2-3 weeks), Phase 4 assault. Army departs May 27 — 19,000 troops, 5 bombards, 200+ wagons. Roll 20: Significant Issue on march — guerrilla harassment costs 43 killed, 87 wounded en route. Army arrives Loja May 29 evening, tired but determined. Siege camp established.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "pietro_calabrese",
            "infante_enrique_de_aragon", "rodrigo_de_perea"
        ],
        "factions_affected": [],
        "location": "Loja",
        "tags": ["military", "march", "artillery", "guerrilla", "roll"],
    },
]

NEW_CHARACTERS = []

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "Arrived at Loja May 29 with 19,000 troops and 5 bombards. Won decisive battle at Granada's gates (May 10). Devastated the Vega (May 11). Army lost 43 killed, 87 wounded on march from guerrilla harassment. Preparing to besiege Loja fortress. Plans to link up with western army at Malaga after taking Loja.",
        "location": "Loja",
    },
    {
        "id": "fadrique_enriquez",
        "current_task": "Delivered devastating heavy cavalry hammer blow at Battle of Granada's Gates; 1,500 heavy cavalry shattered enemy formations. Now with eastern army at Loja.",
        "location": "Loja",
    },
    {
        "id": "alvaro_de_estuniga",
        "current_task": "Western army holds Velez-Malaga and Nerja; 8,700 combat-effective troops. Progress slower than hoped without artillery. Ordered to continue smaller coastal targets while awaiting junction with eastern army.",
        "location": "Velez-Malaga",
    },
    {
        "id": "pietro_calabrese",
        "current_task": "Bombards repaired and operational. Marched from Jaen to Alcala (arrived May 25). Now at Loja surveying bombardment positions. Needs 2-3 days prep before firing.",
        "location": "Loja",
    },
]

NEW_LOCATIONS = []
NEW_FACTIONS = []
FACTION_UPDATES = [
    {
        "faction_id": "royal_court",
        "description": "Decisive victory at Granada's gates (May 10) — sortie force destroyed, 580 prisoners. Vega devastated. Western army took 2 coastal fortresses. Eastern army at Loja with bombards, preparing siege. Plans: take Loja, then combine armies for Malaga.",
    },
]

ROLLS = [
    {
        "event_index": 0,
        "title": "Sultan's Response to Challenge",
        "context": "Juan rides to Granada's gates with 300 cavalry, removes helmet, challenges Sultan. Counter-trap set.",
        "roll_type": "military",
        "date": "1431-05-10",
        "rolled": 48,
        "outcome_range": "46-65",
        "outcome_label": "Full Sortie As Originally Planned",
        "outcome_detail": "Sultan launches complete sortie force of 2,500-3,000 as planned. Full commitment of prepared forces. Gates slam open, troops pour out.",
        "evaluation": "Middle result. Sultan commits fully as intercepted plans indicated. No surprises — the counter-trap can execute as designed.",
        "success_factors": ["Honor culture demands response", "Sultan already planned sortie", "Personal insults unbearable"],
        "failure_factors": [],
    },
    {
        "event_index": 0,
        "title": "Counter-Trap Opening Phase Execution",
        "context": "300 escort retreats to rally point. Hidden infantry must emerge. Light cavalry must respond. Coordination critical.",
        "roll_type": "military",
        "date": "1431-05-10",
        "rolled": 49,
        "outcome_range": "41-58",
        "outcome_label": "Adequate Execution",
        "outcome_detail": "Plan executes as designed with minor issues. Both flanking infantry groups emerge and form line. Light cavalry responds within timeframe. Escort takes 15 dead, ~25 wounded. Rally point reached in good order. Enemy advance checked but not disrupted.",
        "evaluation": "Adequate but not spectacular. The plan works but timing isn't perfect. Northern section of line was under pressure.",
        "success_factors": ["Rehearsed plan", "Disciplined troops", "Good positioning"],
        "failure_factors": ["Timing imperfect", "Northern group slower to form", "Enemy cavalry harassed retreat"],
    },
    {
        "event_index": 0,
        "title": "Battle Outcome — Sortie Engagement",
        "context": "Defensive line holding. 4,000 main infantry arriving. 1,500 heavy cavalry under Don Fadrique preparing hammer blow. Enemy committed with ~2,500 troops.",
        "roll_type": "military",
        "date": "1431-05-10",
        "rolled": 70,
        "outcome_range": "63-76",
        "outcome_label": "Decisive Victory — Trap Springs Well",
        "outcome_detail": "Defensive line dominates. Enemy realizes trap too late. Reinforcements arrive at perfect moments. Heavy cavalry charge crushes enemy. Castilian casualties 60-120 killed, 90-160 wounded. Moorish losses 2,000-2,600 killed/wounded/captured including ~580 prisoners. 150-500 escape. Decisive tactical victory.",
        "evaluation": "Strong result. The counter-trap works as designed. Sultan's military capability severely damaged. Campaign-significant victory.",
        "success_factors": ["Numerical superiority", "Phased reinforcement", "Heavy cavalry hammer", "Enemy trapped"],
        "failure_factors": ["Moroccan veterans (~250) escape in fighting square"],
    },
    {
        "event_index": 1,
        "title": "Western Army Operations (April-May 1431)",
        "context": "12,000 troops with naval support, no bombards, conducting coastal operations for 6 weeks.",
        "roll_type": "military",
        "date": "1431-05-10",
        "rolled": 39,
        "outcome_range": "29-42",
        "outcome_label": "Modest Success",
        "outcome_detail": "Two coastal positions taken: Velez-Malaga (major, 3 weeks siege) and Nerja (minor). Casualties 163 dead, 254 wounded. 8,700 combat-effective remain. Progress slower than hoped without artillery.",
        "evaluation": "Modest but solid. Without bombards, every siege takes weeks. Adequate foothold but reaching operational limits.",
        "success_factors": ["Naval supremacy", "Experienced commanders", "Sultan focused east"],
        "failure_factors": ["No artillery", "Slow traditional sieges", "Casualties moderate"],
    },
    {
        "event_index": 2,
        "title": "March to Loja",
        "context": "19,000 troops with 200+ wagons and 5 bombards march 25 miles SW from Alcala to Loja. Guerrilla fighters active.",
        "roll_type": "military",
        "date": "1431-05-27",
        "rolled": 20,
        "outcome_range": "13-24",
        "outcome_label": "Significant Issue",
        "outcome_detail": "Guerrilla harassment throughout march costs 43 killed, 87 wounded. Army arrives tired but intact on May 29 evening.",
        "evaluation": "Rough march. Guerrillas still dangerous despite being unable to stop the advance.",
        "success_factors": ["Army intact", "Bombards arrive safely"],
        "failure_factors": ["130 casualties from guerrillas", "Troops tired on arrival"],
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
    extraction = {"chapter": "1.19", "book": 1, "events": events, "new_characters": NEW_CHARACTERS,
                  "character_updates": CHARACTER_UPDATES, "new_locations": NEW_LOCATIONS,
                  "new_factions": NEW_FACTIONS, "faction_updates": FACTION_UPDATES,
                  "rolls": ROLLS, "law_references": LAW_REFERENCES}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(extraction, f, indent=2, ensure_ascii=False)
    total_exchanges = sum(len(e["exchanges"]) for e in events)
    print(f"Chapter 1.19: {len(events)} events, {total_exchanges} exchanges, {len(NEW_CHARACTERS)} new chars, {len(ROLLS)} rolls")

if __name__ == "__main__":
    main()
