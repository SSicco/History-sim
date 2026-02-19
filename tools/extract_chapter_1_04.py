#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.04.

Reads tools/preprocessed/chapter_1.04_preprocessed.json and produces
tools/extractions/chapter_1.04_extracted.json in the schema expected
by merge_chapter.py.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.04_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.04_extracted.json"

# -----------------------------------------------------------------------
# Event definitions
# -----------------------------------------------------------------------

EVENT_DEFS = [
    {
        "msgs": (1, 6),
        "date": "1430-05-20",
        "end_date": "1430-09-01",
        "type": "crisis",
        "summary": "While Juan II is away on pilgrimage, the Infantes de Aragón launch their revolt. Infante Juan rallies 15 nobles at Medina del Campo and sends propaganda letters portraying Juan as unstable. The revolt FAILS: only 23 nobles attend their unauthorized assembly at Burgos (expected 30-40); they seize Arévalo fortress and two minor castles but fail to take any major city; Segovia bluntly refuses entry. Álvaro de Luna holds Valladolid and the royal administration, with Juan's secret intelligence cabinet functioning effectively. When rumors of the papal bull reach Castile in August, wavering nobles abandon the Infantes entirely. The revolt collapses, leaving the Infantes as exposed rebels with only ~12% noble support and 3,000 household troops.",
        "characters": [
            "infante_juan_de_aragon", "infante_enrique_de_aragon",
            "alvaro_de_luna", "luis_de_guzman",
            "juan_de_daza", "diego_gomez_de_sandoval",
            "lope_de_barrientos", "inigo_lopez_de_mendoza",
            "rodrigo_manrique"
        ],
        "factions_affected": ["royal_court", "aragonese_faction"],
        "location": "Castile",
        "tags": ["crisis", "revolt", "politics", "roll"],
    },
    {
        "msgs": (7, 10),
        "date": "1430-08-22",
        "end_date": "1430-09-10",
        "type": "crisis",
        "summary": "Sultan Muhammad IX of Granada responds to the crusade bull with emergency measures. Military mobilization FAILS: only 8,000 of 10,000 planned militia raised, fortifications incomplete, 80,000 dinars spent, harvest disrupted, internal discontent rising. However, the appeal to the Muslim world is a CRITICAL SUCCESS: Morocco sends 5,000 professional troops, 1,000 cavalry, 15 war galleys, and 50,000 dinars; Tunisia sends 30,000 dinars and 5-8 galleys; Egypt sends 100,000 dinars and military advisors; the Ottomans send 20,000 dinars and cannon technology with master gunners. Total foreign support: 220,000 dinars, ~8,000 additional troops, 20-25 war galleys. Granada transforms from isolated kingdom to banner of Islamic resistance — jihad vs. crusade. A 12-person diplomatic mission prepares to offer Juan doubled tribute and peaceful conversion terms.",
        "characters": [
            "muhammad_ix"
        ],
        "factions_affected": [],
        "location": "Granada",
        "tags": ["crisis", "military", "diplomacy", "roll"],
    },
    {
        "msgs": (11, 20),
        "date": "1430-08-02",
        "end_date": "1430-08-05",
        "type": "decision",
        "summary": "Juan II's party departs Rome for Florence via the Via Cassia. Critical success roll — they make the journey in just 4 days instead of 6-7, with excellent weather and growing camaraderie. Juan's health issues from months of travel become apparent (bleeding gums, weakness — early scurvy from poor road diet). Captain Fernán and Fray Hernando confront him about his health and force him to eat properly. The party arrives in Florence ahead of schedule and is received by Cosimo de' Medici, the unofficial ruler, who hosts them at the Palazzo Medici.",
        "characters": [
            "juan_ii", "fernan_alonso_de_robles", "fray_hernando",
            "thomas_beaumont", "sergeant_garcia", "corporal_rodrigo",
            "cosimo_de_medici"
        ],
        "factions_affected": [],
        "location": "Florence",
        "tags": ["travel", "health", "roll"],
    },
    {
        "msgs": (21, 28),
        "date": "1430-08-06",
        "end_date": "1430-08-08",
        "type": "diplomacy",
        "summary": "Juan meets privately with Cosimo de' Medici, the de facto ruler of Florence. He openly shares the crusade bull and asks Cosimo to arrange a dinner with Florence's elite and commission a banner — all white, no symbols, but artistically crafted to be proud and large. Juan plans to publicly fasten the sacred relics (True Cross fragment and Saint James bone) to the banner before the crowd. Juan gives up his remaining jewelry and rings, keeping only his father's sword. Cosimo, impressed by the young king's boldness, agrees to host a public gathering in the Piazza della Signoria.",
        "characters": [
            "juan_ii", "cosimo_de_medici"
        ],
        "factions_affected": [],
        "location": "Florence",
        "tags": ["diplomacy", "crusade", "planning"],
    },
    {
        "msgs": (29, 34),
        "date": "1430-08-09",
        "type": "diplomacy",
        "summary": "Juan II delivers a crusade speech before 8,000-10,000 people in Florence's Piazza della Signoria. Critical success roll — the speech is a triumph. Juan speaks of God's kingdom on earth, his act of renunciation before the Pope, the crusade as a calling for all Christendom. He draws his father's sword and cries 'Non Nobis Domine!' The crowd roars back the phrase. He publicly attaches the True Cross fragment and Saint James bone to the all-white banner. The event becomes legendary: Florentine merchants pledge 15,000 florins, 200 volunteers sign up including 50 professional soldiers, the Bishop of Florence endorses the crusade publicly, and word begins spreading across Europe that a young king has risen to complete the Reconquista.",
        "characters": [
            "juan_ii", "fray_hernando", "fernan_alonso_de_robles",
            "thomas_beaumont", "sergeant_garcia", "corporal_rodrigo",
            "cosimo_de_medici"
        ],
        "factions_affected": [],
        "location": "Florence, Piazza della Signoria",
        "tags": ["diplomacy", "crusade", "speech", "roll"],
    },
    {
        "msgs": (35, 56),
        "date": "1430-08-09",
        "end_date": "1430-08-10",
        "type": "decision",
        "summary": "After the Florence triumph, Juan discusses the spiritual implications with Fray Hernando. The confessor warns about the intoxicating power of the crowd's adoration and the danger of certainty born from success. Juan admits he enjoyed the power of commanding a crowd but insists the crusade fervor was genuine, not manufactured. They debate the use of sacred relics as tools — Juan argues he didn't choose this role, the Pope gave him the relics and required them on the banner. Hernando presses on the distinction between divine calling and self-certainty. Juan pushes back firmly: 'Today I succeed, tomorrow I fail. We must not shy away from a challenge just because it is hard.' The relationship between king and confessor deepens through honest disagreement.",
        "characters": [
            "juan_ii", "fray_hernando"
        ],
        "factions_affected": [],
        "location": "Florence",
        "tags": ["religion", "personal", "philosophy"],
    },
]

