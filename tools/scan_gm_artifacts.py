#!/usr/bin/env python3
"""Scan all chapter files for GM thinking/commentary artifacts in assistant (gm) content."""

import json
import os
import re
import glob

EVENTS_DIR = "/home/user/History-sim/resources/data/events"

# Patterns to search for
PATTERNS = {
    "thinking_start": [
        (r'(?i)^Let me think', "Line starts with 'Let me think'"),
        (r'(?i)^I should\b', "Line starts with 'I should'"),
        (r'(?i)^I need to\b', "Line starts with 'I need to'"),
        (r'(?i)^Let me consider', "Line starts with 'Let me consider'"),
        (r'(?i)^Let me plan', "Line starts with 'Let me plan'"),
        (r'(?i)^Let me create', "Line starts with 'Let me create'"),
        (r'(?i)^Let me craft', "Line starts with 'Let me craft'"),
        (r'(?i)^Let me generate', "Line starts with 'Let me generate'"),
        (r'(?i)^Let me write', "Line starts with 'Let me write'"),
        (r'(?i)^Let me describe', "Line starts with 'Let me describe'"),
        (r'(?i)^Let me set', "Line starts with 'Let me set'"),
        (r'(?i)^Let me present', "Line starts with 'Let me present'"),
        (r'(?i)^Let me continue', "Line starts with 'Let me continue'"),
        (r'(?i)^Let me respond', "Line starts with 'Let me respond'"),
        (r'(?i)^Let me address', "Line starts with 'Let me address'"),
        (r'(?i)^Let me handle', "Line starts with 'Let me handle'"),
        (r'(?i)^Let me provide', "Line starts with 'Let me provide'"),
        (r'(?i)^Let me now', "Line starts with 'Let me now'"),
    ],
    "meta_commentary": [
        (r'(?i)This is a good opportunity', "Meta: 'This is a good opportunity'"),
        (r'(?i)\bthe player\b', "Meta: mentions 'the player'"),
        (r'(?i)\bthe user\b', "Meta: mentions 'the user'"),
        (r"(?i)^I'll\b", "Line starts with 'I'll'"),
        (r"(?i)^I will\b", "Line starts with 'I will'"),
        (r'(?i)^I want to\b', "Line starts with 'I want to'"),
        (r'(?i)^Now I', "Line starts with 'Now I'"),
        (r'(?i)\bthis simulation\b', "Meta: 'this simulation'"),
        (r'(?i)\bthis game\b', "Meta: 'this game'"),
        (r'(?i)\bthis scenario\b', "Meta: 'this scenario'"),
        (r'(?i)\bas an AI\b', "Meta: 'as an AI'"),
        (r'(?i)\bAI assistant\b', "Meta: 'AI assistant'"),
        (r'(?i)\blanguage model\b', "Meta: 'language model'"),
        (r'(?i)\broleplay(ing)?\b', "Meta: 'roleplay'"),
        (r'(?i)\bAs the GM\b', "Meta: 'As the GM'"),
        (r'(?i)\bAs a GM\b', "Meta: 'As a GM'"),
        (r'(?i)\bGM note\b', "Meta: 'GM note'"),
        (r'(?i)out of character', "Meta: 'out of character'"),
        (r'(?i)\bOOC\b', "Meta: 'OOC'"),
        (r'(?i)breaking character', "Meta: 'breaking character'"),
        (r'(?i)fourth wall', "Meta: 'fourth wall'"),
        (r'(?i)4th wall', "Meta: '4th wall'"),
    ],
    "asterisk_actions": [
        (r'\*thinks\*', "Asterisk action: *thinks*"),
        (r'\*considers\*', "Asterisk action: *considers*"),
        (r'\*pauses\*', "Asterisk action: *pauses*"),
        (r'\*nods\*', "Asterisk action: *nods*"),
        (r'\*smiles\*', "Asterisk action: *smiles*"),
        (r'\*laughs\*', "Asterisk action: *laughs*"),
        (r'\*sighs\*', "Asterisk action: *sighs*"),
        (r'\*notes\*', "Asterisk action: *notes*"),
        (r'\*adjusts\*', "Asterisk action: *adjusts*"),
        (r'\*clears throat\*', "Asterisk action: *clears throat*"),
        (r'\*whispers\*', "Asterisk action: *whispers*"),
        (r'\*looks\*', "Asterisk action: *looks*"),
        (r'\*turns\*', "Asterisk action: *turns*"),
        (r'\*waves\*', "Asterisk action: *waves*"),
        (r'\*bows\*', "Asterisk action: *bows*"),
        (r'\*frowns\*', "Asterisk action: *frowns*"),
        (r'\*gestures\*', "Asterisk action: *gestures*"),
        (r'\*mutters\*', "Asterisk action: *mutters*"),
    ],
    "xml_tags": [
        (r'<thinking>', "XML tag: <thinking>"),
        (r'</thinking>', "XML tag: </thinking>"),
        (r'<antThinking>', "XML tag: <antThinking>"),
        (r'</antThinking>', "XML tag: </antThinking>"),
        (r'<reflection>', "XML tag: <reflection>"),
        (r'</reflection>', "XML tag: </reflection>"),
        (r'<internal>', "XML tag: <internal>"),
        (r'</internal>', "XML tag: </internal>"),
        (r'<reasoning>', "XML tag: <reasoning>"),
        (r'</reasoning>', "XML tag: </reasoning>"),
        (r'<scratchpad>', "XML tag: <scratchpad>"),
        (r'</scratchpad>', "XML tag: </scratchpad>"),
        (r'<meta>', "XML tag: <meta>"),
        (r'</meta>', "XML tag: </meta>"),
        (r'<plan>', "XML tag: <plan>"),
        (r'</plan>', "XML tag: </plan>"),
        (r'<note>', "XML tag: <note>"),
        (r'</note>', "XML tag: </note>"),
    ],
    "fourth_wall": [
        (r'(?i)\bhistorical(ly)? (accurate|accuracy|inaccurate)\b', "4th wall: discusses historical accuracy"),
        (r'(?i)in (this|the) (story|narrative|game|session|campaign)', "4th wall: 'in this story/narrative/game'"),
        (r'(?i)for (the|this) (story|narrative|plot|session)', "4th wall: 'for the story/narrative'"),
        (r'(?i)from a (narrative|story|game|gameplay) perspective', "4th wall: 'from a narrative perspective'"),
        (r'(?i)game mechanic', "4th wall: 'game mechanic'"),
        (r'(?i)\bplayer agency\b', "4th wall: 'player agency'"),
        (r'(?i)\bplayer character\b', "4th wall: 'player character'"),
        (r'(?i)\bPC\b(?![\w])', "4th wall: 'PC' abbreviation"),
        (r'(?i)\bNPC\b', "4th wall: 'NPC'"),
        (r'(?i)dice roll|roll the dice|rolling dice', "4th wall: dice references"),
    ],
}

