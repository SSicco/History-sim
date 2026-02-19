#!/usr/bin/env python3
"""
One-shot extraction script for Chapter 1.12.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PREPROCESSED = PROJECT_ROOT / "tools" / "preprocessed" / "chapter_1.12_preprocessed.json"
OUTPUT = PROJECT_ROOT / "tools" / "extractions" / "chapter_1.12_extracted.json"

EVENT_DEFS = [
    {
        "msgs": (1, 50),
        "date": "1431-01-29",
        "type": "diplomacy",
        "summary": "Three crucial noble audiences in one day at Toledo's Royal Alcázar. (1) Don Íñigo López de Mendoza the Elder brings son Pedro González de Mendoza (age 30, Salamanca-educated). House Mendoza commits 1,800 levies; Pedro volunteers to take crusader oath at the wedding. Juan clarifies papal bull gives him total command authority — positions assigned on merit, not bloodline. Pedro honest about limited experience, accepts chance to prove himself. Don Íñigo leaves as advocate for the crown. (2) Don Enrique Enríquez, Admiral of Castile, nervous about maritime-based wealth assessment. Juan reassures: assessments valid 10 years, re-assessment if revenue changes. Detailed naval discussion — Castile's fleet is ~30 ships (mostly merchant), compared to Aragon's 60-80 war galleys. Enríquez advocates for long-term fleet development, describes pirate threat from Barbary Coast, offers 4 carracks and 6 caravels for crusade logistics. Juan promises future naval expansion consultation. (3) Don Luis de Guzmán, Master of Santiago — arrived expecting punishment for backing the Infantes. Instead, Juan invites him for wine, shows relics (Guzmán kneels in genuine devotion: 'This is what Santiago was founded for'). Juan explains taxation funds crusade infrastructure under Vatican oversight. Offers choice: field command or honored advisory role. Roll: 56 (Grateful Acceptance) — Guzmán deeply moved, steps down from field command voluntarily, commits Santiago's 2,000 knights fully, pledges to mentor younger commanders. Assigned to eastern army as advisor. Immediately contacts Master of Calatrava to share his experience.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "inigo_lopez_de_mendoza",
            "pedro_gonzalez_de_mendoza", "enrique_enriquez",
            "luis_de_guzman", "isabel_of_portugal", "dona_beatriz"
        ],
        "factions_affected": ["royal_court", "aragonese_faction"],
        "location": "Toledo",
        "tags": ["diplomacy", "politics", "military", "taxation", "naval", "roll"],
    },
    {
        "msgs": (51, 58),
        "date": "1431-01-29",
        "type": "personal",
        "summary": "Evening with Isabel and her Portuguese ladies-in-waiting. Juan joins Isabel in prayer in the Portuguese chapel, shares his vision of God's kingdom on earth — Isabel deeply moved, leads an assured prayer for their sacred partnership. They discuss children, Isabel's mother's letter of support, plans to invite her mother to visit in autumn. Dinner with Dona Beatriz, Dona Inês, and Dona Catarina — Portuguese court stories, Isabel's herbcraft skill revealed (learned from monastery nuns), personal warmth growing. Álvaro reports Master of Calatrava requesting audience, influenced by Guzmán's transformation.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "dona_beatriz",
            "alvaro_de_luna"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["personal", "marriage", "religion"],
    },
    {
        "msgs": (59, 70),
        "date": "1431-01-30",
        "type": "military",
        "summary": "Morning: Juan commissions personal battle armor from Master Gonzalo de Burgos. Design: all-white Milan plate, tall white plume, white tabard, two lightweight ash banner poles (8 feet) attached to saddle streaming white silk banners. White caparison for horse, white shield and lance. Álvaro warns visibility means becoming primary target for every enemy. Master Gonzalo suggests two helmets: show helm for ceremonies, protected helm for intense fighting. Juan requests armor ready for wedding arrival in 17 days — tight deadline but achievable for ceremonial pieces. Immediate fitting session conducted. Midday: Juan assembles all 50 crusaders in the banner chamber. Addresses them on sacred responsibility of guarding relics and banner. Establishes exclusive authority: only these 50 may handle relics, only they guard banner. Warns of battlefield dangers — enemy will target relics and king. Tasks them with developing operational procedures: travel protocols, banner-relic separation in battle, guard rotation, chain of command, passwords. Leads unified prayer. Fray Hernando formally names them the 'Guardian Company.' Veterans and newcomers alike respond with absolute devotion, immediately begin practical planning.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "master_gonzalo_de_burgos",
            "fray_hernando"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["military", "armor", "crusade", "religion", "guardian_company"],
    },
    {
        "msgs": (71, 94),
        "date": "1431-01-30",
        "type": "military",
        "summary": "Don Pedro González de Padilla, Master of Calatrava (~45, professional soldier), arrives at Guzmán's urging. Pledges Calatrava's 1,500 knights and full participation. Juan shares secret two-army strategy: eastern army (23,000 troops) through central frontier with banner/relics, western army from Seville taking coastal ports with naval support. Pedro González provides expert frontier assessment — water supply critical, only 3 viable mountain passes, Sultan will likely concentrate against eastern army. Juan offers him command of the eastern army when Juan is not present. Pedro honestly admits never commanding 23,000 men but accepts with conditions: experienced subordinates, clear authority, support through mistakes. Father Tommaso presents comprehensive budget (35,276 florins for 8-month season: provisions 29,943 florins, cavalry operations 1,622, forward bases 177, intelligence 143). Pedro deeply impressed by unprecedented logistical preparation. Juan then plans with Álvaro: assigns Infante Juan west (advisor to Rodrigo), Infante Enrique east (tactical commander). Writes personal letter to both Infantes framing assignments as honors. Develops staggered deployment strategy: eastern army moves first visibly to draw Sultan's attention; western army holds until Juan signals Sultan is committed, then launches naval invasion. Establishes four-station relay system (Jaén-Córdoba-Écija-Carmona-Seville) for two-day message delivery. Rodrigo given operational freedom within strategic objectives. Administrative packet prepared for Seville including Martín de Córdoba as quartermaster.",
        "characters": [
            "juan_ii", "alvaro_de_luna", "pedro_gonzalez_de_padilla",
            "tommaso_parentucelli"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["military", "strategy", "command", "logistics", "crusade"],
    },
    {
        "msgs": (95, 122),
        "date": "1431-01-30",
        "type": "personal",
        "summary": "Deep emotional evening conversation between Juan and Isabel in the Portuguese chapel. Juan's pragmatic framing ('travel with army until pregnant, kingdom needs heir') deeply hurts Isabel, who'd opened up about fears of failing to have children. Isabel breaks down: she feels reduced to a duty, a problem to solve, not a person. Wants to matter as Isabel, not just as alliance or potential heir-bearer. Juan apologizes for being too practical from military planning all day. Makes promise: every evening together, private prayer, sharing hearts without others present. Isabel shares comprehensive fears: failing at children, traveling with army (never left palaces/convents), being in soldiers' way, Juan stopping seeing her after marriage. Juan claims he's told her he loves her; Isabel gently corrects him — he's been kind and considerate but never actually said those words. Juan confesses he was once in love before — a girl during his pilgrimage, not of royal blood, never told her, put her behind him. Isabel initially hurt ('second choice'), but understanding grows. Key moment: Juan realizes he forgot about the other girl when thinking about love with Isabel — Isabel recognizes this means she matters to him now. Both admit feeling inadequate in love. They walk in the garden, Juan describes white armor, Isabel calls him 'like Saint Michael.' Promise made: daily evening prayer together. Agreement to plan campaign travel with Dona Beatriz. Juan assigns Sancho's guard team permanently to Isabel.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "dona_beatriz"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["personal", "marriage", "emotional"],
    },
    {
        "msgs": (123, 126),
        "date": "1431-01-31",
        "end_date": "1431-02-14",
        "type": "narrative",
        "summary": "Time skip covering final 15 days before wedding. Isabel plans campaign travel with Dona Beatriz and Álvaro — practical logistics ease her fears. More nobles arrive daily, all accepting crusade taxation after word spreads from the three audiences. Master Gonzalo works day and night; delivers completed white armor three days before wedding — polished Milan plate with white plume, even Álvaro struck silent. Guardian Company (50 crusaders) develops procedures under Fray Hernando for relic/banner protection during travel and battle. Pedro González de Padilla spends week in Toledo with Tommaso on eastern army logistics before departing for frontier. Administrative packet dispatched to Rodrigo in Seville with budget, Infante assignments, relay system details, and three administrators. Juan and Isabel pray together every evening as promised — genuine partnership growing, fragile beginnings of love. Crusader recruitment approaches 250 sworn crusaders. Toledo fills to capacity with visitors for wedding and crusade announcement. On evening of February 14, Juan prays alone in banner chamber before father's sword — feels the certainty that he is where God needs him to be.",
        "characters": [
            "juan_ii", "isabel_of_portugal", "alvaro_de_luna",
            "dona_beatriz", "fray_hernando"
        ],
        "factions_affected": [],
        "location": "Toledo",
        "tags": ["preparation", "wedding", "crusade", "personal"],
    },
]

NEW_CHARACTERS = [
    {
        "id": "pedro_gonzalez_de_mendoza",
        "name": "Don Pedro González de Mendoza",
        "aliases": ["pedro_gonzalez_de_mendoza", "pedro_mendoza"],
        "title": "Heir of House Mendoza",
        "born": "1401-00-00",
        "status": ["active"],
        "category": ["military", "nobility"],
        "location": "Toledo",
        "current_task": "Taking crusader oath at royal wedding; committed to serving in crusade with chance to rise through ranks based on merit; House Mendoza pledging 1,800 levies",
        "personality": ["earnest", "honest", "ambitious", "devout"],
        "interests": ["military service", "warfare", "theology", "family honor"],
        "speech_style": "Direct and thoughtful; weighs words carefully; honest about both ambitions and limitations",
        "core_characteristics": "Son and heir of Don Íñigo López de Mendoza the Elder. Age 30, dark-haired with strong family resemblance. Attended Dominican college at Salamanca for two years. Has commanded household guard in frontier skirmishes (up to 300 men) but no major campaign experience. Grandfather fell at Antequera. Volunteered to take crusader oath with genuine fervor after seeing relics. Juan promised him opportunity to rise to greater command based on ability.",
        "faction_ids": ["royal_court"],
        "appearance": {
            "age_appearance": "about 30",
            "build": "strong",
            "hair": "dark",
            "distinguishing_features": "strong family resemblance to father",
        },
    },
    {
        "id": "enrique_enriquez",
        "name": "Don Enrique Enríquez",
        "aliases": ["enrique_enriquez", "don_enrique_enriquez", "admiral_enriquez"],
        "title": "Admiral of Castile",
        "born": "1391-00-00",
        "status": ["active"],
        "category": ["nobility", "naval"],
        "location": "Toledo",
        "current_task": "Committed to full cooperation with crusade assessment teams; offered naval expertise and ships for crusade logistics; future role in Castilian fleet expansion",
        "personality": ["nervous", "competent", "bureaucratic", "knowledgeable"],
        "interests": ["naval affairs", "maritime commerce", "fleet development", "coastal defense"],
        "speech_style": "Starts nervous and formal but becomes animated and confident when discussing naval matters; tends to ramble when anxious",
        "core_characteristics": "Admiral of Castile, approximately 40 years old. Competent administrator rather than warrior, with soft hands and nervous bearing around royalty. Controls unusual maritime-based wealth (ports, fishing rights, salt works, shipping). Provided detailed strategic analysis of Castile's naval weakness (~30 ships vs Aragon's 60-80 war galleys) and advocated for long-term fleet development. Offered 4 carracks, 6 caravels, and ability to contract 8-12 more ships. Confirmed Portuguese dowry galleys individually superior to Granada's fleet.",
        "faction_ids": ["royal_court"],
        "appearance": {
            "age_appearance": "about 40",
            "build": "soft",
            "distinguishing_features": "golden anchor chain of office; soft administrator's hands",
        },
    },
    {
        "id": "pedro_gonzalez_de_padilla",
        "name": "Don Pedro González de Padilla",
        "aliases": ["pedro_gonzalez_de_padilla", "don_pedro_gonzalez_de_padilla"],
        "title": "Master of the Order of Calatrava",
        "born": "1386-00-00",
        "status": ["active"],
        "category": ["military", "nobility"],
        "location": "Toledo",
        "current_task": "Appointed commander of eastern army (23,000 troops) in Juan's absence; working with Tommaso on logistics; preparing to lead the central frontier assault on Granada",
        "personality": ["direct", "professional", "honest", "determined"],
        "interests": ["frontier warfare", "military strategy", "fortification", "command"],
        "speech_style": "Plain-speaking and direct; speaks with professional military precision; asks probing strategic questions",
        "core_characteristics": "Master of the Order of Calatrava, approximately 45 years old. Lean, fit professional soldier who knows the central frontier (Ciudad Real, Calatrava la Nueva, mountain passes into Granada) intimately. Fought Moors in approximately 24 engagements over decades. Came at Guzmán's urging and pledged Calatrava's 1,500 knights. Appointed eastern army commander — honest that he's never led 23,000 men but willing to learn. Provided expert analysis of terrain challenges (water supply, mountain passes, Sultan's likely strategy). Impressed by unprecedented logistical preparation.",
        "faction_ids": ["royal_court"],
        "appearance": {
            "age_appearance": "about 45",
            "build": "lean and fit",
            "hair": "dark with grey at temples",
            "distinguishing_features": "black Calatrava robes with red cross",
        },
    },
    {
        "id": "master_gonzalo_de_burgos",
        "name": "Master Gonzalo de Burgos",
        "aliases": ["master_gonzalo_de_burgos", "gonzalo_de_burgos"],
        "title": "Royal Armorer",
        "born": "1376-00-00",
        "status": ["active"],
        "category": ["artisan"],
        "location": "Toledo",
        "current_task": "Creating Juan's distinctive all-white Milan plate armor with white plume, banner poles, and two helmets; delivered completed armor three days before wedding",
        "personality": ["skilled", "proud", "pragmatic", "enthusiastic"],
        "interests": ["armorcraft", "metalworking", "Milan steel techniques"],
        "speech_style": "Professional and detailed when discussing craft; becomes animated and enthusiastic about challenging commissions",
        "core_characteristics": "Master armorer in his fifties with burn-scarred forearms from decades at the forge. Commissioned to create Juan's distinctive white crusader armor — full Milan plate with white plume, white tabard, banner pole sockets, and two helmets (show helm and combat helm). Pragmatic about battlefield dangers of visibility but embraced the vision. Completed in 17 days working day and night with three apprentices. The commission will make him the most sought-after armorer in Castile.",
        "faction_ids": [],
        "appearance": {
            "age_appearance": "about 55",
            "build": "stocky",
            "distinguishing_features": "burn-scarred forearms",
        },
    },
]

CHARACTER_UPDATES = [
    {
        "id": "juan_ii",
        "current_task": "Wedding eve; white armor ready; eastern army commander appointed; staggered deployment strategy finalized; relay system operational; ~250 crusaders sworn",
        "location": "Toledo",
    },
    {
        "id": "alvaro_de_luna",
        "current_task": "Coordinating wedding and crusade preparations; relay system established; administrative packet sent to Rodrigo in Seville; managing noble arrivals",
        "location": "Toledo",
    },
    {
        "id": "isabel_of_portugal",
        "current_task": "Wedding eve; growing confidence and genuine partnership with Juan; campaign travel planned with Portuguese ladies; daily evening prayers with Juan established",
        "location": "Toledo",
    },
    {
        "id": "inigo_lopez_de_mendoza",
        "current_task": "In Toledo for wedding; committed 1,800 levies to crusade; son Pedro taking crusader oath; cooperating fully with assessment teams; advocating for the crown among other noble houses",
        "location": "Toledo",
    },
    {
        "id": "luis_de_guzman",
        "current_task": "Stepped down from Santiago field command; assigned to eastern army as senior advisor and mentor; Santiago's 2,000 knights fully committed to crusade; advocating crusade to other Military Orders",
        "personality": {"remove": ["politically_aligned_with_infantes"], "add": ["redeemed", "devoted"]},
        "faction_ids": {"remove": ["aragonese_faction"]},
        "speech_style": "Emotional and genuine when discussing the crusade's sacred purpose; carries weight of redemption",
        "location": "Toledo",
    },
    {
        "id": "tommaso_parentucelli",
        "current_task": "Presenting eastern army budget details to commanders; working with Pedro González de Padilla on logistics for 23,000-troop campaign; recommending 20 administrators for eastern army",
        "location": "Toledo",
    },
]

NEW_LOCATIONS = []
NEW_FACTIONS = []
FACTION_UPDATES = [
    {
        "faction_id": "royal_court",
        "member_ids": {"add": ["pedro_gonzalez_de_mendoza", "enrique_enriquez", "pedro_gonzalez_de_padilla"]},
        "description": "All major noble houses and Military Orders now aligned with the crown for the crusade. Eastern army (23,000) under Pedro González de Padilla with Don Luis de Guzmán as advisor. Western army (12,000) under Rodrigo with Infante Juan advising. Assessment teams ready, taxation accepted. Wedding and crusade proclamation imminent.",
    },
]

ROLLS = [
    {
        "event_index": 0,
        "title": "Don Luis de Guzmán's Response to Juan's Grace",
        "context": "After Juan treats Guzmán with extraordinary grace — sharing wine, showing relics, offering genuine choice between field command and advisory role — how does the Master of Santiago respond? He expected punishment for backing the Infantes but received redemption.",
        "roll_type": "diplomacy",
        "date": "1431-01-29",
        "rolled": 56,
        "outcome_range": "success",
        "outcome_label": "Grateful Acceptance",
        "outcome_detail": "Guzmán genuinely moved by Juan's grace and respect. Recognizes he was given more consideration than his past actions warranted. Commits Santiago fully — 2,000 knights, fortresses, resources, knowledge. Steps down from field command voluntarily, admitting his aging body would risk men's lives to protect pride. Pledges to serve as advisor, sharing 33 years of frontier knowledge. Accepts crusade taxation without resistance. Immediately contacts Master of Calatrava to advocate for full Military Order participation.",
        "evaluation": "Excellent outcome. Juan's magnanimous approach converted a potential opponent into a devoted supporter. Guzmán's voluntary step-down and advocacy work exceeded expectations for this range. The combination of religious devotion (seeing the relics), personal respect, and genuine choice enabled Guzmán to feel redeemed rather than diminished.",
        "success_factors": ["Juan's grace and personal hospitality", "Showing relics (spiritual impact)", "Genuine choice offered, not forced", "Clear path to redemption through advisory service"],
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
        "chapter": "1.12",
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
    print(f"Chapter 1.12 extraction complete:")
    print(f"  Events:            {len(events)}")
    print(f"  Total exchanges:   {total_exchanges}")
    print(f"  New characters:    {len(NEW_CHARACTERS)}")
    print(f"  Char updates:      {len(CHARACTER_UPDATES)}")
    print(f"  Rolls:             {len(ROLLS)}")
    print(f"  Written to:        {OUTPUT}")

if __name__ == "__main__":
    main()
