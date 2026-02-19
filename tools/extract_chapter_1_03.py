#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.03.

Reads tools/preprocessed/chapter_1.03_preprocessed.json and produces
tools/extractions/chapter_1.03_extracted.json in the schema expected
by merge_chapter.py.

Event boundaries and metadata are manually determined from reading the
chapter content.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.03_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.03_extracted.json"

# -----------------------------------------------------------------------
# Event definitions
# -----------------------------------------------------------------------

EVENT_DEFS = [
    {
        "msgs": (1, 4),
        "date": "1430-05-15",
        "end_date": "1430-06-02",
        "type": "decision",
        "summary": "Juan II and his pilgrimage party travel from near Valladolid to Santiago de Compostela. A great success roll means the journey goes exceptionally well: warm receptions in Palencia and León, the common people demonstrating genuine affection for the young king, intelligence gathered about noble feuds affecting commoners, and the party arriving in Santiago with stronger bonds and growing popular support.",
        "characters": [
            "juan_ii", "fernan_alonso_de_robles", "fray_hernando",
            "sergeant_garcia", "corporal_rodrigo"
        ],
        "factions_affected": [],
        "location": "Santiago de Compostela",
        "tags": ["travel", "pilgrimage", "roll"],
    },
    {
        "msgs": (5, 12),
        "date": "1430-06-03",
        "end_date": "1430-06-05",
        "type": "decision",
        "summary": "At Santiago, Juan reveals the Rome plan to Captain Fernán and Fray Hernando. They decide on the overland route through France (6-7 weeks) rather than the risky sea voyage. The party is slimmed to 10 people: Juan, Fernán, Fray Hernando, Sergeant García, Corporal Rodrigo, two guards (Martín, Felipe), a secretary (Diego), and newly hired Sir Thomas Beaumont — an English knight who joins for honor and provisions. Juan sends three letters to Álvaro: a public announcement, a sealed letter revealing Rome as the destination, and a private ciphered strategic letter.",
        "characters": [
            "juan_ii", "fernan_alonso_de_robles", "fray_hernando",
            "thomas_beaumont", "alvaro_de_luna"
        ],
        "factions_affected": ["royal_court"],
        "location": "Santiago de Compostela",
        "tags": ["planning", "strategy"],
    },
    {
        "msgs": (13, 16),
        "date": "1430-06-05",
        "end_date": "1430-07-24",
        "type": "decision",
        "summary": "The lean party of 10 travels overland from Santiago through Navarre (a tense crossing through Infante Juan's kingdom), France, and Italy to Rome. Key stops: Archbishop of Toulouse provides a letter of recommendation; Cardinal Pierre de Foix at Avignon gives two letters including a private introduction to Cardinal Orsini; a mercenary captain offers future Italian swords; letters from Álvaro catch up warning that Infante Juan portrays the king as engaged in 'mystical wanderings.' The party sails from Genoa and arrives in Rome on July 24. Success roll — journey achieves its goals with manageable complications.",
        "characters": [
            "juan_ii", "fernan_alonso_de_robles", "fray_hernando",
            "thomas_beaumont", "sergeant_garcia", "corporal_rodrigo"
        ],
        "factions_affected": [],
        "location": "Rome",
        "tags": ["travel", "diplomacy", "roll"],
    },
    {
        "msgs": (17, 46),
        "date": "1430-07-24",
        "end_date": "1430-07-27",
        "type": "diplomacy",
        "summary": "Juan discusses crusade strategy with his companions, then presents himself at the Vatican. Cardinal Giordano Orsini, Pope Martin V's closest advisor, receives Juan for a private meeting. Juan takes an approach of radical honesty — admitting both political and spiritual motivations, describing his 'feelings' and 'pulls,' and asking whether he's a fool or genuinely guided. Orsini neither endorses nor rejects, probing Juan's sincerity and testing his understanding of the Granada challenge. Status quo roll — Orsini finds Juan 'worth meeting' but doesn't commit, and arranges a papal audience.",
        "characters": [
            "juan_ii", "fray_hernando", "fernan_alonso_de_robles",
            "cardinal_orsini"
        ],
        "factions_affected": [],
        "location": "Vatican, Rome",
        "tags": ["diplomacy", "religion", "roll"],
    },
    {
        "msgs": (47, 64),
        "date": "1430-07-28",
        "end_date": "1430-07-30",
        "type": "decision",
        "summary": "Juan experiences intense spiritual struggle before the papal audience. In confession with Fray Hernando, he reveals an overwhelming sense of purpose about something he dares not name — a planned act before the Pope so profound that speaking it aloud might 'taint' it. Hernando probes the discernment question deeply: how to distinguish God's will from one's own desires. Juan weeps, wrestling with doubt, then achieves sudden clarity: 'I know what must be done.' Hernando is troubled by the rapid shift but accepts his king's resolve.",
        "characters": [
            "juan_ii", "fray_hernando"
        ],
        "factions_affected": [],
        "location": "Rome",
        "tags": ["religion", "personal", "crisis", "introspection"],
    },
    {
        "msgs": (65, 90),
        "date": "1430-07-31",
        "type": "diplomacy",
        "summary": "In the intimate papal audience chamber, Juan presents his worldly request (crusade bull) with radical honesty, then performs an unprecedented act: he removes his crown, jewelry, and clothing down to a loincloth, laying everything at Pope Martin V's feet with his father's sword inscribed 'Non Nobis Domine.' Kneeling in cruciform posture, he offers body and soul as God's servant. Pope Martin V, deeply moved, kneels beside Juan, accepts his offering, and commissions him to complete the Reconquista. Great success roll — the Pope grants a plenary crusade bull with sweeping provisions: sole command, call to all Christendom, Military Order obedience, crusade taxation, papal legate, 20,000 florins, sacred relics, and diplomatic pressure on Aragon.",
        "characters": [
            "juan_ii", "pope_martin_v", "cardinal_orsini",
            "fray_hernando", "fernan_alonso_de_robles"
        ],
        "factions_affected": [],
        "location": "Vatican, Rome",
        "tags": ["diplomacy", "religion", "crusade", "roll"],
    },
    {
        "msgs": (91, 124),
        "date": "1430-07-31",
        "end_date": "1430-08-01",
        "type": "decision",
        "summary": "After the papal audience, Juan discusses next steps with Cardinal Orsini and his companions. He decides to wear all-white garments that he won't clean beyond hygiene — stains of mud, blood, and dust will remain as honest testimony to how holy service marks a man. The Pope approves this symbolism. Juan plans to visit Florence and Pisa before sailing from Barcelona to Seville. Sir Thomas is given a seat on Juan's informal travel council. The crusade bull 'Inter Cetera Divinae Providentiae' is reviewed and approved, containing provisions for sole command, crusade taxation, Military Order reform, and terms for Granada after conquest.",
        "characters": [
            "juan_ii", "fray_hernando", "fernan_alonso_de_robles",
            "cardinal_orsini", "thomas_beaumont", "pope_martin_v"
        ],
        "factions_affected": ["royal_court"],
        "location": "Rome",
        "tags": ["planning", "religion", "crusade"],
    },
    {
        "msgs": (125, 150),
        "date": "1430-08-01",
        "end_date": "1430-08-02",
        "type": "diplomacy",
        "summary": "Pope Martin V and Juan pray together, share communion, and the Pope serves Mass with Juan as altar server. The crusade bull is formally signed and sealed with the Fisherman's Ring and papal lead seal. Juan receives two sacred relics: a fragment of the True Cross in a gold reliquary and a finger bone of Saint James in silver. He promises to return them after the crusade. In a wordless farewell, Juan takes the Pope's hand and looks him in the eye — both knowing Martin V may not live to see the crusade's outcome. Juan departs Rome for Florence at first light, carrying the bull, relics, and the weight of his commission.",
        "characters": [
            "juan_ii", "pope_martin_v", "cardinal_orsini",
            "fray_hernando", "fernan_alonso_de_robles", "thomas_beaumont"
        ],
        "factions_affected": [],
        "location": "Vatican, Rome",
        "tags": ["diplomacy", "religion", "crusade", "farewell"],
    },
]

