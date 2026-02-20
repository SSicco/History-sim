#!/usr/bin/env python3
"""
Strip GM thinking/meta text prefixes from chapter event files.

The GM's responses often start with "thinking out loud" text — numbered plans,
first-person analysis, web search results, meta-commentary on the player's
actions — before the actual narrative begins. This script identifies and removes
those prefixes, leaving only the narrative text.

Usage:
    python3 tools/strip_gm_thinking.py stats      # Summary statistics
    python3 tools/strip_gm_thinking.py report      # Show what would be changed
    python3 tools/strip_gm_thinking.py apply       # Apply changes to all chapter files
"""

import json
import re
import sys
from pathlib import Path

EVENTS_DIR = Path(__file__).parent.parent / "resources" / "data" / "events"

# ---------------------------------------------------------------------------
# Physical/dynamic action verbs — strong narrative markers
# (Linking / stative verbs like is/has/was/seems are excluded because they
#  appear in analytical text too.)
# ---------------------------------------------------------------------------
ACTION_VERBS = (
    r"(?:nod|look|step|turn|stand|stood|sat|sit|spoke|speak|bow|smile|laugh|"
    r"walk|stride|rose|lean|cross|gesture|place|drew|draw|raise|shrug|sigh|"
    r"clear|pause|wait|watch|listen|reach|move|open|close|meet|set|take|pour|"
    r"pull|return|begin|start|stop|stare|study|consider|ask|answer|reply|"
    r"respond|shake|wave|point|glance|gaze|frown|grin|chuckle|murmur|mutter|"
    r"whisper|shout|scream|cry|gasp|groan|snort|inhale|exhale|felt|held|grab|"
    r"seize|drop|lift|lower|push|emerge|appear|arrive|enter|exit|leave|depart|"
    r"approach|retreat|advance|withdraw|kneel|bend|stretch|roll|flip|spin|"
    r"twist|squeeze|press|touch|stroke|pat|rub|wipe|brush|pick|put|hang|"
    r"swing|thrust|jab|slash|parry|block|dodge|duck|jump|leap|run|sprint|"
    r"charge|gallop|trot|ride|sail|swim|climb|crawl|fall|collapse|stumble|"
    r"trip|slip|slide|crash|slam|bang|kick|stomp|throw|catch|toss|fling|hurl|"
    r"settle|spread|tap|pace|count|remove|dismount|mount|clap|interject|"
    r"scatter|feed|gather|pour|pull|produce|unfold|beckon|summon|"
    r"straighten|brighten|darken|soften|harden|tighten|loosen|narrow|widen)"
)

# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

