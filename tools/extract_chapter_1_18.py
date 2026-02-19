#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.18.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.18_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.18_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 16),
        "date": "1431-04-15",
        "end_date": "1431-06-15",
        "type": "diplomacy",
        "summary": "Embassy to Rome organized and dispatched. Diego Gomez de Sandoval (Count of Castro) leads the diplomatic mission with Fray Hernando (spiritual witness) and Ahmad al-Zarqali (living proof of conversions). Journey roll 40: Minor Complications — arrives Rome late May in good order. Reception roll 51: Strong Positive. Pope Martin V, elderly and ill, grants nearly two-hour audience. Deeply moved by military report and Juan's personal letter pledging perpetual crusade. Calls it 'validation of his papal legacy.' Ahmad undergoes ten days of theological examination by cardinals, becomes sensation in Rome. Cardinal Capranica becomes strong advocate. Embassy returns with: formal papal letter praising Juan as 'model of Christian kingship' with additional indulgences; warm personal letter from dying Pope; letters from Cardinal Orsini; confirmation of Ahmad's authentic conversion signed by multiple cardinals. Ahmad declines offered position in Rome, returns to Castile. Embassy return estimated late July/early August.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "fray_hernando", "ahmad_al_zarqali",
            "diego_gomez_de_sandoval"
        ],
        "factions_affected": ["royal_court"],
        "location": "Jaen",
        "tags": ["diplomacy", "papal", "embassy", "religion", "roll"],
    },
    {
        "msgs": (17, 22),
        "date": "1431-04-11",
        "end_date": "1431-04-14",
        "type": "military",
        "summary": "The Illora Disaster. Roll 5: DISASTER. Despite having 5 bombards and 15,000 troops, a devastating coordinated guerrilla raid on April 11 strikes the siege camp in three columns. Primary target: powder magazine destroyed using Greek fire — eliminates two-thirds of gunpowder. Two of five bombards damaged (cracked barrel, demolished carriage). 400-600 casualties. Two subsequent assault attempts on wall breaches repulsed with 80 dead and 150 wounded. Morale collapses. Relief force of 2,000-3,000 Moorish troops approaches from south. Master of Calatrava writes anguished letter requesting orders — recommends withdrawal. Total Illora casualties ~600.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "pedro_gonzalez_de_padilla"
        ],
        "factions_affected": [],
        "location": "Illora",
        "tags": ["military", "siege", "disaster", "guerrilla", "roll"],
    },
    {
        "msgs": (23, 32),
        "date": "1431-04-17",
        "end_date": "1431-04-18",
        "type": "narrative",
        "summary": "Juan makes rapid command decisions: (1) Master of Calatrava to withdraw to Alcala la Real; (2) Enrique at Alcala to secure surroundings and fight guerrillas; (3) Captain Rodrigo Manrique at Velez-Malaga to advance on Malaga and the coast — told to exercise independent command rather than waiting for instructions; (4) Alvaro remains in Jaen coordinating. Juan will depart next day to join the eastern army personally. Evening farewell with Isabel — she reveals she is 'almost certain' pregnant. Juan asks for something to remember her by; Isabel gives him her pale blue silk prayer ribbon saying 'Keep it close, Juan. And come back to me.' Juan departs at dawn.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "isabel_of_portugal",
            "rodrigo_manrique"
        ],
        "factions_affected": [],
        "location": "Jaen",
        "tags": ["narrative", "command", "personal", "pregnancy", "farewell"],
    },
    {
        "msgs": (33, 48),
        "date": "1431-04-19",
        "end_date": "1431-04-20",
        "type": "military",
        "summary": "Journey roll 93: Exceptional Journey. Perfect weather, clear routes. On April 19, Juan crests a hill and spots a Calatrava column of 3,000-4,000 withdrawing troops about to be ambushed by 20-23 Moorish raiders. Counter-ambush roll 80: Clear Success. 18 Castilians (Sergeant Garcia, Corporal Rodrigo, Captain Fernan) rout 23 raiders from behind — 8-10 killed, raider commander killed by Garcia. Castilian casualties: two cuts and a twisted ankle. Juan mounts up with banner and rides through the entire demoralized column — effect electric, men shouting 'Castilla!' and 'Santiago!', some weeping. Word spreads: 'the king ambushed the raiders.' Meets Master of Calatrava at column head. Withdrawal orderly, all 15,000 accounted for, damaged bombards salvageable (2 weeks repair). Army arrives Alcala April 20, combined ~19,800 troops.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "fernan_alonso_de_robles",
            "garcia_lopez_de_padilla"
        ],
        "factions_affected": [],
        "location": "Alcala la Real",
        "tags": ["military", "journey", "ambush", "morale", "roll"],
    },
    {
        "msgs": (49, 62),
        "date": "1431-05-04",
        "end_date": "1431-05-07",
        "type": "military",
        "summary": "War council at Alcala after two weeks of rest (May 4). Intelligence roll 26: Adequate Tactical Intelligence — good within 20 miles (Illora 650-700, Moclin 400, Montefrio 200-250, Loja 800-1,000), 14 villages secured, 8 guerrilla groups identified. Don Rodrigo de Perea presents briefing. Juan asks about Loja without artillery — council unanimously advises against (stronger than Illora, which failed even with bombards). Juan proposes bold alternative: march 10,000 troops to Granada itself, carry crusade banner to the gates, demand Sultan's surrender, torch countryside on withdrawal, then return to consolidation. Council stunned but unanimously approves. Enrique: 'magnificent.' Master: 'bold enough to be remembered, cautious enough to succeed.' Enrique commands ~9,800 reserve at Alcala. Force: 6,000 infantry + 4,000 cavalry, 2 weeks supplies.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "infante_enrique_de_aragon",
            "rodrigo_de_perea", "garcia_lopez_de_padilla"
        ],
        "factions_affected": [],
        "location": "Alcala la Real",
        "tags": ["military", "war_council", "strategy", "roll", "bold"],
    },
    {
        "msgs": (63, 68),
        "date": "1431-05-08",
        "end_date": "1431-05-09",
        "type": "military",
        "summary": "March to Granada begins May 8, Juan at the head in white armor with white banners. Deliberately conspicuous — open challenge. Moorish scouts observe but don't engage. Roll 86: Sultan's response — Excellent Strategic Response. Sultan has assembled 3,000-3,500 troops including Moroccan reinforcements that arrived earlier than expected. Roll 79: Unexpected Military Reinforcement confirms larger garrison. Roll 41: Sultan's specific plan — Sortie During Demand Ceremony. All 3,000-3,500 troops positioned inside city with gates ready. When Juan approaches to make formal demand, Sultan refuses from walls then immediately 2,000+ troops pour out to kill or capture the king.",
        "characters": [
            "juan_ii", "pedro_gonzalez_de_padilla", "fadrique_enriquez"
        ],
        "factions_affected": [],
        "location": "Granada",
        "tags": ["military", "march", "roll", "sultan", "trap"],
    },
    {
        "msgs": (69, 82),
        "date": "1431-05-09",
        "end_date": "1431-05-10",
        "type": "military",
        "summary": "Intelligence coup — Roll 93: Near-Certainty. Cavalry scouts intercept Moorish courier Muhammad ibn Tariq carrying sealed documents revealing the entire sortie plan: 2,500-3,000 troops (1,200 regular infantry, 800 Moroccan, 400 Moclin cavalry, 500-700 additional cavalry) will pour from western gate the instant Sultan refuses demand. Goal: kill or capture the king. Juan decides to proceed anyway, turning Sultan's trap into Castilian counter-trap. Plan: 300 elite cavalry escort Juan to ~300 yards from gates; 1,000 infantry secretly deployed overnight in concealed positions 600-700 yards from gate (NOT hidden reserve — rush to form battle line immediately); 2,500 light cavalry screen; 4,500 infantry advance to reinforce; 1,500 heavy cavalry under Don Fadrique delivers hammer. Don Rodrigo de Perea leads night deployment without detection. 300-man escort: 50 Guardian Company, 150 Calatrava heavy cavalry, 100 frontier horsemen. Dawn May 10 — army deployed, Juan about to ride to the gates.",
        "characters": [
            "juan_ii", "fernan_alonso_de_robles", "rodrigo_de_perea",
            "fadrique_enriquez", "garcia_lopez_de_padilla"
        ],
        "factions_affected": [],
        "location": "Granada",
        "tags": ["military", "intelligence", "counter_trap", "battle_planning", "roll"],
    },
]

