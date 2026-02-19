#!/usr/bin/env python3
"""
Preprocess Chapter — Cleans raw Claude chat export JSON files for extraction.

Converts exported Claude chat JSON (from Claude Exporter browser extension) into
clean message lists ready for structured data extraction.

Operations:
  1. Parse messages from raw {role: "Prompt"|"Response", time, say} format
  2. Strip "Thought process:" sections from GM responses
  3. Strip tool-use markers (Tool:, View:, Bash Tool:) from GM responses
  4. Filter meta-discussions (greetings, file loading, rule clarifications)
  5. Output clean JSON to tools/preprocessed/chapter_{id}.json

Usage:
  python3 tools/preprocess_chapter.py 1.01              # Single chapter
  python3 tools/preprocess_chapter.py 1.01 1.02 1.03    # Multiple chapters
  python3 tools/preprocess_chapter.py --all              # All chapters
  python3 tools/preprocess_chapter.py --all --book 1     # All Book 1 chapters
  python3 tools/preprocess_chapter.py --all --book 2     # All Book 2 chapters
  python3 tools/preprocess_chapter.py 1.01 --dry-run     # Preview without writing
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_BOOK1 = PROJECT_ROOT / "resources" / "source_material" / "book1"
SOURCE_BOOK2 = PROJECT_ROOT / "resources" / "source_material" / "book2"
OUTPUT_DIR = PROJECT_ROOT / "tools" / "preprocessed"

# Patterns that indicate meta-discussion (not game content)
META_PATTERNS = [
    # Session setup / file loading
    r"(?i)^(hi,?\s*)?(this is chapter|read the project files|can you read)",
    r"(?i)^read (kingdom|npc|character)",
    r"(?i)^provide a short introduction",
    r"(?i)^(gm:|GM:)\s*(remember|note|the meeting|sotomayor is|the timeline|we are in|actually|correction)",
    # Claude Exporter / tool metadata
    r"(?i)^(I'll read|Let me read|I can see|I have access|Yes, I can confirm|I understand completely)",
    r"(?i)^(Files Read|Current Timeline|I'm ready to)",
    r"(?i)^(I need to:|Looking at the context:|So the player|The user is|The user wants|This is)",
]

# Compiled meta patterns for player messages
PLAYER_META_RE = [re.compile(p) for p in META_PATTERNS[:5]]

# Patterns for GM thinking/tool sections (these get stripped from responses)
THINKING_MARKERS = [
    "Thought process:",
    "Tool:",
    "View:",
    "Bash Tool:",
    "Bash tool:",
]


# ---------------------------------------------------------------------------
# Chapter ID ↔ File Path Mapping
# ---------------------------------------------------------------------------

def chapter_id_to_path(chapter_id: str) -> Path:
    """Map chapter ID (e.g., '1.01', '2.15') to raw source file path."""
    parts = chapter_id.split(".")
    book = int(parts[0])
    chapter_num = int(parts[1])

    if book == 1:
        return SOURCE_BOOK1 / f"Claude-Chapter {chapter_num}.json"
    elif book == 2:
        return SOURCE_BOOK2 / f"Claude-Chapter 2.{chapter_num}.json"
    else:
        raise ValueError(f"Unknown book number: {book}")


def discover_all_chapters(book_filter: int = None) -> list[str]:
    """Discover all available chapter IDs from source directories."""
    chapters = []

    if book_filter is None or book_filter == 1:
        for f in sorted(SOURCE_BOOK1.glob("Claude-Chapter *.json")):
            match = re.search(r"Claude-Chapter (\d+)\.json", f.name)
            if match:
                num = int(match.group(1))
                chapters.append(f"1.{num:02d}")

    if book_filter is None or book_filter == 2:
        for f in sorted(SOURCE_BOOK2.glob("Claude-Chapter 2.*.json")):
            match = re.search(r"Claude-Chapter 2\.(\d+)\.json", f.name)
            if match:
                num = int(match.group(1))
                chapters.append(f"2.{num:02d}")

    # Sort by book then chapter number
    chapters.sort(key=lambda c: (int(c.split(".")[0]), int(c.split(".")[1])))
    return chapters


# ---------------------------------------------------------------------------
# Text Cleaning
# ---------------------------------------------------------------------------

def strip_thinking_and_tools(text: str) -> str:
    """Remove Thought process:, Tool:, View:, Bash Tool: sections from GM text.

    Strategy: Split text into paragraphs (by double newline). Remove paragraphs
    that start with any thinking/tool marker. Keep the rest as narrative.
    """
    # Split into paragraphs
    paragraphs = re.split(r"\n\n+", text)

    clean_paragraphs = []
    skip_until_next = False

    for para in paragraphs:
        stripped = para.strip()
        if not stripped:
            continue

        # Check if this paragraph starts with a thinking/tool marker
        is_meta = False
        for marker in THINKING_MARKERS:
            if stripped.startswith(marker):
                is_meta = True
                break

        # Also catch continuation lines that are clearly part of thinking
        # (numbered lists in thinking, "I should:", "Let me:", etc.)
        if not is_meta and skip_until_next:
            # Check if this looks like continuation of thinking/analysis
            thinking_continuations = [
                r"^(I should|I need to|Let me|So |The user|This is a|Looking at)",
                r"^(From |Based on|However,? (the|I|it|this)|Key |Now I|Now let me)",
                r"^(Good,|Excellent|The key|I'm |So the|From Chapter|From the)",
                r"^(The player|According|I can see|I have|So actually|I'll)",
                r"^(This gives|The seal|However, Juan|Making|Tracking|I can)",
                r"^(The timeline|Juan is currently|The chronology|The precise)",
                r"^(I'm focusing|I'm tracking|Padilla appears)",
                r"^(The upload|The allowed|Let me check|The user said)",
                r"^(This is helpful|Now I have a complete|Let me also)",
            ]
            is_continuation = False
            for pattern in thinking_continuations:
                if re.match(pattern, stripped):
                    is_continuation = True
                    break
            # Short numbered lists in thinking
            if not is_continuation and re.match(r"^\d+\.\s", stripped) and len(stripped) < 200:
                is_continuation = True
            # Short lines that are clearly meta (under 60 chars, no narrative markers)
            if not is_continuation and len(stripped) < 60 and re.match(r"^[A-Z]", stripped):
                # Could be a header or transition — keep if it looks like narrative
                if not re.match(r"^(The |A |An |You |Your |In |On |At |By |For |With |When )", stripped):
                    is_continuation = True

            if is_continuation:
                is_meta = True
            else:
                skip_until_next = False

        if is_meta:
            skip_until_next = True
            continue

        skip_until_next = False
        clean_paragraphs.append(para)

    result = "\n\n".join(clean_paragraphs).strip()
    return result


def is_meta_discussion(text: str, role: str) -> bool:
    """Check if a message is meta-discussion rather than game content."""
    stripped = text.strip()

    # Empty messages
    if not stripped:
        return True

    if role == "Prompt":
        # Player meta: session setup, file loading requests
        for pattern in PLAYER_META_RE:
            if pattern.search(stripped):
                # But don't filter if it also contains game content
                # (e.g., "Hi, This is chapter 2.30. [...] I send for the masters...")
                # Check if there's substantial game content after the meta part
                lines = stripped.split("\n")
                game_lines = [l for l in lines if l.strip() and not any(p.search(l.strip()) for p in PLAYER_META_RE)]
                if not game_lines:
                    return True
                # Has game content mixed in — keep it but note the meta portion
                return False
        return False

    elif role == "Response":
        # GM meta: pure file reading/confirmation responses
        # These are responses that are entirely about reading files, confirming setup, etc.
        # with no narrative content at all
        cleaned = strip_thinking_and_tools(stripped)
        if not cleaned:
            return True

        # Check if the cleaned content is just meta-responses
        meta_only_patterns = [
            r"(?i)^(Yes,? I('ve| have| can)|I'll read|Let me read|I can confirm|I understand|Good, I)",
            r"(?i)^(Files Read:|Current Timeline:|I'm ready to|One question before)",
            r"(?i)^(I have access to all|All seven files|Now I have)",
        ]
        for p in meta_only_patterns:
            if re.match(p, cleaned):
                return True

        return False

    return False


def extract_game_content_from_prompt(text: str) -> str:
    """For player messages that mix meta + game content, extract just the game part."""
    lines = text.strip().split("\n")
    game_lines = []
    skip_meta_block = False

    for line in lines:
        stripped_line = line.strip()

        # Check if this line is meta
        is_meta = False
        for pattern in PLAYER_META_RE:
            if pattern.search(stripped_line):
                is_meta = True
                break

        # Also skip NPC rules blocks and similar meta instructions
        if re.match(r"(?i)^(NPC RULES:|NPC guide|Read kingdom|Provide a short|Dont advance)", stripped_line):
            is_meta = True

        if is_meta:
            skip_meta_block = True
            continue

        # Empty lines after meta blocks
        if skip_meta_block and not stripped_line:
            continue

        skip_meta_block = False
        game_lines.append(line)

    return "\n".join(game_lines).strip()


# ---------------------------------------------------------------------------
# Main Preprocessing
# ---------------------------------------------------------------------------

def preprocess_chapter(chapter_id: str) -> dict:
    """Preprocess a single chapter, returning clean message list."""
    filepath = chapter_id_to_path(chapter_id)

    if not filepath.exists():
        raise FileNotFoundError(f"Chapter file not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        raw = json.load(f)

    metadata = raw.get("metadata", {})
    messages = raw.get("messages", [])

    clean_messages = []
    skipped_count = 0
    msg_index = 0

    for msg in messages:
        role = msg.get("role", "")
        text = msg.get("say", "")
        time_str = msg.get("time", "")

        # Skip entirely meta messages
        if is_meta_discussion(text, role):
            skipped_count += 1
            continue

        # Clean the text
        if role == "Response":
            cleaned_text = strip_thinking_and_tools(text)
            if not cleaned_text.strip():
                skipped_count += 1
                continue
            output_role = "gm"
        elif role == "Prompt":
            cleaned_text = extract_game_content_from_prompt(text)
            if not cleaned_text.strip():
                skipped_count += 1
                continue
            output_role = "player"
        else:
            skipped_count += 1
            continue

        msg_index += 1
        clean_messages.append({
            "index": msg_index,
            "role": output_role,
            "text": cleaned_text,
            "time": time_str,
        })

    result = {
        "chapter": chapter_id,
        "book": int(chapter_id.split(".")[0]),
        "source_file": filepath.name,
        "source_title": metadata.get("title", ""),
        "source_dates": metadata.get("dates", {}),
        "total_raw_messages": len(messages),
        "total_clean_messages": len(clean_messages),
        "skipped_messages": skipped_count,
        "messages": clean_messages,
    }

    return result


def save_preprocessed(chapter_id: str, data: dict) -> Path:
    """Save preprocessed chapter to output directory."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    outpath = OUTPUT_DIR / f"chapter_{chapter_id}_preprocessed.json"

    with open(outpath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return outpath


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Preprocess raw chapter JSON files")
    parser.add_argument("chapters", nargs="*", help="Chapter IDs to process (e.g., 1.01 2.15)")
    parser.add_argument("--all", action="store_true", help="Process all available chapters")
    parser.add_argument("--book", type=int, choices=[1, 2], help="Filter by book (with --all)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    args = parser.parse_args()

    if args.all:
        chapter_ids = discover_all_chapters(args.book)
    elif args.chapters:
        chapter_ids = args.chapters
    else:
        parser.print_help()
        sys.exit(1)

    if not chapter_ids:
        print("No chapters found.")
        sys.exit(1)

    print(f"Preprocessing {len(chapter_ids)} chapter(s)...\n")

    total_raw = 0
    total_clean = 0
    total_skipped = 0

    for chapter_id in chapter_ids:
        try:
            data = preprocess_chapter(chapter_id)
            total_raw += data["total_raw_messages"]
            total_clean += data["total_clean_messages"]
            total_skipped += data["skipped_messages"]

            status = f"  {chapter_id}: {data['total_raw_messages']} raw → {data['total_clean_messages']} clean ({data['skipped_messages']} skipped)"

            if args.dry_run:
                print(status)
                # Show first 2 messages as preview
                for msg in data["messages"][:2]:
                    preview = msg["text"][:120].replace("\n", " ")
                    print(f"    [{msg['role']}] {preview}...")
            else:
                outpath = save_preprocessed(chapter_id, data)
                print(f"{status} → {outpath.name}")

        except FileNotFoundError as e:
            print(f"  {chapter_id}: ERROR - {e}")
        except Exception as e:
            print(f"  {chapter_id}: ERROR - {type(e).__name__}: {e}")

    print(f"\nTotal: {total_raw} raw → {total_clean} clean ({total_skipped} skipped)")


if __name__ == "__main__":
    main()
