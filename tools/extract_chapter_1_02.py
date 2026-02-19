#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.02.

Reads tools/preprocessed/chapter_1.02_preprocessed.json and produces
tools/extractions/chapter_1.02_extracted.json in the schema expected
by merge_chapter.py.

Event boundaries and metadata are manually determined from reading the
chapter content.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.02_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.02_extracted.json"

# -----------------------------------------------------------------------
# Event definitions: (start_msg, end_msg, metadata)
# Messages are player/gm pairs. start/end are inclusive message indices.
# -----------------------------------------------------------------------

EVENT_DEFS = [
    {
        "msgs": (1, 14),
        "date": "1430-05-06",
        "type": "council",
        "summary": "Juan II returns from Medina del Campo and assembles his secret advisory cabinet for the first time. Five members accept: Juan de Daza (treasury), Diego Gómez de Sandoval (court factions), Lope de Barrientos (Church networks), Íñigo López de Mendoza (Mendoza observer), and Rodrigo Manrique (frontier military). Juan challenges them with frank terms about danger and loyalty. Rodrigo provides a detailed briefing on the Granada frontier: 500 miles of low-intensity conflict, informal truces between frontier lords and Moors, and the reality that many nobles profit from perpetual war rather than actual conquest.",
        "characters": [
            "juan_ii", "juan_de_daza", "diego_gomez_de_sandoval",
            "rodrigo_manrique", "lope_de_barrientos", "inigo_lopez_de_mendoza"
        ],
        "factions_affected": ["royal_court"],
        "location": "Valladolid, Royal Palace",
        "tags": ["politics", "council", "military", "planning"],
    },
    {
        "msgs": (15, 26),
        "date": "1430-05-06",
        "type": "council",
        "summary": "The cabinet discusses Aragonese succession (Alfonso V has no heir; the Infantes are next in line), marriage alliances (Portugal safest, Aragon looks like capitulation), and foreign relations. Juan briefs them on the regency arrangement and his pilgrimage. The cabinet expresses alarm but accepts their role: serve Álvaro during Juan's absence and monitor the kingdom. They are told the details of Juan's plans but not the full Rome objective.",
        "characters": [
            "juan_ii", "juan_de_daza", "diego_gomez_de_sandoval",
            "rodrigo_manrique", "lope_de_barrientos",
            "inigo_lopez_de_mendoza", "alvaro_de_luna"
        ],
        "factions_affected": ["royal_court"],
        "location": "Valladolid, Royal Palace",
        "tags": ["politics", "strategy", "diplomacy"],
    },
    {
        "msgs": (27, 56),
        "date": "1430-05-07",
        "type": "decision",
        "summary": "Juan II enters the confessional with Fray Hernando for a deep conversation about faith, purpose, and political morality. Juan confesses he feels purpose — not peace — and asks Hernando to help discern God's voice from ambition. He reveals his intent to seek a crusade bull in Rome. Hernando warns about confusing personal ambition with divine calling, and challenges whether forced conversion serves God. Juan admits he's never heard anything beyond himself in prayer. He asks Hernando to prepare for travel as his companion on the pilgrimage, and the monk accepts with emotion.",
        "characters": [
            "juan_ii", "fray_hernando"
        ],
        "factions_affected": [],
        "location": "Valladolid, Royal Chapel",
        "tags": ["religion", "personal", "introspection"],
    },
    {
        "msgs": (57, 80),
        "date": "1430-05-13",
        "type": "council",
        "summary": "The regency council is formally installed before ~60 witnesses in the great hall. Juan announces his pilgrimage, the council's temporary authority (three-fourths majority), and the Royal Council in Seville for November. The four regency council members are Infante Juan, Infante Enrique, the Archbishop of Toledo, and the Marquis de Santillana. After the ceremony, Juan mingles with concerned nobles: city representative García Fernández (directed to petition Álvaro), Juan de Silva (worried about Álvaro's safety under the Infantes), and Fray Lope de Barrientos (hinting at Church support for a longer journey).",
        "characters": [
            "juan_ii", "alvaro_de_luna", "infante_juan_de_aragon",
            "infante_enrique_de_aragon", "archbishop_cerezuela",
            "marquis_de_santillana", "garcia_fernandez",
            "juan_de_silva", "lope_de_barrientos",
            "fernan_alonso_de_robles"
        ],
        "factions_affected": ["royal_court", "aragonese_faction"],
        "location": "Valladolid, Royal Palace",
        "tags": ["politics", "ceremony", "diplomacy"],
    },
    {
        "msgs": (81, 104),
        "date": "1430-05-13",
        "type": "decision",
        "summary": "After bidding farewell to the Infantes, Juan reveals to Álvaro an audacious plan: fake his departure, circle back secretly with two guards, hide in a pre-positioned shepherd's hut for two days, then crash the first regency council meeting. Álvaro is impressed but warns of risks. They develop the cover story (retrieving his father's sword), prepare a soldier's disguise, and identify a hiding spot. Juan will select his two guards in the moment of departure.",
        "characters": [
            "juan_ii", "alvaro_de_luna",
            "infante_juan_de_aragon", "infante_enrique_de_aragon"
        ],
        "factions_affected": [],
        "location": "Valladolid, Royal Palace",
        "tags": ["strategy", "deception", "planning"],
    },
    {
        "msgs": (105, 120),
        "date": "1430-05-14",
        "end_date": "1430-05-16",
        "type": "decision",
        "summary": "Juan departs on pilgrimage with ~30 people. At the Hermitage of San Millán, he prays with Fray Hernando, then tells the party to continue ahead while he stays to pray. He selects Sergeant García and Corporal Rodrigo as his two guards. After the party leaves, the three ride back in soldier's disguise to hide in a shepherd's hut. Over two cold nights, the guards share war stories — their first kills, the terror before battle, the brotherhood that makes fear bearable. On the morning of Day 3, Juan reveals the full plan to his guards, who are impressed and pledge to follow.",
        "characters": [
            "juan_ii", "fray_hernando", "fernan_alonso_de_robles",
            "sergeant_garcia", "corporal_rodrigo"
        ],
        "factions_affected": [],
        "location": "Valladolid outskirts",
        "tags": ["deception", "preparation", "personal", "military"],
    },
    {
        "msgs": (121, 148),
        "date": "1430-05-16",
        "type": "crisis",
        "summary": "Juan bursts into the first regency council session, catching Infante Juan proposing to make the regency permanent and Infante Enrique advocating removal of Álvaro's loyalists. Juan removes Infante Juan from the council by royal decree. When Juan resists leaving, the king threatens his life — an action he later regrets. After Infante Juan departs in fury, Juan negotiates separately with Enrique, offering to keep him on the council. Enrique accepts, pledging honest counsel. The remaining council addresses the Infantes' proposals: Juan de Daza stays (with shared reports as compromise), Captain Fernán's replacement is deferred, and the permanent council scheme is dead. Juan decrees that the now three-member council must decide by unanimity, effectively giving each member veto power and protecting Álvaro.",
        "characters": [
            "juan_ii", "infante_juan_de_aragon", "infante_enrique_de_aragon",
            "alvaro_de_luna", "archbishop_cerezuela",
            "marquis_de_santillana", "sergeant_garcia"
        ],
        "factions_affected": ["royal_court", "aragonese_faction"],
        "location": "Valladolid, Royal Palace",
        "tags": ["crisis", "confrontation", "politics", "power", "roll"],
    },
    {
        "msgs": (149, 162),
        "date": "1430-05-16",
        "type": "diplomacy",
        "summary": "Juan has Álvaro draft a diplomatic letter to King Alfonso V of Aragon. After Álvaro counsels against an aggressive tone, the letter is framed carefully: acknowledging tensions, noting Infante Juan's removal, emphasizing Enrique's continued role, and expressing regret for heated words. The Archbishop of Toledo co-signs. Juan then rides hard to rejoin his pilgrimage party by nightfall and tells them honestly what happened — including admitting his deception was planned, not divinely inspired.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "archbishop_cerezuela",
            "fernan_alonso_de_robles", "fray_hernando",
            "sergeant_garcia", "alfonso_v"
        ],
        "factions_affected": [],
        "location": "Valladolid, Royal Palace",
        "tags": ["diplomacy", "politics", "honesty"],
    },
    {
        "msgs": (163, 176),
        "date": "1430-05-16",
        "type": "decision",
        "summary": "Fray Hernando confronts Juan privately about using prayer as political cover. Juan turns the question around, asking Hernando about his own prayer experience. Hernando describes prayer as constant struggle to hear beyond oneself. Juan defends his approach: he prays sincerely while thinking strategically, seeing the two as inseparable. Hernando challenges Juan's crusade motivations — has he tried diplomacy first? Juan agrees to attempt peaceful negotiation with Granada before war, but firmly establishes boundaries: Hernando is counselor, not master, and Juan will not be bound by private discussions. The confessor-king relationship is defined: honest spiritual counsel, no extracted obligations.",
        "characters": [
            "juan_ii", "fray_hernando"
        ],
        "factions_affected": [],
        "location": "Road north of Valladolid",
        "tags": ["religion", "personal", "philosophy", "crusade"],
    },
]

