#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.16.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.16_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.16_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 6),
        "date": "1431-04-01",
        "type": "military",
        "summary": "Sultan Muhammad IX's scouts report on Castilian deployment. Roll 73: Good Observation — Sultan learns 23,000 total, identifies siege works with 5,000 elite troops under Infante Enrique, three infantry formations plus 4,000 heavy cavalry reserve under Juan personally, single bombard visible but suspects more. Recognizes professional preparation, may suspect bait. Sultan's decision: Roll 3 — Desperate Frontal Assault. Despite excellent intelligence showing prepared positions and numerical inferiority, Sultan orders immediate attack without rest. Exhausted troops (40 miles in 2 days) push straight toward siege works in march column. Jihad fervor overrides military prudence. Catastrophic decision.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "infante_enrique_de_aragon",
            "garcia_fernandez_de_baeza"
        ],
        "factions_affected": [],
        "location": "Alcala la Real",
        "tags": ["military", "intelligence", "roll", "battle"],
    },
    {
        "msgs": (7, 14),
        "date": "1431-04-01",
        "type": "military",
        "summary": "Battle of Alcala la Real — initial engagement and cavalry charge. Roll 97: Catastrophic Moorish Collapse. Sultan's exhausted troops cannot sustain assault — multiple units break within minutes, formations disintegrate, officers' orders ignored. Enrique's siege works barely scratched. Juan signals infantry advance, joins heavy cavalry (4,000) for flanking maneuver. Roll 17: Contested Breakthrough. Charge devastates fleeing infantry but 2,000 Moroccan elite cavalry counter-charge to protect retreat. Fierce cavalry melee erupts. Juan parries enemy blade in personal combat. Guardian knight Martín de Oviedo takes blade meant for Juan at neck/shoulder gap — wounded saving the king's life. Moroccans eventually driven off but Castilian formation scattered.",
        "characters": [
            "juan_ii", "infante_enrique_de_aragon", "garcia_fernandez_de_baeza",
            "pedro_gonzalez_de_padilla", "rodrigo_de_narvaez",
            "martin_de_oviedo", "fernan_alonso_de_robles"
        ],
        "factions_affected": [],
        "location": "Alcala la Real",
        "tags": ["military", "battle", "cavalry", "roll", "combat"],
    },
    {
        "msgs": (15, 26),
        "date": "1431-04-01",
        "type": "military",
        "summary": "Battle pursuit phase. Juan rides to vantage point to assess battlefield — complete Moorish rout visible, Moroccan cavalry screening Sultan's retreat. Roll 29: Moderate Rally — Juan rides in circle with raised sword gathering scattered cavalry, ~800 knights respond (of 1,500 nearby). Álvar Pérez de Guzmán joins with 200 knights. Juan leads 800 cavalry to reinforce pursuit, targets Moroccan rearguard protecting Sultan's fleeing mob (4,000-5,000). Roll 13: Contested Breakthrough. Moroccan cavalry forms blocking force — fierce cavalry battle. Guardian knight wounded protecting Juan. Charge breaks through but disorganized, ~500-800 enemy killed before darkness. Sultan escapes with 2,000-3,000 survivors. Juan ends pursuit, consolidates, leads troops back to Third Battle line.",
        "characters": [
            "juan_ii", "alvar_perez_de_guzman", "garcia_fernandez_de_baeza",
            "pedro_gonzalez_de_padilla", "rodrigo_de_narvaez"
        ],
        "factions_affected": [],
        "location": "Alcala la Real",
        "tags": ["military", "battle", "pursuit", "cavalry", "roll"],
    },
    {
        "msgs": (27, 30),
        "date": "1431-04-01",
        "end_date": "1431-04-02",
        "type": "military",
        "summary": "Victory consolidation. Juan leads troops back to siege works as darkness falls. Infante Enrique embraces Juan — his position held perfectly. Camp organizing: triple watches, medical stations, prisoner management. Preliminary casualty report: Castilian dead ~400-500, seriously wounded ~300-400, light wounds ~600-800 (total ~1,500-1,700 of 23,000). Enemy dead on field ~4,000-5,000, prisoners ~1,200, escaped with Sultan ~2,000-3,000. Sultan's field army destroyed — 10,000-11,000 of 16,000 casualties. Around midnight, white flag from Alcala la Real fortress. Garrison delegation emerges under truce.",
        "characters": [
            "juan_ii", "infante_enrique_de_aragon", "pedro_gonzalez_de_padilla",
            "pietro_calabrese"
        ],
        "factions_affected": [],
        "location": "Alcala la Real",
        "tags": ["military", "consolidation", "casualties", "victory"],
    },
    {
        "msgs": (31, 38),
        "date": "1431-04-02",
        "type": "diplomacy",
        "summary": "Fortress of Alcala la Real capitulation. Roll 96: Complete Capitulation — Strategic Breakthrough. Garrison commander Yusuf ibn Rashid (age ~50, 32 years service, 23 battles) comes not just to surrender but to convert. Having watched Sultan's entire 16,000-man army destroyed in one afternoon, many garrison members experience crisis of faith. Of 380 garrison, 70+ wish to convert to Christianity and join the crusade. Yusuf's son Ibrahim (age 28) also converting — moved by seeing Christian surgeons treat wounded Moors and Juan leading from the front. Qadi Ahmad al-Zarqali (age ~40) not yet converting but faith profoundly shaken. Garrison offers fortress intact with all intelligence: maps, troop dispositions, supply caches, Sultan's strategic plans. Juan offers generous terms: lay down arms, keep possessions, safe passage for those who wish to leave. Captain Rodrigo sent with 20 knights to disarm garrison and raise Castilian banner. Unprecedented propaganda earthquake across the frontier.",
        "characters": [
            "juan_ii", "yusuf_ibn_rashid", "ibrahim_ibn_yusuf",
            "ahmad_al_zarqali", "pedro_gonzalez_de_padilla",
            "infante_enrique_de_aragon", "rodrigo_de_narvaez",
            "garcia_fernandez_de_baeza", "fernan_alonso_de_robles"
        ],
        "factions_affected": ["royal_court"],
        "location": "Alcala la Real",
        "tags": ["diplomacy", "surrender", "conversion", "roll", "intelligence"],
    },
    {
        "msgs": (39, 44),
        "date": "1431-04-02",
        "type": "diplomacy",
        "summary": "Qadi Ahmad al-Zarqali's spiritual crisis and decision. Juan offers Ahmad freedom to leave or join the royal court as advisor/translator with complete religious freedom — no forced conversion, time to search his soul. Roll 77: Genuine Acceptance. Ahmad accepts — sees rare opportunity to honestly engage with Christianity after 21 years studying only Islamic tradition. 'Expert in answers I was taught, not questions I discovered myself.' Cannot return to Granada — how would he counsel faith he doubts? Commits to honest seeking, faithful service as translator/advisor on Muslim culture and Granada's politics. Promises truth wherever it leads, not conversion. Chapter closes with fortress secured, Castilian banner flying, converts beginning instruction with Fray Hernando.",
        "characters": [
            "juan_ii", "ahmad_al_zarqali", "fray_hernando"
        ],
        "factions_affected": [],
        "location": "Alcala la Real",
        "tags": ["diplomacy", "religion", "conversion", "roll", "personal"],
    },
]