# -----------------------------------------------------------------------
# New characters
# -----------------------------------------------------------------------

NEW_CHARACTERS = [
    {
        "id": "thomas_beaumont",
        "name": "Sir Thomas Beaumont",
        "aliases": ["thomas_beaumont", "sir_thomas", "the_english_knight"],
        "title": "Knight",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Traveling with Juan II",
        "current_task": "Serving as military escort and informal advisor on Juan II's Rome journey; given seat on travel council",
        "personality": ["experienced", "honorable", "eager", "capable"],
        "interests": ["combat", "travel", "military tactics"],
        "speech_style": "Practical English directness with chivalric courtesy",
        "core_characteristics": "English knight encountered at Santiago de Compostela, hired for honor and provisions rather than pay. Experienced with French roads from military service. Helped select horses and check equipment. Accompanied by his squire Peter. Proved valuable for his knowledge of European travel routes and combat experience.",
        "faction_ids": ["royal_court"],
        "appearance": {},
    },
    {
        "id": "cardinal_orsini",
        "name": "Cardinal Giordano Orsini",
        "aliases": ["cardinal_orsini", "orsini"],
        "title": "Cardinal",
        "born": "1365-00-00",
        "status": ["active"],
        "category": ["religious"],
        "location": "Vatican, Rome",
        "current_task": "Serving as Pope Martin V's closest advisor; facilitated Juan II's papal audience and crusade bull",
        "personality": ["sophisticated", "politically_astute", "discerning", "cautious"],
        "interests": ["papal politics", "Church diplomacy", "spiritual discernment"],
        "speech_style": "Fluent Castilian; probing and careful, with the measured tone of a man who has seen everything",
        "core_characteristics": "Pope Martin V's closest advisor, ~65 in 1430. Speaks fluent Castilian. Initially cautious about Juan II's mix of spiritual seeking and political calculation, but was profoundly moved by the act of renunciation before the Pope. Helped draft the crusade bull and offered to write to Spanish bishops about what he witnessed. Warned Juan about papal succession politics.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "mid-60s",
        },
    },
    {
        "id": "pope_martin_v",
        "name": "Pope Martin V",
        "aliases": ["pope_martin_v", "martin_v", "pope_martin", "holy_father"],
        "title": "Pope",
        "born": "1369-00-00",
        "status": ["active"],
        "category": ["religious"],
        "location": "Vatican, Rome",
        "current_task": "Granted crusade bull 'Inter Cetera Divinae Providentiae' to Juan II; nearing end of pontificate",
        "personality": ["sharp", "practical", "emotional_when_moved", "legacy_minded"],
        "interests": ["Church unity", "papal authority", "legacy"],
        "speech_style": "Formal papal register that breaks into genuine warmth when moved; speaks with authority of the Vicar of Christ",
        "core_characteristics": "Pope since 1417 (ended the Western Schism). Age 72 in 1430, frail but sharp-eyed. Deeply moved by Juan II's act of complete renunciation — knelt beside the young king and personally commissioned the crusade. Granted sweeping crusade bull with sole command, taxation authority, Military Order reform, 20,000 florins, sacred relics, and diplomatic pressure on Aragon. Warned Juan to use these powers wisely.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "early 70s",
            "build": "frail",
            "distinguishing_features": "sharp, intelligent eyes despite age; trembling hands",
        },
    },
]

