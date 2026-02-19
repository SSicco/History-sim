#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.13.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.13_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.13_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 6),
        "date": "1431-02-15",
        "type": "personal",
        "summary": "Wedding morning at the Royal Alcázar. Chief Chamberlain Don Rodrigo de Villalobos supervises preparations. Juan changes the plan — instead of arming at the cathedral, he dons the white armor privately at the palace. Master Gonzalo de Burgos fits the full Milan plate: arming doublet, leg harness, breastplate, arm harness, gauntlets, gorget, great bascinet with white egret plume, and plain white surcoat without device. Two nine-foot banner poles with white silk banners are attached to saddle brackets. Juan mounts the white destrier and rides test circles in the courtyard — the banners stream eight feet behind like angel wings. Álvaro: 'You look like the Archangel Michael himself.' Fray Hernando blesses the armor with holy water. Guardian Company (50 crusaders) assembled with banner and reliquaries. Procession forms: banner-bearers, reliquary-bearers, crusader honor guard, royal household guard (30 knights), Álvaro at Juan's right hand.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "master_gonzalo_de_burgos",
            "fray_hernando", "don_rodrigo_de_villalobos"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["personal", "armor", "preparation", "wedding"],
    },
    {
        "msgs": (7, 10),
        "date": "1431-02-15",
        "type": "ceremony",
        "summary": "The grand procession through Toledo. Juan commands 'Guardians! We ride!' and the Guardian Company responds 'For Christ and Castile!' Popular response to the white-armored king with streaming banners is overwhelming (Roll: 79 — Overwhelming Positive Response). Streets packed five-six deep, people falling to knees, crying 'An angel! Saint Michael rides to war!' Monks from San Juan de los Reyes join spontaneously. Elderly widow breaks through barriers: 'For my son who fell at Antequera! Finish the work!' At the cathedral plaza, Juan removes his helmet and addresses the crowd — proclaims the Reconquista, promises to march for Granada, asks for prayers. Dismounts, walks to Isabel who waits terrified in her white Portuguese wedding gown. Takes her delicate hand in his gauntleted one, kisses it: 'It will be alright.' She mouths back: 'I trust you.' Together they enter the cathedral.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "alvaro_de_luna",
            "cardinal_capranica", "archbishop_cerezuela",
            "fray_hernando", "inigo_lopez_de_mendoza",
            "pedro_gonzalez_de_mendoza", "enrique_enriquez"
        ],
        "factions_affected": ["royal_court"],
        "location": "Toledo",
        "tags": ["ceremony", "procession", "wedding", "crusade", "roll"],
    },
    {
        "msgs": (11, 18),
        "date": "1431-02-15",
        "type": "ceremony",
        "summary": "Three-hour High Mass in full plate armor at the Cathedral of Toledo. Two thousand witnesses pack the nave, entire congregation kneels as banner and relics process in. Juan endures extreme physical ordeal — shifting weight constantly, muscles trembling, vision darkening briefly during consecration. Isabel holds his hand throughout, whispering encouragement. At the 1:40 mark, Cardinal Capranica unveils the banner and relics to the public for the first time — pure white silk banner with golden True Cross reliquary and silver Saint James bone reliquary. Congregation falls to knees in waves, widespread weeping. Marriage vows: Juan says 'I do. Sí.' Isabel says 'I do. Sim.' Rings exchanged — Juan removes gauntlet to place gold band on Isabel's finger. Isabel crowned as Queen of Castile by Capranica and Archbishop jointly. Communion distributed to two thousand people (30 minutes). Mass ends after three hours and five minutes. Juan and Isabel emerge to thunderous crowd outside.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "cardinal_capranica",
            "archbishop_cerezuela", "alvaro_de_luna", "dona_beatriz",
            "fray_hernando", "inigo_lopez_de_mendoza",
            "enrique_enriquez", "luis_de_guzman"
        ],
        "factions_affected": ["royal_court"],
        "location": "Toledo",
        "tags": ["ceremony", "wedding", "mass", "coronation", "banner", "relics"],
    },
    {
        "msgs": (19, 22),
        "date": "1431-02-15",
        "type": "ceremony",
        "summary": "Public blessing and crusader recruitment on the cathedral plaza platform. Walking to platform, Juan privately tells Isabel the armor was hell — she laughs, breaking tension. Cardinal Capranica proclaims the crusade publicly, Archbishop endorses in Spanish for the common people. Juan addresses the crowd with a realistic speech — acknowledges years of hard work ahead, cold nights on watch, endless sieges, the need to remember this moment when glory seems far away. Offers crusade service regardless of station, promises Granada lands as rewards. Draws his father's sword and cries 'Non nobis domine!' Ten thousand voices echo back. Over 300 volunteers rush forward immediately. Fray Hernando organizes recruitment lines. Diego and clerks begin recording names. Guardian Company holds formation as symbol of sacred purpose.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "cardinal_capranica",
            "archbishop_cerezuela", "alvaro_de_luna", "fray_hernando"
        ],
        "factions_affected": ["royal_court"],
        "location": "Toledo",
        "tags": ["ceremony", "crusade", "recruitment", "speech"],
    },
    {
        "msgs": (23, 26),
        "date": "1431-02-15",
        "type": "narrative",
        "summary": "Royal tour through Toledo lasting nearly two hours. Commercial districts: guild masters bow as procession passes. Metalworkers donate 50 florins, cloth merchants pledge banners, leatherworkers offer saddles at cost. Artisan quarters: smiths' apprentices hold hammers high in salute, elderly carpenter weeps for grandson taking the oath. Jewish quarter: rabbi pledges 10,000 maravedís and community loyalty — carefully calculated to show support without attracting resentment. Northern residential districts: lesser nobles pledge men and supplies. A widow in black cries out about her husband at Antequera and son now taking the oath; Isabel sends coins via a guard. Juan's body in agony after 4+ hours in armor but maintains the image. Return to Alcázar — Juan practically falls from horse. Master Gonzalo supervises disarming piece by piece; padding soaked through with sweat. Juan's feet swollen and red. Isabel stays with him. Álvaro reports over 300 new crusaders sworn, recruitment still continuing.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "alvaro_de_luna",
            "master_gonzalo_de_burgos", "don_rodrigo_de_villalobos"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["tour", "procession", "disarming", "guilds", "recruitment"],
    },
    {
        "msgs": (27, 28),
        "date": "1431-02-15",
        "type": "diplomacy",
        "summary": "Noble dinner at the Alcázar great hall — approximately 200 of Castile's most important figures. Juan rests and changes into normal court dress, feeling light as a feather. After multiple courses and building tension, Álvaro announces the practical crusade measures. Juan announces: 5% tax on noble estate revenues, 10% on church revenues, joint crown-Vatican assessment teams, 2,000 maravedí exemption for personal crusade service. Also invokes papal bull authority to raise noble levies — ancient feudal contract obligations. Promises Granada lands divided among fighters by contribution. Committed houses (Mendoza, Enríquez, Guzmán) respond enthusiastically. Calculating nobility rises with reservation — 5% is substantial but opposition is politically dangerous after the day's fervor. Don García de Ayala reluctantly complies but warns about poor harvests. Cardinal Capranica endorses: 'This is how a Christian king prosecutes holy war.' Six nobles approach Álvaro during dinner about taking crusader oaths specifically to reduce tax burden. Isabel observes: 'You've given them no room to refuse without looking like they oppose the crusade itself.'",
        "characters": [
            "juan_ii", "isabel_of_portugal", "alvaro_de_luna",
            "cardinal_capranica", "archbishop_cerezuela",
            "inigo_lopez_de_mendoza", "pedro_gonzalez_de_mendoza",
            "enrique_enriquez", "luis_de_guzman", "dona_beatriz"
        ],
        "factions_affected": ["royal_court"],
        "location": "Toledo",
        "tags": ["diplomacy", "taxation", "dinner", "politics", "crusade"],
    },
]