NEW_CHARACTERS = [
    {
        "id": "yusuf_ibn_rashid",
        "name": "Yusuf ibn Rashid",
        "aliases": ["yusuf_ibn_rashid", "yusuf"],
        "title": "Former Commander of Alcala la Real Fortress",
        "born": "1381-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Alcala la Real",
        "current_task": "Converting to Christianity and swearing fealty to Castilian crown; offering 32 years of military experience and intelligence on Granada's defenses to the crusade; facilitating peaceful garrison disarmament",
        "personality": ["professional", "honorable", "pragmatic", "devout"],
        "interests": ["military service", "fortress defense", "faith", "honor"],
        "speech_style": "Heavily accented Castilian. Formal, professional soldier's bearing. Speaks with 32 years of hard-won authority.",
        "core_characteristics": "Age ~50. Served Granada for 32 years, held five fortresses, fought in 23 battles. Scarred face, graying beard, steady eyes. Witnessed the Battle of Alcala la Real from his walls — the catastrophic destruction of Sultan's 16,000-man army in a single afternoon caused a profound crisis of faith. Chose to convert to Christianity and join the crusade, bringing his son and 70+ garrison members with him. Offers complete intelligence on Granada's defenses.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "about 50",
            "build": "weathered soldier",
            "hair": "graying",
            "distinguishing_features": "scarred face; graying beard; steady eyes of a veteran commander",
        },
    },
    {
        "id": "ibrahim_ibn_yusuf",
        "name": "Ibrahim ibn Yusuf",
        "aliases": ["ibrahim_ibn_yusuf", "ibrahim"],
        "title": "Former Officer of Alcala la Real Garrison",
        "born": "1403-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Alcala la Real",
        "current_task": "Converting to Christianity alongside his father; joining the crusade army; moved by witnessing Christian mercy toward wounded Moors and Juan's personal leadership",
        "personality": ["honorable", "brave", "honest", "impressionable"],
        "interests": ["military service", "honor", "faith"],
        "speech_style": "Halting Castilian. Direct and honest. Speaks with the earnestness of a young man confronting hard truths.",
        "core_characteristics": "Age 28. Son of Yusuf ibn Rashid. Admitted killing Christians in battle. Moved to conversion by witnessing Christian surgeons tending wounded Moors, and Juan leading from the front. Conversion driven by observed character rather than coercion.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "late 20s",
            "build": "athletic",
            "distinguishing_features": "bears resemblance to his father Yusuf",
        },
    },
    {
        "id": "ahmad_al_zarqali",
        "name": "Ahmad al-Zarqali",
        "aliases": ["ahmad_al_zarqali", "ahmad", "the_qadi"],
        "title": "Former Qadi of Alcala la Real / Royal Court Advisor",
        "born": "1391-00-00",
        "status": ["active"],
        "category": ["court", "religious"],
        "location": "Alcala la Real",
        "current_task": "Joined Juan II's royal court as advisor and translator; complete religious freedom to search his soul; providing counsel on Muslim customs, Granada's politics and culture; studying Christianity with genuine openness while maintaining Muslim practice",
        "personality": ["intellectual", "honest", "scholarly", "conflicted"],
        "interests": ["theology", "Islamic law", "comparative religion", "truth-seeking", "Arabic literature"],
        "speech_style": "Excellent Castilian. Thoughtful, scholarly, precise. Searches for exactly the right words. Honest about uncertainty rather than pretending conviction.",
        "core_characteristics": "Age ~40. Qadi (Islamic judge/religious figure) of Alcala la Real for 9 years. Studied in Granada for 12 years. Can recite Quran from memory. Faith profoundly shaken by witnessing the catastrophic destruction of the Sultan's jihad army. Not converting but in deep spiritual crisis. Joined Juan's court to honestly engage with Christianity — 'expert in answers I was taught, not questions I discovered myself.' Values truth over comfortable certainty. Promises honest seeking, not conversion.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "about 40",
            "build": "scholarly",
            "hair": "dark",
            "distinguishing_features": "intelligent, haunted eyes; fine scholar's robes",
        },
    },
    {
        "id": "martin_de_oviedo",
        "name": "Martín de Oviedo",
        "aliases": ["martin_de_oviedo", "martin"],
        "title": "Guardian Knight",
        "born": "1396-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Alcala la Real",
        "current_task": "Recovering from serious wound sustained saving King Juan II during the Battle of Alcala la Real; blade caught him where shoulder met neck in gap in plate armor",
        "personality": ["loyal", "selfless", "veteran", "devoted"],
        "interests": ["service to the king", "Guardian Company", "family"],
        "speech_style": "Simple, direct soldier's speech. Few words, strong actions.",
        "core_characteristics": "Guardian knight with 15 years of service and 3 campaigns. Father of two daughters. Saved Juan II's life during the Battle of Alcala la Real by interposing himself between the king and a Moroccan mamluk's blade. Took the strike at the neck/shoulder gap in his armor. Fell wounded but survived.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "mid 30s",
            "build": "sturdy",
            "distinguishing_features": "neck/shoulder wound from Battle of Alcala la Real",
        },
    },
]

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "Victorious at Battle of Alcala la Real — first true battle. Led cavalry charges personally, parried enemy blade in combat, experienced real violence. Fortress secured with unprecedented mass conversion. Ahmad al-Zarqali joined court. Army resting, tending wounded, consolidating. ~21,300 combat effective. Sultan's field army destroyed.",
        "location": "Alcala la Real",
    },
    {
        "id": "infante_enrique_de_aragon",
        "current_task": "Held siege works perfectly during Battle of Alcala la Real — elite troops cut down exhausted attackers with minimal Castilian casualties. Proven himself in the most demanding independent command. Redemption arc fulfilled.",
        "location": "Alcala la Real",
    },
    {
        "id": "pedro_gonzalez_de_padilla",
        "current_task": "Led Second Battle during the battle; maintained discipline and tactical reserve. Now coordinating post-battle consolidation, casualty assessment, and prisoner management at Alcala la Real",
        "location": "Alcala la Real",
    },
    {
        "id": "garcia_fernandez_de_baeza",
        "current_task": "Led First Battle — struck Sultan's left flank, maintained good formation order during pursuit. Distinguished himself in battle.",
        "location": "Alcala la Real",
    },
    {
        "id": "rodrigo_de_narvaez",
        "current_task": "Led Third Battle — maintained perfect order as reserve, anchored the line. Barely engaged as enemy broke before reaching his position.",
        "location": "Alcala la Real",
    },
    {
        "id": "alvar_perez_de_guzman",
        "current_task": "Rallied 200 knights to Juan's banner during pursuit phase; served as cavalry commander during the battle consolidation",
        "location": "Alcala la Real",
    },
    {
        "id": "pietro_calabrese",
        "current_task": "Single bombard deployed as bait at siege works — deception plan worked perfectly. Never needed to fire additional shots. All 5 bombards intact and ready for continued operations",
        "location": "Alcala la Real",
    },
    {
        "id": "fernan_alonso_de_robles",
        "current_task": "Crusaders held at siege works under Enrique's command. Guardian Company engaged in cavalry combat — several knights wounded protecting the king",
        "location": "Alcala la Real",
    },
    {
        "id": "fray_hernando",
        "current_task": "Beginning instruction for 70+ Muslim converts from Alcala la Real garrison; managing unprecedented mass conversion process",
        "location": "Alcala la Real",
    },
]

