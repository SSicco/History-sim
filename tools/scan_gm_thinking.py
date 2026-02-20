#!/usr/bin/env python3
"""
Scan all chapter event files for GM thinking/commentary text that should have been stripped.
Searches only "gm" role exchanges in chapter JSON files.
"""

import json
import os
import re
import glob

EVENTS_DIR = "/home/user/History-sim/resources/data/events"

# Patterns to search for, grouped by category
PATTERNS = {
    "1. Thinking/reasoning phrases": [
        (r'(?i)(?:^|\n)\s*Let me think', "Line starting with 'Let me think'"),
        (r'(?i)(?:^|\n)\s*I should\b', "Line starting with 'I should'"),
        (r'(?i)(?:^|\n)\s*I need to\b', "Line starting with 'I need to'"),
        (r'(?i)(?:^|\n)\s*Let me consider', "Line starting with 'Let me consider'"),
        (r'(?i)(?:^|\n)\s*I\'ll need to', "Line starting with 'I'll need to'"),
        (r'(?i)(?:^|\n)\s*Let me figure', "Line starting with 'Let me figure'"),
        (r'(?i)(?:^|\n)\s*I think I', "Line starting with 'I think I'"),
    ],
    "2. Meta-commentary about simulation": [
        (r'(?i)This is a good opportunity', "'This is a good opportunity'"),
        (r'(?i)(?<!\w)the player(?!\s+king)(?!\s+character)', "'the player' (not 'the player king')"),
        (r'(?i)(?:^|\n)\s*I\'ll\b', "Line starting with 'I'll'"),
        (r'(?i)(?:^|\n)\s*I will\b', "Line starting with 'I will'"),
        (r'(?i)the simulation', "'the simulation'"),
        (r'(?i)the game\b', "'the game'"),
        (r'(?i)game mechanic', "'game mechanic'"),
        (r'(?i)as an AI', "'as an AI'"),
        (r'(?i)language model', "'language model'"),
        (r'(?i)as a GM', "'as a GM'"),
        (r'(?i)as the GM', "'as the GM'"),
        (r'(?i)this scenario', "'this scenario'"),
    ],
    "3. Asterisk action markers": [
        (r'\*thinks\*', "*thinks*"),
        (r'\*considers\*', "*considers*"),
        (r'\*pauses\*', "*pauses*"),
        (r'\*nods\*', "*nods*"),
        (r'\*smiles\*', "*smiles*"),
        (r'\*laughs\*', "*laughs*"),
        (r'\*sighs\*', "*sighs*"),
        (r'\*frowns\*', "*frowns*"),
        (r'\*whispers\*', "*whispers*"),
        (r'\*looks\*', "*looks*"),
        (r'\*adjusts\*', "*adjusts*"),
        (r'\*leans\*', "*leans*"),
        (r'\*turns\*', "*turns*"),
        (r'\*waves\*', "*waves*"),
        (r'\*bows\*', "*bows*"),
        (r'\*gestures\*', "*gestures*"),
        (r'\*steps\*', "*steps*"),
        (r'\*clears throat\*', "*clears throat*"),
        (r'\*rises\*', "*rises*"),
    ],
    "4. XML thinking tags": [
        (r'<thinking>', "<thinking>"),
        (r'</thinking>', "</thinking>"),
        (r'<antThinking>', "<antThinking>"),
        (r'</antThinking>', "</antThinking>"),
        (r'<reflection>', "<reflection>"),
        (r'</reflection>', "</reflection>"),
        (r'<inner_monologue>', "<inner_monologue>"),
        (r'<scratchpad>', "<scratchpad>"),
        (r'<reasoning>', "<reasoning>"),
    ],
    "5. References to 'the user' or 'the player'": [
        (r'(?i)\bthe user\b', "'the user'"),
        (r'(?i)\buser\'s\b', "'user's'"),
        (r'(?i)\bplayer\'s\b(?!\s+(?:king|character|majesty|forces|army|troops|men|allies|enemies|foes))', "'player's' (not possessive of in-game entity)"),
    ],
    "6. Fourth-wall breaking": [
        (r'(?i)in this (?:role-?play|roleplay|RP)', "'in this roleplay'"),
        (r'(?i)(?:role-?play|roleplay) (?:scenario|session)', "'roleplay scenario/session'"),
        (r'(?i)out of character', "'out of character'"),
        (r'(?i)\bOOC\b', "'OOC'"),
        (r'(?i)(?:your|the) (?:next )?(?:move|turn|action|choice|decision)\s*(?:is|would be|could be|should be)', "prompting player action mechanically"),
        (r'(?i)what would you like to do\?', "'what would you like to do?'"),
        (r'(?i)what do you do\?', "'what do you do?'"),
        (r'(?i)how do you (?:respond|proceed|react)\?', "'how do you respond/proceed?'"),
        (r'(?i)what is your (?:response|decision|choice)\?', "'what is your response?'"),
        (r'(?i)difficulty (?:check|rating|class|level)', "'difficulty check/rating'"),
        (r'(?i)\bDC \d+', "'DC [number]'"),
        (r'(?i)hit points?\b', "'hit points'"),
        (r'(?i)\bHP\b', "'HP'"),
        (r'(?i)\bXP\b', "'XP'"),
        (r'(?i)experience points', "'experience points'"),
        (r'(?i)saving throw', "'saving throw'"),
        (r'(?i)ability (?:check|score)', "'ability check/score'"),
    ],
}