# -----------------------------------------------------------------------
# New characters (not yet in characters.json database)
# -----------------------------------------------------------------------

NEW_CHARACTERS = [
    {
        "id": "juan_de_daza",
        "name": "Juan de Daza",
        "aliases": ["juan_de_daza", "daza"],
        "title": "Treasury Official",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["economic"],
        "location": "Valladolid",
        "current_task": "Serving in Juan II's secret advisory cabinet; tracking treasury flows and urban intelligence",
        "personality": ["pragmatic", "careful", "competent"],
        "interests": ["treasury management", "urban intelligence", "financial flows"],
        "speech_style": "Practical and measured; speaks from experience with money and commerce",
        "core_characteristics": "Treasury official and commoner in Juan II's secret advisory cabinet. Meticulous record-keeper. The Infantes later tried to remove him for being loyal to Álvaro, but Juan II retained him with a compromise: shared reports to the regency council.",
        "faction_ids": ["royal_court"],
        "appearance": {},
    },
    {
        "id": "diego_gomez_de_sandoval",
        "name": "Diego Gómez de Sandoval, Count of Castro",
        "aliases": ["diego_gomez_de_sandoval", "count_of_castro", "sandoval"],
        "title": "Count of Castro",
        "born": "1398-00-00",
        "status": ["active"],
        "category": ["nobility"],
        "location": "Valladolid",
        "current_task": "Serving in Juan II's secret advisory cabinet; observing court factions",
        "personality": ["sophisticated", "cautious", "observant"],
        "interests": ["court politics", "faction dynamics"],
        "speech_style": "Refined and diplomatic; careful word choice reflecting converso awareness of social dynamics",
        "core_characteristics": "Converso noble in Juan II's secret advisory cabinet. Tasked with observing court factions. His family faces occasional discrimination, making him keenly aware of political undercurrents. Age ~32 in 1430.",
        "faction_ids": ["royal_court"],
        "appearance": {},
    },
    {
        "id": "rodrigo_manrique",
        "name": "Rodrigo Manrique",
        "aliases": ["rodrigo_manrique"],
        "title": "Frontier Soldier",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Granada frontier",
        "current_task": "Serving in Juan II's secret advisory cabinet; providing military intelligence on the frontier",
        "personality": ["blunt", "direct", "experienced", "pragmatic"],
        "interests": ["frontier defense", "military strategy", "combat"],
        "speech_style": "Short, blunt, soldierly. Cuts through formality with harsh frontier honesty. Barks laughs at courtly pretension.",
        "core_characteristics": "Frontier veteran of 20+ years in Juan II's secret advisory cabinet. Provides military intelligence. Gave a brutally honest assessment of the Granada frontier: most frontier lords profit from perpetual low-intensity conflict. Any real conquest would take 8-15 years and require unified command.",
        "faction_ids": ["royal_court"],
        "appearance": {},
    },
    {
        "id": "garcia_fernandez",
        "name": "García Fernández",
        "aliases": ["garcia_fernandez"],
        "title": "City Representative",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["economic"],
        "location": "Seville",
        "current_task": "Representing city interests at the Valladolid court",
        "personality": ["practical", "concerned", "respectful"],
        "interests": ["trade", "city governance", "tax policy"],
        "speech_style": "Careful and deferential; a merchant choosing words before authority",
        "core_characteristics": "City representative (possibly from Seville) who attended the regency installation. Raised practical concerns about daily governance during the king's absence. Directed to petition Álvaro for routine matters.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "weathered",
        },
    },
    {
        "id": "juan_de_silva",
        "name": "Juan de Silva",
        "aliases": ["juan_de_silva", "silva"],
        "title": "",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["nobility"],
        "location": "Valladolid",
        "current_task": "Supporting Álvaro de Luna's network; concerned about Álvaro's safety under the regency",
        "personality": ["loyal", "worried", "proper"],
        "interests": ["court politics", "Álvaro's faction"],
        "speech_style": "Quiet and measured; speaks carefully to avoid being overheard",
        "core_characteristics": "Mid-ranking noble in Álvaro de Luna's network. Attended the regency installation and expressed concern about Álvaro's safety — warning that the Infantes might charge Álvaro with a crime during Juan's absence.",
        "faction_ids": ["royal_court"],
        "appearance": {},
    },
    {
        "id": "sergeant_garcia",
        "name": "Sergeant García",
        "aliases": ["sergeant_garcia", "garcia"],
        "title": "Sergeant of the Royal Guard",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Valladolid",
        "current_task": "Accompanying Juan II on pilgrimage after serving as one of two guards in the deception operation",
        "personality": ["grizzled", "loyal", "steady", "brave"],
        "interests": ["soldiering", "duty", "survival"],
        "speech_style": "Blunt and experienced; speaks with the weight of twenty years of frontier service",
        "core_characteristics": "Grizzled veteran in his forties with scars on his weathered face. One of the two guards Juan II selected for his secret return to Valladolid. Shared honest war stories during the two-night wait in the shepherd's hut. First kill at seventeen. Has served the crown faithfully for decades.",
        "faction_ids": ["royal_court"],
        "appearance": {
            "age_appearance": "forties",
            "distinguishing_features": "scars on weathered face",
        },
    },
    {
        "id": "corporal_rodrigo",
        "name": "Corporal Rodrigo",
        "aliases": ["corporal_rodrigo"],
        "title": "Corporal of the Royal Guard",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Valladolid",
        "current_task": "Accompanying Juan II on pilgrimage after serving as one of two guards in the deception operation",
        "personality": ["steady", "loyal"],
        "interests": ["soldiering"],
        "speech_style": "Practical and direct",
        "core_characteristics": "Eight-year veteran of the royal guard. One of the two guards selected for Juan II's secret return to Valladolid. Shared that the waiting before battle is worse than the battle itself.",
        "faction_ids": ["royal_court"],
        "appearance": {},
    },
    {
        "id": "marquis_de_santillana",
        "name": "Marquis de Santillana",
        "aliases": ["marquis_de_santillana"],
        "title": "Marquis de Santillana",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["nobility"],
        "location": "Valladolid",
        "current_task": "Serving on the regency council during Juan II's pilgrimage",
        "personality": ["calculating", "measured", "cautious"],
        "interests": ["governance", "family power", "political balance"],
        "speech_style": "Measured and careful; weighs every word for political implications",
        "core_characteristics": "Elder Mendoza family representative on the regency council. The Mendoza family is one of Castile's great noble houses, rivals to the Velascos. Initially a four-member council (with Infante Juan), now serves on the three-member unanimous-consent council alongside Infante Enrique and the Archbishop of Toledo.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "around fifty",
        },
    },
    {
        "id": "alfonso_v",
        "name": "Alfonso V of Aragon",
        "aliases": ["alfonso_v", "alfonso_of_aragon", "alfonso_the_magnanimous"],
        "title": "King of Aragon",
        "born": "1396-00-00",
        "status": ["active"],
        "category": ["foreign_ruler"],
        "location": "Aragon",
        "current_task": "Pursuing Italian ambitions (seeking Naples); received diplomatic letter about his brothers' conduct in Castile",
        "personality": ["ambitious", "focused_on_italy", "diplomatic"],
        "interests": ["Italian conquest", "Naples", "Mediterranean power"],
        "speech_style": "",
        "core_characteristics": "King of Aragon, ~34 in 1430, known as 'the Magnanimous.' Married to María of Castile (Juan II's sister) but has no heir. Focused on Italian ambitions — seeking Naples. His younger brothers (the Infantes Juan and Enrique) meddle in Castilian politics while Alfonso pursues Mediterranean power. A diplomatic letter was sent to him after Infante Juan was removed from the regency council.",
        "faction_ids": [],
        "appearance": {},
    },
]