# -----------------------------------------------------------------------
# Character updates
# -----------------------------------------------------------------------

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "Received crusade bull from Pope Martin V; departing Rome for Florence, then Barcelona and Seville for the Royal Council",
        "personality": {"add": ["renunciant", "divinely_commissioned"]},
        "location": "Rome (departing for Florence)",
    },
    {
        "id": "fray_hernando",
        "current_task": "Accompanying Juan II; witnessed the act of renunciation before the Pope; serving as spiritual guide on the return journey",
        "location": "Rome (departing for Florence)",
    },
    {
        "id": "fernan_alonso_de_robles",
        "current_task": "Commanding Juan's lean travel party of 10; organizing the return journey through Italy and Barcelona",
        "location": "Rome (departing for Florence)",
    },
    {
        "id": "sergeant_garcia",
        "location": "Rome (departing for Florence)",
    },
    {
        "id": "corporal_rodrigo",
        "location": "Rome (departing for Florence)",
    },
    {
        "id": "alvaro_de_luna",
        "current_task": "Administering Castile during Juan's absence; sent letters warning that Infante Juan portrays the king as engaged in 'mystical wanderings'",
    },
    {
        "id": "infante_juan_de_aragon",
        "current_task": "Returned to his estates; writing letters to Castilian nobles claiming Juan has abandoned the realm for mystical wanderings",
    },
]