NEW_CHARACTERS = [
    {
        "id": "don_rodrigo_de_villalobos",
        "name": "Don Rodrigo de Villalobos",
        "aliases": ["don_rodrigo_de_villalobos", "rodrigo_de_villalobos", "villalobos"],
        "title": "Chief Chamberlain of the Royal Household",
        "born": "1371-00-00",
        "status": ["active"],
        "category": ["court"],
        "location": "Toledo",
        "current_task": "Managing royal household logistics for wedding day and ongoing court operations; coordinating procession routes, armoring schedules, and noble arrivals",
        "personality": ["precise", "formal", "reliable", "awed"],
        "interests": ["court protocol", "logistics", "royal ceremony"],
        "speech_style": "Formal and professionally precise; occasionally overcome by genuine emotion when witnessing extraordinary events",
        "core_characteristics": "Elderly chief chamberlain who supervised all wedding day preparations with military precision. Coordinated Juan's private armoring at the Alcázar, managed the processional route through Toledo, and organized the return. A man of protocol and order who was visibly moved beyond his usual formality by the spectacle of Juan in white armor.",
        "faction_ids": ["royal_court"],
        "appearance": {
            "age_appearance": "elderly",
            "build": "average",
            "distinguishing_features": "bearing of a senior court official",
        },
    },
]

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "Wedding completed; married and crowned Isabel as Queen; crusade publicly proclaimed to overwhelming response (300+ new volunteers); taxation announced and accepted by nobility; preparing for spring 1431 campaign launch",
        "location": "Toledo",
    },
    {
        "id": "isabel_of_portugal",
        "title": "Queen of Castile",
        "current_task": "Crowned Queen of Castile at the wedding; growing confidence and partnership with Juan; overcoming initial terror to show queenly composure; observing noble politics with sharp intelligence",
        "location": "Toledo",
    },
    {
        "id": "alvaro_de_luna",
        "current_task": "Wedding and crusade proclamation executed successfully; managing noble compliance with taxation; coordinating crusader recruitment (300+ new volunteers); preparing assessment teams for spring deployment",
        "location": "Toledo",
    },
    {
        "id": "master_gonzalo_de_burgos",
        "current_task": "White armor commission completed and proven through 4-hour wedding ordeal; supervised disarming after the ceremony; armor performed flawlessly without a single joint failure or broken strap",
        "location": "Toledo",
    },
    {
        "id": "fray_hernando",
        "current_task": "Blessed Juan's armor before the procession; organizing crusader recruitment at the cathedral; processing 300+ new volunteers with evaluation for fitness and purpose; Guardian Company formally named",
        "location": "Toledo",
    },
    {
        "id": "cardinal_capranica",
        "current_task": "Officiated the royal wedding and Isabel's coronation; proclaimed crusade publicly with full papal authority; endorsed taxation program to the nobility; described the day as 'the power of genuine faith wedded to political theater'",
        "location": "Toledo",
    },
    {
        "id": "archbishop_cerezuela",
        "current_task": "Co-officiated the royal wedding with Cardinal Capranica; endorsed the crusade in Spanish for the common people; member of the taxation oversight committee alongside Juan and Capranica",
        "location": "Toledo",
    },
]

