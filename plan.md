# Castile 1430 — Development Plan

## What's Done (Phase 1: MVP Core Loop)

The core gameplay loop is fully functional. A player can create a campaign, send actions to Claude, receive narrated responses with metadata, and have the full game state persist across sessions.

### Completed Systems

| System | Files | Status |
|--------|-------|--------|
| **API Integration** | `api_client.gd` | Claude API with retry logic (3 attempts, exponential backoff), prompt caching headers, model selection |
| **Prompt Assembly** | `prompt_assembler.gd` + `resources/gm_prompts/` | 3-layer cached prompt system: L1 GM Guidelines, L2 call-type templates (narrative, persuasion, chaos, chapter_start, year_end), L3 dynamic scene context |
| **Game State** | `game_state_manager.gd` | Tracks date, location, chapter, scene_characters, roll state, running_summary, call_type. Full save/load. Emits signals on all changes |
| **Conversation Buffer** | `conversation_buffer.gd` | 8-exchange rolling window, auto-archives by date, provides API message formatting |
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
- `layer2_chapter_start.txt` — Scene setting procedure, situation briefing, momentum
- `layer2_year_end.txt` — Treasury presentation, economic decisions
- `metadata_format.txt` — Reference: all JSON metadata fields and event types

### Data Files (created at campaign start, all empty/default)

`characters.json`, `factions.json`, `events.json`, `laws.json`, `timeline.json`, `roll_history.json`, `economy.json`, `game_state.json`, plus auto-created `conversations/` and `chapter_summaries/` directories.

---

## What's Next

### Phase 2: Data Population — Characters, Events, and Conversations

**Priority: HIGH** — The game starts with empty data files. Claude has to invent everyone from scratch, and the scene context (Layer 3) has no character data to pull from. This makes early gameplay thin and disconnected from the ~70 sessions of existing story.

**Goal:** Populate the game's data files from existing sources — CHARACTER_DATABASE.md, historical events, and the ~70 chat sessions that form the story so far. This gives the game engine a rich foundation to work from.

#### 2A: Character Database

Build `resources/data/characters.json` from chapter data using `tools/build_characters.py`.

The script reads all `chapter_02_*.json` files, extracts characters from encounter participant lists, canonicalises them via a curated alias map (270+ characters), and outputs the full character schema defined in CONVENTIONS.md Section 2.

**Schema** (see CONVENTIONS.md for full field reference):

```json
{
  "id": "lucia_deste",
  "name": "Queen Lucia d'Este",
  "aliases": ["lucia", "lucia_d_este", "lucia_deste", ...],
  "title": "",
  "born": "0000-00-00",
  "status": ["active"],
  "category": ["royal_family", "italian"],
  "location": "Toledo, Alcázar",
  "current_task": "",
  "personality": [],
  "interests": [],
  "red_lines": [],
  "speech_style": "",
  "event_refs": ["evt_1433_00296", "evt_1433_00304", ...]
}
```

**Auto-populated fields:** `id`, `name`, `aliases`, `category`, `status` (defaults to active), `location` (from latest chapter appearance), `event_refs` (all events the character appears in).

**Fields requiring manual curation:** `title`, `born`, `personality`, `interests`, `red_lines`, `speech_style`, `current_task`. These can be populated from CHARACTER_DATABASE.md in a later pass — empty fields do not block the app.

**Tasks:**
- [x] Build `characters.json` from chapter data via `tools/build_characters.py --write`
- [ ] Enrich characters with data from CHARACTER_DATABASE.md (title, born, personality, etc.)
- [ ] Modify `game_state_manager.gd` → `initialize_new_campaign()` to load characters
- [ ] Verify characters appear in Layer 3 scene context via the debug panel

#### 2B: Starter Events Database

Populate `resources/data/starter_events.json` with key historical events from CHARACTER_DATABASE.md and chat history. These provide context for Claude and give the timeline viewer (Phase 7) something to display from the start.

**Tasks:**
- [ ] Define event schema (extend current `events.json` format if needed)
- [ ] Extract key events from CHARACTER_DATABASE.md (battles, treaties, deaths, marriages, etc.)
- [ ] Create `resources/data/starter_events.json`
- [ ] Wire `event_refs` in character entries to point to relevant starter events
- [ ] Modify campaign initialization to load starter events

#### 2C: Conversation Archive Import

There are ~70 existing chat sessions containing the story, decisions, and events that have shaped the simulation. These need to be imported into the game's conversation archive so the engine can reference prior exchanges.

**Tasks:**
- [ ] Determine export method for existing chat sessions (see notes below)
- [ ] Define import format — map exported chats into the game's `conversations/{YYYY-MM-DD}.json` structure
- [ ] Build or script the import pipeline
- [ ] Extract events and character updates from imported conversations (stretch goal)

**Notes on chat export:** Exporting project conversations from Claude.ai is not natively supported with a one-click export. Options:
1. **Manual copy-paste** — tedious but reliable for smaller batches
2. **Browser DevTools** — inspect network requests in Claude.ai; conversation data is fetched as JSON from the API. Copy from the Network tab
3. **Claude.ai API** — if using the API directly (not the web UI), conversations are already in your control as API request/response logs
4. **Third-party tools** — browser extensions or scripts that scrape the Claude.ai UI (check terms of service)

Recommended approach: prioritize the character and event databases first (2A, 2B). Conversation import (2C) can follow once the core data is in place.

---

### Phase 3: Characters & Laws Review Panels

**Priority: HIGH** — The player needs to see who exists in the game world and what laws are in effect, without having to ask Claude "who is at court?"