# -----------------------------------------------------------------------
# New locations
# -----------------------------------------------------------------------

NEW_LOCATIONS = [
    {
        "location_id": "santiago_de_compostela",
        "name": "Santiago de Compostela",
        "region": "Galicia",
        "description": "Major Christian pilgrimage destination in northwest Castile. Site of the shrine of Saint James. Archbishop provided letters of recommendation for Juan II's journey to Rome.",
        "sub_locations": ["Cathedral of Saint James"],
    },
    {
        "location_id": "rome",
        "name": "Rome",
        "region": "Papal States",
        "description": "Seat of the papacy and center of Western Christendom. Pope Martin V resides in the Vatican. Site of Juan II's dramatic act of renunciation and the granting of the crusade bull 'Inter Cetera Divinae Providentiae.'",
        "sub_locations": ["Vatican", "Papal Audience Chamber", "Monastery of Santa Maria in Trastevere"],
    },
]

# -----------------------------------------------------------------------
# New factions
# -----------------------------------------------------------------------

NEW_FACTIONS = []

# -----------------------------------------------------------------------
# Faction updates
# -----------------------------------------------------------------------

FACTION_UPDATES = [
    {
        "faction_id": "royal_court",
        "member_ids": {
            "add": ["thomas_beaumont"]
        },
    },
]

# -----------------------------------------------------------------------
# Rolls
# -----------------------------------------------------------------------