NEW_LOCATIONS = []
NEW_FACTIONS = []
FACTION_UPDATES = [
    {
        "faction_id": "royal_court",
        "member_ids": {"add": ["don_rodrigo_de_villalobos"]},
        "description": "Royal wedding completed; Isabel crowned Queen. Crusade publicly proclaimed with overwhelming popular support (Roll 79). Over 300 new crusaders recruited in single afternoon. Taxation announced: 5% noble estates, 10% church, joint crown-Vatican assessment, 2,000 maravedí exemption for personal service. All major noble houses compliant. Spring 1431 campaign launch preparations underway.",
    },
]

ROLLS = [
    {
        "event_index": 1,
        "title": "Popular Response to Royal Wedding Procession",
        "context": "Juan rides through Toledo in unprecedented white plate armor with streaming white banners on a white destrier, preceded by the Guardian Company carrying the blessed banner and relics. The visual spectacle is extraordinary — no one in Toledo has seen anything like it. The crowd has been waiting since before dawn. Factors in favor: deeply religious society, legitimate papal crusade, unprecedented visual spectacle, weeks of anticipation, Toledo as religious heart of Castile, Portuguese alliance welcomed. Factors against: Juan is young and untested, crusade hasn't achieved anything yet, medieval cynicism about royal theater, not everyone wants sons going to war.",
        "roll_type": "social",
        "date": "1431-02-15",
        "rolled": 79,
        "outcome_range": "66-85",
        "outcome_label": "Overwhelming Positive Response",
        "outcome_detail": "Deafening roar from tens of thousands. Widespread tears and open weeping. Strong religious ecstasy in significant portions of crowd. People falling to knees spontaneously. 'Angel of God' and 'Saint Michael' rhetoric spreading rapidly. Veterans and widows crying out for fallen loved ones. Monks and clergy joining procession spontaneously. Young men desperate to volunteer immediately. Even skeptical nobles caught up in the moment. Sense of divine providence and sacred mission. The spectacle transcends normal royal theater into genuine mass movement.",
        "evaluation": "Strong success. The combination of unprecedented visual spectacle (white armor, streaming banners, white destrier), legitimate religious authority (papal relics, blessed banner), and months of careful preparation created a response exceeding normal royal theater. Not quite universal fervor (86+), but enough to create irresistible political momentum — opposition to the crusade becomes politically and religiously dangerous.",
        "success_factors": ["Unprecedented white armor visual", "Streaming banner-wing effect", "Legitimate papal relics", "Weeks of popular anticipation", "Toledo as religious capital", "Well-executed Guardian Company discipline"],
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
        "chapter": "1.13",
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
    print(f"Chapter 1.13 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Written to:        {OUTPUT}")

if __name__ == "__main__":
    main()