# -----------------------------------------------------------------------
# New characters
# -----------------------------------------------------------------------

NEW_CHARACTERS = [
    {
        "id": "cosimo_de_medici",
        "name": "Cosimo de' Medici",
        "aliases": ["cosimo_de_medici", "cosimo", "medici"],
        "title": "De facto ruler of Florence",
        "born": "1389-09-27",
        "status": ["active"],
        "category": ["foreign_ruler", "economic"],
        "location": "Florence",
        "current_task": "Hosting Juan II's visit and supporting the crusade speech; commissioned the all-white banner",
        "personality": ["intelligent", "sophisticated", "politically_astute", "generous"],
        "interests": ["banking", "art", "politics", "patronage"],
        "speech_style": "Refined, witty, speaks with the confidence of immense wealth and political acumen",
        "core_characteristics": "De facto ruler of Florence through the Medici banking fortune. Age ~41 in 1430. First encountered Juan on the road during the France journey, offering advice about approaching the Pope. Hosted Juan at the Palazzo Medici and arranged the grand public speech in the Piazza della Signoria. Impressed by Juan's boldness and spiritual conviction.",
        "faction_ids": [],
        "appearance": {},
    },
    {
        "id": "luis_de_guzman",
        "name": "Don Luis de Guzmán",
        "aliases": ["luis_de_guzman"],
        "title": "Master of the Order of Santiago",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["military", "nobility"],
        "location": "Castile",
        "current_task": "Allied with the Infantes' revolt; Master of Santiago, the wealthiest military order",
        "personality": ["ambitious", "grim", "politically_aligned_with_infantes"],
        "interests": ["military orders", "power", "Castilian politics"],
        "speech_style": "",
        "core_characteristics": "Master of the Order of Santiago, the largest and wealthiest military order in Castile. Allied with the Infantes de Aragón during their failed revolt. One of the few major figures to support the rebellion openly.",
        "faction_ids": ["aragonese_faction"],
        "appearance": {},
    },
]