def get_surrounding_context(text, match_start, match_end, chars=100):
    """Get text around a match for context."""
    # Get the line containing the match
    line_start = text.rfind('\n', 0, match_start)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1
    line_end = text.find('\n', match_end)
    if line_end == -1:
        line_end = len(text)

    context = text[line_start:line_start + 150]
    return context.replace('\n', ' ').strip()

def scan_file(filepath):
    """Scan a single chapter file for artifacts."""
    findings = []

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chapter = data.get("chapter", os.path.basename(filepath))
    events = data.get("events", [])

    for event in events:
        event_id = event.get("event_id", "unknown")
        exchanges = event.get("exchanges", [])

        for ex_idx, exchange in enumerate(exchanges):
            role = exchange.get("role", "")
            # Only check GM/assistant content
            if role not in ("gm", "assistant"):
                continue

            text = exchange.get("text", "")
            if not text:
                continue

            # Check each pattern category
            for category, patterns in PATTERNS.items():
                for pattern_re, description in patterns:
                    # For patterns that check line starts, we need to check each line
                    if pattern_re.startswith('^') or pattern_re.startswith('(?i)^'):
                        for line in text.split('\n'):
                            line_stripped = line.strip()
                            match = re.search(pattern_re, line_stripped)
                            if match:
                                context = line_stripped[:150]
                                findings.append({
                                    "file": os.path.basename(filepath),
                                    "chapter": chapter,
                                    "event_id": event_id,
                                    "exchange_idx": ex_idx,
                                    "category": category,
                                    "description": description,
                                    "context": context,
                                })
                    else:
                        for match in re.finditer(pattern_re, text):
                            context = get_surrounding_context(text, match.start(), match.end())
                            findings.append({
                                "file": os.path.basename(filepath),
                                "chapter": chapter,
                                "event_id": event_id,
                                "exchange_idx": ex_idx,
                                "category": category,
                                "description": description,
                                "context": context,
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
        print("No GM thinking/commentary artifacts found.")
        return

    # Group by category
    by_category = {}
    for f in all_findings:
        cat = f["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(f)

    # Print results
    print(f"TOTAL FINDINGS: {len(all_findings)}\n")
    print("=" * 120)

    for category, findings in sorted(by_category.items()):
        print(f"\n{'='*120}")
        print(f"CATEGORY: {category.upper()} ({len(findings)} findings)")
        print(f"{'='*120}")

        for f in findings:
            print(f"\n  File: {f['file']}")
            print(f"  Event: {f['event_id']}, Exchange: {f['exchange_idx']}")
            print(f"  Pattern: {f['description']}")
            print(f"  Context: {f['context'][:150]}")
            print(f"  {'~'*100}")


if __name__ == "__main__":
    main()
