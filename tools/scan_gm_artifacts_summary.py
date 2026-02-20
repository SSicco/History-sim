#!/usr/bin/env python3
"""Generate a concise per-chapter summary of GM artifacts found."""

import json
import os
import re
import glob
from collections import defaultdict

EVENTS_DIR = "/home/user/History-sim/resources/data/events"

def scan_for_artifacts(text):
    """Returns list of (category, subcategory, context) tuples for artifacts found."""
    findings = []
    lines = text.split('\n')

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Let me... patterns
        if re.match(r'^Let me (think|consider|plan|create|craft|generate|write|describe|set|present|continue|respond|address|handle|provide|now|first|check|look|review|assess|figure|work|build|develop|explore|process|determine|search|incorporate|play|make sure|approach|reason|break)', stripped, re.IGNORECASE):
            findings.append(("GM_THINKING", "Let me...", stripped[:100]))
            continue

        # I should/need/will at start with meta words
        if re.match(r'^I (should|need to|want to)\b', stripped, re.IGNORECASE):
            meta_indicators = ['dice', 'roll', 'scene', 'narrative', 'character', 'player', 'response',
                              'present', 'describe', 'create', 'establish', 'convey', 'portray',
                              'realistic', 'historically', 'simulate', 'prompt', 'context',
                              'exchange', 'incorporate', 'maintain', 'ensure', 'provide',
                              'approach', 'handle', 'focus', 'emphasize', 'balance',
                              'show', 'demonstrate', 'make this', 'make sure', 'keep',
                              'avoid', 'note that', 'remember', 'think about', 'table',
                              'draft', 'write', 'clarify', 'brief', 'short', 'concise',
                              'NPC', 'GM', 'user', 'acknowledge', 'confirm', 'search',
                              'set up', 'start', 'narrate', 'chapter', 'summary', 'document']
            lower = stripped.lower()
            if any(ind in lower for ind in meta_indicators):
                findings.append(("GM_THINKING", "I should/need to...", stripped[:100]))
                continue

        # "Now I..." or "Now let me..."
        if re.match(r'^Now (I|let me)\b', stripped, re.IGNORECASE):
            findings.append(("GM_THINKING", "Now I/let me...", stripped[:100]))
            continue

        # "This is a good/critical/important..." with meta context
        if re.match(r'^This is (a|an) (good|critical|excellent|great|perfect|important|interesting|key)\b', stripped, re.IGNORECASE):
            meta_words = ['opportunity', 'moment', 'chance', 'time', 'place', 'point', 'scene',
                         'stopping', 'where', 'requiring', 'outcome']
            if any(w in stripped.lower() for w in meta_words):
                findings.append(("GM_THINKING", "This is a good/critical...", stripped[:100]))
                continue

        # "Given the..." dice/roll references
        if re.match(r'^Given (the|that)\b', stripped, re.IGNORECASE):
            if any(w in stripped.lower() for w in ['dice', 'roll', 'result', 'outcome', 'status quo', 'probability']):
                findings.append(("GM_THINKING", "Given the (dice ref)", stripped[:100]))
                continue

        # "the player" reference
        if re.search(r'\bthe player\b', stripped, re.IGNORECASE):
            if not re.search(r'"[^"]*\bthe player\b[^"]*"', stripped, re.IGNORECASE):
                findings.append(("META_REF", "the player", stripped[:100]))
                continue

        # "the user" reference
        if re.search(r'\bthe user\b', stripped, re.IGNORECASE):
            if not re.search(r'"[^"]*\bthe user\b[^"]*"', stripped, re.IGNORECASE):
                findings.append(("META_REF", "the user", stripped[:100]))
                continue

        # "NPC" reference
        if re.search(r'\bNPC\b', stripped):
            findings.append(("META_REF", "NPC", stripped[:100]))
            continue

        # "As the GM" or "GM note"
        if re.search(r'\b(As the GM|As a GM|GM note|DM note)\b', stripped, re.IGNORECASE):
            findings.append(("META_REF", "GM/DM ref", stripped[:100]))
            continue

    # Check for paragraph-level patterns
    paragraphs = text.split('\n\n')
    for para in paragraphs:
        para_stripped = para.strip()
        if not para_stripped:
            continue

        # "Perfect!" / "Great!" / "Excellent!" GM exclamations
        if re.match(r'^(Perfect|Great|Excellent|Wonderful|Fantastic|Amazing)(!|,|\.)', para_stripped, re.IGNORECASE):
            findings.append(("GM_THINKING", "GM exclamation", para_stripped[:100]))

        # "Alright," / "OK," / "Okay," GM planning
        if re.match(r'^(Alright|OK|Okay),', para_stripped, re.IGNORECASE):
            if any(w in para_stripped.lower() for w in ['let me', 'now', 'i need', 'i should', 'i have', 'i understand']):
                findings.append(("GM_THINKING", "GM planning (Alright/OK)", para_stripped[:100]))

        # "I can..." meta
        if re.match(r'^I can\b', para_stripped, re.IGNORECASE):
            if any(w in para_stripped.lower() for w in ['do this', 'create', 'describe', 'present', 'handle', 'work with', 'absolutely', 'develop']):
                findings.append(("GM_THINKING", "I can... (meta)", para_stripped[:100]))

        # "For this scene/response"
        if re.match(r'^For this (scene|response|exchange|event|narrative|moment)', para_stripped, re.IGNORECASE):
            findings.append(("GM_THINKING", "For this scene...", para_stripped[:100]))

    # XML tags
    xml_patterns = ['<thinking>', '</thinking>', '<antThinking>', '</antThinking>',
                    '<reflection>', '</reflection>', '<reasoning>', '</reasoning>',
                    '<scratchpad>', '</scratchpad>']
    for tag in xml_patterns:
        if tag.lower() in text.lower():
            idx = text.lower().index(tag.lower())
            context = text[max(0,idx-10):idx+len(tag)+80].replace('\n', ' ')
            findings.append(("XML_TAG", tag, context[:100]))

    # Dice/roll mechanical references in meta context
    for match in re.finditer(r'\b(?:dice roll|d100|roll result|probability assessment)\b', text, re.IGNORECASE):
        start = max(0, match.start() - 40)
        end = min(len(text), match.end() + 60)
        context = text[start:end].replace('\n', ' ')
        if any(w in context.lower() for w in ['given', 'outcome', 'should', 'let me', 'need to', 'result from', 'based on the']):
            findings.append(("MECHANICAL", "dice/roll in meta context", context[:100]))

    return findings


