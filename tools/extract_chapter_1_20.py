#!/usr/bin/env python3
"""One-shot extraction script for Chapter 1.20."""
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.20_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.20_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 14),
        "date": "1431-05-30",
        "end_date": "1431-06-02",
        "type": "military",
        "summary": "Siege of Loja begins. May 30: Juan meets scouts — Roll 59: Factional Conflict discovered. Bodies of 7 Moorish fighters found: 3 Granada regulars killed 4 Berber/North African allies (or vice versa). Evidence of internal coalition tensions between Sultan's local forces and foreign reinforcements. Calabrese surveys bombardment positions: 3 bombards at main gate (400 yards), 2 at eastern wall near postern gate. Needs 2-3 days to prepare. Siege lines planned to fully encircle. Surrender offer sent — Roll 41: Standard Refusal. Polite but firm rejection, garrison settles in for siege. Bombardment begins after preparations complete. Roll 92: RAPID BREACH — bombards perform exceptionally. Wall section collapses after just 3 days of bombardment. Major breach opened.",
        "characters": [
            "juan_ii", "pietro_calabrese", "pedro_gonzalez_de_padilla",
            "rodrigo_de_perea"
        ],
        "factions_affected": [],
        "location": "Loja",
        "tags": ["military", "siege", "bombardment", "roll", "intelligence"],
    },
    {
        "msgs": (15, 24),
        "date": "1431-06-03",
        "end_date": "1431-06-06",
        "type": "diplomacy",
        "summary": "Loja surrender negotiation. After rapid breach, garrison commander Qaid Yusuf ibn Musa comes out to negotiate. Roll 53: Accepts with Face-Saving Request. Yusuf asks for ceremonial surrender — garrison marches out in formation with banners flying, weapons shouldered, keys surrendered to Juan personally at the gates. Needs written safe-conduct in Juan's hand with royal seal. Juan agrees, gives 3 days. Bombardment halted. June 6: Formal surrender ceremony. 800 garrison marches out in perfect formation, Yusuf surrenders fortress keys. Juan pledges safe passage, no forced conversions, civilian protection. Garrison departs north toward Granada with honor. Loja taken in 7 days with zero assault casualties. Precedent set: honorable resistance meets honorable terms.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "fray_hernando",
            "qaid_yusuf_ibn_musa"
        ],
        "factions_affected": ["royal_court"],
        "location": "Loja",
        "tags": ["diplomacy", "surrender", "ceremony", "honor", "roll"],
    },
    {
        "msgs": (25, 50),
        "date": "1431-06-08",
        "end_date": "1431-06-14",
        "type": "military",
        "summary": "March from Loja to Malaga. Garcia Lopez de Padilla left commanding 600-man Loja garrison. Army of ~18,270 departs June 8 with bombards. Six-day march through rough mountain country. Light guerrilla harassment but nothing serious — Granada's field forces shattered. On June 12, contact with western army. June 13: Alvaro de Estuniga rides out to meet Juan. Armies unite — 30,000+ combined. June 14: Camp established on hills overlooking Malaga. City has 20,000 inhabitants, strong walls, Alcazaba fortress, Gibralfaro castle above. Harbor with ships. Combined strength: ~30,270 combat-effective plus 5 bombards. Chapter ends with armies before Malaga, greatest Castilian army in generations assembled.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "alvaro_de_estuniga",
            "fadrique_enriquez", "infante_enrique_de_aragon", "pietro_calabrese",
            "garcia_lopez_de_padilla", "rodrigo_de_perea"
        ],
        "factions_affected": [],
        "location": "Malaga",
        "tags": ["military", "march", "reunion", "combined_army"],
    },
]

NEW_CHARACTERS = [
    {
        "id": "qaid_yusuf_ibn_musa",
        "name": "Qaid Yusuf ibn Musa",
        "aliases": ["qaid_yusuf_ibn_musa", "qaid_yusuf", "yusuf_ibn_musa"],
        "title": "Former Commander of Loja Fortress",
        "born": "1381-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "En route to Granada",
        "current_task": "Departed Loja with 800-man garrison under safe-conduct after ceremonial surrender. Marching north to Granada. Professional soldier who negotiated face-saving terms.",
        "personality": ["professional", "pragmatic", "honorable", "experienced"],
        "interests": ["military duty", "honor", "garrison command"],
        "speech_style": "Professional, dignified. Speaks directly about military realities. Concerned with his men's honor.",
        "core_characteristics": "Experienced garrison commander. Gray-bearded veteran. Negotiated surrender of Loja after rapid breach made defense hopeless. Asked for ceremonial surrender to preserve his men's honor. First major fortress commander to surrender by negotiation rather than assault. His words to Juan: 'You have proven stronger. I ask that you remember your word.'",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "about 50",
            "build": "weathered soldier",
            "hair": "gray beard",
            "distinguishing_features": "experienced commander's bearing",
        },
    },
]

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "Before Malaga with 30,270 combined troops (eastern + western armies). Loja taken in 7 days with zero assault casualties. Ceremonial surrender precedent established. Preparing to besiege Malaga — Granada's second city, vital port.",
        "location": "Malaga",
    },
    {
        "id": "garcia_lopez_de_padilla",
        "current_task": "Left commanding 600-man garrison at Loja. Orders: keep order, protect civilians, begin wall repairs, establish supply lines from Alcala.",
        "location": "Loja",
    },
    {
        "id": "alvaro_de_estuniga",
        "current_task": "Western army reunited with eastern army at Malaga. Combined force 30,270. Took Velez-Malaga and Nerja during independent operations.",
        "location": "Malaga",
    },
    {
        "id": "pietro_calabrese",
        "current_task": "5 bombards operational at Malaga. Surveying positions for city bombardment. Experienced from rapid breach at Loja (3 days).",
        "location": "Malaga",
    },
]