def is_clearly_thinking(first_line, para):
    """Return True if a paragraph is clearly GM thinking / meta content."""
    fl = first_line.strip()
    if not fl:
        return True  # blank paragraph

    # Numbered list item: "1. Do this", "2) Do that"
    if re.match(r"^\d+[\.\)\:]\s", fl):
        return True

    # Bullet / dash list item
    if re.match(r"^[-\*•]\s", fl):
        return True

    # First person (GM meta voice)
    if re.match(r"^(I |I'm |I'll |I've |I'd |I need|I should|I want|I can|I think|I was)", fl):
        return True
    if re.match(r"^(Let me|My |Me )", fl):
        return True

    # "This is/should/could/was …" analytical opener
    if re.match(r"^This\s+(is|should|could|would|might|was|needs|requires|creates|chapter|isn)", fl, re.I):
        return True
    if re.match(r"^That\s+(is|said|was|would|could|should|means|makes)", fl, re.I):
        return True

    # "The key / The question / The player …" analytical
    if re.match(
        r"^(The|A)\s+(key|question|player|GM|main|issue|most|first|second|third|"
        r"problem|challenge|goal|important|critical|biggest|real|fact|point|idea|"
        r"risk|complication|consideration|implication|advantage|benefit|danger|"
        r"difficulty|tricky|upshot|lesson|math|calculation|bottom|net|overall|"
        r"result|outcome|truth|reality|situation|scenario|thing|reason|answer)",
        fl, re.I):
        return True

    # Note/Thought process/Important markers
    if re.match(r"^(Note|Important|Thought\s*process|Thinking|NB)\s*[:!\-]?", fl, re.I):
        return True

    # Good/Very good roleplaying, question, etc.
    if re.match(
        r"^(Good|Very\s+good|Excellent|Great|Nice|Interesting|Perfect)\s+"
        r"(roleplaying|roleplay|question|move|point|idea|decision|choice|thinking)",
        fl, re.I):
        return True

    # Meta-commentary about Juan / the player
    if re.match(r"^Juan\s+(is|has|was|should|wants|would|doesn't|didn't)", fl):
        return True
    if re.match(r"^He'?s?\s+(is|has|was|making|showing|being|trying|asking|right|correct|wrong)", fl):
        return True
    if re.match(r"^She'?s?\s+(is|has|was|making|showing|being|trying|asking|right|correct|wrong)", fl):
        return True
    if re.match(r"^(The player|The user)\s", fl, re.I):
        return True

    # Connective / continuation starters (when preceded by other thinking)
    if re.match(r"^(Now[,\s]|So[,\s]|However|But |Also[,\s]|Actually|Wait[,\s]|"
                r"Hmm|Okay|Ok,|OK,|Well[,\s]|Right[,\s]|Alright|Yes[,\s]|No[,\s])", fl):
        return True

    # Questions to self
    if re.match(r"^(What |How |Why |Should |Could |Would |Where |When |Who |Which )", fl):
        # Check it's not a narrative question (would have dialogue markers)
        if '"' not in para and '"' not in para and 'Your Majesty' not in para:
            return True

    # Process / investigation verbs
    if re.match(r"^(Looking\s+at|Checking|Reviewing|Considering|Thinking\s+about|"
                r"Processing|Searching|Analyzing|Reading|Examining)", fl, re.I):
        return True

    # Web search block
    if "Web Search:" in fl:
        return True

    # Causal / conditional openers (when not part of narrative)
    # Use \b instead of trailing space so "In reality," also matches
    if re.match(r"^(Since|Given|Because|Based on|From |For |After |Before |"
                r"During |In this|In terms|In order|In general|In reality|"
                r"In fact|In summary|In total|In conclusion|In addition|"
                r"In particular|In practice|In theory|In my|In the game|"
                r"In our|In any)\b", fl):
        if '"' not in para and '\u201c' not in para and 'Your Majesty' not in para:
            return True

    # Ordinal openers
    if re.match(r"^(First[,:\s]|Second[,:\s]|Third[,:\s]|Fourth|Fifth|Finally[,:\s]|"
                r"Next[,:\s]|Then[,:\s]|Meanwhile[,:\s]|Additionally)", fl):
        if '"' not in para and '"' not in para:
            return True

    # Enumerative starters
    if re.match(r"^(Several|Multiple|Two|Three|Four|Five|Some|Many|A\s+few|Various)\s", fl):
        if '"' not in para and '"' not in para:
            return True

    # "Here is/are", "There is/are" (analytical)
    if re.match(r"^(Here|There)\s+(is|are|was|were)", fl):
        return True

    # "Regarding / Concerning / As for"
    if re.match(r"^(Regarding|Concerning|As\s+for|As\s+to|About\s+)", fl):
        return True

    # "Remember / Recall"
    if re.match(r"^(Remember|Recall|Keep\s+in\s+mind|Bear\s+in\s+mind)", fl):
        return True

    # "Overall / In summary"
    if re.match(r"^(Overall|To\s+sum|To\s+summarize)", fl):
        return True

    # Web search result lines (title + URL pattern)
    if re.search(r"(wikipedia\.org|\.com|\.net|\.edu)\s*$", fl):
        return True

    # Analytical verbs applied to characters (not action verbs)
    # e.g. "Carlos is the son of", "Álvaro would be cautious", "The Infantes need to"
    if re.match(r"^(?:The\s+)?[A-Z\u00c0-\u00dc][a-z\u00e0-\u00fc']+(?:\s+(?:de|del|di|la|ibn|al-|von)\s+"
                r"[A-Za-z\u00e0-\u00fc']+)*(?:\s+[A-Z\u00c0-\u00dc][\w']*)*\s+"
                r"(?:is|are|was|were|has|had|have|would|could|should|might|may|"
                r"needs?|requires?|represents?|means?|seems?|appears?|deserves?|"
                r"tends?|lacks?|faces?|remains?|becomes?|involves?)\s", fl):
        if '"' not in para and '\u201c' not in para and 'Your Majesty' not in para:
            return True

    # Meta-sentences about narrative structure
    # e.g. "The stage is now set for Chapter 26", "This will likely focus on..."
    if re.match(r"^The\s+stage\b|^The\s+scene\b|^The\s+chapter\b|^The\s+session\b|"
                r"^The\s+next\b|^The\s+previous\b|^The\s+following\b|"
                r"^The\s+story\b|^The\s+narrative\b|^The\s+plot\b", fl, re.I):
        if '"' not in para and '\u201c' not in para:
            return True

    # Starts with lowercase (narrative almost never does)
    if fl[0].islower():
        return True

    return False