# -----------------------------------------------------------------------
# Character updates (characters already in characters.json)
# -----------------------------------------------------------------------

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "Departing on pilgrimage to Santiago, secretly planning to continue to Rome; exposed Infantes' plot to make regency permanent",
        "personality": {"add": ["bold", "deceptive_when_needed"]},
        "location": "Road north of Valladolid",
    },
    {
        "id": "alvaro_de_luna",
        "current_task": "Administering the kingdom during Juan's absence; protected by unanimous-consent council structure",
        "location": "Valladolid",
    },
    {
        "id": "fray_hernando",
        "current_task": "Accompanying Juan II on pilgrimage as confessor and spiritual guide; established boundaries of spiritual counsel",
        "location": "Road north of Valladolid",
    },
    {
        "id": "fernan_alonso_de_robles",
        "current_task": "Leading the pilgrimage party guard; Captain position deferred from council review",
        "location": "Road north of Valladolid",
    },
    {
        "id": "lope_de_barrientos",
        "current_task": "Serving in Juan II's secret advisory cabinet monitoring Church networks; hinted at supporting a longer journey beyond Santiago",
        "faction_ids": {"add": ["royal_court"]},
    },
    {
        "id": "inigo_lopez_de_mendoza",
        "current_task": "Serving in Juan II's secret advisory cabinet as Mendoza family observer",
    },
    {
        "id": "infante_juan_de_aragon",
        "current_task": "Removed from regency council after being caught plotting to make it permanent; departed Valladolid in fury",
        "personality": {"add": ["overconfident"]},
        "location": "Unknown (departed Valladolid)",
    },
    {
        "id": "infante_enrique_de_aragon",
        "current_task": "Remaining on regency council after brother's removal; pledged honest counsel to Juan II",
        "personality": {"add": ["pragmatic"]},
    },
    {
        "id": "archbishop_cerezuela",
        "current_task": "Serving on the regency council; co-signed diplomatic letter to Alfonso V of Aragon",
        "location": "Valladolid",
    },
]

