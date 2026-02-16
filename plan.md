# Castile 1430 — Development Plan

## What's Done (Phase 1: MVP Core Loop)

The core gameplay loop is fully functional. A player can create a campaign, send actions
to Claude, receive narrated responses with metadata, and have the full game state persist
across sessions.

### Completed Systems

| System | Files | Status |
|--------|-------|--------|
| **API Integration** | `api_client.gd` | Claude API with retry logic, prompt caching headers, model selection |
| **Prompt Assembly** | `prompt_assembler.gd` + `resources/gm_prompts/` | 3-layer cached prompt system: L1 GM Guidelines, L2 call-type templates, L3 dynamic scene context |
| **Game State** | `game_state_manager.gd` | Tracks date, location, scene_characters, roll state, call_type. Full save/load |
| **Conversation Buffer** | `conversation_buffer.gd` | 8-exchange rolling window, API message formatting |
| **Response Parser** | `response_parser.gd` | Extracts narrative + JSON metadata from Claude responses |
| **Data Persistence** | `data_manager.gd` | JSON I/O, campaign directory management, config storage |
| **d100 Roll System** | `roll_engine.gd` | Roll validation, history logging, state transitions |
| **Chat UI** | `chat_panel.gd` | Narrative display, player input, roll input, thinking indicator |
| **Header Bar** | `header_bar.gd` | Location, date, characters, Debug/Settings buttons |
| **Settings Screen** | `settings_screen.gd` | API key, model, campaign create/load |
| **Debug Panel** | `debug_panel.gd` | F12 overlay showing full prompt structure |
| **Prompt Retry Manager** | `prompt_retry_manager.gd` | Reflection → fetch → GM call → retry with character resolution |
| **Main Controller** | `main.gd` | Wires all dependencies, routes signals |

---

## CURRENT PRIORITY: Event-Based Architecture

### Core Concepts

**Event** = A narrative scene spanning multiple exchanges. An audience with a noble,
a march through a province, a negotiation with the Pope. Characters and location stay
stable within an event. This stability is what makes prompt caching work.

**Exchange** = A single player prompt + GM response pair. Multiple exchanges happen
within one event.

**The old system's problems:**
1. Two parallel record systems (events.json vs conversations/[date].json)
2. Conversations die on in-game date change → Claude has amnesia
3. Events are incomplete — Claude decides what to log, creating gaps
4. Chapter system is legacy (workaround for context window limits)
5. chapter_start call type persists incorrectly on resume
6. Start date is hardcoded instead of derived from data

---

### How Prompt Caching Works (for this application)

The API caches **prefixes** of the system prompt based on `cache_control` markers.
If the prefix is identical to a recent call, it's a cache hit.

| | Token Cost |
|---|---|
| Normal input | 1.0x |
| Cache write (first time) | 1.25x (25% more) |
| Cache read (subsequent) | 0.1x (90% cheaper) |
| Cache TTL | 5 minutes (refreshed on each hit) |

**Our system prompt structure:**
```
L1: GM Guidelines        (~1000 tokens)  ← cache_control: ephemeral
L2: Call-type template    (~600 tokens)   ← cache_control: ephemeral
L3: Scene context         (~1500 tokens)  ← cache_control: ephemeral
─── cache boundary ───
Enrichment (if any)       (variable)      ← NOT cached
Messages (last 8 exch.)   (~4000 tokens)  ← NOT cached (changes every turn)
```

**During a stable event** (same characters, location, call type):
- First exchange: L1+L2+L3 written to cache at 1.25x = ~3,875 token-equivalents
- Every subsequent exchange: cache read at 0.1x = ~310 token-equivalents
- Over 15 exchanges in one event: 3,875 + (14 × 310) = **8,215** vs 15 × 3,100 = **46,500**
- **~82% savings** on system prompt tokens

**Cache breaks when:**
- Characters present change (L3 changes)
- Location changes (L3 changes)
- Call type changes (L2 changes — e.g., narrative → persuasion)
- More than 5 minutes between exchanges

**This is why events matter for cost.** Within an event, characters and location
are stable → the cache hits every time. When the event ends and a new one starts,
the cache resets once, then hits again for the new event's duration.

**Context window:** Claude Sonnet 4.5 has 200K tokens. A typical call uses ~8-12K
tokens (system ~3K + messages ~4K + enrichment ~1K + output ~1K). That's ~5% of the
window. Context size is not a constraint — cost is the real concern, and caching
addresses that.

---

### The Event Model

#### What is an event?

An event is a scene — a coherent narrative unit where location and characters are
mostly stable. Examples from the simulation:
- "Audience with the Bishop of Toledo" (12 exchanges)
- "March to Granada" (8 exchanges)
- "Negotiation with Pope Eugenius IV" (20 exchanges)

Events span multiple exchanges. Within an event, the system prompt stays stable,
so prompt caching works. When the event ends, we create a summary and log it.

#### Event lifecycle