NEW_CHARACTERS = [
    {
        "id": "garcia_lopez_de_padilla",
        "name": "Don García López de Padilla",
        "aliases": ["garcia_lopez_de_padilla"],
        "title": "Senior Calatrava Knight",
        "born": "1388-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Granada",
        "current_task": "Senior Calatrava knight serving in the eastern army; commanded the column section saved from ambush by Juan; participates in war councils and battle planning at Granada",
        "personality": ["professional", "loyal", "tactical"],
        "interests": ["Calatrava Order", "military tactics", "siege warfare"],
        "speech_style": "Professional military speech. Tactical and respectful.",
        "core_characteristics": "Senior Calatrava knight. Commands column section that Juan's personal escort saved from Moorish ambush. Provides tactical advice on positioning and gate bottleneck at Granada.",
        "faction_ids": [],
        "appearance": {},
    },
    {
        "id": "rodrigo_de_perea",
        "name": "Don Rodrigo de Perea",
        "aliases": ["rodrigo_de_perea", "perea"],
        "title": "Reconnaissance Coordinator, Eastern Army",
        "born": "1393-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Granada",
        "current_task": "Reconnaissance coordinator for the eastern army; presented intelligence briefing at war council; personally led the night deployment of 1,000 flanking infantry at Granada without detection",
        "personality": ["precise", "competent", "resourceful", "quiet"],
        "interests": ["reconnaissance", "intelligence gathering", "field operations"],
        "speech_style": "Precise and factual. Presents intelligence clearly with qualifications on confidence levels.",
        "core_characteristics": "Reconnaissance coordinator for the eastern army. Presents intelligence briefings. Personally led the critical night deployment of 1,000 infantry into concealed positions near Granada's gates — succeeded without detection.",
        "faction_ids": [],
        "appearance": {},
    },
    {
        "id": "fadrique_enriquez",
        "name": "Don Fadrique Enríquez de Mendoza",
        "aliases": ["fadrique_enriquez", "fadrique_enriquez_de_mendoza", "admiral_fadrique"],
        "title": "Admiral of Castile / Cavalry Commander",
        "born": "1386-00-00",
        "status": ["active"],
        "category": ["military", "nobility"],
        "location": "Granada",
        "current_task": "Commands the cavalry response (2,500 light + 1,500 heavy) for the planned battle at Granada's gates; told Juan directly 'Trust me to win the battle'; fought at Antequera under Juan's father",
        "personality": ["confident", "experienced", "authoritative", "battle-hardened"],
        "interests": ["cavalry warfare", "naval command", "military honor"],
        "speech_style": "Confident, direct, authoritative. Speaks with the weight of decades of command experience.",
        "core_characteristics": "Age ~45. Admiral of Castile. Scarred veteran who fought at Antequera under Juan I. Commands all cavalry forces at Granada (2,500 light + 1,500 heavy). His job is to deliver the hammer blow when the Sultan's sortie emerges. 'Trust me to win the battle.'",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "mid 40s",
            "build": "powerful",
            "distinguishing_features": "scarred; veteran bearing; fought at Antequera",
        },
    },
]

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "At Granada's gates with 10,000 troops. About to ride to the walls with 300 elite cavalry to demand Sultan's surrender — knowing Sultan plans sortie to kill him. Counter-trap set: 1,000 hidden infantry, 2,500 light cavalry, 4,500 infantry, 1,500 heavy cavalry. Carrying Isabel's blue silk prayer ribbon. Dawn May 10, 1431.",
        "location": "Granada",
    },
    {
        "id": "alvaro_de_luna",
        "current_task": "At Jaen coordinating logistics and communications between all three armies; managing damaged bombard repairs; caring for wounded; watching over Isabel",
        "location": "Jaen",
    },
    {
        "id": "isabel_of_portugal",
        "current_task": "At Jaen; 'almost certain' pregnant (conceived early March, ~6-7 weeks); gave Juan her pale blue silk prayer ribbon as farewell token; anxious for his safety",
        "location": "Jaen",
    },
    {
        "id": "pedro_gonzalez_de_padilla",
        "current_task": "Withdrew from Illora after disastrous siege failure; now with Juan at Granada's gates with the eastern army; participating in battle planning for the counter-trap",
        "location": "Granada",
    },
    {
        "id": "infante_enrique_de_aragon",
        "current_task": "Commands ~9,800 reserve troops at Alcala la Real; holding the base while Juan marches on Granada; wanting to join but accepting the reserve role",
        "location": "Alcala la Real",
    },
    {
        "id": "fernan_alonso_de_robles",
        "current_task": "Commanding Juan's personal escort; led counter-ambush against 23 Moorish raiders (roll 80); selected the 300-man elite escort for Granada approach (50 Guardian, 150 Calatrava, 100 frontier); pledged to keep Juan alive during the battle",
        "location": "Granada",
    },
    {
        "id": "fray_hernando",
        "current_task": "En route to Rome with embassy delegation; accompanied by Ahmad al-Zarqali and Diego Gomez de Sandoval; will testify before Pope Martin V",
        "location": "En route to Rome",
    },
    {
        "id": "ahmad_al_zarqali",
        "current_task": "En route to Rome as living proof of crusade's spiritual victories; will undergo theological examination by cardinals; becomes sensation in Rome; declines offered position; returns to Castile",
        "location": "En route to Rome",
    },
    {
        "id": "rodrigo_manrique",
        "current_task": "Commanding western army at Velez-Malaga; ordered to advance on Malaga and secure entire coast; told to exercise independent command",
        "location": "Velez-Malaga",
    },
    {
        "id": "pietro_calabrese",
        "current_task": "Repairing 2 damaged bombards at Jaen (cracked barrel and demolished carriage); estimates 2 weeks for repairs; 3 undamaged bombards also at Jaen",
        "location": "Jaen",
    },
]