# -----------------------------------------------------------------------
# Character updates
# -----------------------------------------------------------------------

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "In Florence after triumphant crusade speech; suffering from early scurvy and malnutrition; preparing to continue to Barcelona and then Seville",
        "personality": {"add": ["charismatic_speaker"]},
        "location": "Florence",
    },
    {
        "id": "fray_hernando",
        "current_task": "Warning Juan about the spiritual dangers of certainty and crowd adoration; concerned about pride",
        "location": "Florence",
    },
    {
        "id": "fernan_alonso_de_robles",
        "current_task": "Managing the travel party; confronted Juan about his health; organizing return to Spain",
        "location": "Florence",
    },
    {
        "id": "muhammad_ix",
        "current_task": "Preparing for jihad against the crusade; received massive foreign Muslim support; sending diplomatic mission to Seville",
        "location": "Granada",
    },
    {
        "id": "alvaro_de_luna",
        "current_task": "Successfully defended the kingdom against the Infantes' revolt; maintained control of Valladolid and royal administration",
    },
    {
        "id": "infante_juan_de_aragon",
        "current_task": "Revolt failed; holds only Arévalo and two minor castles; exposed as rebel with minimal support (~12% of nobility)",
        "location": "Arévalo",
    },
    {
        "id": "infante_enrique_de_aragon",
        "current_task": "Participated in failed revolt while nominally on regency council; weakened position",
    },
]

# -----------------------------------------------------------------------
# New locations
# -----------------------------------------------------------------------

NEW_LOCATIONS = [
    {
        "location_id": "florence",
        "name": "Florence",
        "region": "Italy",
        "description": "Wealthy Italian city-state dominated by the Medici banking family. Cosimo de' Medici is de facto ruler. Site of Juan II's triumphant crusade speech in the Piazza della Signoria that drew 8,000-10,000 people and generated major financial and military pledges.",
        "sub_locations": ["Palazzo Medici", "Piazza della Signoria"],
    },
]

# -----------------------------------------------------------------------
# New factions / faction updates
# -----------------------------------------------------------------------

NEW_FACTIONS = []

FACTION_UPDATES = [
    {
        "faction_id": "aragonese_faction",
        "member_ids": {"add": ["luis_de_guzman"]},
        "description": "Coalition of the Infantes de Aragón and allied nobles. Their revolt during Juan's absence failed — only seized Arévalo and two minor castles, won ~12% noble support. Master of Santiago (Luis de Guzmán) is their most important military ally. Must now negotiate from weakness at the November Royal Council.",
    },
]

# -----------------------------------------------------------------------
# Rolls
# -----------------------------------------------------------------------

