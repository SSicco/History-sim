# History-Sim Prompt Engine — Complete Design Specification

This document describes the full architecture of the prompt engine for the Godot-based historical simulation game "Castile 1430." Another developer or AI session should be able to re-implement the entire system from this document alone.

---

## 1. OVERVIEW: TWO-CALL ARCHITECTURE

Every player input triggers **two API calls**, not one:

1. **Call 1 — Context Agent (Haiku):** A cheap, fast call to `claude-haiku-4-5-20251001` that decides what game data (characters, events, laws) the main GM needs to answer this specific player input. It returns search queries, not narrative.

2. **Call 2 — Main GM (Sonnet):** The full narrative call to `claude-sonnet-4-5-20250929` that actually generates the story response. Its prompt is assembled from 4 layers, including the data that Call 1 retrieved.

**Why two calls?** The character database and event history can be huge. Sending everything to Sonnet every time wastes tokens and money. Instead, Haiku acts as a cheap router — it reads compact indexes and decides what subset of data the main call actually needs. This keeps the Sonnet prompt lean and focused.

**Exception:** Roll results (d100) skip Call 1 entirely and go straight to Call 2, because the GM already knows the context from the previous exchange where it generated the probability table.

---

## 2. THE COMPLETE CALL FLOW

```
Player types input
    │
    ▼
main._on_player_message(text)
    ├─ Save input, begin session recording
    ├─ Advance sticky context exchange counter
    ├─ Build compact character index + event index
    └─ Send to ContextAgent.request_context()  ──── CALL 1 (Haiku)
            │
            ▼
    Haiku returns JSON: {needs_search: true/false, ...queries}
            │
        ┌───┴───┐
        │       │
    [search]  [skip]
        │       │
        ▼       │
    Execute searches against local data    │
    Add results to StickyContext            │
    Check for overflow → new event if so   │
        │       │
        └───┬───┘
            │
            ▼
    PromptAssembler.assemble_prompt()
    Build 4 system layers + messages
            │
            ▼
    ApiClient.send_message()  ──── CALL 2 (Sonnet)
            │
            ▼
    ResponseParser extracts {narrative, metadata}
            │
            ▼
    - Display narrative to player
    - Update GameState from metadata
    - Log events from metadata to events.json
    - Save exchange to conversation buffer
    - Check if profile refresh needed (every 8 events)
    - Check if location changed → clear sticky context
    - Auto-save game state
```

---

## 3. CALL 1 — THE CONTEXT AGENT (Haiku)

### What it receives

