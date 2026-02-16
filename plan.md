# Castile 1430 — Development Plan

## What's Done (Phase 1: MVP Core Loop)

The core gameplay loop is fully functional. A player can create a campaign, send actions to Claude, receive narrated responses with metadata, and have the full game state persist across sessions.

### Completed Systems

| System | Files | Status |
|--------|-------|--------|
| **API Integration** | `api_client.gd` | Claude API with retry logic (3 attempts, exponential backoff), prompt caching headers, model selection |
| **Prompt Assembly** | `prompt_assembler.gd` + `resources/gm_prompts/` | 3-layer cached prompt system: L1 GM Guidelines, L2 call-type templates (narrative, persuasion, chaos, year_end), L3 dynamic scene context |
| **Game State** | `game_state_manager.gd` | Tracks date, location, scene_characters, roll state, call_type. Full save/load. Emits signals on all changes |
| **Conversation Buffer** | `conversation_buffer.gd` | 8-exchange rolling window, provides API message formatting |
| **Response Parser** | `response_parser.gd` | Extracts narrative + JSON metadata block from Claude responses. Handles malformed JSON gracefully |
| **Data Persistence** | `data_manager.gd` | JSON I/O for all data files, campaign directory management, config storage |
| **d100 Roll System** | `roll_engine.gd` | Validates 1-100 input, logs to roll_history.json, state transitions (awaiting_roll → roll_result) |
| **Chat UI** | `chat_panel.gd` + `chat_panel.tscn` | Narrative display (BBCode RichTextLabel), player input, roll input (conditional), thinking indicator |
| **Header Bar** | `header_bar.gd` | Location, formatted date, characters present, Debug and Settings buttons |
| **Settings Screen** | `settings_screen.gd` + inline in `main.tscn` | API key (masked), model dropdown, campaign create/load, start date |
| **Debug Panel** | `debug_panel.gd` | F12 overlay showing full prompt in collapsible sections: Config, L1, L2, L3, Messages. Token estimate |
| **Main Controller** | `main.gd` | Wires all dependencies, routes signals, handles keyboard shortcuts (Escape, F12, Ctrl+S) |

### Prompt Templates (all populated)

- `layer1_gm_guidelines.txt` — 5 core rules (NPC autonomy, response discipline, player agency, historical authenticity, d100 system) + response format
- `layer2_medieval_norms.txt` — Political structure, social hierarchy, forms of address, honor culture, religion, warfare, economy
- `layer2_persuasion.txt` — When to roll, table format, modifiers, narration rules
- `layer2_chaos.txt` — Triggers, table format, grounded outcomes
- `layer2_year_end.txt` — Treasury presentation, economic decisions
- `metadata_format.txt` — Reference: all JSON metadata fields and event types

### Data Files (created at campaign start)

`characters.json`, `factions.json`, `events.json`, `laws.json`, `timeline.json`, `roll_history.json`, `economy.json`, `game_state.json`

---

## CURRENT PRIORITY: Unify Events & Conversations, Remove Chapters

### Problem Summary

The current system has two parallel record-keeping systems that should be one:
- **events.json**: Permanent, but incomplete (Claude decides what to log), no full text
- **conversations/[date].json**: Has full text, but dies on date change, date-scoped

Additionally, the chapter system is legacy — it was a workaround for context window
limits that the database + reflection system makes unnecessary.

The result: Claude has amnesia across in-game days, the event log has gaps,
and chapter_start instructions appear when just continuing a game.

---

### Phase A: Unify Events and Conversations

#### A1. Expand the event schema

Add `player_input` and `gm_response` fields to events. Every exchange automatically
creates an event entry. The existing fields (type, summary, characters, location, tags)
remain for searchability in the reflection index.

**New exchange event schema:**
```json
{
  "event_id": "evt_1435_00123",
  "date": "1435-06-12",
  "type": "conversation",
  "summary": "Juan discussed trade negotiations with the Venetian ambassador",
  "characters": ["juan_ii", "venetian_ambassador"],
  "location": "Valladolid, Throne Room",
  "tags": [],
  "status": "resolved",
  "player_input": "I ask the ambassador about Venice's terms for the trade route",
  "gm_response": "The ambassador bows deeply, his silk robes rustling..."
}
```

Existing starter events (500+ from chapters 2-28) keep their current fields
(`chapter`, `sub_chapter`, etc.) as legacy data. They have no `player_input`
or `gm_response` — that's fine, they're historical records from before the
live simulation started.

**Files changed:**
- `game_state_manager.gd` — new method `log_exchange()` to always log exchanges
- `response_parser.gd` — remove `events` from EMPTY_METADATA (Claude no longer
  curates events; every response is auto-logged)

#### A2. Replace ConversationBuffer with events.json reads

Instead of loading from `conversations/[date].json`, load the last 8 exchanges
directly from events.json by filtering for entries that have `player_input` set.