ROLLS = [
    {
        "event_index": 0,  # Infantes' Revolt
        "title": "Infantes' Revolt Outcome",
        "context": "The Infantes de Aragón attempt a revolt during Juan II's absence, trying to rally nobles, seize fortresses, and establish permanent control. The revolt was predetermined by a previous roll (chapter 1.01) but its success is assessed here.",
        "roll_type": "chaos",
        "date": "1430-09-01",
        "rolled": None,
        "outcome_range": "failure",
        "outcome_label": "Failure",
        "outcome_detail": "The Infantes accomplish very little. Only 23 nobles attend their unauthorized assembly. They seize Arévalo and two minor castles but fail to take any major city. Álvaro holds Valladolid easily. When rumors of the papal bull spread, remaining support collapses. They end as exposed rebels with ~12% noble backing.",
        "evaluation": "The revolt was assessed as 'Likely to Fail' even before the roll. Álvaro's competent defense, Juan's intelligence cabinet, and the papal bull rumors all worked against the Infantes. Their overreach in chapter 1.02 had already weakened their credibility.",
        "success_factors": [],
        "failure_factors": [
            "Limited noble support after chapter 1.02 humiliation",
            "Álvaro's competent defense of royal administration",
            "Juan's intelligence cabinet functioning well",
            "Cities loyal to the crown",
            "Papal bull rumors devastating to rebel cause",
        ],
    },
    {
        "event_index": 1,  # Sultan's response - military
        "title": "Granada Military Mobilization",
        "context": "Sultan Muhammad IX attempts emergency military mobilization: raising 10,000 militia, stockpiling supplies, improving fortifications on 20 frontier castles.",
        "roll_type": "military",
        "date": "1430-09-01",
        "rolled": None,
        "outcome_range": "failure",
        "outcome_label": "Failure",
        "outcome_detail": "Only 8,000 of planned 10,000 militia raised, many poorly trained and resentful (conscripted during harvest). Fortification improvements incomplete. 80,000 dinars spent. Internal discontent rising among merchants and farmers.",
        "evaluation": "Rushed mobilization during harvest season created economic disruption. The professional 8,000-man army remains intact but the additional militia are of limited quality.",
        "success_factors": [
            "Professional army intact",
            "Some fortification work completed",
        ],
        "failure_factors": [
            "Mobilization during harvest season",
            "Economic disruption from requisitions",
            "Rushed timeline",
            "Internal resentment",
        ],
    },
    {
        "event_index": 1,  # Sultan's response - Muslim world
        "title": "Muslim World Alliance",
        "context": "Sultan Muhammad IX appeals to Morocco, Tunisia, Egypt, and the Ottoman Empire for support against the Christian crusade.",
        "roll_type": "diplomacy",
        "date": "1430-09-10",
        "rolled": None,
        "outcome_range": "critical_success",
        "outcome_label": "Critical Success",
        "outcome_detail": "Unprecedented response from the Muslim world: Morocco sends 5,000 troops, 1,000 cavalry, 15 war galleys, 50,000 dinars; Tunisia sends 30,000 dinars and 5-8 galleys; Egypt sends 100,000 dinars and military advisors; Ottomans send 20,000 dinars and cannon technology with master gunners. Total: 220,000 dinars, ~8,000 troops, 20-25 war galleys. Religious scholars declare defense of Granada as jihad. Granada transforms into the standard-bearer of Islamic resistance.",
        "evaluation": "The papal crusade bull and Juan's dramatic spiritual acts convinced the Muslim world this was an existential threat. The scale of support far exceeded historical precedent, turning a regional conflict into a civilizational confrontation.",
        "success_factors": [
            "Crusade bull perceived as existential threat to Islam in Iberia",
            "Religious solidarity across Muslim world",
            "Ottoman strategic interest in weakening Christendom",
            "Morocco's proximity and military capability",
            "Egypt's wealth and prestige",
        ],
        "failure_factors": [],
    },
    {
        "event_index": 2,  # Journey to Florence
        "title": "Rome to Florence Journey",
        "context": "Juan II's lean party of 10 travels from Rome to Florence via the Via Cassia, approximately 6-7 days normally.",
        "roll_type": "travel",
        "date": "1430-08-05",
        "rolled": None,
        "outcome_range": "critical_success",
        "outcome_label": "Critical Success",
        "outcome_detail": "Journey completed in just 4 days with excellent weather and growing party camaraderie. Juan's health issues (early scurvy) are identified and addressed by companions. Arrived in Florence ahead of schedule and received by Cosimo de' Medici.",
        "evaluation": "Perfect conditions, experienced party, well-maintained roads. The critical success allowed early arrival and time for health recovery.",
        "success_factors": [
            "Well-maintained Italian roads",
            "Experienced travel party",
            "Good weather",
            "Well-rested horses from Rome",
        ],
        "failure_factors": [
            "Juan's developing health issues",
        ],
    },
    {
        "event_index": 4,  # Florence speech
        "title": "Florence Crusade Speech",
        "context": "Juan II delivers a public crusade speech before 8,000-10,000 people in Florence's Piazza della Signoria, attaching sacred relics to his white banner and calling for support.",
        "roll_type": "persuasion",
        "date": "1430-08-09",
        "rolled": None,
        "outcome_range": "critical_success",
        "outcome_label": "Critical Success",
        "outcome_detail": "The speech becomes legendary. Juan's passionate delivery, the drawing of his father's sword with 'Non Nobis Domine,' and the public attachment of relics to the white banner creates religious fervor. Florentine merchants pledge 15,000 florins, 200 volunteers sign up including 50 professional soldiers, the Bishop of Florence endorses publicly. Word spreads across Europe of a young king risen to complete the Reconquista.",
        "evaluation": "Juan's genuine conviction, combined with powerful theatrical elements (sword, relics, white banner, youth) and Cosimo's staging of the event, created a perfect moment. His growing reputation from Rome magnified the impact.",
        "success_factors": [
            "Genuine spiritual conviction",
            "Powerful theatrical elements (relics, sword, white banner)",
            "Cosimo's staging and elite audience",
            "Youth as asset — passionate and sincere",
            "Papal endorsement lending authority",
        ],
        "failure_factors": [
            "Health issues (managed)",
            "Foreign king on foreign soil",
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
        "chapter": "1.04",
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
    print(f"Chapter 1.04 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  New locations:     {len(NEW_LOCATIONS)}")
    print(f"  New factions:      {len(NEW_FACTIONS)}")
    print(f"  Faction updates:   {len(FACTION_UPDATES)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Written to:        {OUTPUT}")


if __name__ == "__main__":
    main()