NEW_LOCATIONS = []

NEW_FACTIONS = []
FACTION_UPDATES = [
    {
        "faction_id": "royal_court",
        "description": "Decisive victory at Battle of Alcala la Real (April 1, 1431). Sultan's 16,000-man field army destroyed — 10,000-11,000 casualties, Sultan fled with 2,000-3,000 survivors. Castilian casualties light (~1,500-1,700 of 23,000). Fortress surrendered with unprecedented mass conversion — 70+ garrison converting, qadi joining court. Complete intelligence windfall. Western army launching simultaneously. Granada's military power broken. Two-army strategy executing perfectly.",
    },
]

ROLLS = [
    {
        "event_index": 0,
        "title": "Sultan's Scout Report on Castilian Deployment",
        "context": "Sultan's scouts approach Castilian positions at Alcala la Real. Deception plan in place: siege works appear vulnerable with 5,000 troops and single bombard, main army of 18,000 concealed. Cavalry screen active.",
        "roll_type": "intelligence",
        "date": "1431-04-01",
        "rolled": 73,
        "outcome_range": "72-85",
        "outcome_label": "Good Observation — Tactical Clarity",
        "outcome_detail": "Skilled scouts identify force composition: 23,000 total, siege works with 5,000 elite under Infante Enrique, three infantry formations, 4,000 heavy cavalry under Juan personally. Single bombard visible, suspects more. Construction deliberate, not panicked. May suspect bait. Professional preparation recognized.",
        "evaluation": "Good result for Sultan — accurate picture of Castilian strength. Should have warned against attack. Makes the Sultan's subsequent decision even more catastrophic.",
        "success_factors": ["Experienced scouts", "Multiple observation angles", "Hours of surveillance"],
        "failure_factors": ["Doesn't know exact battle plan", "Hidden bombards not confirmed"],
    },
    {
        "event_index": 0,
        "title": "Sultan's Strategic Decision",
        "context": "Sultan Muhammad IX has good intelligence (roll 73). Knows 23,000 fresh Castilian troops in prepared positions with artillery. His 16,000 are exhausted from 40-mile forced march. Outnumbered, outgunned, out-positioned. But jihad declared — political/religious pressure to act.",
        "roll_type": "military",
        "date": "1431-04-01",
        "rolled": 3,
        "outcome_range": "1-8",
        "outcome_label": "Desperate Frontal Assault — Immediate Attack",
        "outcome_detail": "Sultan refuses to accept he missed his window. Orders immediate frontal assault despite exhaustion, numerical inferiority, and prepared positions. No rest, no tactical refinement. Jihad fervor overrides military prudence. Troops kept in march column, pushed straight at siege works. Catastrophic decision.",
        "evaluation": "Extraordinary low roll. The worst possible military decision given the intelligence available. Dooms 16,000 men. Jihad fervor and desperation completely override rational military judgment.",
        "success_factors": [],
        "failure_factors": ["Troop exhaustion total", "Numerical inferiority", "Attacking prepared positions", "No rest", "No tactical deployment"],
    },
    {
        "event_index": 1,
        "title": "Initial Battle Engagement",
        "context": "Sultan's exhausted 16,000 assault Castilian positions. Enrique holds siege works with 5,000 elite. Juan deploys 18,000 reserves — three infantry battles advance, heavy cavalry flanks. Sultan's troops have marched 40 miles in 2 days with no rest before combat.",
        "roll_type": "military",
        "date": "1431-04-01",
        "rolled": 97,
        "outcome_range": "93-100",
        "outcome_label": "Catastrophic Moorish Collapse — Immediate Rout",
        "outcome_detail": "Sultan's gambit fails spectacularly within first hour. Exhausted troops cannot sustain assault. Multiple units break on initial contact. Panic spreads through army. Enrique's defenders barely scratched. Deploying Castilian battles encounter fleeing enemies, not formed resistance. Enemy army disintegrating into mob before cavalry even charges.",
        "evaluation": "Near-maximum roll creating historic one-sided victory. Combined with Sultan's disastrous roll of 3, this is a perfect storm. Exhaustion was so total that battle ended before truly beginning.",
        "success_factors": ["Complete exhaustion of enemy", "Elite defenders at siege works", "Coordinated deployment", "Deception plan working"],
        "failure_factors": [],
    },
    {
        "event_index": 1,
        "title": "Juan's First Cavalry Charge",
        "context": "Juan leads 4,000 heavy cavalry in flanking charge against collapsing Moorish infantry. Guardian Company protecting him. Enemy formations already disintegrating. But Moroccan elite cavalry (2,000) still in the field.",
        "roll_type": "military",
        "date": "1431-04-01",
        "rolled": 17,
        "outcome_range": "9-22",
        "outcome_label": "Partial Success — Hard Fighting",
        "outcome_detail": "Charge devastates fleeing infantry but Moroccan professional cavalry counter-charges. Fierce melee erupts. Guardian Company heavily engaged protecting Juan. Juan parries enemy blade in personal combat. Guardian knight Martín de Oviedo wounded saving Juan's life (blade at neck/shoulder gap). Moroccans eventually driven off. Charge successful but messy — Juan shaken by violence.",
        "evaluation": "Low-middle roll creating real danger for Juan despite overall victory. The Moroccan counter-charge adds drama and personal stakes. Juan's first real combat experience is visceral and dangerous.",
        "success_factors": ["Overwhelming numbers", "Enemy infantry already breaking"],
        "failure_factors": ["Moroccan elite cavalry counter-charge", "Guardian casualties", "Personal danger to king"],
    },
    {
        "event_index": 2,
        "title": "Cavalry Rally Attempt",
        "context": "After initial charge, Juan's 4,000 cavalry scattered in pursuit. Juan rides to vantage point, then attempts to rally scattered knights for organized pursuit. White armor visible, True Cross banner streaming.",
        "roll_type": "leadership",
        "date": "1431-04-01",
        "rolled": 29,
        "outcome_range": "26-45",
        "outcome_label": "Moderate Rally — Respectable Force",
        "outcome_detail": "~800 knights respond over 10-15 minutes. Guardian Company forms core. Don Álvar Pérez de Guzmán brings 200 knights. Not everyone answers — many continue individual pursuits. Some great lords' retinues ignore call. Adequate but not overwhelming response. Authority tested but not failed.",
        "evaluation": "Middle-low result reflecting realistic difficulty of rallying scattered cavalry after a victorious charge. Glory-seeking and exhaustion compete with royal authority.",
        "success_factors": ["King's visible presence", "White armor and banner", "Victory momentum"],
        "failure_factors": ["Knights pursuing glory/plunder", "Exhaustion", "Scattered formation"],
    },
    {
        "event_index": 2,
        "title": "Pursuit Flanking Charge",
        "context": "Juan leads 800 rallied cavalry to reinforce pursuit. Targets Moroccan rearguard (1,200-1,500) protecting Sultan's fleeing mob (4,000-5,000). Same tactic: lead initially, let guard overtake before contact. 45 minutes daylight remaining.",
        "roll_type": "military",
        "date": "1431-04-01",
        "rolled": 13,
        "outcome_range": "13-28",
        "outcome_label": "Contested Breakthrough — Hard Fight",
        "outcome_detail": "Moroccan cavalry forms blocking force, fights desperately. Running cavalry battle. Charge hits organized resistance. Formation scattered in fighting. Guardian knight wounded. Breakthrough achieved but disorganized. ~500-800 enemy killed in pursuit before darkness. Sultan's main body (3,000+) escapes into gathering dusk. Moroccan cavalry successfully screens most of retreat.",
        "evaluation": "Another low roll creating hard fighting where easy victory expected. Consistent theme: the cavalry pursuit phases were the hardest part of an otherwise one-sided battle. Moroccan professionals proving their quality even in defeat.",
        "success_factors": ["Numerical advantage", "Enemy infantry defenseless"],
        "failure_factors": ["Moroccan professional resistance", "Lost cohesion", "Darkness approaching"],
    },
    {
        "event_index": 4,
        "title": "Fortress Garrison Surrender Response",
        "context": "Garrison of 380 watched entire battle from walls. Sultan's army destroyed. No relief possible. Juan offers generous terms: lay down arms, keep possessions, safe passage. Or bombardment by 5 bombards.",
        "roll_type": "diplomacy",
        "date": "1431-04-02",
        "rolled": 96,
        "outcome_range": "96-100",
        "outcome_label": "Complete Capitulation — Strategic Breakthrough",
        "outcome_detail": "Commander Yusuf ibn Rashid comes not just to surrender but to convert. 70+ of 380 garrison wish to convert to Christianity and join crusade. Qadi's faith profoundly shaken. Offer fortress intact with complete intelligence. Propaganda earthquake across the frontier.",
        "evaluation": "Near-maximum roll creating unprecedented strategic development. Combined with the catastrophic battle, creates theological crisis across Granada. Every fortress commander will hear about this.",
        "success_factors": ["Witnessed catastrophic defeat", "Generous terms", "Crisis of faith", "Practical hopelessness"],
        "failure_factors": [],
    },
    {
        "event_index": 5,
        "title": "Qadi's Response to Court Invitation",
        "context": "Ahmad al-Zarqali, qadi of Alcala la Real, in deep spiritual crisis. Juan offers freedom to leave or join court with complete religious freedom. No pressure to convert.",
        "roll_type": "diplomacy",
        "date": "1431-04-02",
        "rolled": 77,
        "outcome_range": "69-82",
        "outcome_label": "Genuine Acceptance — Sees Opportunity",
        "outcome_detail": "Ahmad accepts — rare chance to honestly engage with Christianity. Expert in answers taught, not questions discovered. Values intellectual/spiritual exploration. Practical: safer than returning to Granada. Honest: 'I do not promise conversion, but I promise honest seeking.' Sincere acceptance motivated by intellectual and spiritual curiosity.",
        "evaluation": "Good result creating a complex, interesting court advisor character. Neither blind convert nor hostile prisoner — a genuine truth-seeker whose presence enriches the court.",
        "success_factors": ["Genuine offer of freedom", "Intellectual opportunity", "Practical safety"],
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
        "chapter": "1.16",
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
    print(f"Chapter 1.16 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  New locations:     {len(NEW_LOCATIONS)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Written to:        {OUTPUT}")

if __name__ == "__main__":
    main()