def is_clearly_narrative(first_line, para):
    """Return True if a paragraph is clearly narrative content."""
    fl = first_line.strip()
    if not fl:
        return False

    # 1. ALL CAPS scene header (THE COURTYARD, THE ASSEMBLY, etc.)
    if re.match(r"^[A-Z][A-Z\s'\-—:,\.&]+$", fl) and 3 < len(fl) < 100:
        # Exclude list headers that appear in thinking
        if not re.match(r"^(FOR |ALSO |AND |OR |BUT |NOTE|IMPORTANT|FIRST|SECOND|"
                        r"THIRD|CURRENT|TOTAL|WEB |STRONG|FIRM|WHAT|HOW|WHY)", fl):
            return True

    # 2. Second person — always narrative
    if re.match(r"^(You |Your )", fl):
        return True

    # 3. Direct dialogue (starts with opening quote)
    if fl[0] in '""\u201c':
        return True

    # 4. Character name + physical action verb
    #    e.g. "Álvaro nods", "The old man chuckles", "Fray Hernando's face shows"
    name_action = re.match(
        r"^(?:The\s+)?[A-ZÁÉÍÓÚÑ][a-záéíóúñ']+(?:\s+(?:de|del|di|la|ibn|al-|von)\s+[A-Za-záéíóúñ']+)*"
        r"(?:'s\s+\w+)?\s+" + ACTION_VERBS, fl
    )
    if name_action:
        return True

    # 5. Character name possessive + body/expression noun
    if re.match(
        r"^(?:The\s+)?[A-ZÁÉÍÓÚÑ][a-záéíóúñ']+(?:'s)\s+"
        r"(?:face|eyes|expression|voice|hand|hands|tone|gaze|look|smile|frown|"
        r"manner|bearing|posture|gesture|reaction|response|answer|reply|words|"
        r"silence|jaw|brow|lips|mouth|head|shoulders|body|chest|back|arms|"
        r"fingers|feet|stance|mood|demeanor|attention|focus)",
        fl):
        return True

    # 6. Title-case scene header with location/date marker
    #    e.g. "Granada's Response: April 3-25, 1431"
    #    e.g. "Alcázar of Seville, September 29, 1430"
    if re.match(r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñ']+'s\s+(Report|Response|Summary|Assessment|"
                r"Reply|Reaction|Decision|Offer|Proposal|Letter|Account|View|Gambit|"
                r"Warning|Dilemma|Choice|Request|Position|Verdict)", fl):
        return True
    # Date/location header
    if re.match(r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+(?:de|del|of|di))?.*\d{4}", fl) and len(fl) < 100:
        return True

    # 7. Short title-case line (< 80 chars, no period, looks like scene header)
    if len(fl) < 80 and not fl.endswith(('.', '?', '!', ':')):
        words = fl.split()
        if 1 <= len(words) <= 10:
            # Most words start with caps (allowing articles/prepositions lowercase)
            small_words = {'of', 'the', 'and', 'in', 'for', 'de', 'del', 'la',
                           'al-', 'ibn', 'a', 'an', 'to', 'at', 'by', 'on',
                           'with', 'from', 'vs', 'or', 'nor'}
            cap_count = sum(1 for w in words if w[0].isupper() or w.lower() in small_words)
            if cap_count == len(words):
                # Exclude obvious thinking starters
                if not re.match(
                    r"^(This|That|The\s+(?:key|question|player|GM|main|issue|most|"
                    r"first|second|third|problem|challenge)|My|I |Let|Now|So|Also|"
                    r"But|However|Note|Important|Good|Very|Looking|Checking|"
                    r"Regarding|Overall|Several|Here|There|Since|Given|Because|"
                    r"Remember|Current|Total|What|How|Why|Should|Could|Would|"
                    r"Where|When|Who|Which|Some|Many|A\s+few|Various|"
                    r"Juan|He|She|They|It|We|These|Those|Each|Every|"
                    r"After|Before|During|Between)", fl):
                    return True

    # 8. Location header pattern: "City/Place, Date"
    if re.match(r"^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s[A-Za-záéíóúñ]+)*,\s+\w+\s+\d", fl):
        return True

    # 9. Paragraph with heavy dialogue and length (even if first line is ambiguous)
    quote_count = para.count('"') + para.count('\u201c') + para.count('\u201d')
    if quote_count >= 4 and len(para.strip()) > 300:
        return True

    return False


def has_soft_narrative_markers(para):
    """Check if an ambiguous paragraph has narrative-ish qualities."""
    # Contains dialogue quotes
    if '"' in para or '\u201c' in para or '\u201d' in para:
        return True
    # Contains "Your Majesty"
    if "Your Majesty" in para:
        return True
    # Is substantial (> 300 chars)
    if len(para.strip()) > 300:
        return True
    return False


# ---------------------------------------------------------------------------
# Main stripping logic
# ---------------------------------------------------------------------------

def _strip_thinking_once(text):
    """
    One pass: strip thinking prefix from the beginning of text.
    Returns (cleaned_text, stripped_text, was_modified).
    """
    paragraphs = re.split(r"\n\n+", text)
    if not paragraphs:
        return text, "", False

    # Find first non-empty paragraph
    first_para = ""
    for p in paragraphs:
        if p.strip():
            first_para = p.strip()
            break

    first_line = first_para.split("\n")[0].strip() if first_para else ""

    if not is_clearly_thinking(first_line, first_para):
        return text, "", False

    # Walk forward through paragraphs to find the narrative start
    narrative_idx = None

    for i, para in enumerate(paragraphs):
        stripped_para = para.strip()
        if not stripped_para:
            continue

        para_first_line = stripped_para.split("\n")[0].strip()

        # Clearly narrative → this is our start
        if is_clearly_narrative(para_first_line, stripped_para):
            narrative_idx = i
            break

        # Clearly thinking → keep scanning
        if is_clearly_thinking(para_first_line, stripped_para):
            continue

        # Ambiguous paragraph
        if i > 0:
            # We've already passed thinking paragraphs
            if has_soft_narrative_markers(stripped_para):
                narrative_idx = i
                break
            # Short-to-medium ambiguous paragraph — keep scanning
            if len(stripped_para) < 250:
                continue
            # Long ambiguous paragraph — treat as narrative start
            narrative_idx = i
            break
        else:
            # First paragraph is ambiguous — don't strip anything
            return text, "", False

    if narrative_idx is None or narrative_idx == 0:
        return text, "", False

    cleaned = "\n\n".join(paragraphs[narrative_idx:]).strip()
    stripped = "\n\n".join(paragraphs[:narrative_idx]).strip()

    # Safety: don't strip more than 95% of the text
    if len(cleaned) < len(text.strip()) * 0.05:
        return text, "", False

    if not cleaned:
        return text, "", False

    return cleaned, stripped, True


def strip_thinking_prefix(text):
    """
    Strip GM thinking/meta text from the beginning of a response.
    Runs iteratively (up to 5 passes) to handle multi-layer thinking.
    Returns (cleaned_text, all_stripped_text, was_modified).
    """
    all_stripped = []
    current = text

    for _ in range(5):
        cleaned, stripped, modified = _strip_thinking_once(current)
        if not modified:
            break
        all_stripped.append(stripped)
        current = cleaned

    if all_stripped:
        return current, "\n\n".join(all_stripped), True
    return text, "", False


# ---------------------------------------------------------------------------
# Also strip web search blocks that appear mid-text (rare but possible)
# ---------------------------------------------------------------------------

def strip_web_search_blocks(text):
    """Remove embedded 'Web Search:' blocks from text."""
    # Pattern: "Web Search: <query>\n<result lines ending with URLs>\n"
    # These blocks are separated by blank lines
    paragraphs = re.split(r"\n\n+", text)
    cleaned_paragraphs = []
    stripped_count = 0

    for para in paragraphs:
        stripped_para = para.strip()
        if not stripped_para:
            cleaned_paragraphs.append(para)
            continue

        lines = stripped_para.split("\n")

        # Check if this is a web search block
        is_web = False

        # Starts with "Web Search:"
        if any(line.strip().startswith("Web Search:") for line in lines):
            is_web = True

        # Block of URL-like search results (title + domain pattern)
        if not is_web:
            url_lines = sum(
                1 for line in lines
                if re.search(r"\b\w+\.(?:org|com|net|edu|info)\s*$", line.strip())
            )
            if url_lines >= 2 and url_lines >= len(lines) * 0.4:
                is_web = True

        if is_web:
            stripped_count += 1
        else:
            cleaned_paragraphs.append(para)

    if stripped_count > 0:
        return "\n\n".join(cleaned_paragraphs).strip(), stripped_count
    return text, 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def process_files(mode="stats"):
    """Process all chapter files."""
    chapter_files = sorted(EVENTS_DIR.glob("chapter_*.json"))

    total_gm_exchanges = 0
    total_stripped = 0
    total_web_blocks = 0
    total_chars_removed = 0
    files_modified = 0

    for chapter_file in chapter_files:
        with open(chapter_file, encoding="utf-8") as f:
            data = json.load(f)

        file_modified = False

        for event in data.get("events", []):
            for exchange in event.get("exchanges", []):
                if exchange.get("role") != "gm":
                    continue

                total_gm_exchanges += 1
                text = exchange.get("text", "")
                original_len = len(text)

                # Phase 1: Strip web search blocks first (always meta content)
                cleaned, web_count = strip_web_search_blocks(text)
                was_modified = web_count > 0
                total_web_blocks += web_count

                # Phase 2: Strip thinking prefix (iterative)
                cleaned2, stripped, think_modified = strip_thinking_prefix(cleaned)
                if think_modified:
                    was_modified = True
                    cleaned = cleaned2

                # Phase 3: Strip any remaining web search blocks revealed by stripping
                cleaned3, web_count2 = strip_web_search_blocks(cleaned)
                if web_count2 > 0:
                    total_web_blocks += web_count2
                    was_modified = True
                    cleaned = cleaned3

                if was_modified:
                    total_stripped += 1
                    chars_removed = original_len - len(cleaned)
                    total_chars_removed += chars_removed

                    if mode == "report":
                        print(f"\n{'=' * 70}")
                        print(f"FILE: {chapter_file.name}  EVENT: {event.get('id', '?')}")
                        print(f"STRIPPED: {chars_removed} chars ({chars_removed * 100 // original_len}% of {original_len})")
                        if stripped:
                            preview = stripped[:300].replace("\n", "\\n")
                            print(f"REMOVED: {preview}{'...' if len(stripped) > 300 else ''}")
                        kept_preview = cleaned[:120].replace("\n", "\\n")
                        print(f"KEPT FROM: {kept_preview}...")

                    if mode == "apply":
                        exchange["text"] = cleaned
                        file_modified = True

        if file_modified:
            files_modified += 1
            with open(chapter_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.write("\n")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"SUMMARY")
    print(f"{'=' * 70}")
    print(f"Total GM exchanges:    {total_gm_exchanges}")
    print(f"Exchanges stripped:    {total_stripped} ({total_stripped * 100 // max(total_gm_exchanges, 1)}%)")
    print(f"Web search blocks:     {total_web_blocks}")
    print(f"Characters removed:    {total_chars_removed:,}")
    print(f"Files modified:        {files_modified}")

    if mode == "stats":
        print(f"\nRun with 'report' to see details, or 'apply' to make changes.")
    elif mode == "apply":
        print(f"\nChanges applied to {files_modified} files.")
    else:
        print(f"\nDry run — no files were modified. Run with 'apply' to make changes.")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "stats"
    if mode not in ("stats", "report", "apply"):
        print(f"Usage: {sys.argv[0]} [stats|report|apply]")
        sys.exit(1)
    process_files(mode)
