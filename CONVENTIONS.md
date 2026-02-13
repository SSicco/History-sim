# Castile 1430 — Naming & Data Conventions

This document defines naming rules, data schemas, and formatting conventions used throughout the project. All contributors (human and AI) should follow these standards.

---

## 1. Character IDs

Character IDs are the primary key used in `characters.json`, `scene_characters` metadata, event logs, and all code references.

### Rules

| Rule | Example |
|------|---------|
| Lowercase ASCII only (strip accents) | Álvaro → `alvaro` |
| Underscores for spaces and particles | Álvaro de Luna → `alvaro_de_luna` |
| Exclude titles and ranks from ID | King Juan II → `juan_ii`, not `king_juan_ii` |
| Use roman numerals where part of name | Władysław III → `wladyslaw_iii` |
| Disambiguate by role if names collide | `demetrios_komnenos` vs `demetrios_worker` |
| Deceased characters keep their ID | No special prefix/suffix for dead characters |

### Accent Stripping Reference

| Original | Stripped |
|----------|---------|
| á, à, â, ä | a |
| é, è, ê, ë | e |
| í, ì, î, ï | i |
| ó, ò, ô, ö | o |
| ú, ù, û, ü | u |
| ñ | n |
| ł | l |
| ś, š | s |
| ź, ž | z |
| ć, č | c |

---

## 2. Character JSON Schema

Every character in `characters.json` (and `starter_characters.json`) must follow this schema.

```json
{
  "id": "alvaro_de_luna",
  "name": "Álvaro de Luna",
  "title": "Constable of Castile, Count of San Esteban",
  "born": "1393-06-01",
  "status": ["active"],
  "category": ["court_advisor"],
  "location": "Toledo, Royal Palace",
  "current_task": "Managing kingdom affairs",
  "personality": ["ambitious", "cunning", "loyal to the king", "charismatic"],
  "interests": ["consolidating power", "suppressing noble opposition", "patronage of arts"],
  "red_lines": ["will never voluntarily surrender his position", "will not tolerate public disrespect"],
  "speech_style": "Formal and confident, uses flattery with the king, cold precision with rivals",
  "event_refs": []
}
```

### Field Reference

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (see Section 1) |
| `name` | string | Yes | Display name with original accents/diacritics |
| `title` | string | Yes | Formal title(s), comma-separated if multiple |
| `born` | string | Yes | Date of birth in `"YYYY-MM-DD"` format. If only a year or approximate age is known, generate a plausible date (see notes below) |
| `status` | array[string] | Yes | One or more status tags (see status list below). Statuses can overlap |
| `category` | array[string] | Yes | One or more category tags (see category list below). Characters can belong to multiple categories |
| `location` | string | Yes | Current location in `"City, Specific Place"` format. For deceased: `"Deceased"` |
| `current_task` | string | Yes | What they are currently doing. For deceased: brief legacy note |
| `personality` | array[string] | Yes | 3-6 short trait keywords or phrases |
| `interests` | array[string] | Yes | 2-4 current goals or active pursuits. Can be empty `[]` when data is not yet available |
| `red_lines` | array[string] | Yes | 1-3 hard behavioral limits. Can be empty `[]` when data is not yet available |
| `speech_style` | string | Yes | One sentence describing how they talk. Can be `""` when data is not yet available |
| `event_refs` | array[string] | Yes | Array of event IDs (`"evt_{year}_{5digit}"`). Empty `[]` at campaign start. Reserved for future cross-referencing between characters and events |

### Date of Birth (`born`) — Generation Rules

Age is never stored directly. The game engine calculates age at display time from `born` and the current in-game date.

When the source gives an **exact date** (e.g., "born March 6, 1405"), use it: `"1405-03-06"`.

When the source gives only an **approximate age or year**, generate a plausible DOB:

| Source Says | How to Generate `born` |
|-------------|----------------------|
| `"Age: 34 (born March 6, 1405)"` | Use exact date: `"1405-03-06"` |
| `"Age: ~46"` | Subtract from campaign year, pick a plausible month/day: `"1393-06-01"` |
| `"Age: 29-30 (born ~1409-1410)"` | Pick midpoint year, plausible date: `"1409-08-15"` |
| `"Age: Unknown"` | Use `"0000-00-00"` to indicate unknown DOB |
| `"Middle-aged"` | Estimate ~40-45, generate accordingly |
| `"Age: Died at 17 (born 1415)"` | Use year with plausible date: `"1415-04-01"` |

Generated dates are acceptable — the game needs a value to calculate age, and a plausible estimate is better than no data. The CHARACTER_DATABASE.md remains the authoritative source for what is known vs estimated.

### Category Values

Categories are **not mutually exclusive** — a character can belong to multiple groups. For example, Bishop Oleśnicki is `["religious", "polish_hungarian"]`, and Lucia d'Este is `["royal_family", "italian"]`.

| Category ID | Description | Examples |
|-------------|-------------|---------|
| `royal_family` | The king's immediate family | Juan II, Lucia, Catalina, Fernando |
| `court_advisor` | Royal court officials and advisors | Álvaro de Luna, Diego de Daza, Isaac de Baeza |
| `iberian_royalty` | Other Iberian monarchs and royals | Duarte I, María de Trastámara, Henry the Navigator |
| `nobility` | Major nobles of the realm | Can overlap with court_advisor, military, etc. |
| `papal_court` | Pope and papal officials | Eugenius IV, Tommaso Parentucelli |
| `byzantine` | Constantinople court and people | Emperor John VIII, Patriarch Joseph II |
| `ottoman` | Ottoman Empire figures | Sultan Murad II, Hamza Bey |
| `italian` | Italian state rulers and figures | Cosimo de' Medici, Niccolò III d'Este |
| `military` | Military and naval commanders | Admiral Ataíde, Admiral Vilaragut |
| `religious` | Church figures (any level) | Fray Tomás de Torquemada, Bishop Oleśnicki |
| `economic` | Merchants, bankers, specialists | Musa Keita, Hans von Steinberg |
| `household` | Royal household staff | Doña Beatriz, Marta, Ser Benedetto |
| `polish_hungarian` | Polish-Hungarian court | Władysław III, Oleśnicki, Koniecpol |

### Status Values

Statuses are **not mutually exclusive** — a character can be `["active", "wounded"]` or `["exiled", "ill"]`. The only exception is `deceased`, which should not combine with `active`.

| Status | Meaning | Character Behavior |
|--------|---------|-------------------|
| `active` | Alive and participating | Can appear in scenes, be referenced by Claude |
| `deceased` | Dead | Should never appear in scenes. May be referenced in memory/dialogue |
| `exiled` | Removed from main theater | Should not appear at court. May appear if player travels to their location |
| `wounded` | Physically injured | Can appear but behavior should reflect injury |
| `ill` | Suffering from illness | Can appear but behavior should reflect sickness |
| `pregnant` | With child | Affects travel, risk, and NPC behavior |
| `imprisoned` | Held captive | Cannot freely appear in scenes; location is place of captivity |
| `absent` | Away from their usual location | Not available at their normal post (e.g., on campaign, pilgrimage) |

### Personality, Interests, and Red Lines Guidelines

These fields distill the rich narrative descriptions in CHARACTER_DATABASE.md into compact arrays for the game engine.