**Files changed:**
- `conversation_buffer.gd` — rewrite to read from events.json:
  - `initialize()` loads last 8 exchanges with `player_input` from events.json
  - `add_exchange()` becomes a no-op (logging moves to game_state_manager)
  - `get_api_messages()` reads from the loaded exchanges
  - Remove `_save_current_conversation()` and all date-scoping logic
  - Remove `_current_chapter` entirely
- `data_manager.gd` — remove `save_conversation()`, `load_conversation()`,
  `list_conversation_dates()`, `save_chapter_summary()`, `load_chapter_summary()`
- `main.gd` — simplify conversation_buffer initialization (no date/chapter params),
  remove `set_scene_context()` calls, move exchange logging to game_state_manager

#### A3. Auto-log every exchange

Move logging from "Claude decides" to "always happens." After every GM response:
1. `game_state_manager.log_exchange()` creates an event with full text + metadata
2. Claude still returns `summary_update` and `scene_characters` in its metadata
   (needed for the compact reflection index and scene tracking)
3. The `events` array in Claude's response metadata is removed — Claude no longer
   decides what counts as an event

**Claude's new metadata contract:**
```json
{
  "scene_characters": ["char_id1", "char_id2"],
  "location": "City, Place",
  "date": "YYYY-MM-DD",
  "awaiting_roll": false,
  "roll_type": null,
  "summary_update": "One-line summary of this exchange (REQUIRED)",
  "dialogue": [{"speaker": "char_id", "type": "speech"}],
  "juan_acted": false,
  "confidence": 0.0-1.0,
  "missing_context": [...]
}
```

Note: `summary_update` becomes mandatory — it's the one-liner that populates the
compact reflection index. Without it, the reflection system has nothing to show
for this exchange.

**Files changed:**
- `game_state_manager.gd` — new `log_exchange(player_input, gm_response, metadata)`
- `main.gd` — call `log_exchange()` in `_on_api_response()`
- `response_parser.gd` — remove `events` from EMPTY_METADATA
- All GM prompt templates — update metadata format to remove `events` array,
  make `summary_update` required
- `metadata_format.txt` — update reference doc

---

### Phase B: Remove Chapter System

#### B1. Remove chapter tracking

- Remove `current_chapter`, `chapter_title` from GameStateManager
- Remove `advance_chapter()` method
- Remove `chapter_changed` signal
- Remove `chapter` field from new event entries (keep in legacy starter events)
- Remove chapter from `game_state.json` save format

#### B2. Remove chapter_start call type

- Remove `"chapter_start"` from call types
- Stop loading `layer2_chapter_start.txt` template
- Remove `"chapter_start"` from `SKIP_REFLECTION_TYPES` in prompt_retry_manager
- On campaign load, default `current_call_type` to `"narrative"`

#### B3. Handle running_summary

**QUESTION FOR USER**: Without chapters, `running_summary` grows unbounded (it was
cleared on chapter advance). Options:
- **A) Remove entirely** — rely on reflection system + last 8 exchanges for context
- **B) Keep but auto-truncate** — cap at ~500 words, oldest lines dropped
- **C) Replace with periodic compression** — every N exchanges, compress the summary

**Files changed:**
- `game_state_manager.gd` — remove chapter vars, signals, advance_chapter()
- `prompt_assembler.gd` — remove "Chapter N: Title" from scene context,
  remove/modify "CHAPTER SUMMARY SO FAR" section
- `prompt_retry_manager.gd` — remove "chapter_start" from SKIP_REFLECTION_TYPES
- `conversation_buffer.gd` — remove _current_chapter references
- `main.gd` — remove chapter references from initialization and display
- `debug_panel.gd` — remove chapter display

---

### Phase C: Fix Date & Location Derivation

#### C1. Derive state from last event on load

When loading a campaign, derive current_date and current_location from the last
event in events.json instead of relying on game_state.json:

```gdscript
func _derive_state_from_events() -> void:
    var events_data = data_manager.load_json("events.json")
    if events_data and not events_data["events"].is_empty():
        var last = events_data["events"].back()
        current_date = last.get("date", current_date)
        current_location = last.get("location", current_location)
```

#### C2. Remove campaign start date hardcoding

- `initialize_new_campaign()` — check starter_events.json for last event date
- The "brand new simulation from scratch" edge case is out of scope

**Files changed:**
- `game_state_manager.gd` — add `_derive_state_from_events()`, call on load
- `main.gd` — simplify campaign loading

---

### Phase D: Fix call_type Persistence

#### D1. Default to "narrative" on load

When loading a saved game, force `current_call_type = "narrative"` unless actively
awaiting a roll result:

```gdscript
if current_call_type in ["chapter_start"]:
    current_call_type = "narrative"
if not awaiting_roll and current_call_type == "roll_result":
    current_call_type = "narrative"
```