```
EVENT START (implicit: first exchange, or after previous event ends)
    │
    ├── Exchange 1: player_input → gm_response (cache WRITE — 1.25x)
    ├── Exchange 2: player_input → gm_response (cache READ — 0.1x)
    ├── Exchange 3: player_input → gm_response (cache READ — 0.1x)
    ├── ...
    │
EVENT END (triggered by location/date change in metadata, or manual)
    │
    ├── Create summary from accumulated summary_updates
    ├── Record characters (union of all scene_characters across exchanges)
    ├── Store full event with exchanges to events.json
    └── Start new event
```

#### What triggers event end?

Detected automatically from Claude's metadata:
- **Location changes** — Claude returns a different `location`
- **Date changes** — Claude returns a different `date`

Could also be manual (future UI button), but auto-detection covers most cases.

#### Data storage

**During an active event:**

`active_event.json` — the current scene's exchange buffer:
```json
{
  "start_date": "1435-06-12",
  "location": "Valladolid, Throne Room",
  "characters": ["juan_ii", "venetian_ambassador"],
  "exchanges": [
    {
      "player_input": "I ask the ambassador about Venice's terms",
      "gm_response": "The ambassador bows deeply...",
      "summary": "Juan inquired about Venetian trade terms",
      "timestamp": "2026-02-16T14:30:00"
    },
    ...
  ]
}
```

The last 8 exchanges from this file become the `messages` array in the API call.
This file persists across game sessions (no data loss on close/crash).

**When the event ends:**

The active event is finalized and appended to `events.json`:
```json
{
  "event_id": "evt_1435_00123",
  "date": "1435-06-12",
  "type": "audience",
  "summary": "Juan negotiated trade terms with the Venetian ambassador. Venice offered...",
  "characters": ["juan_ii", "venetian_ambassador"],
  "location": "Valladolid, Throne Room",
  "tags": [],
  "status": "resolved",
  "exchanges": [
    {"player_input": "...", "gm_response": "...", "summary": "..."},
    ...
  ]
}
```

The full exchanges are preserved in the event for history/debugging. The `summary`
field is what the reflection index uses (compact, searchable). The `exchanges` array
is only loaded when specifically needed (e.g., if the last 8 exchanges span two events
and we need to reach back into the previous one).

#### What does gm_response serve?

| Purpose | Needs full text? | When? |
|---------|-----------------|-------|
| Conversation history (messages array) | YES | Last 8 exchanges |
| Chat panel display | YES | Current session |
| Reflection index search | NO | Uses summary |
| Debug panel | YES | On demand |
| Historical record | Optional | Archived in event |

Full text is only actively needed for the **last 8 exchanges** and display. After
that, the summary is what matters. But we archive the full text in the event anyway
so nothing is ever lost.

---

### Phase A: Active Event System

#### A1. Create active_event.json buffer

Replace the date-scoped `conversations/[date].json` system with a single
`active_event.json` that persists the current scene's exchanges.

**ConversationBuffer rewrite:**
- `initialize()` → load `active_event.json` (not date-scoped)
- `add_exchange()` → append to `active_event.json`
- `get_api_messages()` → return last 8 exchanges from buffer
  - If active event has fewer than 8, reach back into the last completed event
    in `events.json` to fill the gap (ensures no amnesia on event transitions)
- Remove all date-scoping, chapter tracking, `_save_current_conversation()`

**Files changed:**
- `conversation_buffer.gd` — rewrite as active event buffer
- `data_manager.gd` — remove conversation/chapter methods, add active_event I/O
- `main.gd` — simplify initialization, remove `set_scene_context()` calls

#### A2. Auto-detect event boundaries

When Claude's metadata returns a different location or date, the current event ends:
1. Finalize active event → create summary from accumulated `summary_update` entries
2. Append completed event (with exchanges) to `events.json`
3. Start new active event with the new location/date

Detection happens in `game_state_manager.update_from_metadata()`, which already
tracks location and date changes.

**Files changed:**
- `game_state_manager.gd` — add `_finalize_active_event()` and `_start_new_event()`,
  call them when location/date changes in `update_from_metadata()`

#### A3. Auto-log every exchange to the active event

Every GM response automatically appends to the active event. Claude no longer
decides what to log. The `events` array in Claude's metadata is removed.

Claude still provides in every response:
- `summary_update` (REQUIRED) — one-liner for the reflection index
- `scene_characters` — who is present
- `location` / `date` — for boundary detection

**New metadata contract (events array removed):**
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

**Files changed:**
- `game_state_manager.gd` — new `log_exchange()` called after every response
- `response_parser.gd` — remove `events` from EMPTY_METADATA
- `main.gd` — call `log_exchange()` in `_on_api_response()`

---

### Phase B: Remove Chapter System

#### B1. Remove chapter tracking
- Remove `current_chapter`, `chapter_title` from GameStateManager
- Remove `advance_chapter()`, `chapter_changed` signal
- Remove chapter from `game_state.json` save format
- Keep `chapter`/`sub_chapter` in existing starter events as legacy data