# Patterns to exclude from "I'll" / "I will" because they're valid in-character speech
# (Characters in the narrative saying "I'll" or "I will" is fine)
# We need to be smart about this - only flag if it appears to be GM meta-text, not dialogue

def get_context(text, match, context_chars=100):
    """Get surrounding context for a match."""
    start = max(0, match.start() - 20)
    end = min(len(text), match.start() + context_chars)
    snippet = text[start:end].replace('\n', '\\n')
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet

def scan_file(filepath):
    """Scan a single chapter file for problematic patterns."""
    findings = []

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chapter = data.get("chapter", "unknown")

    for event in data.get("events", []):
        event_id = event.get("event_id", "unknown")

        for ex_idx, exchange in enumerate(event.get("exchanges", [])):
            if exchange.get("role") != "gm":
                continue

            text = exchange.get("text", "")
            if not text:
                continue

            for category, patterns in PATTERNS.items():
                for pattern, description in patterns:
                    for match in re.finditer(pattern, text):
                        context = get_context(text, match)
                        findings.append({
                            "file": os.path.basename(filepath),
                            "chapter": chapter,
                            "event_id": event_id,
                            "exchange_idx": ex_idx,
                            "category": category,
                            "pattern": description,
                            "context": context,
                            "match_text": match.group(0),
                        })

    return findings

def main():
    chapter_files = sorted(glob.glob(os.path.join(EVENTS_DIR, "chapter_*.json")))

    print(f"Scanning {len(chapter_files)} chapter files...\n")

    all_findings = []
    for filepath in chapter_files:
        findings = scan_file(filepath)
        all_findings.extend(findings)

    if not all_findings:
        print("NO ISSUES FOUND - all chapter files are clean.")
        return

    # Group by category
    by_category = {}
    for f in all_findings:
        cat = f["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(f)

    print(f"TOTAL FINDINGS: {len(all_findings)}\n")
    print("=" * 100)

    for category in sorted(by_category.keys()):
        findings = by_category[category]
        print(f"\n{'=' * 100}")
        print(f"CATEGORY: {category}")
        print(f"Count: {len(findings)}")
        print(f"{'=' * 100}")

        for f in findings:
            print(f"\n  File: {f['file']}")
            print(f"  Event: {f['event_id']}, Exchange idx: {f['exchange_idx']}")
            print(f"  Pattern: {f['pattern']}")
            print(f"  Match: '{f['match_text']}'")
            print(f"  Context: {f['context']}")
            print(f"  {'-' * 80}")

if __name__ == "__main__":
    main()