NEW_LOCATIONS = [
    {
        "location_id": "granada_city",
        "name": "Granada",
        "region": "Emirate of Granada",
        "description": "Capital of the Emirate of Granada. Site of the Alhambra palace. Sultan Muhammad IX's court. Juan II's army of 10,000 has marched to its gates on May 8-9, 1431 for a formal surrender demand. Sultan has 3,000-3,500 troops ready for a sortie. Counter-trap set by Castilians who intercepted the plan.",
        "sub_locations": [
            "The Alhambra",
            "Western Gate",
            "City Walls",
            "Castilian Camp (1 mile from walls)"
        ],
    },
]

NEW_FACTIONS = []
FACTION_UPDATES = [
    {
        "faction_id": "royal_court",
        "description": "Bold pivot: after Illora siege disaster (roll 5), Juan marches 10,000 directly to Granada's gates. Embassy to Rome succeeds (roll 51). Sultan plans sortie to kill Juan but courier intercepted (roll 93). Counter-trap set for May 10. Isabel almost certainly pregnant. Alvaro coordinates from Jaen. Western army advancing on Malaga coast.",
    },
]

ROLLS = [
    {
        "event_index": 0,
        "title": "Embassy Journey to Rome",
        "context": "Delegation (Diego, Fray Hernando, Ahmad, 3 guards) travels from Jaen to Rome overland.",
        "roll_type": "travel",
        "date": "1431-05-01",
        "rolled": 40,
        "outcome_range": "31-50",
        "outcome_label": "Minor Complications",
        "outcome_detail": "Embassy arrives Rome late May in good order with only routine travel difficulties. No significant incidents.",
        "evaluation": "Adequate result. Safe arrival is the key outcome.",
        "success_factors": ["Royal safe conduct", "Experienced diplomat leading"],
        "failure_factors": ["Minor road difficulties"],
    },
    {
        "event_index": 0,
        "title": "Rome's Reception of Embassy",
        "context": "Embassy presents military report, Juan's personal letter pledging perpetual crusade, and Ahmad al-Zarqali as living proof of conversions. Pope Martin V elderly and ill.",
        "roll_type": "diplomacy",
        "date": "1431-06-01",
        "rolled": 51,
        "outcome_range": "46-65",
        "outcome_label": "Strong Positive Reception",
        "outcome_detail": "Pope grants nearly two-hour audience despite frailty. Deeply moved. Calls crusade 'validation of his papal legacy.' Ahmad examined by cardinals for 10 days, becomes sensation. Returns with: formal papal letter praising Juan as 'model of Christian kingship,' dying Pope's personal blessing, Cardinal Orsini's commendation, Ahmad's conversion certified by multiple cardinals.",
        "evaluation": "Strong result. Juan's international standing dramatically elevated. Every future Pope inherits this correspondence.",
        "success_factors": ["Living proof in Ahmad", "Juan's personal letter", "Military victories", "Pope's legacy concerns"],
        "failure_factors": [],
    },
    {
        "event_index": 1,
        "title": "Siege of Illora Progress",
        "context": "15,000 troops with 5 bombards besieging Illora under Master of Calatrava. Guerrilla raiders active in the area. Powder supplies being transported via vulnerable supply lines.",
        "roll_type": "military",
        "date": "1431-04-11",
        "rolled": 5,
        "outcome_range": "01-08",
        "outcome_label": "DISASTER",
        "outcome_detail": "Coordinated night raid by 800-1,000 guerrillas strikes camp in three columns April 11. Powder magazine destroyed with Greek fire — two-thirds of gunpowder eliminated. Two bombards damaged (cracked barrel, demolished carriage). 400-600 casualties. Two assault attempts repulsed (80 dead, 150 wounded). Morale collapses. Relief force approaching. Master recommends withdrawal.",
        "evaluation": "Near-worst possible outcome. Demonstrates guerrilla warfare's effectiveness. Campaign's first major setback. Propaganda victory for Granada.",
        "success_factors": [],
        "failure_factors": ["Powder magazine vulnerability", "Guerrilla sophistication", "Supply line exposure"],
    },
    {
        "event_index": 3,
        "title": "Journey Jaen to Alcala la Real",
        "context": "Juan rides south with ~20 escort to join eastern army. Spring weather, frontier territory with guerrilla activity.",
        "roll_type": "travel",
        "date": "1431-04-19",
        "rolled": 93,
        "outcome_range": "91-98",
        "outcome_label": "Exceptional Journey",
        "outcome_detail": "Perfect weather, clear routes. On April 19 crests hill to see Calatrava column of 3,000-4,000 about to be ambushed by 20-23 Moorish raiders. Discovers ambush in progress, enabling counter-attack.",
        "evaluation": "Outstanding result. Not just safe travel but an opportunity to save troops and boost morale dramatically.",
        "success_factors": ["Perfect conditions", "Alert scouts", "Good timing"],
        "failure_factors": [],
    },
    {
        "event_index": 3,
        "title": "Counter-Ambush of Moorish Raiders",
        "context": "Juan's 18-man escort (2 left with horses) attacks 23 Moorish raiders from behind as they launch ambush on Calatrava column. Total surprise.",
        "roll_type": "military",
        "date": "1431-04-19",
        "rolled": 80,
        "outcome_range": "71-85",
        "outcome_label": "Clear Success",
        "outcome_detail": "Counter-ambush strikes raiders from behind with total surprise. Raider commander killed by Sergeant Garcia. 8-10 raiders killed or wounded in 3 minutes, rest scatter. Castilian casualties: two minor cuts and a twisted ankle.",
        "evaluation": "Decisive small-unit action. Combined with the ride through the column, transforms army morale.",
        "success_factors": ["Total surprise", "Professional soldiers", "Numerical advantage at point of contact"],
        "failure_factors": [],
    },
    {
        "event_index": 4,
        "title": "Scout Intelligence from Alcala la Real",
        "context": "Two weeks of reconnaissance from Alcala la Real base. Multiple scout patrols sent to map fortress dispositions and guerrilla activity.",
        "roll_type": "intelligence",
        "date": "1431-05-04",
        "rolled": 26,
        "outcome_range": "21-35",
        "outcome_label": "Adequate Tactical Intelligence",
        "outcome_detail": "Good within 20 miles: Illora 650-700, Moclin 400, Montefrio 200-250, Loja 800-1,000. 14 villages secured. 8 guerrilla groups identified, 2 camps destroyed. Strategic picture incomplete — Granada assembling 8,000-12,000 by summer. 4 scouts lost (3 killed, 1 captured).",
        "evaluation": "Adequate for local operations but limited strategic picture. The scout losses reflect guerrilla activity.",
        "success_factors": ["Two weeks of sustained effort", "Multiple patrols"],
        "failure_factors": ["Guerrilla interference", "4 scouts lost", "Strategic picture incomplete"],
    },
    {
        "event_index": 5,
        "title": "Sultan's Strategic Response to March on Granada",
        "context": "Juan marches 10,000 troops openly toward Granada. Sultan has been rebuilding forces since Alcala disaster. What is his response?",
        "roll_type": "military",
        "date": "1431-05-09",
        "rolled": 86,
        "outcome_range": "81-93",
        "outcome_label": "Excellent Strategic Response",
        "outcome_detail": "Sultan demonstrates unexpected competence. Has assembled 3,000-3,500 troops including Moroccan reinforcements arriving earlier than expected (roll 79 confirms). Plans a massive sortie (roll 41: all troops positioned behind gates, pour out when Juan approaches to kill/capture the king during demand ceremony).",
        "evaluation": "High roll giving the Sultan real teeth. The sortie plan is cunning — violating parley customs for a decapitation strike.",
        "success_factors": ["Moroccan reinforcements early", "Unified court", "Desperation breeds audacity"],
        "failure_factors": ["Still outnumbered", "Plan depends on surprise"],
    },
    {
        "event_index": 6,
        "title": "Castilian Detection of Sultan's Sortie Plan",
        "context": "10,000 Castilians within a mile of Granada. Walls more heavily manned than expected. Cavalry scouts patrolling.",
        "roll_type": "intelligence",
        "date": "1431-05-09",
        "rolled": 93,
        "outcome_range": "91-98",
        "outcome_label": "Near-Certainty — Specific Intelligence",
        "outcome_detail": "Cavalry scouts intercept Moorish courier Muhammad ibn Tariq carrying sealed documents from Moclin fortress to Sultan. Documents reveal entire sortie plan: 2,500-3,000 troops will pour from western gate when Sultan refuses demand. Explicit goal: 'Kill or capture the Christian king.' Courier confirms authenticity.",
        "evaluation": "Near-maximum roll. Transforms the situation completely — Juan now knows every detail of the Sultan's plan and can set a counter-trap.",
        "success_factors": ["Active cavalry patrols", "Lucky interception", "Documents explicitly detailed"],
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
        "chapter": "1.18",
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
    print(f"Chapter 1.18 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  New locations:     {len(NEW_LOCATIONS)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Written to:        {OUTPUT}")

if __name__ == "__main__":
    main()
