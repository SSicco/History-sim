#!/usr/bin/env python3
"""Add missing characters to characters.json identified by review_needed.json flags."""

import json
import sys

CHARACTERS_FILE = "resources/data/characters.json"

NEW_CHARACTERS = [
    {
        "id": "luis_de_guzman_niebla",
        "name": "Don Luis de Guzmán (Niebla)",
        "aliases": ["luis_de_guzman_niebla"],
        "title": "Brother of the Count of Niebla",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["nobility"],
        "location": "Niebla",
        "current_task": "Defected from his brother Count Diego during the garrison mutiny at Niebla. Pleaded for mercy for the mad Count.",
        "personality": ["conflicted", "emotional", "loyal"],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "Count Diego de Medina-Sidonia's younger brother. Stood beside Diego at the failed parley but turned against him when Diego ordered the garrison to die rather than surrender. Led the officers' delegation to surrender Niebla.",
        "rolled_traits": [],
        "faction_ids": [],
        "event_refs": ["evt_1432_00275", "evt_1432_00276", "evt_1432_00277", "evt_1432_00278", "evt_1432_00279"],
        "appearance": {},
        "portrait_prompt": ""
    },
    {
        "id": "doctor_fernandez",
        "name": "Doctor Fernández",
        "aliases": ["doctor_fernandez", "dr_fernandez"],
        "title": "Royal Physician",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["royal_court"],
        "location": "Toledo",
        "current_task": "Serving as royal physician, attended the births of both Catalina and Fernando.",
        "personality": ["experienced", "dedicated", "competent"],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "Longtime royal physician who attended Juan's own birth. Revived baby Catalina after a difficult delivery. Trusted medical authority in the royal household.",
        "rolled_traits": [],
        "faction_ids": ["royal_court"],
        "event_refs": ["evt_1432_00158", "evt_1432_00159"],
        "appearance": {},
        "portrait_prompt": ""
    },
    {
        "id": "maria_wet_nurse",
        "name": "María (Wet Nurse)",
        "aliases": ["maria_wet_nurse", "the_wet_nurse"],
        "title": "Royal Wet Nurse",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["royal_court"],
        "location": "Toledo",
        "current_task": "Nursing Princess Catalina.",
        "personality": ["sturdy", "reliable", "maternal"],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "Sturdy Toledo woman chosen as wet nurse for Princess Catalina. A recurring presence in the royal nursery.",
        "rolled_traits": [],
        "faction_ids": ["royal_court"],
        "event_refs": ["evt_1432_00158"],
        "appearance": {},
        "portrait_prompt": ""
    },
    {
        "id": "rodrigo_fernandez_castellan",
        "name": "Rodrigo Fernández",
        "aliases": ["rodrigo_fernandez_castellan", "castellan_rodrigo"],
        "title": "Castellan of Niebla",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Niebla",
        "current_task": "Led the garrison mutiny against Count Diego, surrendered Niebla to the crown.",
        "personality": ["experienced", "pragmatic", "loyal", "weathered"],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "Old castellan of Niebla who removed Count Diego from command when the Count ordered the garrison to die. Led the officers' surrender delegation.",
        "rolled_traits": [],
        "faction_ids": [],
        "event_refs": ["evt_1432_00275", "evt_1432_00276"],
        "appearance": {},
        "portrait_prompt": ""
    },
    {
        "id": "father_miguel",
        "name": "Father Miguel",
        "aliases": ["father_miguel"],
        "title": "Chaplain",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["clergy"],
        "location": "Constantinople",
        "current_task": "Serving as chaplain to the crusade fleet, providing Latin instruction.",
        "personality": ["pious", "dedicated", "scholarly"],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "Chaplain who provides Latin instruction and is involved in cathedral conversion plans during the crusade.",
        "rolled_traits": [],
        "faction_ids": ["crusade_delegation"],
        "event_refs": ["evt_1433_00370"],
        "appearance": {},
        "portrait_prompt": ""
    },
    {
        "id": "giovanni_rossi",
        "name": "Giovanni Rossi",
        "aliases": ["giovanni_rossi"],
        "title": "Standard-bearer of the True Cross",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Constantinople",
        "current_task": "Carrying the True Cross banner for the crusade.",
        "personality": ["devoted", "resilient", "humble"],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "One-handed blacksmith turned crusader. Carries the True Cross banner with fierce devotion despite his disability.",
        "rolled_traits": [],
        "faction_ids": ["crusade_delegation"],
        "event_refs": ["evt_1433_00370"],
        "appearance": {
            "distinguishing_features": "One-handed, carries True Cross banner"
        },
        "portrait_prompt": ""
    },
    {
        "id": "brother_guillem",
        "name": "Brother Guillem",
        "aliases": ["brother_guillem"],
        "title": "Benedictine Monk",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["clergy"],
        "location": "Constantinople",
        "current_task": "Spiritual counsel to the crusaders, intermediary to the Byzantine delegation.",
        "personality": ["scholarly", "diplomatic", "pious"],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "Benedictine monk who leads the monastery-trained voices among the crusaders. Serves as spiritual counsel and intermediary to the Byzantine delegation.",
        "rolled_traits": [],
        "faction_ids": ["crusade_delegation"],
        "event_refs": ["evt_1433_00370", "evt_1433_00384"],
        "appearance": {},
        "portrait_prompt": ""
    },
    {
        "id": "andrea_vescovi",
        "name": "Andrea Vescovi",
        "aliases": ["andrea_vescovi"],
        "title": "Crusader Company Commander",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Constantinople",
        "current_task": "Commanding a company of crusaders.",
        "personality": ["devoted", "humble", "transformed", "determined"],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "The first crusader sworn to Juan's cause. A gangly Florentine farmer's son who has been transformed into a hardened company commander. Scarred from campaigns.",
        "rolled_traits": [],
        "faction_ids": ["crusade_delegation"],
        "event_refs": ["evt_1433_00370", "evt_1433_00384"],
        "appearance": {
            "distinguishing_features": "Scarred, hardened from campaigns, originally gangly"
        },
        "portrait_prompt": ""
    },
    {
        "id": "abbott_rodrigo_gonzalez",
        "name": "Abbott Rodrigo González",
        "aliases": ["abbott_rodrigo", "rodrigo_gonzalez"],
        "title": "Abbott, Chief Castilian Delegate to the Council of Basel",
        "born": "1360-00-00",
        "status": ["active"],
        "category": ["clergy"],
        "location": "Basel",
        "current_task": "Leading the 32-member Castilian delegation at the Council of Basel.",
        "personality": ["experienced", "precise", "energetic", "elderly"],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "73 years old, remarkably energetic for his age. Chief Castilian delegate at Basel who moves with surprising speed. Manages the complex theological and political negotiations at the Council.",
        "rolled_traits": [],
        "faction_ids": ["castilian_delegation"],
        "event_refs": ["evt_1433_00384", "evt_1433_00385"],
        "appearance": {
            "age_appearance": "early 70s",
            "distinguishing_features": "Surprisingly quick-moving for his age"
        },
        "portrait_prompt": ""
    },
    {
        "id": "cardinal_giuliano_cesarini",
        "name": "Cardinal Giuliano Cesarini",
        "aliases": ["cesarini", "cardinal_cesarini", "giuliano_cesarini"],
        "title": "Cardinal, President of the Council of Basel",
        "born": "1398-00-00",
        "status": ["active"],
        "category": ["clergy"],
        "location": "Basel",
        "current_task": "Presiding over the Council of Basel as papal legate, attempting to hold the Church together between papal and conciliar factions.",
        "personality": ["intelligent", "exhausted", "diplomatic", "sincere", "weary", "hopeful"],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "President of the Council of Basel and papal legate. An intelligent, sincere churchman crushed by the weight of trying to hold together a fractured Church. Found genuine hope in Juan's theological insights about human error vs. Church error. Deeply impressed by Juan's spiritual maturity.",
        "rolled_traits": [],
        "faction_ids": ["papacy", "council_of_basel"],
        "event_refs": ["evt_1433_00389", "evt_1433_00390", "evt_1433_00391"],
        "appearance": {
            "age_appearance": "early 40s",
            "distinguishing_features": "Intelligent face, dark circles under eyes, lines around mouth from exhaustion"
        },
        "portrait_prompt": ""
    },
    {
        "id": "jean_de_rochetaillee",
        "name": "Jean de Rochetaillée",
        "aliases": ["jean_de_rochetaillee", "bishop_of_senez"],
        "title": "Bishop of Senez",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["clergy"],
        "location": "Basel",
        "current_task": "French conciliarist at Basel, advocating for reform.",
        "personality": ["radical", "intellectual", "passionate"],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "French conciliarist bishop who influenced Juan's thinking on the Hussite question and church reform. Part of the radical reform faction at Basel.",
        "rolled_traits": [],
        "faction_ids": ["council_of_basel"],
        "event_refs": ["evt_1433_00387"],
        "appearance": {},
        "portrait_prompt": ""
    },
    {
        "id": "cardinal_louis_aleman",
        "name": "Cardinal Louis Aleman",
        "aliases": ["louis_aleman", "cardinal_aleman"],
        "title": "Cardinal",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["clergy"],
        "location": "Basel",
        "current_task": "Leading the French radical faction at the Council of Basel, opposing papal authority.",
        "personality": ["radical", "ambitious", "antagonistic", "political"],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "French radical leader at the Council of Basel. Heads the faction most hostile to papal authority. His group demanded audience with Juan upon learning of his presence.",
        "rolled_traits": [],
        "faction_ids": ["council_of_basel"],
        "event_refs": ["evt_1433_00384"],
        "appearance": {},
        "portrait_prompt": ""
    },
    {
        "id": "fernando_de_castilla",
        "name": "Prince Fernando of Castile",
        "aliases": ["fernando", "prince_fernando", "infante_fernando"],
        "title": "Infante of Castile",
        "born": "1433-09-01",
        "status": ["active"],
        "category": ["royal_family"],
        "location": "Toledo",
        "current_task": "Infant son of Juan II and Queen Isabel, being cared for by Doña Beatriz in Toledo.",
        "personality": ["infant", "calm"],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "Son and heir of Juan II and Queen Isabel. Isabel died in childbirth delivering him. Being raised by Doña Beatriz in Toledo while Juan travels. Dark eyes like his mother and sister Catalina.",
        "rolled_traits": [],
        "faction_ids": ["royal_court"],
        "event_refs": ["evt_1433_00421", "evt_1433_00422"],
        "appearance": {
            "age_appearance": "infant",
            "distinguishing_features": "Dark eyes like his mother Isabel"
        },
        "portrait_prompt": ""
    },
    {
        "id": "commander_yahya_ibn_nasir",
        "name": "Commander Yahya ibn Nasir",
        "aliases": ["yahya_ibn_nasir", "commander_yahya"],
        "title": "Fortress Commander",
        "born": "0000-00-00",
        "status": ["active"],
        "category": ["military"],
        "location": "Morocco",
        "current_task": "Commanding fortress operations.",
        "personality": ["military", "strategic", "pragmatic"],
        "interests": [],
        "speech_style": "",
        "core_characteristics": "Fortress commander who appeared during the Granada and Morocco campaigns. Identity sometimes confused with Commander Martin de Alcala in the narrative.",
        "rolled_traits": [],
        "faction_ids": [],
        "event_refs": ["evt_1432_00300"],
        "appearance": {},
        "portrait_prompt": ""
    }
]


def main():
    with open(CHARACTERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing_ids = {c["id"] for c in data["characters"]}
    added = []
    skipped = []

    for char in NEW_CHARACTERS:
        if char["id"] in existing_ids:
            skipped.append(char["id"])
        else:
            data["characters"].append(char)
            added.append(char["id"])

    # Update meta count
    data["meta"]["total_characters"] = len(data["characters"])

    with open(CHARACTERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Added {len(added)} characters:")
    for cid in added:
        print(f"  + {cid}")
    if skipped:
        print(f"\nSkipped {len(skipped)} (already exist):")
        for cid in skipped:
            print(f"  - {cid}")
    print(f"\nTotal characters now: {data['meta']['total_characters']}")


if __name__ == "__main__":
    main()
