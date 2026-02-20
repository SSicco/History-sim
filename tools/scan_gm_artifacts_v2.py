#!/usr/bin/env python3
"""
Refined scan for GM thinking/commentary artifacts.
Focus on REAL artifacts: text that is clearly GM reasoning/planning,
not in-character dialogue that happens to match patterns.
"""

import json
import os
import re
import glob
from collections import defaultdict

EVENTS_DIR = "/home/user/History-sim/resources/data/events"

def scan_for_thinking_blocks(text, event_id, ex_idx, filename, chapter):
    """Look for blocks of GM thinking/reasoning that were not stripped.
    These are typically paragraphs that discuss what to do, reference dice rolls
    mechanically, discuss the player, etc."""
    findings = []

    lines = text.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue

        # Category 1: Lines that clearly start with GM internal reasoning
        # "Let me..." patterns (not in dialogue)
        if re.match(r'^Let me (think|consider|plan|create|craft|generate|write|describe|set|present|continue|respond|address|handle|provide|now|first|check|look|review|assess|figure|work|build|develop|explore|process|determine|search|incorporate|play|make sure|approach|reason|break)', stripped, re.IGNORECASE):
            findings.append({
                "file": filename, "chapter": chapter, "event_id": event_id,
                "exchange_idx": ex_idx, "category": "GM_THINKING",
                "subcategory": "Let me...",
                "context": stripped[:150]
            })
            continue

        # "I should..." / "I need to..." / "I want to..." at start of line (GM self-talk)
        if re.match(r'^I (should|need to|want to|will|\'ll)\b', stripped, re.IGNORECASE):
            # Exclude if it looks like in-character Juan II speech (often in quotes or first person narrative)
            # GM self-talk tends to be about meta concerns
            meta_indicators = ['dice', 'roll', 'scene', 'narrative', 'character', 'player', 'response',
                              'present', 'describe', 'create', 'establish', 'convey', 'portray',
                              'realistic', 'historically', 'simulate', 'prompt', 'context',
                              'exchange', 'incorporate', 'maintain', 'ensure', 'provide',
                              'approach', 'handle', 'focus', 'emphasize', 'balance',
                              'show', 'demonstrate', 'make this', 'make sure', 'keep',
                              'avoid', 'note that', 'remember', 'think about']
            lower = stripped.lower()
            if any(ind in lower for ind in meta_indicators):
                findings.append({
                    "file": filename, "chapter": chapter, "event_id": event_id,
                    "exchange_idx": ex_idx, "category": "GM_THINKING",
                    "subcategory": "I should/need/will (meta)",
                    "context": stripped[:150]
                })
                continue

        # "Now I..." or "Now let me..." at start
        if re.match(r'^Now (I|let me)\b', stripped, re.IGNORECASE):
            findings.append({
                "file": filename, "chapter": chapter, "event_id": event_id,
                "exchange_idx": ex_idx, "category": "GM_THINKING",
                "subcategory": "Now I/let me...",
                "context": stripped[:150]
            })
            continue

        # "This is a good..." meta-commentary
        if re.match(r'^This is (a good|an? (excellent|great|perfect|important|interesting|key|critical))', stripped, re.IGNORECASE):
            meta_words = ['opportunity', 'moment', 'chance', 'time', 'place', 'point', 'scene']
            if any(w in stripped.lower() for w in meta_words):
                findings.append({
                    "file": filename, "chapter": chapter, "event_id": event_id,
                    "exchange_idx": ex_idx, "category": "GM_THINKING",
                    "subcategory": "This is a good/great/important...",
                    "context": stripped[:150]
                })
                continue

        # "Given the..." dice roll / mechanical reasoning
        if re.match(r'^Given (the|that)\b', stripped, re.IGNORECASE):
            if any(w in stripped.lower() for w in ['dice', 'roll', 'result', 'outcome', 'status quo', 'probability']):
                findings.append({
                    "file": filename, "chapter": chapter, "event_id": event_id,
                    "exchange_idx": ex_idx, "category": "GM_THINKING",
                    "subcategory": "Given the (dice/roll reference)",
                    "context": stripped[:150]
                })
                continue

        # References to "the player" (not in quotes)
        if re.search(r'\bthe player\b', stripped, re.IGNORECASE):
            # Check it's not inside quotation marks
            if not re.search(r'"[^"]*\bthe player\b[^"]*"', stripped, re.IGNORECASE):
                findings.append({
                    "file": filename, "chapter": chapter, "event_id": event_id,
                    "exchange_idx": ex_idx, "category": "META_REFERENCE",
                    "subcategory": "the player",
                    "context": stripped[:150]
                })
                continue

        # References to "the user" (not in quotes)
        if re.search(r'\bthe user\b', stripped, re.IGNORECASE):
            if not re.search(r'"[^"]*\bthe user\b[^"]*"', stripped, re.IGNORECASE):
                findings.append({
                    "file": filename, "chapter": chapter, "event_id": event_id,
                    "exchange_idx": ex_idx, "category": "META_REFERENCE",
                    "subcategory": "the user",
                    "context": stripped[:150]
                })
                continue

        # "As the GM" or "As a GM"
        if re.search(r'\b[Aa]s (the|a) GM\b', stripped):
            findings.append({
                "file": filename, "chapter": chapter, "event_id": event_id,
                "exchange_idx": ex_idx, "category": "META_REFERENCE",
                "subcategory": "As the/a GM",
                "context": stripped[:150]
            })
            continue

        # "GM note" or "DM note"
        if re.search(r'\b(GM|DM) note\b', stripped, re.IGNORECASE):
            findings.append({
                "file": filename, "chapter": chapter, "event_id": event_id,
                "exchange_idx": ex_idx, "category": "META_REFERENCE",
                "subcategory": "GM/DM note",
                "context": stripped[:150]
            })
            continue

        # "NPC" reference
        if re.search(r'\bNPC\b', stripped):
            findings.append({
                "file": filename, "chapter": chapter, "event_id": event_id,
                "exchange_idx": ex_idx, "category": "META_REFERENCE",
                "subcategory": "NPC reference",
                "context": stripped[:150]
            })
            continue

        # OOC / out of character
        if re.search(r'\bOOC\b', stripped) or re.search(r'\bout of character\b', stripped, re.IGNORECASE):
            findings.append({
                "file": filename, "chapter": chapter, "event_id": event_id,
                "exchange_idx": ex_idx, "category": "META_REFERENCE",
                "subcategory": "OOC/out of character",
                "context": stripped[:150]
            })
            continue

    # Category 2: XML thinking tags anywhere in text
    xml_patterns = [
        (r'<thinking>', "<thinking>"),
        (r'</thinking>', "</thinking>"),
        (r'<antThinking>', "<antThinking>"),
        (r'</antThinking>', "</antThinking>"),
        (r'<reflection>', "<reflection>"),
        (r'</reflection>', "</reflection>"),
        (r'<internal>', "<internal>"),
        (r'</internal>', "</internal>"),
        (r'<reasoning>', "<reasoning>"),
        (r'</reasoning>', "</reasoning>"),
        (r'<scratchpad>', "<scratchpad>"),
        (r'</scratchpad>', "</scratchpad>"),
        (r'<plan>', "<plan>"),
        (r'</plan>', "</plan>"),
    ]
    for pattern, tag_name in xml_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            match = re.search(pattern, text, re.IGNORECASE)
            start = max(0, match.start() - 20)
            end = min(len(text), match.end() + 100)
            context = text[start:end].replace('\n', ' ')
            findings.append({
                "file": filename, "chapter": chapter, "event_id": event_id,
                "exchange_idx": ex_idx, "category": "XML_TAGS",
                "subcategory": tag_name,
                "context": context[:150]
            })

    # Category 3: Asterisk action markers (these are sometimes OK in-character, flag them)
    asterisk_patterns = [
        r'\*thinks\*', r'\*considers\*', r'\*pauses\*', r'\*notes\*',
        r'\*adjusts\*', r'\*reflects\*',
    ]
    for pat in asterisk_patterns:
        for match in re.finditer(pat, text, re.IGNORECASE):
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 100)
            context = text[start:end].replace('\n', ' ')
            findings.append({
                "file": filename, "chapter": chapter, "event_id": event_id,
                "exchange_idx": ex_idx, "category": "ASTERISK_ACTIONS",
                "subcategory": match.group(),
                "context": context[:150]
            })

    # Category 4: Multi-line thinking blocks (paragraphs that are entirely meta)
    # Look for paragraphs starting with clear GM reasoning markers
    paragraphs = text.split('\n\n')
    for para in paragraphs:
        para_stripped = para.strip()
        if not para_stripped:
            continue

        # Paragraphs with bullet lists about what to do
        if re.match(r'^[-•]\s*(The|This|I|He|She|It|We|My|Make|Show|Describe|Present|Include|Establish|Maintain|Keep|Ensure|Have|Create|Build|Develop|Focus)', para_stripped):
            # Check if multiple bullets look like GM planning
            bullet_lines = [l for l in para_stripped.split('\n') if l.strip().startswith(('-', '•'))]
            meta_count = 0
            for bl in bullet_lines:
                if any(w in bl.lower() for w in ['should', 'player', 'narrative', 'scene', 'realistic', 'historically', 'convey', 'portray', 'establish', 'maintain']):
                    meta_count += 1
            if meta_count >= 2:
                findings.append({
                    "file": filename, "chapter": chapter, "event_id": event_id,
                    "exchange_idx": ex_idx, "category": "GM_THINKING_BLOCK",
                    "subcategory": "Meta bullet list",
                    "context": para_stripped[:150]
                })

        # Look for "Perfect!" or "Great!" or "Excellent!" at start of paragraph (GM excitement)
        if re.match(r'^(Perfect|Great|Excellent|Wonderful|Fantastic|Amazing|OK|Okay|Alright|Right)(!|,|\.|\.\.\.)', para_stripped, re.IGNORECASE):
            findings.append({
                "file": filename, "chapter": chapter, "event_id": event_id,
                "exchange_idx": ex_idx, "category": "GM_THINKING",
                "subcategory": "GM exclamation (Perfect!/Great!/etc.)",
                "context": para_stripped[:150]
            })

        # "I can..." at start of paragraph followed by meta words
        if re.match(r'^I can\b', para_stripped, re.IGNORECASE):
            if any(w in para_stripped.lower() for w in ['do this', 'create', 'describe', 'present', 'handle', 'work with', 'absolutely']):
                findings.append({
                    "file": filename, "chapter": chapter, "event_id": event_id,
                    "exchange_idx": ex_idx, "category": "GM_THINKING",
                    "subcategory": "I can... (meta)",
                    "context": para_stripped[:150]
                })

        # "Here's what..." or "Here is what..." planning
        if re.match(r'^Here\'s (what|how|my|the)', para_stripped, re.IGNORECASE):
            if any(w in para_stripped.lower() for w in ['plan', 'approach', 'thinking', 'strategy', 'breakdown']):
                findings.append({
                    "file": filename, "chapter": chapter, "event_id": event_id,
                    "exchange_idx": ex_idx, "category": "GM_THINKING",
                    "subcategory": "Here's what/how... (planning)",
                    "context": para_stripped[:150]
                })

        # "For this scene/response/exchange" planning
        if re.match(r'^For this (scene|response|exchange|event|narrative|moment)', para_stripped, re.IGNORECASE):
            findings.append({
                "file": filename, "chapter": chapter, "event_id": event_id,
                "exchange_idx": ex_idx, "category": "GM_THINKING",
                "subcategory": "For this scene/response...",
                "context": para_stripped[:150]
            })

        # "The key here is..." meta reasoning
        if re.match(r'^The (key|important thing|challenge|goal|idea|point|trick|question) (here |is )', para_stripped, re.IGNORECASE):
            if any(w in para_stripped.lower() for w in ['narrative', 'scene', 'player', 'response', 'convey', 'balance', 'maintain']):
                findings.append({
                    "file": filename, "chapter": chapter, "event_id": event_id,
                    "exchange_idx": ex_idx, "category": "GM_THINKING",
                    "subcategory": "The key/important thing here is...",
                    "context": para_stripped[:150]
                })

    # Category 5: "dice roll" or "d100" mechanical references in narrative text
    # (not in roll result sections)
    dice_refs = list(re.finditer(r'\b(?:dice roll|d100|roll result|probability assessment)\b', text, re.IGNORECASE))
    for match in dice_refs:
        start = max(0, match.start() - 40)
        end = min(len(text), match.end() + 100)
        context = text[start:end].replace('\n', ' ')
        # Check if it's in a meta/reasoning context
        if any(w in context.lower() for w in ['given', 'outcome', 'should', 'status quo', 'let me', 'need to', 'result from', 'based on']):
            findings.append({
                "file": filename, "chapter": chapter, "event_id": event_id,
                "exchange_idx": ex_idx, "category": "MECHANICAL_REFERENCE",
                "subcategory": "dice/roll mechanical reference",
                "context": context[:150]
            })

    return findings