ROLLS = [
    {
        "event_index": 0,  # Journey to Santiago (0-indexed)
        "title": "Pilgrimage to Santiago",
        "context": "Juan II and his party of ~30 travel from near Valladolid through Castile to Santiago de Compostela. High probability of success given they travel in their own kingdom with a well-equipped royal escort.",
        "roll_type": "travel",
        "date": "1430-06-02",
        "rolled": None,
        "outcome_range": "critical_success",
        "outcome_label": "Great Success",
        "outcome_detail": "The journey goes exceptionally well. Warm receptions in Palencia and León, common people showing genuine affection. Intelligence gathered about noble feuds affecting commoners. Party arrives in Santiago with stronger bonds, growing popular support, and deeper understanding of the kingdom.",
        "evaluation": "Ideal conditions: own territory, established pilgrimage route, well-equipped guard, spring weather. The great success added popular goodwill and valuable intelligence.",
        "success_factors": [
            "Traveling in own kingdom",
            "Well-established pilgrimage route",
            "Professional guard escort",
            "Good weather (May-June)",
            "Recent demonstration of royal authority",
        ],
        "failure_factors": [
            "Infante Juan's hostility (newly removed)",
            "Political tensions among nobles",
        ],
    },
    {
        "event_index": 2,  # Journey to Rome (0-indexed)
        "title": "Overland Journey to Rome",
        "context": "A lean party of 10 travels from Santiago through Navarre, France, and Italy to Rome. Route through France is well-established but crosses Infante Juan's kingdom of Navarre.",
        "roll_type": "travel",
        "date": "1430-07-24",
        "rolled": None,
        "outcome_range": "success",
        "outcome_label": "Success",
        "outcome_detail": "The party arrives in Rome by late July with time for papal diplomacy. Letters of recommendation gathered from Toulouse and Avignon. Some complications: tense crossing through Navarre, a horse injury, and concerning letters from home about Infante Juan's propaganda campaign. But nothing derails the plan.",
        "evaluation": "Well-planned route with good letters of introduction. The complications (Navarre tension, horse injury) were manageable. Cardinal de Foix's private letter to Orsini proved invaluable.",
        "success_factors": [
            "Well-established route through France",
            "Summer travel season",
            "Sir Thomas's knowledge of French roads",
            "Strong letters of recommendation",
        ],
        "failure_factors": [
            "Navarre crossing through hostile territory",
            "Horse injury in Pyrenees",
            "Budget strain from replacement horse",
            "Infante Juan's intelligence networks",
        ],
    },
    {
        "event_index": 3,  # Orsini meeting (0-indexed)
        "title": "Cardinal Orsini Audience",
        "context": "Juan II meets Cardinal Giordano Orsini, Pope Martin V's closest advisor, using an approach of radical honesty about his spiritual and political motivations.",
        "roll_type": "persuasion",
        "date": "1430-07-27",
        "rolled": None,
        "outcome_range": "status_quo",
        "outcome_label": "Status Quo",
        "outcome_detail": "Orsini neither endorses nor rejects Juan's approach. He finds the young king 'worth meeting' and arranges a papal audience, but doesn't commit to supporting the crusade bull. He remains uncertain whether Juan is a genuine seeker or confused, but is intrigued enough to proceed.",
        "evaluation": "The radical honesty strategy was high-risk. Describing vague 'feelings' and 'pulls' could have seemed unstable, but Juan's sincerity and letters of recommendation earned him a chance. The status quo result is functional — it gets him before the Pope.",
        "success_factors": [
            "Radical honesty about mixed motives",
            "Strong letters of recommendation",
            "Fray Hernando's careful testimony",
            "Cardinal de Foix's private letter",
        ],
        "failure_factors": [
            "Vague description of spiritual experiences",
            "Youth and inexperience",
            "Mixing political calculation with spiritual seeking",
        ],
    },
    {
        "event_index": 5,  # Papal audience (0-indexed)
        "title": "Act of Renunciation Before the Pope",
        "context": "Juan II strips himself of crown, wealth, and clothing before Pope Martin V, offering body and soul as God's servant. An unprecedented act of complete submission and self-offering.",
        "roll_type": "persuasion",
        "date": "1430-07-31",
        "rolled": None,
        "outcome_range": "critical_success",
        "outcome_label": "Great Success",
        "outcome_detail": "Pope Martin V is profoundly moved — kneels beside Juan, accepts his offering, and personally commissions the crusade. Grants a sweeping crusade bull with sole command, call to all Christendom, Military Order obedience, crusade taxation authority, papal legate, 20,000 florins, sacred relics (True Cross fragment, Saint James bone), and diplomatic pressure on Aragon. The Pope embraces Juan and whispers: 'This was grace.'",
        "evaluation": "The unprecedented vulnerability transformed a political petition into a spiritual event. An 18-year-old king naked before the Pope, enacting the inscription 'Non Nobis Domine,' touched the dying pontiff's legacy instincts and genuine faith. Everything Juan had built — the letters, the honesty with Orsini, the spiritual struggles — culminated in this moment.",
        "success_factors": [
            "Unprecedented dramatic vulnerability",
            "Deep medieval Christian symbolism (kenosis)",
            "Sword inscription 'Non Nobis Domine' perfectly aligned",
            "Built on weeks of genuine spiritual seeking",
            "Pope's legacy motivation (aging, aware of mortality)",
            "Prior groundwork with Orsini",
        ],
        "failure_factors": [
            "Could have seemed unhinged or theatrical",
            "Fray Hernando's visible shock",
            "Extreme vulnerability in political context",
        ],
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

    # Build events
    events = []
    for edef in EVENT_DEFS:
        start, end = edef["msgs"]
        exchanges = []
        for idx in range(start, end + 1):
            if idx in msg_by_index:
                m = msg_by_index[idx]
                exchanges.append({
                    "role": m["role"],
                    "text": m["text"],
                })

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
        "chapter": "1.03",
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

    # Print stats
    total_exchanges = sum(len(e["exchanges"]) for e in events)
    print(f"Chapter 1.03 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  New locations:     {len(NEW_LOCATIONS)}")
    print(f"  New factions:      {len(NEW_FACTIONS)}")
    print(f"  Faction updates:   {len(FACTION_UPDATES)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Law references:    {len(LAW_REFERENCES)}")
    print(f"  Written to:        {OUTPUT}")


if __name__ == "__main__":
    main()