**personality** — Short trait keywords or phrases:
- Good: `["ambitious", "cunning", "loyal to the king", "charismatic"]`
- Bad: `["Has been consolidating power since the early days of Juan's reign and maintains careful control over court access"]` (too long, that's a description not a trait)

**interests** — Current goals or active pursuits (not biography):
- Good: `["consolidating power", "suppressing noble opposition"]`
- Bad: `["was born in 1390"]` (that's history, not an interest)

**red_lines** — Things this character will absolutely not do:
- Good: `["will never voluntarily surrender his position"]`
- Bad: `["is ambitious"]` (that's personality, not a red line)

**speech_style** — One sentence capturing voice and manner:
- Good: `"Formal and confident, uses flattery with the king, cold precision with rivals"`
- Bad: `"Speaks"` (too vague)

---

## 3. Location Format

All locations use the format: `"City, Specific Place"`

### Examples

| Correct | Incorrect |
|---------|-----------|
| `"Toledo, Royal Palace"` | `"Royal Palace"` (missing city) |
| `"Kraków, Wawel Castle"` | `"Krakow"` (missing specific place, missing accent) |
| `"Constantinople, Imperial Palace"` | `"Constantinople"` (add specific place when known) |
| `"Rome, Vatican"` | `"The Vatican in Rome"` (use comma format) |
| `"Sierra Nevada, Silver Mines"` | `"the silver mines"` (use proper format) |

When the specific place is unknown or the character roams: `"Toledo"` (city only is acceptable).

---

## 4. Date Format

**ISO 8601 everywhere:** `"YYYY-MM-DD"`

| Context | Format | Example |
|---------|--------|---------|
| Game state | `"1439-09-15"` | September 15, 1439 |
| Events | `"1439-09-15"` | Same |
| Conversation logs | `"1439-09-15"` | Filename: `1439-09-15.json` |
| Economy | Year only as integer | `1439` |
| Laws | `"1439-09-15"` | `date_enacted` field |

When exact day is unknown, use `-01` as default: `"1437-11-01"` for "late 1437 (November)".

---

## 5. Event IDs & Event Types

### Event ID Format

`evt_{year}_{5-digit-sequence}` — includes the in-game year the event occurred, plus a globally unique 5-digit sequence number.

**Examples:** `evt_1432_00001`, `evt_1439_00342`, `evt_1441_10001`

- The **year** is the in-game year when the event happened (not the real-world year)
- The **sequence** is a global auto-incrementing counter (not per-year), supporting up to 99,999 events
- Managed by `game_state_manager.gd` → `_auto_log_events()`. The `next_id` counter in `events.json` tracks the global sequence
- The year component is extracted from the event's `date` field at creation time

### Canonical Event Types

From `metadata_format.txt`:

| Type | Use For |
|------|---------|
| `decision` | Player decisions with consequences |
| `diplomatic_proposal` | Treaties, alliances, negotiations |
| `promise` | Oaths, vows, commitments |
| `battle` | Military engagements |
| `law_enacted` | New laws or decrees |
| `law_repealed` | Laws struck down |
| `relationship_change` | Shifts in character relationships |
| `npc_action` | NPC-initiated actions |
| `economic_event` | Trade, treasury, financial events |
| `roll_result` | Outcome of d100 rolls |
| `ceremony` | Coronations, weddings, funerals |
| `death` | Character deaths |
| `birth` | Births |
| `marriage` | Marriages |
| `treaty` | Formal treaty signing |
| `betrayal` | Treachery, broken oaths |
| `military_action` | Troop movements, sieges, mobilization |
| `construction` | Building projects |
| `religious_event` | Church events, councils, reforms |

---

## 6. Cross-References in CHARACTER_DATABASE.md

The CHARACTER_DATABASE.md uses a cross-reference system for human readers. These references are **not parsed by the game engine** — they exist for editorial tracking only.

### Format

| Type | Format | Example |
|------|--------|---------|
| Chapter reference | `[Ch. X.Y]` | `[Ch. 2.54]` |
| Book reference | `[Book X]` | `[Book 1]` |
| Character reference | `[CHAR: Name]` | `[CHAR: Álvaro de Luna]` |
| Location reference | `[LOC: Name]` | `[LOC: Toledo]` |

**Note:** Earlier versions used `[REF: Chapter_2_54_Summary.docx]` format pointing to external files. These should be migrated to the shorter `[Ch. X.Y]` format, which references in-game chapter numbers rather than external documents.

---

## 7. File & Directory Naming

### Source Files

| Type | Convention | Example |
|------|-----------|---------|
| GDScript | `snake_case.gd` | `game_state_manager.gd` |
| Scenes | `snake_case.tscn` | `chat_panel.tscn` |
| Prompt templates | `layer{N}_{description}.txt` | `layer1_gm_guidelines.txt`, `layer2_medieval_norms.txt` |
| Reference files | `snake_case.txt` | `metadata_format.txt` |

### Data Files (Runtime)

| File | Location | Purpose |
|------|----------|---------|
| `characters.json` | Campaign dir | Active character database |
| `factions.json` | Campaign dir | Faction data |
| `events.json` | Campaign dir | Event log |
| `laws.json` | Campaign dir | Laws and decrees |
| `timeline.json` | Campaign dir | Scheduled and past events |
| `roll_history.json` | Campaign dir | d100 roll log |
| `economy.json` | Campaign dir | Treasury and economy |
| `game_state.json` | Campaign dir | Current game state |
| `conversations/{DATE}.json` | Campaign dir | Daily conversation logs |
| `chapter_summaries/chapter_{NN}.json` | Campaign dir | Chapter summaries (zero-padded 2 digits) |

### Resource Data (Bundled with Game)

| File | Location | Purpose |
|------|----------|---------|
| `starter_characters.json` | `resources/data/` | Default characters loaded at campaign start |

### Campaign Directory Structure

```
user://save_data/{campaign_name}/
  characters.json
  factions.json
  events.json
  laws.json
  timeline.json
  roll_history.json
  economy.json
  game_state.json
  conversations/
    {YYYY-MM-DD}.json
  chapter_summaries/
    chapter_{NN}.json
  portraits/
```

---

## 8. Law Schema

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

- `law_id`: Format `law_XXX` (zero-padded 3 digits)
- `proposed_by`: Uses character ID
- `status`: `"active"` or `"repealed"`

---

## 9. Code Conventions (GDScript)

| Element | Convention | Example |
|---------|-----------|---------|
| Class name | `PascalCase` | `GameStateManager` |
| Variables | `snake_case` | `current_date` |
| Private variables | `_snake_case` | `_layer2_templates` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_TOKENS`, `SAVE_BASE_DIR` |
| Signals | `snake_case` | `state_changed`, `date_changed` |
| Functions | `snake_case` | `save_game_state()` |
| Private functions | `_snake_case` | `_build_scene_context()` |
| Exported vars | `snake_case` with `@export` | `@export var game_state: GameStateManager` |

---

## 10. Mapping CHARACTER_DATABASE.md to JSON

When converting entries from the markdown database to `starter_characters.json`, follow this mapping:

| MD Field | JSON Field | Conversion Notes |
|----------|-----------|-----------------|
| `## Character Name` | `name` | Keep original accents |
| *(generate from name)* | `id` | Apply Section 1 rules |
| *(extract from text)* | `title` | Pull formal title from text or Key Events |
| `**Age:**` | `born` | Convert to `"YYYY-MM-DD"`. If source gives exact DOB, use it. If only age or approximate year, generate a plausible date (see Section 2 notes) |
| *(determine from content)* | `status` | `["active"]` unless marked DECEASED/exiled/etc. Multiple statuses can apply |
| *(determine from section heading + content)* | `category` | Map from MD section + role. A character can belong to multiple categories |
| `**Current Location:**` | `location` | Strip `[Ch. X.Y]` refs, use `"City, Place"` format |
| `**Current Task:**` | `current_task` | Copy directly |
| `**Personality Traits:**` | `personality` | Distill bullet points into 3-6 short keywords |
| *(synthesize from traits + events)* | `interests` | Infer 2-4 current goals from personality and events |
| *(synthesize from personality)* | `red_lines` | Infer 1-3 hard limits from personality and behavior |
| *(synthesize from traits + events)* | `speech_style` | Write one sentence based on personality description |
| *(empty at start)* | `event_refs` | Always `[]` for starter characters (events are runtime) |

### Incremental Data Population

Not all fields need to be filled at initial conversion. The required fields for a character to function in the game engine are: `id`, `name`, `born`, `status`, `category`, `location`, `current_task`, and `personality`. The remaining fields (`title`, `interests`, `red_lines`, `speech_style`, `event_refs`) can be left empty (`""`, `[]`) and populated in a later pass. Empty fields do not block the app from functioning — Claude will work with whatever data is available and can infer behavior from personality and context.