**Remaining valid call types:** narrative, persuasion, chaos, roll_result, year_end, battle

**Files changed:**
- `game_state_manager.gd` — sanitize call_type on load

---

### Phase E: Add Character Index to Reflection

#### E1. Include compact character index in reflection prompt

Add a character index alongside the event index so Claude can request character
data proactively:

```
═══ CHARACTER INDEX ═══
[alvaro_de_luna] Álvaro de Luna | Condestable de Castilla | Valladolid
[bishop_toledo] Gutierre de Toledo | Bishop of Toledo | Toledo
```

#### E2. Update reflection response format

Allow Claude to return both event IDs and character IDs:

```json
{
  "event_ids": ["evt_1433_00012"],
  "character_ids": ["alvaro_de_luna"]
}
```

The retry manager already handles `{"event_ids": [...]}`. Extend to also process
`character_ids` and inject those characters into enrichment text.

**Files changed:**
- `layer0_reflection.txt` — add character index section, update response format
- `prompt_assembler.gd` — build character index text, inject into reflection prompt
- `prompt_retry_manager.gd` — parse character_ids from reflection, fetch character data

---

### Phase F: Update GM Prompt Templates

- Remove `events` array from metadata instructions in all templates
- Make `summary_update` explicitly required
- Remove chapter references from all templates
- Rename "CHAPTER SUMMARY SO FAR" to "STORY SO FAR" (if keeping running_summary)

**Files changed:**
- `layer1_gm_guidelines.txt`
- `layer2_medieval_norms.txt`
- `layer2_persuasion.txt`
- `layer2_chaos.txt`
- `layer2_year_end.txt`
- `metadata_format.txt`
- `prompt_assembler.gd`

---

### Execution Order

1. **Phase D** (fix call_type) — smallest, prevents chapter_start on resume
2. **Phase C** (date derivation) — small, ensures correct date on load
3. **Phase B** (remove chapters) — medium, cleans up state
4. **Phase A** (unify events+conversations) — largest, core architecture
5. **Phase E** (character index in reflection) — builds on unified system
6. **Phase F** (update templates) — final polish

---

### Open Questions for User

1. **Running summary** — remove, truncate, or compress? (Phase B3)
2. **gm_response stored in events** — narrative text only, or include the raw JSON
   metadata block too? (Recommend: narrative only; metadata is stored in event fields)
3. **ConversationBuffer class** — fully delete the class, or repurpose as thin reader
   over events.json? (Recommend: repurpose to keep interface stable for prompt_assembler
   and debug_panel)

---

## Future Work

### Characters & Laws Review Panels

**Priority: HIGH** — The player needs to see who exists in the game world and what laws are in effect.

- Characters panel: side overlay listing all characters, grouped by location
- Laws panel: side overlay showing active laws/decrees
- See CONVENTIONS.md for full schemas

### Character Updates from Claude

**Priority: MEDIUM** — Extend metadata to include `character_updates` so Claude can
update character location, task, personality as the story progresses.

### Battle Template

**Priority: MEDIUM** — `MAX_TOKENS` has `"battle": 800` but no `layer2_battle.txt`.

### Economy Dashboard

**Priority: LOW** — UI for reviewing treasury data mid-game.

### Timeline & Events Viewer

**Priority: LOW** — Chronological browser for all logged events with filtering.

### Visual Polish

**Priority: LOW** — Medieval fonts, icons, themes, character portraits.

---

## Architecture Notes

### Signal flow
```
ChatPanel.message_submitted → Main._on_player_message()
  → PromptRetryManager.handle_player_input()
    → PromptAssembler.assemble_reflection_prompt() → ApiClient.send_raw_message()
      → ApiClient.raw_response_received → RetryManager._on_raw_response()
        → PromptAssembler.assemble_prompt() / assemble_enriched_prompt()
          → ApiClient.send_message()
            → ApiClient.response_received → RetryManager._on_gm_response()
              → Main._on_api_response()
                → ChatPanel.append_narrative()
                → GameStateManager.update_from_metadata()
                → GameStateManager.log_exchange()
```

### Adding a new header button + panel
1. Add `Button` node in `main.tscn` under `Layout/HeaderBar/MarginContainer/HBoxContainer`
2. Add `@onready var` + signal in `header_bar.gd`
3. Add overlay `PanelContainer` node in `main.tscn` under root
4. Create script, add ext_resource to scene, wire in `main.gd`

### Adding a new metadata field
1. Add to `metadata_format.txt`
2. Add to `response_parser.gd` EMPTY_METADATA
3. Handle in `game_state_manager.gd` → `update_from_metadata()`
4. Instruct Claude in `layer1_gm_guidelines.txt`

### Key directories
- Scripts: `scripts/`
- Scenes: `scenes/`
- Prompt templates: `resources/gm_prompts/`
- Game data (runtime): `user://save_data/[campaign]/`
- App config: `user://config.json`
