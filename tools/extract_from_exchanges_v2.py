#!/usr/bin/env python3
"""
Extract from Exchanges v2 — Improved extraction with lessons learned.

Improvements over v1:
  - Pre-processing: strips GM thinking/meta text before sending to Haiku
  - Alias-aware: loads known_aliases.json so Haiku uses canonical IDs
  - Stronger prompt: explicit numeric range format, DOB estimation,
    faction context, age validation rules
  - Post-processing validation: fixes outcome_range format, removes
    hallucinated rolls, validates character IDs against aliases
  - Richer known-character context: DOB, faction, aliases sent to Haiku

Usage:
  python3 tools/extract_from_exchanges_v2.py --chapter 2.25
  python3 tools/extract_from_exchanges_v2.py --from 2.25 --to 2.60
  python3 tools/extract_from_exchanges_v2.py --all
  python3 tools/extract_from_exchanges_v2.py --chapter 2.25 --dry-run
  python3 tools/extract_from_exchanges_v2.py --review-only

Options:
  --force         Overwrite existing extraction even if non-stub
  --review-only   Write review_needed.json without calling API
  --dry-run       Show what would be processed, don't call API
"""

import json
import os
import re
import sys
import time
import argparse
import unicodedata
from pathlib import Path
from datetime import datetime

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "resources" / "data"
TOOLS_DIR = PROJECT_ROOT / "tools"
EXTRACTIONS_DIR = TOOLS_DIR / "extractions"
EVENTS_DIR = DATA_DIR / "events"
ALIASES_FILE = TOOLS_DIR / "known_aliases.json"

API_URL = "https://api.anthropic.com/v1/messages"
API_MODEL = "claude-haiku-4-5-20251001"
API_VERSION = "2023-06-01"
MAX_TOKENS = 16384