The Context Agent gets:
- The player's raw input text
- Current in-game date and location
- IDs of data already in sticky context (so it doesn't re-search)
- A **compact character index**: one line per character, format `id | name | title | location | status`
- A **compact event index**: last 100 events, one line each, format `event_id | date | type | summary (max 80 chars) | characters`

### System prompt (constant)

```
You translate player intent into search queries for a historical simulation game.
The player is King Juan II of Castile (15th century). You must determine which
characters, events, and laws are relevant to the player's input.

Available search fields:
- character_search: {"keywords": [...], "ids": [...], "categories": [...], "locations": [...]}
- event_search: {"keywords": [...], "characters": [...], "types": [...],
                  "date_after": "YYYY-MM-DD", "date_before": "YYYY-MM-DD"}
- law_search: {"keywords": [...], "status": "active"|"repealed"|""}

Event types: decision, diplomatic_proposal, promise, battle, law_enacted,
  law_repealed, relationship_change, npc_action, economic_event, roll_result,
  ceremony, death, birth, marriage, treaty, betrayal, military_action,
  construction, religious_event

Character categories: royal_family, court_advisor, iberian_royalty, nobility,
  papal_court, byzantine, ottoman, italian, military, religious, economic,
  household, polish_hungarian

Respond with ONLY valid JSON. If the conversation flows naturally from recent
context and no new data is needed, respond:
{"needs_search": false}

If context is needed, respond:
{"needs_search": true, "character_search": {...}, "event_search": {...},
 "law_search": {...}, "event_detail_ids": [...]}

Rules:
- "my love", "my wife", "the queen" → search for Juan's wife
- "my children" → search royal_family category
- Only include event_detail_ids for events the player explicitly asks to recall in detail
- Be generous with keywords — better to find too much than miss something
- Keep searches focused. Do not search for broad topics unless the player asks broadly
```

### User content template

```
Player input: "{player_input}"
Current date: {date}
Current location: {location}

Already in context (do not re-search):
- Characters: {sticky_character_ids}
- Events: {sticky_event_ids}

CHARACTER INDEX:
{one line per character: id | name | title | location | status}

EVENT INDEX (last 100):
{one line per event: event_id | date | type | summary | characters}
```

### Response handling

- Strips markdown code fences if present (```json...```)
- Parses JSON
- If `needs_search` is false → emits `context_skipped`, proceed to Call 2
- If `needs_search` is true → execute local searches, add to sticky context
- On parse failure → treat as skip (graceful degradation)

### Profile Refresh (separate Haiku call)

The Context Agent also handles profile refreshes (a different system prompt):

```
You maintain King Juan II's profile for a historical simulation game.
Given Juan's current profile and recent events, produce an updated profile.

The profile must include:
1. Who Juan is (titles, key traits, faith, ambitions)
2. His family (wife, children with birth dates — NOT ages)
3. His story arc (major achievements, current chapter)
4. His current situation and task
5. Key relationships and alliances

Keep it under 500 words. Use birth dates (YYYY-MM-DD), never ages.
Write in third person, present tense. Focus on what's narratively relevant NOW.
Respond with ONLY the profile text, no JSON wrapping.
```

Triggered every 8 events. Receives: current profile text, last 8 events, current date, royal family character data.

---

## 4. LOCAL SEARCH ENGINE (after Haiku returns queries)

The search engine runs locally (no API call) against cached data.

### Budget caps
- **Characters:** max 4 results
- **Events:** max 6 results
- **Laws:** max 3 results

### Character search scoring
| Match type | Score |
|---|---|
| Direct ID match | +50 |
| Keyword in name | +20 |
| Keyword in title | +10 |
| Keyword in current_task | +5 |
| Category match | +8 |
| Location match | +12 |
| Status filter | hard filter (exclude if no match) |

Sorted by score descending, return top 4.

### Event search scoring
| Match type | Score |
|---|---|
| Keyword in summary | +10 |
| Character ID match | +15 |
| Event type match | +8 |
| Recency bonus (has a date) | +1 |
| Date range filters | hard filter |

Sorted by score descending, then date descending for ties, return top 6.

### Law search scoring
| Match type | Score |
|---|---|
| Keyword in title | +15 |
| Keyword in summary | +10 |
| Status filter | hard filter |

Return top 3.

### Event detail recall

When the Haiku agent returns `event_detail_ids`, the system loads the conversation exchanges from that event's date. It looks for exchanges that reference the event ID, or falls back to the last 3 exchanges from that day. These are injected into the sticky context alongside the event summary.

---

## 5. STICKY CONTEXT — The Memory System

Sticky context persists data **across exchanges within a single event boundary**. It avoids re-fetching the same characters/events every turn.

### How it works

- Each player input increments the exchange counter
- Search results are added: `add_characters()`, `add_events()`, `add_laws()`
- Already-loaded IDs are sent to Haiku so it won't re-search them
- Data stays in sticky until an **event boundary** clears it

### Token budget: 3000 tokens

Estimated at 4 characters = 1 token.

### What triggers a new event boundary (sticky clear)

1. **Sticky overflow:** If total tokens exceed 3000 after adding new search results, sticky is cleared and a system message `[New event — context reset]` is shown
2. **Location change:** If the GM's metadata includes a different `location` than the current one, sticky is cleared
3. **Session start/load:** Sticky starts empty

### Data stored in sticky

- **Characters:** keyed by `id`, full character dict
- **Events:** keyed by `event_id`, with record dict + detail flag + conversation exchanges array
- **Laws:** keyed by `law_id`, full law dict
- **Pull log:** array of `{exchange, type, id, tokens}` for diagnostics

### Format for prompt injection

When sticky has items, it formats them under headers:

```
═══ RELEVANT CHARACTERS ═══
### Álvaro de Luna
Title: Constable of Castile
Born: 1390-06-01
Location: Valladolid, Royal Palace
Current Task: Managing frontier defense
Personality: cunning, ambitious
Speech Style: formal, respectful
Red Lines: betrayal of the Crown

═══ RELEVANT PAST EVENTS ═══
[1430-03-15] diplomatic_proposal — Count of Haro proposes alliance (characters: count_of_haro, alvaro_de_luna)

═══ RELEVANT LAWS ═══
[1430-01-20] Cortes Tax Reform — New tax structure approved (status: active)
```

---

## 6. CALL 2 — THE MAIN GM PROMPT (4-Layer System)

The prompt is built from 4 system content blocks, each marked with `cache_control: {"type": "ephemeral"}` for API-level prompt caching.

### Layer 1: GM Guidelines (static, always cached)

File: `resources/gm_prompts/layer1_gm_guidelines.txt`

Contains 5 core rules:

**RULE 1: NPC AUTONOMY**
- NPCs resist by default. They have their own interests, fears, ambitions, red lines.
- Default to resistance: conditional agreement, partial agreement, deflection, outright refusal, counter-demands.
- Juan is King but NOT an absolute monarch. Nobility, clergy, Cortes all have real power.
- "A session where every NPC agrees with Juan is a FAILED session."

**RULE 2: RESPONSE DISCIPLINE**
- 80-150 words typical. Max 200 for normal dialogue. Max 400 for major scenes.
- ONE beat per response (one NPC speaks, or one thing happens).
- End on a moment that invites Juan's response.
- "Think of pacing like a tennis match. You hit the ball to Juan. Then you WAIT."

**RULE 3: PLAYER AGENCY IS SACRED**
- NEVER generate actions, speech, thoughts, feelings, or decisions for Juan. NEVER.
- Never write "Juan said/felt/thought/nodded/turned/stood/walked..."
- Never move Juan to a new location or advance time without his instruction.
- After something happens, describe what Juan can OBSERVE, then STOP.

**RULE 4: HISTORICAL AUTHENTICITY**
- Period-appropriate language, titles, forms of address.
- Castilian conventions: Conde, Marqués, Duque, etc.
- Church as dominant force. Rigid social hierarchy. Honor culture.

**RULE 5: d100 RESOLUTION SYSTEM**
- When outcome is uncertain, generate a d100 probability table.
- Always include catastrophic and exceptional ranges.
- Present table, then STOP and wait for roll.
- Table is binding — never override a roll result.

**RESPONSE FORMAT** (also in Layer 1):
- End every response with a ```json``` metadata block
- Fields: scene_characters, location, date, awaiting_roll, roll_type, summary_update, events, dialogue, juan_acted (must always be false)

### Layer 2: Call-Type Template (changes based on situation)

The game has different "call types" that load different Layer 2 templates:

| Call Type | Template File | When Used |
|---|---|---|
| `narrative` | `layer2_medieval_norms.txt` | Default — normal conversation and narration |
| `persuasion` | `layer2_persuasion.txt` | When Juan tries to persuade/negotiate |
| `chaos` | `layer2_chaos.txt` | Random events — travel, disease, battles |
| `roll_result` | Uses the matching skill template (persuasion/chaos/narrative based on `roll_type`) | After a d100 roll is submitted |
| `chapter_start` | `layer2_chapter_start.txt` | Opening a new chapter |
| `year_end` | `layer2_year_end.txt` | December treasury report |

**Persuasion template** covers:
- When to use rolls (specific request, change mind, negotiate, inspire/intimidate)
- When NOT to use rolls (obvious agree/refuse, trivial, casual)
- Favorable modifiers (recent benefits, leverage, aligned interests, NPC weakness)
- Unfavorable modifiers (past wrongs, conflicting interests, NPC strength, no precedent, broken promises)
- Table format: 5-8 ranges, always include catastrophic (1-X) and exceptional (Y-100)

**Chaos template** covers:
- Triggers (travel, sieges, childbirth, disease, seasons, political instability, foreign affairs)
- Context-specific table building (travel: roads/bandits/escort; military: forces/terrain/morale; health: age/season/medicine)
- Always include mundane/nothing-happens ranges
- Results must be historically plausible and can create new story threads

**Medieval norms template** covers:
- Political structure (Crown NOT absolute, power shared with Grandes, Church, Cortes)
- Social hierarchy (10 tiers from King to religious minorities)
- Forms of address (Vuestra Majestad, Vuestra Señoría, Su Eminencia, etc.)
- Honor culture, religion's role, warfare, economy

**Chapter start template**: Scene setting (200-300 words), situation briefing via in-character NPCs, open the floor with momentum

**Year-end template**: Treasury report narrated in-character by treasurer/chancellor, economic decisions presented as advisor proposals

### Layer 3: Juan II Profile (refreshed every 8 events)

Prepended with: `═══ JUAN II — PLAYER CHARACTER ═══`

Contains ~300-500 words describing Juan's identity, family (with birth dates, never ages), story arc, current situation. Updated by Haiku every 8 logged events.

Initial bootstrap profile includes: titles, family tree with birth dates, major story achievements, current situation.

### Layer 4: Scene Context (dynamic every exchange)

Built fresh each turn. Contains:

```
═══ CURRENT SITUATION ═══
Date: {current_date}
Location: {current_location}
Chapter {N}: {chapter_title}

{sticky context formatted — characters, events, laws}

═══ LAST 10 EVENTS ═══
[date] type — summary (characters)
[date] type — summary (characters)
... (always included for continuity)

═══ CHAPTER SUMMARY SO FAR ═══
{running_summary text}
```

### Messages array

After the 4 system blocks, the messages array contains:
- The last **8 exchanges** from the conversation buffer as alternating `{role: "user", content: player_input}` and `{role: "assistant", content: gm_response}` pairs
- The new player input appended as a final `{role: "user", content: text}`

### Max tokens by call type

```
narrative:     400
persuasion:    1500
chaos:         1500
roll_result:   600
chapter_start: 1000
year_end:      2000
battle:        800
```

---

## 7. RESPONSE PARSING

The GM's response is expected to have two parts:
1. **Narrative text** — everything before the last ```json``` block
2. **Metadata JSON** — the content between the last ```json ... ``` fences

The parser extracts both. The metadata has these fields with defaults:

```json
{
  "scene_characters": [],
  "location": "",
  "date": "",
  "awaiting_roll": false,
  "roll_type": null,
  "summary_update": "",
  "events": [],
  "dialogue": [],
  "juan_acted": false
}
```

### What happens with metadata

- `scene_characters` → updates `GameState.scene_characters`, displayed in header
- `location` → if different from current, triggers sticky clear + new event
- `date` → updates current in-game date
- `awaiting_roll` + `roll_type` → shows roll input UI, sets call type for next exchange
- `summary_update` → appended to `GameState.running_summary`
- `events` → auto-logged to `events.json` with generated `event_id`, current date/location/chapter
- `dialogue` → recorded (speaker + type)
- `juan_acted` → should always be false (self-check)

### Event auto-logging format

Each event from metadata gets saved as:
```json
{
  "event_id": "evt_XXXX",
  "date": "current_date",
  "chapter": current_chapter,
  "type": "event.type",
  "summary": "event.summary",
  "characters": ["character_ids"],
  "factions_affected": [],
  "location": "current_location",
  "tags": [],
  "status": "resolved"
}
```

---

## 8. GAME STATE

Managed by `GameStateManager`. Core fields:

```
current_date: String = "1430-01-01"
current_location: String = "Valladolid, Royal Palace"
current_chapter: int = 1
chapter_title: String = "The Reign Begins"
scene_characters: Array = []       # character IDs present in scene
awaiting_roll: bool = false
roll_type: String = ""             # "persuasion", "chaos", or ""
running_summary: String = ""       # grows with each summary_update
current_call_type: String = "narrative"
```

Auto-saved to `game_state.json` after every exchange.

---

## 9. CONVERSATION BUFFER

Maintains a rolling window of **last 8 exchanges** for the API messages array. This is what gives the GM conversational memory within a session.

Each exchange stores:
```json
{
  "exchange_id": "exch_TIMESTAMP",
  "timestamp": "ISO timestamp",
  "player_input": "what the player typed",
  "gm_response": "the narrative text",
  "event_refs": ["evt_1234"],
  "metadata": { ... }
}
```

On date change or location change, the current conversation is saved and a new one starts. Saved to `conversations/{YYYY-MM-DD}.json`.

---

## 10. ROLL MECHANICS

When the GM's metadata has `awaiting_roll: true`:
1. The roll input UI appears
2. Player enters a number 1-100
3. System validates (integer, 1-100 range)
4. Logs to `roll_history.json`
5. Sets `current_call_type = "roll_result"`
6. **Skips the context agent** — goes straight to Call 2
7. Layer 2 template is chosen based on `roll_type` (persuasion → persuasion template, chaos → chaos template)
8. The player input becomes `"d100 roll result: {value}"`

---

## 11. DATA PERSISTENCE LAYOUT

```
user://save_data/
├── config.json                        # API key, model, last campaign
└── {campaign_name}/
    ├── game_state.json               # Current state snapshot
    ├── characters.json               # All characters (parsed from CHARACTER_DATABASE.md)
    ├── events.json                   # All logged events with next_id counter
    ├── laws.json                     # Laws enacted/repealed
    ├── factions.json                 # Faction data
    ├── timeline.json
    ├── roll_history.json             # All d100 rolls
    ├── economy.json
    ├── juan_profile.txt              # Profile text + metadata (JSON)
    ├── conversations/
    │   └── {YYYY-MM-DD}.json         # Exchanges for each in-game date
    ├── chapter_summaries/
    │   └── chapter_{NN}.json
    ├── api_logs/
    │   └── {timestamp}_{call_number}.json  # Per-call cost/usage logs
    ├── diagnostics/
    │   ├── rec_{timestamp}.json      # Full session recording
    │   ├── rec_{timestamp}_REPORT.txt # Human-readable report
    │   ├── event_{NNN}.json          # Per-event diagnostics
    │   └── session_{timestamp}.json  # Session summary
    └── portraits/
```

Test mode appends `__test` to the campaign directory name.

---

## 12. PROFILE MANAGEMENT

- Stored in `juan_profile.txt` as JSON with `profile_text`, `last_refresh_event_count`, `last_updated`
- Refreshed every **8 events** via Haiku call
- Initial bootstrap template hardcoded in `ProfileManager.get_initial_template()`
- Refresh sends: current profile + last 8 events + current date + royal family character data
- Haiku returns updated profile text (max 500 words, third person, present tense, birth dates not ages)

---

## 13. CHARACTER DATABASE

Source: `CHARACTER_DATABASE.md` (Markdown format)

Parsed into `characters.json` on new campaign creation. Each character has:
```json
{
  "id": "alvaro_de_luna",
  "name": "Álvaro de Luna",
  "title": "Constable of Castile",
  "born": "1390-06-01",
  "status": ["active"],
  "category": ["court_advisor", "nobility"],
  "location": "Valladolid, Royal Palace",
  "current_task": "Managing frontier defense",
  "personality": ["cunning", "ambitious"],
  "interests": [],
  "red_lines": ["betrayal of the Crown"],
  "speech_style": "formal, respectful",
  "event_refs": []
}
```

Character categories: `royal_family, court_advisor, iberian_royalty, nobility, papal_court, byzantine, ottoman, italian, military, religious, economic, household, polish_hungarian`

---

## 14. DIAGNOSTICS & SESSION RECORDING

Three diagnostic systems run in parallel:

### Session Recorder
Records EVERYTHING about every exchange: the full system prompt sent to Haiku, Haiku's raw response, the search results, the sticky snapshot, the full prompt sent to Sonnet (all 4 layers with char counts and token estimates), Sonnet's raw response, the parsed narrative and metadata, token usage, costs. Saved as JSON + human-readable text report.

### Event Diagnostics
Tracks per-event statistics: number of exchanges, context pulls, sticky snapshots, costs, end reason. An "event" = sequence of exchanges between sticky context resets.

### API Logger
Logs every API call with: model, call type, usage breakdown (input/output/cache_write/cache_read tokens), cost, request summary, response summary.

**Pricing table used for cost calculation:**
```
claude-sonnet-4-5-20250929:
  input: $3.00/M, output: $15.00/M, cache_write: $3.75/M, cache_read: $0.30/M

claude-haiku-4-5-20251001:
  input: $0.80/M, output: $4.00/M, cache_write: $1.00/M, cache_read: $0.08/M
```

---

## 15. SCENE TREE & NODE WIRING

```
Main (Control) — orchestrates everything
├── DataManager (Node) — all file I/O
├── GameStateManager (Node) — game state + auto-event-logging
├── ApiClient (Node) — HTTP calls to Anthropic API with retry logic
├── PromptAssembler (Node) — builds the 4-layer prompt
├── ConversationBuffer (Node) — rolling 8-exchange window
├── RollEngine (Node) — validates d100 input
├── ApiLogger (Node) — cost tracking
├── ContextAgent (Node) — Haiku calls (own HTTPRequest)
├── ProfileManager (Node) — Layer 3 profile management
├── EventDiagnostics (Node) — per-event tracking
├── SessionRecorder (Node) — full exchange recording
├── Layout (VBoxContainer)
│   ├── HeaderBar — shows date, location, characters present
│   └── ContentArea
│       └── ChatPanel — narrative display + player input + roll UI
├── SettingsScreen — API key, model, campaign management, test mode
└── DebugPanel — collapsible sections showing all prompt layers, usage, diagnostics
```

All dependencies are wired in `main._ready()` via direct property assignment (not @export in scene). Signals connect the flow.

---

## 16. KEY DESIGN PRINCIPLES

1. **Two models, two jobs:** Haiku routes context cheaply. Sonnet writes narrative with quality. Never mix these roles.

2. **Sticky context prevents redundant fetches:** Once a character is pulled into context, it stays there until the event boundary. Haiku is told what's already loaded.

3. **Event boundaries keep context fresh:** When sticky overflows (>3000 tokens) or location changes, everything clears. This prevents stale data from accumulating.

4. **Player agency is non-negotiable:** Rule 3 is the most important rule. The GM never generates Juan's actions, speech, thoughts, or movement. Ever.

5. **Prompt caching saves money:** Layers 1-3 use `ephemeral` cache control. Layer 1 (guidelines) and Layer 2 (call type) rarely change, so they cache heavily. Layer 3 (profile) changes every 8 events. Layer 4 is always dynamic.

6. **Last 10 events always included:** Regardless of what the context agent finds, the most recent 10 events are always in Layer 4 for continuity.

7. **Conversation buffer gives short-term memory:** The last 8 exchanges are always in the messages array, giving the GM awareness of the immediate conversation.

8. **Everything is recorded:** Session recorder captures every prompt, every response, every decision at every step. This allows full debugging of any exchange after the fact.

9. **Graceful degradation:** If Haiku fails or returns unparseable JSON, the system skips context search and proceeds with whatever is in sticky. The game doesn't crash.

10. **Roll results are binding:** When a d100 table is generated, the outcome matching the roll MUST be narrated. No softening, overriding, or re-interpretation.