#### B2. Remove chapter_start call type
- Remove from call types, stop loading `layer2_chapter_start.txt`
- Remove from `SKIP_REFLECTION_TYPES` in prompt_retry_manager
- Default `current_call_type` to `"narrative"` on load

#### B3. Replace running_summary with event-scoped summary
Running summary was chapter-scoped (cleared on chapter advance). Replace with:
- Each active event accumulates `summary_update` entries
- These are concatenated into the event's summary when finalized
- The scene context in the prompt shows the active event's accumulated summary
  (renamed from "CHAPTER SUMMARY SO FAR" to "CURRENT SCENE SO FAR")
- No unbounded growth — resets naturally when the event ends

**Files changed:**
- `game_state_manager.gd` — remove chapter vars/signals/methods
- `prompt_assembler.gd` — remove chapter from scene context, rename summary section
- `prompt_retry_manager.gd` — remove chapter_start from SKIP_REFLECTION_TYPES
- `conversation_buffer.gd` — remove _current_chapter
- `main.gd` — remove chapter references
- `debug_panel.gd` — remove chapter display

---

### Phase C: Fix Date & Location Derivation

#### C1. Derive state from data on load
When loading a campaign, derive current state from the data itself:
- If `active_event.json` exists → use its date/location/characters
- Else if `events.json` has events → use last event's date/location
- Default `current_call_type` to `"narrative"` (fix stale chapter_start)

#### C2. Remove campaign start date hardcoding
- `initialize_new_campaign()` checks starter_events.json for last event date
- "Brand new simulation from scratch" is out of scope

**Files changed:**
- `game_state_manager.gd` — `_derive_state_from_data()`, sanitize call_type on load
- `main.gd` — simplify campaign loading

---

### Phase D: Add Character Index to Reflection

#### D1. Include character index in reflection prompt
Add compact character list alongside event index:
```
═══ CHARACTER INDEX ═══
[alvaro_de_luna] Álvaro de Luna | Condestable de Castilla | Valladolid
[bishop_toledo] Gutierre de Toledo | Bishop of Toledo | Toledo
```

#### D2. Update reflection response format
Allow Claude to return event IDs AND character IDs:
```json
{
  "event_ids": ["evt_1433_00012"],
  "character_ids": ["alvaro_de_luna"]
}
```

Extend retry manager to process `character_ids` and inject character data
into enrichment text.

**Files changed:**
- `layer0_reflection.txt` — add character index, update response format
- `prompt_assembler.gd` — build character index, inject into reflection
- `prompt_retry_manager.gd` — parse character_ids, fetch character data

---

### Phase E: Update GM Prompt Templates

- Remove `events` array from metadata instructions in all templates
- Make `summary_update` explicitly required ("ALWAYS provide this field")
- Remove all chapter references
- Rename "CHAPTER SUMMARY SO FAR" → "CURRENT SCENE SO FAR"

**Files changed:**
- `layer1_gm_guidelines.txt` — update RESPONSE FORMAT section
- `layer2_medieval_norms.txt` — remove chapter refs
- `layer2_persuasion.txt` — remove chapter refs
- `layer2_chaos.txt` — remove chapter refs
- `layer2_year_end.txt` — remove chapter refs
- `metadata_format.txt` — update reference doc

---

### Execution Order

1. **Phase B** (remove chapters) — clean up dead weight first
2. **Phase C** (date/location derivation + call_type fix) — fix resume behavior
3. **Phase A** (active event system) — core architecture change
4. **Phase E** (update templates) — align Claude's instructions with new system
5. **Phase D** (character index in reflection) — enhancement, builds on above

---

## Future Work

### Characters & Laws Review Panels
**Priority: HIGH** — Side overlays for browsing characters and laws.

### Character Updates from Claude
**Priority: MEDIUM** — `character_updates` metadata field for location/task changes.

### Battle Template
**Priority: MEDIUM** — `layer2_battle.txt` for combat scenes.

### Economy Dashboard
**Priority: LOW** — Treasury review UI.

### Timeline & Events Viewer
**Priority: LOW** — Chronological event browser with filtering.

### Visual Polish
**Priority: LOW** — Medieval fonts, icons, themes, portraits.

---

## Architecture Notes

### Signal flow (after refactor)
```
ChatPanel.message_submitted → Main._on_player_message()
  → PromptRetryManager.handle_player_input()
    → Reflection (optional): searches events.json + characters.json indexes
    → GM call: L1 + L2 + L3 (cached) + enrichment + messages
      → Main._on_api_response()
        → ChatPanel.append_narrative()
        → GameStateManager.update_from_metadata()
          → If location/date changed: finalize event → start new event
        → GameStateManager.log_exchange() → append to active_event.json
        → ConversationBuffer.reload() → refresh last 8 exchanges
```

### Key directories
- Scripts: `scripts/`
- Scenes: `scenes/`
- Prompt templates: `resources/gm_prompts/`
- Game data (runtime): `user://save_data/[campaign]/`
- App config: `user://config.json`