# Known facts for age validation (born year → used to flag wrong ages)
KNOWN_BIRTH_YEARS = {
    "juan_ii": 1412,
    "tomas_de_torquemada": 1420,
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def normalize_id(name: str) -> str:
    """Convert a name string to a snake_case ID."""
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_only = nfkd.encode("ASCII", "ignore").decode("ASCII")
    return re.sub(r"[^a-z0-9]+", "_", ascii_only.lower()).strip("_")


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

def get_api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not key:
        config_path = PROJECT_ROOT / ".api_key"
        if config_path.exists():
            key = config_path.read_text().strip()
    if not key:
        print("ERROR: No API key found.")
        print("Set ANTHROPIC_API_KEY env var or create .api_key file in project root.")
        sys.exit(1)
    return key


def call_haiku(api_key: str, system_prompt: str, user_message: str,
               max_retries: int = 3) -> dict:
    """Call Claude Haiku with retry logic.

    Timeout is 60s per request. Backoff is capped at 16s.
    With 3 retries, worst case is ~3 min per chapter (not 15 min).
    """
    headers = {
        "x-api-key": api_key,
        "anthropic-version": API_VERSION,
        "content-type": "application/json",
    }
    payload = {
        "model": API_MODEL,
        "max_tokens": MAX_TOKENS,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_message}],
    }

    for attempt in range(max_retries):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)

            if resp.status_code == 200:
                data = resp.json()
                text = data.get("content", [{}])[0].get("text", "")
                usage = data.get("usage", {})
                return {"text": text, "usage": usage, "error": None}

            if resp.status_code == 429:
                wait = min(2 ** (attempt + 1), 16)
                print(f"    Rate limited (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
                time.sleep(wait)
                continue

            if resp.status_code >= 500:
                wait = min(2 ** (attempt + 1), 16)
                print(f"    Server error {resp.status_code} (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
                time.sleep(wait)
                continue

            return {"text": "", "usage": {}, "error": f"HTTP {resp.status_code}: {resp.text[:200]}"}

        except requests.exceptions.Timeout:
            wait = min(2 ** (attempt + 1), 16)
            print(f"    Timeout (attempt {attempt+1}/{max_retries}), waiting {wait}s...")
            time.sleep(wait)
        except requests.exceptions.RequestException as e:
            return {"text": "", "usage": {}, "error": str(e)}

    return {"text": "", "usage": {}, "error": "Max retries exceeded"}


# ---------------------------------------------------------------------------
# GM thinking / meta text stripping (pre-processing)
# ---------------------------------------------------------------------------

# Physical/dynamic action verbs — strong narrative markers
ACTION_VERBS_RE = re.compile(
    r"(?:nod|look|step|turn|stand|stood|sat|sit|spoke|speak|bow|smile|laugh|"
    r"walk|stride|rose|lean|cross|gesture|place|drew|draw|raise|shrug|sigh|"
    r"clear|pause|wait|watch|listen|reach|move|open|close|meet|set|take|pour|"
    r"pull|return|begin|start|stop|stare|study|consider|ask|answer|reply|"
    r"respond|shake|wave|point|glance|gaze|frown|grin|chuckle|murmur|mutter|"
    r"whisper|shout|scream|cry|gasp|groan|snort|inhale|exhale|felt|held|grab|"
    r"seize|drop|lift|lower|push|emerge|appear|arrive|enter|exit|leave|depart|"
    r"approach|retreat|advance|withdraw|kneel|bend|stretch|roll|flip|spin|"
    r"twist|squeeze|press|touch|stroke|settle|spread|tap|pace|remove|dismount|"
    r"mount|clap|interject|scatter|feed|gather|produce|unfold|beckon|summon|"
    r"straighten|brighten|darken|soften|harden|tighten|loosen|narrow|widen)"
)


def is_clearly_thinking(first_line: str, para: str) -> bool:
    """Return True if a paragraph is clearly GM thinking / meta content."""
    fl = first_line.strip()
    if not fl:
        return True

    # Numbered list item
    if re.match(r"^\d+[\.\)\:]\s", fl):
        return True

    # Bullet / dash list
    if re.match(r"^[-\*•]\s", fl):
        return True

    # First person (GM meta voice)
    if re.match(r"^(I |I'm |I'll |I've |I'd |I need|I should|I want|I can|I think|I was)", fl):
        return True
    if re.match(r"^(Let me|My |Me )", fl):
        return True

    # "This is/should/could..." analytical opener
    if re.match(r"^This\s+(is|should|could|would|might|was|needs|requires|creates|chapter|isn)", fl, re.I):
        return True
    if re.match(r"^That\s+(is|said|was|would|could|should|means|makes)", fl, re.I):
        return True

    # "The key/question/player..." analytical
    if re.match(
        r"^(The|A)\s+(key|question|player|GM|main|issue|most|first|second|third|"
        r"problem|challenge|goal|important|critical|biggest|real|fact|point|idea|"
        r"risk|complication|consideration|implication|advantage|benefit|danger|"
        r"difficulty|tricky|upshot|lesson|math|calculation|bottom|net|overall|"
        r"result|outcome|truth|reality|situation|scenario|thing|reason|answer|"
        r"file|document|decree|chapter|roll|contrast|gap|irony|"
        r"papal|current|crusade|actual|logical|"
        r"fundamental|core|basic|central|primary|secondary|existing|original|"
        r"revised|proposed|above|user|established|crucial|essential)",
        fl, re.I):
        return True

    # "They're/They are" meta about NPCs
    if re.match(r"^They'?r?e?\s+(also|are|were|will|would|could|should|have|had|"
                r"need|want|don't|didn't|can't|introducing|proposing|asking)", fl):
        if '"' not in para and '\u201c' not in para:
            return True

    # "If" conditional (non-narrative)
    if re.match(r"^If\s+(the|they|we|I|he|she|this|that|Juan|it|Basel|Granada)", fl):
        if '"' not in para and '\u201c' not in para and 'Your Majesty' not in para:
            return True

    # Tool use labels
    if re.match(r"^(Tool:|Bash Tool:|Create File:|View:|Read:|Write:|Edit:)", fl):
        return True

    # Note/Thought process markers
    if re.match(r"^(Note|Important|Thought\s*process|Thinking|NB)\s*[:!\-]?", fl, re.I):
        return True

    # Good roleplaying praise
    if re.match(
        r"^(Good|Very\s+good|Excellent|Great|Nice|Interesting|Perfect)\s+"
        r"(roleplaying|roleplay|question|move|point|idea|decision|choice|thinking)",
        fl, re.I):
        return True

    # Meta about Juan / the player
    if re.match(r"^Juan\s+(is|has|was|should|wants|would|doesn't|didn't)", fl):
        return True
    if re.match(r"^(The player|The user)\s", fl, re.I):
        return True

    # Connective starters
    if re.match(r"^(Now[,\s]|So[,\s]|However|But |Also[,\s]|Actually|Wait[,\s]|"
                r"Hmm|Okay|Ok,|OK,|Well[,\s]|Right[,\s]|Alright|Yes[,\s]|No[,\s])", fl):
        return True

    # Questions to self (not narrative dialogue)
    if re.match(r"^(What |How |Why |Should |Could |Would |Where |When |Who |Which )", fl):
        if '"' not in para and '\u201c' not in para and 'Your Majesty' not in para:
            return True

    # Process / investigation verbs
    if re.match(r"^(Looking\s+at|Checking|Reviewing|Considering|Thinking\s+about|"
                r"Processing|Searching|Analyzing|Reading|Examining)", fl, re.I):
        return True

    # Web search block
    if "Web Search:" in fl:
        return True

    # Causal / conditional openers (non-narrative)
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
        if '"' not in para and '\u201c' not in para:
            return True

    # "Here is/are", "There is/are"
    if re.match(r"^(Here|There)\s+(is|are|was|were)", fl):
        return True

    # "Regarding / Concerning / As for"
    if re.match(r"^(Regarding|Concerning|As\s+for|As\s+to|About\s+)", fl):
        return True

    # "Remember / Recall"
    if re.match(r"^(Remember|Recall|Keep\s+in\s+mind|Bear\s+in\s+mind)", fl):
        return True

    # "Overall / To summarize"
    if re.match(r"^(Overall|To\s+sum|To\s+summarize)", fl):
        return True

    # Web URLs
    if re.search(r"(wikipedia\.org|\.com|\.net|\.edu)\s*$", fl):
        return True

    # Analytical verbs applied to characters
    if re.match(r"^(?:The\s+)?[A-Z\u00c0-\u00dc][a-z\u00e0-\u00fc']+(?:\s+(?:de|del|di|la|ibn|al-|von)\s+"
                r"[A-Za-z\u00e0-\u00fc']+)*(?:\s+[A-Z\u00c0-\u00dc][\w']*)*\s+"
                r"(?:is|are|was|were|has|had|have|would|could|should|might|may|"
                r"needs?|requires?|represents?|means?|seems?|appears?|deserves?|"
                r"tends?|lacks?|faces?|remains?|becomes?|involves?)\s", fl):
        if '"' not in para and '\u201c' not in para and 'Your Majesty' not in para:
            return True

    return False


def is_narrative_paragraph(para: str) -> bool:
    """Return True if a paragraph looks like actual narrative."""
    fl = para.split("\n")[0].strip()
    if not fl:
        return False

    # Dialogue markers
    if '"' in para or '\u201c' in para or '\u2014' in para:
        return True

    # Character title + name doing something
    if re.match(r"^(Don |Doña |King |Queen |Prince |Princess |Cardinal |Bishop |"
                r"Pope |Brother |Father |Fray |Captain |Commander |Admiral |"
                r"Archbishop |Duke |Count |Sergeant |Baron |Marquis |Sheikh |Imam )", fl):
        return True

    # Action verb early in first line
    match = ACTION_VERBS_RE.search(fl[:120])
    if match and match.start() < 60:
        return True

    # Scene-setting descriptions
    if re.match(r"^(The\s+(sun|moon|wind|rain|snow|dawn|dusk|morning|evening|night|"
                r"room|hall|chamber|palace|castle|church|courtyard|garden|road|"
                r"ship|fleet|army|crowd|city|walls|gates|door|torch|candle|fire))", fl, re.I):
        return True

    return False


def strip_gm_thinking(text: str) -> str:
    """Strip GM thinking/meta paragraphs from the beginning of GM text."""
    if not text or len(text) < 20:
        return text

    paragraphs = re.split(r"\n\n+", text)
    if len(paragraphs) <= 1:
        return text

    # Find where narrative begins
    first_narrative_idx = 0
    for i, para in enumerate(paragraphs):
        first_line = para.split("\n")[0]

        if is_narrative_paragraph(para):
            first_narrative_idx = i
            break

        if is_clearly_thinking(first_line, para):
            first_narrative_idx = i + 1
            continue

        # Ambiguous — keep it (conservative)
        first_narrative_idx = i
        break

    if first_narrative_idx >= len(paragraphs):
        # Everything was thinking — return original to be safe
        return text

    if first_narrative_idx == 0:
        return text

    result = "\n\n".join(paragraphs[first_narrative_idx:])
    return result


def detect_role_swap(exchanges: list) -> bool:
    """Detect if player/gm roles appear swapped (GM-style content in player role)."""
    swap_signals = 0
    for ex in exchanges:
        role = ex.get("role", "")
        text = ex.get("text", "")[:500]

        if role == "player":
            # Player messages with narrative descriptions suggest swapped roles
            if re.search(r"^(The|A)\s+(sun|hall|chamber|courtyard|room)", text):
                swap_signals += 1
            if re.search(r"(Your Majesty|bowed|spoke solemnly|voice echoed)", text):
                swap_signals += 1
        elif role == "gm":
            # GM messages that are very short (< 100 chars) with first person
            if len(text) < 100 and re.match(r"^(I |I'm |I'll )", text):
                swap_signals += 1

    # More than 3 signals suggests systematic role swap
    return swap_signals >= 3


# ---------------------------------------------------------------------------
# Alias resolution
# ---------------------------------------------------------------------------

def build_alias_index(aliases: dict, characters_db: list) -> dict:
    """Build reverse lookup: any alias → canonical_id."""
    index = {}
    for canonical_id, info in aliases.items():
        index[canonical_id] = canonical_id
        for alias in info.get("aliases", []):
            index[alias] = canonical_id

    # Also map existing character IDs to themselves
    for c in characters_db:
        cid = c["id"]
        if cid not in index:
            index[cid] = cid
        # Add character's aliases
        for alias in c.get("aliases", []):
            if alias not in index:
                index[alias] = cid

    return index


def resolve_id(raw_id: str, alias_index: dict) -> str:
    """Resolve an ID through the alias index."""
    return alias_index.get(raw_id, raw_id)


# ---------------------------------------------------------------------------
# Prompts (v2 — much stronger)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a data extraction assistant for a historical simulation game set in 1430s Castile (starting 1430). You read game session transcripts (player/GM exchanges) and extract structured data.

You MUST respond with valid JSON only. No markdown fences, no explanation, no commentary outside the JSON.

CRITICAL RULES:

1. CHARACTER IDs: Use lowercase_with_underscores (e.g., "alvaro_de_luna"). For clergy, use their title form: "cardinal_capranica" not "prospero_capranica", "pope_eugenius_iv" not "eugenius_iv". Check the KNOWN CHARACTERS list — if a character is already there, use their EXACT id.

2. CHARACTER DEDUPLICATION: Before creating a new character, check if they match anyone in the known characters list by name, title, or aliases. Cardinals, bishops, popes often have multiple name forms. If unsure, add a review_flag instead of creating a duplicate.

3. ROLLS: Only extract rolls where the text EXPLICITLY shows a d100 number (e.g., "Roll: 74", "d100: 83", "rolled 45"). Do NOT invent or infer rolls. If a roll is mentioned but no number given, skip it.

4. OUTCOME RANGES: Must be numeric format "NN-NN" (e.g., "01-10", "61-80", "94-100"). NEVER use labels like "critical_success" or descriptive phrases. If the text shows a range table, use the exact ranges from the table. If not, use standard ranges: 01-10, 11-25, 26-40, 41-60, 61-80, 81-93, 94-100.

5. DATES: Use YYYY-MM-DD format. The game starts in 1430. Juan II was born 1412-03-06 (age 18 in 1430). Validate that character ages make sense for the date.

6. BIRTH YEAR ESTIMATION: When the text mentions a character's age or age-related description (e.g., "a man in his fifties", "young captain", "elderly bishop"), estimate their birth year. For "young" (20s-30s), "middle-aged" (40s-50s), "elderly" (60s+).

7. FACTION ASSIGNMENT: For new characters, assign faction_ids from the known factions list. Clergy → castilian_church/papacy/council_of_basel. Military → castile/military_orders. Nobility → royal_court. Granadan → granada. If genuinely unaffiliated, use "independent".

8. GM THINKING: Ignore any text that is clearly GM meta-commentary (numbered plans, first-person analysis, "I think...", "The player..."). Extract only from narrative text and dialogue.

9. CONTINUITY: Track children correctly. Juan II's children with Lucia d'Este should be numbered based on the KNOWN CHARACTERS list (check existing children). Do not call a child "second" if it's actually the first with that partner.

10. ANACHRONISMS: Flag any reference to events/terms that are anachronistic for the 1430s (e.g., "Pragmatic Sanction" before 1438, institutions that don't exist yet)."""


def build_extraction_prompt(chapter_id: str, events: list,
                            known_characters: dict, known_factions: list,
                            alias_index: dict) -> str:
    """Build the user message for extraction."""
    parts = []
    parts.append(f"# Chapter {chapter_id} — Extract enrichment data\n")
    parts.append("Read each event's exchange text below and extract the requested data.\n")

    for i, evt in enumerate(events):
        parts.append(f"\n## Event {i} — {evt.get('type', '?')} — {evt.get('date', '?')}")
        parts.append(f"Location: {evt.get('location', '?')}")
        parts.append(f"Characters: {', '.join(evt.get('characters', []))}")
        parts.append(f"Summary: {evt.get('summary', '')}")

        # Include exchange text — pre-processed to strip GM thinking
        exchanges = evt.get("exchanges", [])
        exchange_text = []
        total_chars = 0
        for ex in exchanges:
            text = ex.get("text", "")
            role = ex.get("role", "unknown")

            # Strip GM thinking from GM responses
            if role == "gm":
                text = strip_gm_thinking(text)

            # Cap per-event exchange text at ~15000 chars
            if total_chars + len(text) > 15000:
                exchange_text.append(f"[{role.upper()}]: {text[:2000]}... [TRUNCATED]")
                break
            exchange_text.append(f"[{role.upper()}]: {text}")
            total_chars += len(text)

        parts.append("\n### Exchange text:")
        parts.append("\n".join(exchange_text))

    # Known characters context (enriched)
    if known_characters:
        parts.append("\n\n## KNOWN CHARACTERS (already in database — use these exact IDs)")
        for cid, cdata in known_characters.items():
            aliases_str = ""
            if cdata.get("aliases"):
                aliases_str = f" (aliases: {', '.join(cdata['aliases'][:5])})"
            faction_str = ""
            if cdata.get("faction_ids"):
                faction_str = f" [factions: {', '.join(cdata['faction_ids'][:3])}]"
            born_str = ""
            if cdata.get("born") and cdata["born"] != "0000-00-00":
                born_str = f" born={cdata['born'][:4]}"
            parts.append(f"- {cid}: {cdata.get('name', '?')} — "
                         f"{cdata.get('title', '(no title)')}"
                         f"{born_str}{aliases_str}{faction_str}")

    # Known factions
    if known_factions:
        parts.append("\n\n## KNOWN FACTIONS (use these IDs for faction assignments)")
        for f in known_factions:
            parts.append(f"- {f['faction_id']}: {f.get('name', '?')} ({f.get('type', '?')})")

    parts.append("""

## Requested output

Return a JSON object with these keys:

```json
{
  "character_updates": [
    {
      "id": "character_id",
      "current_task": "What they are doing now (specific, detailed)",
      "location": "Where they are now (if changed)",
      "status": ["active"],
      "confidence": "high"
    }
  ],
  "new_characters": [
    {
      "id": "character_id",
      "name": "Full Name",
      "title": "Their title or role (required — use '(untitled)' for commoners)",
      "born": "YYYY-00-00 (estimate from age clues, or 0000-00-00 if no clues)",
      "category": ["nobility|clergy|military|household|economic|other"],
      "faction_ids": ["faction_id"],
      "appearance": {
        "age_appearance": "description",
        "build": "description",
        "hair": "description",
        "distinguishing_features": "description"
      },
      "speech_style": "How they speak (10+ words, from actual dialogue)",
      "personality": ["trait1", "trait2"],
      "interests": ["interest1"],
      "core_characteristics": "1-2 sentence summary of who they are"
    }
  ],
  "character_descriptions": [
    {
      "id": "existing_character_id",
      "appearance": {
        "age_appearance": "description from text",
        "build": "description from text",
        "hair": "description from text",
        "distinguishing_features": "description from text"
      },
      "speech_style": "How they speak based on their dialogue (10+ words)",
      "personality_traits": ["trait1", "trait2"],
      "interests": ["interest1", "interest2"],
      "confidence": "high"
    }
  ],
  "rolls": [
    {
      "event_index": 0,
      "title": "Brief title for the roll",
      "context": "Why the roll is happening",
      "roll_type": "military|diplomacy|persuasion|chaos|travel|espionage|religion|economy|intrigue|personal",
      "date": "YYYY-MM-DD",
      "rolled": 74,
      "outcome_range": "61-80",
      "outcome_label": "Brief label",
      "outcome_detail": "What specifically happened as a result",
      "evaluation": "Assessment of significance",
      "success_factors": ["factor1"],
      "failure_factors": ["factor2"],
      "ranges": [
        {"range": "01-10", "label": "Critical Failure", "summary": "..."},
        {"range": "11-25", "label": "Failure", "summary": "..."}
      ]
    }
  ],
  "faction_updates": [
    {
      "faction_id": "faction_id",
      "description": "2-4 sentences on current status and outlook",
      "confidence": "high"
    }
  ],
  "law_references": [
    {
      "law_id": "law_NNN or new_law_title",
      "event_index": 0,
      "action": "enacted|modified|repealed|referenced",
      "summary": "What the law does"
    }
  ],
  "location_descriptions": [
    {
      "location_name": "Location Name",
      "description": "1-3 sentences from the exchange text",
      "sub_locations": ["specific areas mentioned"]
    }
  ],
  "review_flags": [
    {
      "type": "character|roll|faction|law|location|continuity|anachronism|age_error",
      "detail": "Description of what needs human review",
      "event_index": 0
    }
  ]
}
```

CRITICAL RULES FOR OUTPUT:
- character_updates: Only for characters whose situation MATERIALLY CHANGES
- character_descriptions: Only when text provides EXPLICIT physical/speech details
- new_characters: Characters in the exchanges NOT in the known characters list. Provide title, faction, and birth year estimate.
- rolls: ONLY extract rolls with explicit d100 values in the text. outcome_range MUST be "NN-NN" format. Include the full range table if the GM provided one.
- faction_updates: Use known faction IDs only
- review_flags: Flag duplicates, age inconsistencies, anachronisms, ambiguous character identities
- Empty arrays are fine if a category has nothing to extract
- Do NOT add juan_ii to any faction — he is already assigned
""")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Post-processing validation
# ---------------------------------------------------------------------------

NUMERIC_RANGE_RE = re.compile(r"^\d{1,3}-\d{1,3}$")

LABEL_TO_RANGE = {
    "critical_failure": "01-10",
    "revolt": "01-10",
    "failure": "11-25",
    "mixed_negative": "26-40",
    "mixed": "26-40",
    "partial_failure": "26-40",
    "status_quo": "41-60",
    "success": "61-80",
    "strong_success": "81-93",
    "major_success": "81-93",
    "critical_success": "94-100",
}


def infer_range_from_rolled(rolled: int) -> str:
    """Given a rolled value, return the standard numeric range."""
    if rolled <= 10:
        return "01-10"
    elif rolled <= 25:
        return "11-25"
    elif rolled <= 40:
        return "26-40"
    elif rolled <= 60:
        return "41-60"
    elif rolled <= 80:
        return "61-80"
    elif rolled <= 93:
        return "81-93"
    else:
        return "94-100"


def validate_and_fix_rolls(rolls: list, chapter_id: str) -> tuple:
    """Validate and fix roll data. Returns (fixed_rolls, warnings)."""
    fixed = []
    warnings = []

    for r in rolls:
        rolled = r.get("rolled")

        # Remove hallucinated rolls (no actual d100 value)
        if rolled is None:
            warnings.append(f"  Removed hallucinated roll: '{r.get('title', '?')}' (no d100 value)")
            continue

        # Ensure rolled is an integer
        try:
            rolled = int(rolled)
            r["rolled"] = rolled
        except (TypeError, ValueError):
            warnings.append(f"  Removed invalid roll value '{rolled}': '{r.get('title', '?')}'")
            continue

        # Validate rolled is in d100 range
        if rolled < 1 or rolled > 100:
            warnings.append(f"  Removed out-of-range roll {rolled}: '{r.get('title', '?')}'")
            continue

        # Fix outcome_range format
        rng = r.get("outcome_range", "") or ""
        if rng and not NUMERIC_RANGE_RE.match(rng):
            # Try label conversion
            label_key = rng.lower().replace(" ", "_")
            if label_key in LABEL_TO_RANGE:
                old = rng
                r["outcome_range"] = LABEL_TO_RANGE[label_key]
                warnings.append(f"  Fixed range label '{old}' → '{r['outcome_range']}'")
            else:
                # Infer from rolled value
                r["outcome_range"] = infer_range_from_rolled(rolled)
                warnings.append(f"  Fixed descriptive range '{rng}' → '{r['outcome_range']}'")
        elif not rng:
            r["outcome_range"] = infer_range_from_rolled(rolled)

        # Validate ranges array entries
        if r.get("ranges"):
            for range_entry in r["ranges"]:
                rng_str = range_entry.get("range", "")
                if rng_str and not NUMERIC_RANGE_RE.match(rng_str):
                    # Try to fix
                    label_key = rng_str.lower().replace(" ", "_")
                    if label_key in LABEL_TO_RANGE:
                        range_entry["range"] = LABEL_TO_RANGE[label_key]

        fixed.append(r)

    return fixed, warnings


def validate_character_ids(api_data: dict, alias_index: dict, chapter_id: str) -> list:
    """Validate character IDs and resolve aliases. Returns warnings."""
    warnings = []

    # Fix character_updates IDs
    for cu in api_data.get("character_updates", []):
        raw_id = cu.get("id", "")
        canonical = resolve_id(raw_id, alias_index)
        if canonical != raw_id:
            warnings.append(f"  Resolved character update '{raw_id}' → '{canonical}'")
            cu["id"] = canonical

    # Fix character_descriptions IDs
    for cd in api_data.get("character_descriptions", []):
        raw_id = cd.get("id", "")
        canonical = resolve_id(raw_id, alias_index)
        if canonical != raw_id:
            warnings.append(f"  Resolved character description '{raw_id}' → '{canonical}'")
            cd["id"] = canonical

    # Check new_characters for duplicates
    new_chars = api_data.get("new_characters", [])
    deduped = []
    for nc in new_chars:
        raw_id = nc.get("id", "")
        canonical = resolve_id(raw_id, alias_index)
        if canonical != raw_id and canonical in alias_index:
            warnings.append(f"  Removed duplicate new character '{raw_id}' "
                            f"(already exists as '{canonical}')")
            continue
        # Also normalize the ID
        nc["id"] = canonical
        deduped.append(nc)
    api_data["new_characters"] = deduped

    # Validate faction_ids on new characters
    for nc in api_data.get("new_characters", []):
        faction_ids = nc.get("faction_ids", [])
        if not faction_ids:
            warnings.append(f"  New character '{nc.get('id')}' has no faction_ids")

    return warnings


def validate_faction_references(api_data: dict, known_faction_ids: set,
                                 chapter_id: str) -> list:
    """Check faction_ids reference valid factions."""
    warnings = []

    for fu in api_data.get("faction_updates", []):
        fid = fu.get("faction_id", "")
        if fid and fid not in known_faction_ids:
            warnings.append(f"  Unknown faction in update: '{fid}'")

    # Don't add juan_ii to faction membership
    for nc in api_data.get("new_characters", []):
        if nc.get("id") == "juan_ii":
            warnings.append("  Haiku tried to create juan_ii as new character — removed")
            api_data["new_characters"].remove(nc)

    return warnings


# ---------------------------------------------------------------------------
# Chapter processing
# ---------------------------------------------------------------------------

def is_stub_extraction(extraction_path: Path) -> bool:
    """Check if an extraction file is a stub (no enrichment)."""
    if not extraction_path.exists():
        return True
    data = load_json(extraction_path)
    updates = data.get("character_updates", [])
    return len(updates) == 0


def get_known_characters(events: list, characters_db: list) -> dict:
    """Get enriched known character data for characters appearing in events."""
    char_ids = set()
    for evt in events:
        for cid in evt.get("characters", []):
            char_ids.add(cid)

    char_lookup = {c["id"]: c for c in characters_db}
    # Also build alias → character lookup
    alias_to_char = {}
    for c in characters_db:
        for alias in c.get("aliases", []):
            alias_to_char[alias] = c

    result = {}
    for cid in sorted(char_ids):
        char = char_lookup.get(cid) or alias_to_char.get(cid)
        if char:
            result[char["id"]] = {
                "name": char.get("name", ""),
                "title": char.get("title", ""),
                "born": char.get("born", ""),
                "aliases": char.get("aliases", []),
                "faction_ids": char.get("faction_ids", []),
                "category": char.get("category", []),
            }
    return result


def parse_api_response(text: str) -> dict:
    """Parse JSON from API response, handling markdown fences."""
    text = text.strip()
    # Remove markdown code fences
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        # Try to find JSON in the text
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {"error": f"Failed to parse JSON: {e}", "raw": text[:500]}


def merge_extraction_data(existing: dict, api_data: dict) -> dict:
    """Merge API extraction data into existing extraction file."""
    # Character updates
    if api_data.get("character_updates"):
        existing["character_updates"] = api_data["character_updates"]

    # Rolls
    if api_data.get("rolls"):
        existing["rolls"] = api_data["rolls"]

    # Faction updates
    if api_data.get("faction_updates"):
        existing["faction_updates"] = api_data["faction_updates"]

    # Law references
    if api_data.get("law_references"):
        existing["law_references"] = api_data["law_references"]

    # New characters from v2 (Haiku now returns these directly)
    if api_data.get("new_characters"):
        # Merge with existing new_characters, preferring API data
        existing_ids = {nc["id"] for nc in existing.get("new_characters", [])}
        for nc in api_data["new_characters"]:
            if nc["id"] not in existing_ids:
                existing.setdefault("new_characters", []).append(nc)
            else:
                # Update existing entry with enrichment
                for enc in existing["new_characters"]:
                    if enc["id"] == nc["id"]:
                        if nc.get("appearance"):
                            enc["appearance"] = nc["appearance"]
                        if nc.get("speech_style"):
                            enc["speech_style"] = nc["speech_style"]
                        if nc.get("personality"):
                            enc["personality"] = nc["personality"]
                        if nc.get("title"):
                            enc["title"] = nc["title"]
                        if nc.get("born") and nc["born"] != "0000-00-00":
                            enc["born"] = nc["born"]
                        if nc.get("faction_ids"):
                            enc["faction_ids"] = nc["faction_ids"]
                        if nc.get("core_characteristics"):
                            enc["core_characteristics"] = nc["core_characteristics"]
                        break

    # Enrich existing new_characters with descriptions
    if api_data.get("character_descriptions"):
        desc_lookup = {d["id"]: d for d in api_data["character_descriptions"]}
        for nc in existing.get("new_characters", []):
            cid = nc.get("id", "")
            if cid in desc_lookup:
                desc = desc_lookup[cid]
                if desc.get("appearance"):
                    nc["appearance"] = desc["appearance"]
                if desc.get("speech_style"):
                    nc["speech_style"] = desc["speech_style"]
                if desc.get("personality_traits") and len(desc["personality_traits"]) > len(nc.get("personality", [])):
                    nc["personality"] = desc["personality_traits"]
                if desc.get("interests") and len(desc["interests"]) > len(nc.get("interests", [])):
                    nc["interests"] = desc["interests"]

    # Enrich new_locations with descriptions
    if api_data.get("location_descriptions"):
        loc_lookup = {}
        for ld in api_data["location_descriptions"]:
            name = ld.get("location_name", "").lower().replace(" ", "_")
            loc_lookup[name] = ld
        for nl in existing.get("new_locations", []):
            lid = nl.get("location_id", "").lower()
            name = nl.get("name", "").lower().replace(" ", "_")
            match = loc_lookup.get(lid) or loc_lookup.get(name)
            if match:
                if match.get("description"):
                    nl["description"] = match["description"]
                if match.get("sub_locations"):
                    nl["sub_locations"] = match["sub_locations"]

    # Store review flags
    if api_data.get("review_flags"):
        existing["_review_flags"] = api_data["review_flags"]

    return existing


def process_chapter(chapter_id: str, api_key: str, alias_index: dict,
                    known_faction_ids: set, dry_run: bool = False,
                    force: bool = False) -> dict:
    """Process a single chapter. Returns stats dict."""
    stats = {"chapter": chapter_id, "status": "skipped", "input_tokens": 0,
             "output_tokens": 0, "cost": 0.0, "review_flags": 0,
             "validation_warnings": 0}

    chapter_path = EVENTS_DIR / f"chapter_{chapter_id}.json"
    if not chapter_path.exists():
        stats["status"] = "missing"
        print(f"  {chapter_id}: SKIP (no chapter file)")
        return stats

    extraction_path = EXTRACTIONS_DIR / f"chapter_{chapter_id}_extracted.json"
    if not force and extraction_path.exists() and not is_stub_extraction(extraction_path):
        stats["status"] = "already_enriched"
        print(f"  {chapter_id}: SKIP (already enriched, use --force to overwrite)")
        return stats

    chapter_data = load_json(chapter_path)
    events = chapter_data.get("events", [])
    if not events:
        stats["status"] = "no_events"
        print(f"  {chapter_id}: SKIP (no events)")
        return stats

    # Check for role swapping
    for evt in events:
        if detect_role_swap(evt.get("exchanges", [])):
            print(f"  {chapter_id}: WARNING — possible role swap detected in event")

    # Load known characters (enriched)
    characters_db = load_json(DATA_DIR / "characters.json").get("characters", [])
    known_chars = get_known_characters(events, characters_db)

    # Load known factions
    factions_db = load_json(DATA_DIR / "factions.json").get("factions", [])
    known_factions_list = [{"faction_id": f["faction_id"],
                            "name": f.get("name", ""),
                            "type": f.get("type", "")} for f in factions_db]

    # Build prompt
    prompt = build_extraction_prompt(chapter_id, events, known_chars,
                                     known_factions_list, alias_index)
    prompt_tokens = len(prompt) // 4  # Rough estimate

    if dry_run:
        stats["status"] = "dry_run"
        stats["input_tokens"] = prompt_tokens
        print(f"  {chapter_id}: DRY RUN — {len(events)} events, "
              f"~{prompt_tokens:,} input tokens")
        return stats

    print(f"  {chapter_id}: Processing {len(events)} events "
          f"(~{prompt_tokens:,} tokens)...", end="", flush=True)

    # Call API
    t0 = time.time()
    result = call_haiku(api_key, SYSTEM_PROMPT, prompt)
    elapsed = time.time() - t0

    if result["error"]:
        stats["status"] = "error"
        print(f" ERROR: {result['error']}")
        return stats

    usage = result.get("usage", {})
    stats["input_tokens"] = usage.get("input_tokens", 0)
    stats["output_tokens"] = usage.get("output_tokens", 0)
    stats["cost"] = (stats["input_tokens"] * 0.80 / 1_000_000 +
                     stats["output_tokens"] * 4.00 / 1_000_000)

    # Parse response
    api_data = parse_api_response(result["text"])
    if "error" in api_data:
        stats["status"] = "parse_error"
        print(f" PARSE ERROR: {api_data['error']}")
        debug_path = TOOLS_DIR / f"debug_response_{chapter_id}.txt"
        debug_path.write_text(result["text"])
        print(f"    Raw response saved to {debug_path}")
        return stats

    # --- Post-processing validation ---
    all_warnings = []

    # 1. Validate and fix rolls
    if api_data.get("rolls"):
        fixed_rolls, roll_warnings = validate_and_fix_rolls(api_data["rolls"], chapter_id)
        api_data["rolls"] = fixed_rolls
        all_warnings.extend(roll_warnings)

    # 2. Validate character IDs against aliases
    char_warnings = validate_character_ids(api_data, alias_index, chapter_id)
    all_warnings.extend(char_warnings)

    # 3. Validate faction references
    fac_warnings = validate_faction_references(api_data, known_faction_ids, chapter_id)
    all_warnings.extend(fac_warnings)

    stats["validation_warnings"] = len(all_warnings)

    # Print warnings
    if all_warnings:
        print(f"\n    Validation ({len(all_warnings)} fixes):")
        for w in all_warnings[:10]:
            print(f"    {w}")
        if len(all_warnings) > 10:
            print(f"    ... and {len(all_warnings) - 10} more")

    # Load or create extraction file
    if extraction_path.exists():
        existing = load_json(extraction_path)
    else:
        existing = {
            "chapter": chapter_id,
            "book": chapter_data.get("book", 1),
            "events": events,
            "new_characters": [],
            "character_updates": [],
            "new_locations": [],
            "new_factions": [],
            "rolls": [],
            "law_references": [],
            "faction_updates": [],
        }

    # Merge API data
    enriched = merge_extraction_data(existing, api_data)

    # Add extraction metadata
    enriched["_extraction_meta"] = {
        "version": "2.0",
        "timestamp": datetime.now().isoformat(),
        "model": API_MODEL,
        "input_tokens": stats["input_tokens"],
        "output_tokens": stats["output_tokens"],
        "cost_usd": stats["cost"],
        "elapsed_seconds": round(elapsed, 1),
        "validation_warnings": len(all_warnings),
    }

    save_json(extraction_path, enriched)

    # Count results
    n_updates = len(api_data.get("character_updates", []))
    n_new_chars = len(api_data.get("new_characters", []))
    n_descs = len(api_data.get("character_descriptions", []))
    n_rolls = len(api_data.get("rolls", []))
    n_flags = len(api_data.get("review_flags", []))
    stats["review_flags"] = n_flags
    stats["status"] = "success"

    print(f" OK ({elapsed:.1f}s) — {n_updates} updates, {n_new_chars} new chars, "
          f"{n_descs} descs, {n_rolls} rolls, {n_flags} flags, "
          f"{len(all_warnings)} fixed, ${stats['cost']:.3f}")

    return stats


# ---------------------------------------------------------------------------
# Review flags aggregation
# ---------------------------------------------------------------------------

def collect_review_flags():
    """Collect all review flags from extraction files into review_needed.json."""
    all_flags = []
    for path in sorted(EXTRACTIONS_DIR.glob("chapter_*_extracted.json")):
        data = load_json(path)
        chapter = data.get("chapter", "?")
        for flag in data.get("_review_flags", []):
            flag["chapter"] = chapter
            all_flags.append(flag)

    output_path = TOOLS_DIR / "review_needed.json"
    save_json(output_path, {
        "total_flags": len(all_flags),
        "flags": all_flags,
    })
    print(f"\nWrote {len(all_flags)} review flags to {output_path}")


# ---------------------------------------------------------------------------
# Chapter discovery
# ---------------------------------------------------------------------------

def get_chapter_range(from_ch: str, to_ch: str) -> list:
    """Generate chapter IDs from range."""
    chapters = []
    for path in sorted(EVENTS_DIR.glob("chapter_*.json")):
        ch = path.stem.replace("chapter_", "")
        chapters.append(ch)

    def ch_key(c):
        parts = c.split(".")
        return (int(parts[0]), int(parts[1]))

    from_key = ch_key(from_ch)
    to_key = ch_key(to_ch)

    return [c for c in chapters if from_key <= ch_key(c) <= to_key]


def get_all_needing_enrichment() -> list:
    """Find all chapters that have stub extractions."""
    chapters = []
    for path in sorted(EVENTS_DIR.glob("chapter_*.json")):
        ch = path.stem.replace("chapter_", "")
        extraction_path = EXTRACTIONS_DIR / f"chapter_{ch}_extracted.json"
        if is_stub_extraction(extraction_path):
            chapters.append(ch)
    return chapters


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Extract enrichment data from chapter exchanges via Haiku (v2 — improved)")
    parser.add_argument("--chapter", type=str, help="Process single chapter (e.g., 2.25)")
    group = parser.add_argument_group("range")
    group.add_argument("--from", dest="from_ch", type=str, help="Start chapter")
    group.add_argument("--to", dest="to_ch", type=str, help="End chapter")
    parser.add_argument("--all", action="store_true",
                        help="Process all chapters needing enrichment")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be processed")
    parser.add_argument("--force", action="store_true",
                        help="Overwrite existing non-stub extractions")
    parser.add_argument("--review-only", action="store_true",
                        help="Only collect review flags")
    args = parser.parse_args()

    if args.review_only:
        collect_review_flags()
        return

    # Determine chapters to process
    if args.chapter:
        chapters = [args.chapter]
    elif args.from_ch and args.to_ch:
        chapters = get_chapter_range(args.from_ch, args.to_ch)
    elif args.all:
        chapters = get_all_needing_enrichment()
    else:
        parser.print_help()
        return

    if not chapters:
        print("No chapters to process.")
        return

    print(f"Extract from Exchanges v2")
    print(f"Processing {len(chapters)} chapter(s): {chapters[0]} — {chapters[-1]}\n")

    # Load global data (once, not per chapter)
    print("Loading databases...")
    aliases = load_json(ALIASES_FILE) if ALIASES_FILE.exists() else {}
    characters_db = load_json(DATA_DIR / "characters.json").get("characters", [])
    factions_db = load_json(DATA_DIR / "factions.json").get("factions", [])

    alias_index = build_alias_index(aliases, characters_db)
    known_faction_ids = {f["faction_id"] for f in factions_db}

    print(f"  {len(alias_index)} alias mappings, {len(known_faction_ids)} factions, "
          f"{len(characters_db)} characters\n")

    # Get API key (skip for dry run)
    api_key = "" if args.dry_run else get_api_key()

    total_stats = {
        "processed": 0, "skipped": 0, "errors": 0,
        "input_tokens": 0, "output_tokens": 0, "cost": 0.0,
        "review_flags": 0, "validation_warnings": 0,
    }
    failed_chapters = []       # Track which chapters failed and why
    consecutive_errors = 0     # Abort if API seems persistently down
    MAX_CONSECUTIVE_ERRORS = 3

    for ch in chapters:
        stats = process_chapter(ch, api_key, alias_index, known_faction_ids,
                                dry_run=args.dry_run, force=args.force)

        if stats["status"] == "success":
            total_stats["processed"] += 1
            consecutive_errors = 0  # Reset on success
        elif stats["status"] in ("error", "parse_error"):
            total_stats["errors"] += 1
            failed_chapters.append({"chapter": ch, "reason": stats["status"]})
            consecutive_errors += 1
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                remaining = [c for c in chapters if c > ch]
                if remaining:
                    print(f"\n  ABORT: {MAX_CONSECUTIVE_ERRORS} consecutive errors — "
                          f"API appears down. Skipping {len(remaining)} remaining "
                          f"chapter(s): {remaining[0]}–{remaining[-1]}")
                    for r in remaining:
                        failed_chapters.append({"chapter": r, "reason": "skipped_after_abort"})
                    total_stats["errors"] += len(remaining)
                break
        else:
            total_stats["skipped"] += 1
            consecutive_errors = 0  # Skips (already enriched) don't count

        total_stats["input_tokens"] += stats["input_tokens"]
        total_stats["output_tokens"] += stats["output_tokens"]
        total_stats["cost"] += stats["cost"]
        total_stats["review_flags"] += stats["review_flags"]
        total_stats["validation_warnings"] += stats.get("validation_warnings", 0)

    # --- Summary ---
    print(f"\n{'='*60}")
    print(f"  Processed:     {total_stats['processed']}")
    print(f"  Skipped:       {total_stats['skipped']}")
    print(f"  Errors:        {total_stats['errors']}")
    print(f"  Input tokens:  {total_stats['input_tokens']:,}")
    print(f"  Output tokens: {total_stats['output_tokens']:,}")
    print(f"  Total cost:    ${total_stats['cost']:.3f}")
    print(f"  Review flags:  {total_stats['review_flags']}")
    print(f"  Validation fixes: {total_stats['validation_warnings']}")

    # --- Failed chapters report ---
    if failed_chapters:
        print(f"\n  FAILED CHAPTERS ({len(failed_chapters)}):")
        for fc in failed_chapters:
            print(f"    - chapter {fc['chapter']}: {fc['reason']}")
        print(f"\n  To retry failed chapters, run:")
        failed_ids = [fc["chapter"] for fc in failed_chapters]
        if len(failed_ids) == 1:
            print(f"    python3 tools/extract_from_exchanges_v2.py --chapter {failed_ids[0]}")
        else:
            print(f"    python3 tools/extract_from_exchanges_v2.py --from {failed_ids[0]} --to {failed_ids[-1]}")
    else:
        print(f"\n  All chapters processed successfully!")

    print(f"{'='*60}")

    # Collect review flags after processing
    if total_stats["processed"] > 0 and not args.dry_run:
        collect_review_flags()


if __name__ == "__main__":
    main()