NEW_LOCATIONS = [
    {
        "location_id": "malaga",
        "name": "Málaga",
        "region": "Granada coast",
        "description": "Granada's second city and vital Mediterranean port. Population ~20,000. Strong walls, Alcazaba fortress on hill within the city, Gibralfaro castle above. Harbor with ships. Combined Castilian army of 30,270 with 5 bombards assembled on hills NE of the city on June 14, 1431.",
        "sub_locations": ["Alcazaba Fortress", "Gibralfaro Castle", "City Walls", "Harbor", "Castilian Camp (NE hills)"],
    },
]

NEW_FACTIONS = []
FACTION_UPDATES = [
    {
        "faction_id": "royal_court",
        "description": "Loja taken in 7 days (June 6) — zero assault casualties, ceremonial surrender. Armies united before Malaga (June 14) — 30,270 combined with 5 bombards. Garrisons at Alcala la Real (1,500), Illora (800), Loja (600), Velez-Malaga (2,800), Nerja (500). Preparing siege of Granada's second city.",
    },
]

ROLLS = [
    {
        "event_index": 0,
        "title": "Scout Discovery at Loja",
        "context": "Scout patrol found dead Moorish fighters near Loja. Manner of death unusual.",
        "roll_type": "intelligence",
        "date": "1431-05-30",
        "rolled": 59,
        "outcome_range": "46-60",
        "outcome_label": "Factional Conflict",
        "outcome_detail": "Bodies killed by fellow Muslims — different tribal/regional insignia. Granada regulars vs North African allies. Evidence of coalition tensions between Sultan's local forces and foreign reinforcements.",
        "evaluation": "Significant intelligence. Exploitable political division within Granada's forces.",
        "success_factors": ["Active scouting"],
        "failure_factors": [],
    },
    {
        "event_index": 0,
        "title": "Loja Garrison Response to Surrender Offer",
        "context": "Formal surrender offer before bombardment. Strong fortress, recent defeats but garrison fresh.",
        "roll_type": "diplomacy",
        "date": "1431-06-01",
        "rolled": 41,
        "outcome_range": "26-70",
        "outcome_label": "Defiant Refusal — Standard Preparation",
        "outcome_detail": "Polite but firm rejection. Garrison settles into professional defensive preparation. No heroics, no provocations. Standard siege warfare.",
        "evaluation": "Expected outcome. Most likely result given honor culture and fortress strength.",
        "success_factors": [],
        "failure_factors": ["Honor demands resistance", "Fresh garrison", "Strong walls"],
    },
    {
        "event_index": 0,
        "title": "Bombardment Progress at Loja",
        "context": "5 bombards positioned at two points. Garrison of 800-1,000 in well-maintained fortress.",
        "roll_type": "military",
        "date": "1431-06-02",
        "rolled": 92,
        "outcome_range": "88-95",
        "outcome_label": "Rapid Breach",
        "outcome_detail": "Bombards perform exceptionally. Major wall section collapses after just 3 days of bombardment. Breach opened far faster than expected. Garrison's defensive calculations shattered.",
        "evaluation": "Outstanding result. Loja's walls couldn't withstand sustained bombardment. Rapid breach makes assault imminent, forcing surrender negotiation.",
        "success_factors": ["5 bombards concentrated fire", "Experienced crews", "Wall weakness identified"],
        "failure_factors": [],
    },
    {
        "event_index": 1,
        "title": "Loja Garrison Surrender Negotiation",
        "context": "Major breach opened. Garrison commander comes out to negotiate. Hopeless military situation.",
        "roll_type": "diplomacy",
        "date": "1431-06-03",
        "rolled": 53,
        "outcome_range": "46-62",
        "outcome_label": "Accepts with Face-Saving Request",
        "outcome_detail": "Commander accepts surrender but asks for ceremony: march out in formation with banners, surrender keys to Juan personally, written safe-conduct with royal seal. Needs to show his men they negotiated honorable terms. 3-day deadline.",
        "evaluation": "Good result. Fortress taken without assault. Costs nothing of substance but establishes powerful precedent.",
        "success_factors": ["Rapid breach made defense hopeless", "Juan's reputation for mercy", "Pragmatic commander"],
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
        event = {"date": edef["date"], "type": edef["type"], "summary": edef["summary"],
                 "characters": edef["characters"], "factions_affected": edef["factions_affected"],
                 "location": edef["location"], "tags": edef["tags"], "status": "resolved", "exchanges": exchanges}
        if "end_date" in edef:
            event["end_date"] = edef["end_date"]
        events.append(event)
    extraction = {"chapter": "1.20", "book": 1, "events": events, "new_characters": NEW_CHARACTERS,
                  "character_updates": CHARACTER_UPDATES, "new_locations": NEW_LOCATIONS,
                  "new_factions": NEW_FACTIONS, "faction_updates": FACTION_UPDATES,
                  "rolls": ROLLS, "law_references": LAW_REFERENCES}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(extraction, f, indent=2, ensure_ascii=False)
    total_exchanges = sum(len(e["exchanges"]) for e in events)
    print(f"Chapter 1.20: {len(events)} events, {total_exchanges} exchanges, {len(NEW_CHARACTERS)} new chars, {len(ROLLS)} rolls")

if __name__ == "__main__":
    main()