def main():
    chapter_files = sorted(glob.glob(os.path.join(EVENTS_DIR, "chapter_*.json")))
    print(f"Scanning {len(chapter_files)} chapter files...\n")

    all_findings = []

    for filepath in chapter_files:
        filename = os.path.basename(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        chapter = data.get("chapter", filename)
        events = data.get("events", [])

        for event in events:
            event_id = event.get("event_id", "unknown")
            exchanges = event.get("exchanges", [])

            for ex_idx, exchange in enumerate(exchanges):
                role = exchange.get("role", "")
                if role not in ("gm", "assistant"):
                    continue

                text = exchange.get("text", "")
                if not text:
                    continue

                findings = scan_for_thinking_blocks(text, event_id, ex_idx, filename, chapter)
                all_findings.extend(findings)

    if not all_findings:
        print("No GM thinking/commentary artifacts found.")
        return

    # Group by category
    by_category = defaultdict(list)
    for f in all_findings:
        by_category[f["category"]].append(f)

    # Summary
    print(f"TOTAL FINDINGS: {len(all_findings)}")
    print()
    for cat in sorted(by_category.keys()):
        print(f"  {cat}: {len(by_category[cat])}")
    print()

    # Detailed output
    for category in sorted(by_category.keys()):
        findings = by_category[category]
        print(f"\n{'='*120}")
        print(f"CATEGORY: {category} ({len(findings)} findings)")
        print(f"{'='*120}")

        for f in findings:
            print(f"\n  File: {f['file']}  |  Chapter: {f['chapter']}  |  Event: {f['event_id']}  |  Exchange idx: {f['exchange_idx']}")
            print(f"  Subcategory: {f['subcategory']}")
            print(f"  Context: {f['context'][:150]}")
            print(f"  {'~'*100}")


if __name__ == "__main__":
    main()
