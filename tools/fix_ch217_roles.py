#!/usr/bin/env python3
"""
Fix role-swapped exchanges in chapter_2.17.json.

Several events in this chapter have player/gm roles inverted:
- "player" role contains GM output (starting with "Thought process:...")
- "gm" role contains actual player input

This script also removes pure web search URL block exchanges.

Usage:
    python3 tools/fix_ch217_roles.py report   # Show what would change
    python3 tools/fix_ch217_roles.py apply     # Apply changes
"""

import json
import re
import sys
from pathlib import Path

CH217 = Path(__file__).parent.parent / "resources" / "data" / "events" / "chapter_2.17.json"


def is_web_search_only(text):
    """Return True if the exchange text is entirely web search results."""
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    if not lines:
        return False
    url_lines = sum(
        1 for line in lines
        if re.search(r"\b\w+\.(?:org|com|net|edu|info|io)\s*$", line)
    )
    # At least 3 URL lines and > 50% are URLs
    return url_lines >= 3 and url_lines >= len(lines) * 0.5


def process(mode="report"):
    with open(CH217, encoding="utf-8") as f:
        data = json.load(f)

    swaps = 0
    removals = 0

    for event in data.get("events", []):
        exchanges = event.get("exchanges", [])
        indices_to_remove = []

        for i, ex in enumerate(exchanges):
            text = ex.get("text", "")

            # Detect GM output misattributed as "player"
            if ex.get("role") == "player" and text.lstrip().startswith("Thought process:"):
                if mode == "report":
                    print(f"\nSWAP player→gm: event={event.get('event_id')}, exchange {i}")
                    print(f"  Text starts: {text[:80]}...")
                ex["role"] = "gm"
                swaps += 1

                # The next exchange should be player input misattributed as "gm"
                if i + 1 < len(exchanges) and exchanges[i + 1].get("role") == "gm":
                    next_text = exchanges[i + 1].get("text", "")
                    if mode == "report":
                        print(f"  SWAP gm→player: exchange {i+1}")
                        print(f"  Text: {next_text[:80]}...")
                    exchanges[i + 1]["role"] = "player"
                    swaps += 1

            # Detect pure web search URL blocks
            if ex.get("role") == "gm" and is_web_search_only(text):
                if mode == "report":
                    print(f"\nREMOVE web search block: event={event.get('event_id')}, exchange {i}")
                    lines = text.strip().split("\n")
                    print(f"  Lines: {len(lines)}, first: {lines[0][:60]}...")
                indices_to_remove.append(i)
                removals += 1

        # Also check for the last event where roles are inverted starting from "gm"
        # Pattern: role="gm" but text is clearly player input, followed by
        # role="player" with "Thought process:" (already handled above)
        # We need to also catch the FIRST exchange when it starts with "gm" but is player
        for i, ex in enumerate(exchanges):
            text = ex.get("text", "")
            # If this is "gm" and the NEXT exchange is "gm" (after our swap),
            # and this text looks like player input, swap it to player
            if (ex.get("role") == "gm" and i + 1 < len(exchanges)
                    and exchanges[i + 1].get("role") == "gm"):
                # Exclude GM thinking text (references "the user"/"they want me",
                # or contains "Let me search/think" self-talk)
                gm_indicators = (
                    "the user" in text.lower()
                    or "they want me" in text.lower()
                    or "they also want" in text.lower()
                    or "Let me search" in text
                    or "Let me think" in text
                    or "Let me look" in text
                    or text.lstrip().startswith("Thought process:")
                )
                # Short text without GM self-talk indicators = likely player
                if len(text) < 500 and not gm_indicators:
                    if mode == "report":
                        print(f"\nSWAP gm→player (unpaired): event={event.get('event_id')}, exchange {i}")
                        print(f"  Text: {text[:80]}...")
                    ex["role"] = "player"
                    swaps += 1

        # Remove web search blocks (in reverse order to preserve indices)
        for idx in reversed(indices_to_remove):
            exchanges.pop(idx)

    print(f"\n{'='*50}")
    print(f"Role swaps: {swaps}")
    print(f"Exchanges removed: {removals}")

    if mode == "apply":
        with open(CH217, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("Changes applied.")
    else:
        print("Dry run — no changes made. Run with 'apply' to apply.")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "report"
    if mode not in ("report", "apply"):
        print(f"Usage: {sys.argv[0]} [report|apply]")
        sys.exit(1)
    process(mode)