# -----------------------------------------------------------------------
# New locations
# -----------------------------------------------------------------------

NEW_LOCATIONS = [
    # No truly new major locations. Events take place in Valladolid
    # (already exists) and briefly on the road. Sub-locations are added
    # via location updates if needed.
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
            "add": [
                "juan_de_daza", "diego_gomez_de_sandoval",
                "rodrigo_manrique", "juan_de_silva",
                "sergeant_garcia"
            ]
        },
        "description": "The inner circle loyal to Juan II. Now includes a secret advisory cabinet (Daza, Sandoval, Barrientos, Mendoza, Manrique) plus core court figures. Álvaro de Luna administers the kingdom during Juan's pilgrimage, protected by a unanimous-consent regency council.",
    },
    {
        "faction_id": "aragonese_faction",
        "description": "Coalition of nobles allied with the Infantes de Aragón. Infante Juan removed from regency council after being caught plotting to make it permanent. Infante Enrique remains on the council, pledging honest counsel. Faction's power significantly weakened by the exposure.",
    },
]

# -----------------------------------------------------------------------
# Rolls
# -----------------------------------------------------------------------

ROLLS = [
    {
        "event_index": 6,  # The Council Ambush event (0-indexed)
        "title": "Subterfuge Secrecy",
        "context": "Juan II staged a fake departure on pilgrimage and is hiding near Valladolid to crash the first regency council meeting. This roll determines whether the Infantes have discovered the deception.",
        "roll_type": "intrigue",
        "date": "1430-05-16",
        "rolled": None,  # Result described as "status quo"
        "outcome_range": "status_quo",
        "outcome_label": "Status Quo",
        "outcome_detail": "The Infantes received vague information that something seems off — Captain Fernán seemed troubled, the hermitage prayer was unusual — but couldn't piece together the full picture. They proceed with their plans despite slight uncertainty.",
        "evaluation": "Juan's tight circle of knowledge and short timeline kept the plan mostly secret. However, the unusual behavior at the hermitage raised suspicions that prevented total surprise.",
        "success_factors": [
            "Very small circle of knowledge (only Álvaro knew the plan)",
            "Short timeline (only 3 days)",
            "Legitimate departure ceremony with full party",
            "Plausible cover story (prayer at hermitage)",
        ],
        "failure_factors": [
            "Fray Hernando's suspicions about the prayer",
            "Captain Fernán's visible concern",
            "Infantes' own intelligence networks",
            "Unusual behavior of king staying behind to pray",
        ],
    },
    {
        "event_index": 6,  # Same event (0-indexed)
        "title": "Infantes' Council Boldness",
        "context": "The Infantes hold their first regency council meeting while Juan II is supposedly away on pilgrimage. This roll determines how aggressively they push their agenda.",
        "roll_type": "chaos",
        "date": "1430-05-16",
        "rolled": None,  # Result described as "critical success" (for Juan — the Infantes overreach)
        "outcome_range": "critical_success",
        "outcome_label": "Critical Success",
        "outcome_detail": "The Infantes make extremely bold moves far exceeding expectations: proposing to make the regency permanent, removing Álvaro's loyalists from key positions, and openly discussing how to constrain the king upon his return. Their spectacular overreach provides perfect ammunition for Juan's surprise entrance.",
        "evaluation": "Despite the status quo on secrecy (vague suspicions), the Infantes' overconfidence drove them to reveal their full hand. Infante Juan's proposal to formalize permanent constraints on royal authority was far more aggressive than merely administering the realm.",
        "success_factors": [
            "Infantes believed Juan was truly gone",
            "First meeting — eager to establish precedent",
            "Overconfidence after getting regency power",
            "Desire to lock in gains before Juan returns",
        ],
        "failure_factors": [
            "Enrique's brief hesitation about king's hermitage behavior",
            "Archbishop and Marquis expressed caution",
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
        "chapter": "1.02",
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
    print(f"Chapter 1.02 extraction complete:")
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