#### 3A: Characters Panel

A side panel or overlay (toggled by a header button) that displays all known characters from `characters.json`.

**Requirements:**
- [ ] Add "Characters" button to header bar (between Debug and Settings)
- [ ] Create `characters_panel.gd` — overlay listing all characters
- [ ] Each character entry: name, title, location, personality summary
- [ ] Clicking a character expands to show full details (interests, red lines, speech style, recent events)
- [ ] Characters should be grouped or filterable by location (at court vs. elsewhere)
- [ ] Read-only — data is updated by Claude's metadata, not the player

#### 3B: Laws Panel

A side panel or overlay showing active laws/decrees from `laws.json`.

**Requirements:**
- [ ] Add "Laws" button to header bar
- [ ] Create `laws_panel.gd` — overlay listing all enacted laws
- [ ] Each law entry: title, date enacted, summary, status (active/repealed)
- [ ] Laws are added by Claude via metadata events of type `law_enacted` / `law_repealed`
- [ ] Need to extend `game_state_manager.gd` → `update_from_metadata()` to detect law events and write to `laws.json`

#### Law schema:

```json
{
  "law_id": "law_001",
  "title": "Edict of Valladolid",
  "date_enacted": "1430-03-15",
  "summary": "Restricts noble retinues to 50 armed men within city walls",
  "proposed_by": "alvaro_de_luna",
  "status": "active",
  "tags": ["military", "nobility"]
}
```

---

### Phase 4: Character Updates from Claude

**Priority: MEDIUM** — Currently Claude returns `scene_characters` as a list of IDs, but doesn't update character data (location changes, new personality traits discovered, etc.). The character database grows stale.

#### Tasks:
- [ ] Extend metadata format to include a `character_updates` field:
  ```json
  "character_updates": [
    {"id": "alvaro_de_luna", "location": "Segovia", "current_task": "Raising troops"}
  ]
  ```
- [ ] Update `metadata_format.txt` to document the new field
- [ ] Add `layer1_gm_guidelines.txt` instruction telling Claude to emit character_updates when NPCs change location, task, or attitude
- [ ] Extend `game_state_manager.gd` to apply character_updates to `characters.json`
- [ ] Extend `response_parser.gd` EMPTY_METADATA to include the new field

---

### Phase 5: Battle Template

**Priority: MEDIUM** — `MAX_TOKENS` has a `"battle": 800` entry but there's no `layer2_battle.txt` template.

#### Tasks:
- [ ] Create `resources/gm_prompts/layer2_battle.txt` — rules for narrating battles, siege mechanics, troop morale, commander decisions, casualty reporting
- [ ] Add `"battle"` key to `_layer2_templates` loading in `prompt_assembler.gd` (it will auto-load if the file exists, just needs the mapping in `template_files`)
- [ ] Define when `current_call_type` switches to `"battle"` (manual trigger? Claude metadata?)

---

### Phase 6: Economy Dashboard

**Priority: LOW** — The `economy.json` structure exists and the year_end prompt tells Claude to present treasury data, but there's no UI to review it mid-game.

#### Tasks:
- [ ] Add "Treasury" button to header bar or settings
- [ ] Create `economy_panel.gd` — displays current treasury balance, revenue/expense breakdown by category
- [ ] Show year-over-year comparison if multiple years exist
- [ ] Read-only — updated by year_end call type responses

---

### Phase 7: Timeline & Events Viewer

**Priority: LOW** — Events are logged to `events.json` with full metadata but there's no way to browse them.

#### Tasks:
- [ ] Create `events_panel.gd` — chronological list of all logged events
- [ ] Filter by: type, character, chapter, date range
- [ ] Each event shows: date, type icon/tag, summary, characters involved
- [ ] Optionally link to conversation exchange where the event occurred

---

### Phase 8: Chapter Management

**Priority: LOW** — `advance_chapter()` exists but there's no UI trigger for it. Chapter summaries are saved but not viewable.

#### Tasks:
- [ ] Add "End Chapter" button or command (in settings or header)
- [ ] Show chapter summary before advancing
- [ ] Create chapter review panel to browse past chapter summaries
- [ ] Consider auto-triggering chapter_start prompt after advancing

---

### Phase 9: Visual Polish

**Priority: LOW** — All UI is functional but uses Godot defaults. The resources/fonts, icons, and themes directories are empty.

#### Tasks:
- [ ] Add a medieval/period-appropriate font (e.g., IM Fell or similar)
- [ ] Create a Godot theme resource matching the dark color scheme used in code
- [ ] Add icons for header bar buttons (scroll icon for characters, gavel for laws, etc.)
- [ ] Character portraits system (the `portraits/` directory and `dialogue` metadata field exist but aren't used)
- [ ] Improve chat panel formatting — indentation for NPC speech, visual separation between exchanges

---

## Architecture Notes for Future Sessions

### Signal flow
```
ChatPanel.message_submitted → Main._on_player_message()
  → PromptAssembler.assemble_prompt() → ApiClient.send_message()
    → ApiClient.response_received → Main._on_api_response()
      → ChatPanel.append_narrative()
      → GameStateManager.update_from_metadata()
      → ConversationBuffer.add_exchange()
```

### Adding a new header button + panel
1. Add `Button` node in `main.tscn` under `Layout/HeaderBar/MarginContainer/HBoxContainer`
2. Add `@onready var` + signal in `header_bar.gd`
3. Add overlay `PanelContainer` node in `main.tscn` under root (sibling of SettingsScreen, DebugPanel)
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