def main():
    chapter_files = sorted(glob.glob(os.path.join(EVENTS_DIR, "chapter_*.json")))
    print(f"Scanning {len(chapter_files)} chapter files...\n")

    grand_total = 0
    category_totals = defaultdict(int)

    # Per-chapter details
    all_details = []

    for filepath in chapter_files:
        filename = os.path.basename(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        chapter = data.get("chapter", filename)
        events = data.get("events", [])
        chapter_findings = []

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

                findings = scan_for_artifacts(text)
                for cat, subcat, ctx in findings:
                    chapter_findings.append({
                        "event_id": event_id,
                        "ex_idx": ex_idx,
                        "category": cat,
                        "subcategory": subcat,
                        "context": ctx,
                    })
                    category_totals[cat] += 1

        grand_total += len(chapter_findings)

        if chapter_findings:
            all_details.append((chapter, filename, chapter_findings))

    # Print summary
    print(f"GRAND TOTAL: {grand_total} findings across {len(all_details)} chapters\n")
    print("By category:")
    for cat, count in sorted(category_totals.items()):
        print(f"  {cat}: {count}")
    print()

    # Per-chapter summary
    print("=" * 120)
    print("PER-CHAPTER BREAKDOWN")
    print("=" * 120)

    for chapter, filename, findings in all_details:
        # Count subcategories
        sub_counts = defaultdict(int)
        for f in findings:
            sub_counts[f["subcategory"]] += 1

        print(f"\n--- Chapter {chapter} ({filename}) --- {len(findings)} findings ---")
        for sub, cnt in sorted(sub_counts.items(), key=lambda x: -x[1]):
            print(f"    {sub}: {cnt}")

    # Detailed listing
    print("\n\n" + "=" * 120)
    print("DETAILED FINDINGS (every match)")
    print("=" * 120)

    for chapter, filename, findings in all_details:
        print(f"\n{'='*80}")
        print(f"CHAPTER {chapter} ({filename})")
        print(f"{'='*80}")

        for f in findings:
            print(f"\n  [{f['category']}] {f['subcategory']}")
            print(f"  Event: {f['event_id']}  |  Exchange: {f['ex_idx']}")
            print(f"  Text: {f['context']}")
            print(f"  {'~'*70}")


if __name__ == "__main__":
    main()
