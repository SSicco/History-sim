# Quality Standard — Castile 1430 Data Pipeline

This document defines what "complete" and "correct" data looks like for every
database in the project. All chapter processing must meet these standards before
being considered done. Use `tools/validate_quality.py` (see Section 7) to
check compliance.

---

## 1. Scope

This standard covers all data from **Book 1** (chapters 1.01–1.44) and
**Book 2** (chapters 2.01–2.24). Every chapter produces two artifacts:

| Artifact | Location | Purpose |
|---|---|---|
| **Event chapter file** | `resources/data/events/chapter_X.XX.json` | Events with exchanges, merged into `events.json` |
| **Extraction file** | `tools/extractions/chapter_X.XX_extracted.json` | Characters, locations, factions, rolls, laws, updates |

Both must exist and meet the standards below.

---

## 2. Event Chapter Files

**Location:** `resources/data/events/chapter_X.XX.json`

### 2.1 Required fields per event

| Field | Type | Required | Rule |
|---|---|---|---|
| `event_id` | string | Yes | Format: `evt_YYYY_NNNNN` (e.g., `evt_1430_00001`) |
| `book` | integer | Yes | 1 or 2 |
| `chapter` | string | Yes | Format: `X.XX` (e.g., `"1.01"`) |
| `date` | string | Yes | ISO format `YYYY-MM-DD` |
| `end_date` | string/null | Yes | Null for single-day events |
| `type` | string | Yes | One of the standard event types (see 2.2) |
| `summary` | string | Yes | 1–3 sentences, factual, captures outcome |
| `characters` | array[string] | Yes | All character IDs involved; minimum 1 |
| `factions_affected` | array[string] | Yes | All factions whose interests are affected; can be empty |
| `location` | string | Yes | Specific: "Valladolid, Royal Palace" not just "Valladolid" |
| `tags` | array[string] | Yes | Semantic tags; minimum 1 |
| `status` | string | Yes | `"resolved"` or `"ongoing"` |
| `exchanges` | array[object] | Yes | Full player/GM conversation; minimum 2 entries |
| `roll` | string/null | Yes | Roll ID if a roll occurred, otherwise null |

### 2.2 Standard event types

`council`, `decision`, `military_action`, `battle`, `siege`, `diplomacy`,
`negotiation`, `ceremony`, `personal`, `intrigue`, `espionage`, `travel`,
`religious`, `economic`, `legal`, `crisis`, `discovery`, `chapter_wrap`

### 2.3 Exchange format

Each exchange object has exactly two fields:
```json
{ "role": "player", "text": "..." }
{ "role": "gm", "text": "..." }
```

### 2.4 Character ID format

All character IDs use `lowercase_with_underscores`. No spaces, no capitals,
no hyphens. IDs must match `characters.json` entries exactly. Use
`tools/known_aliases.json` to resolve variants before writing.

**Bad:** `Captain Fernan`, `captain-fernan`, `CaptainFernan`
**Good:** `fernan_alonso_de_robles`

---

## 3. Extraction Files

**Location:** `tools/extractions/chapter_X.XX_extracted.json`

Every extraction file has this top-level structure:
```json
{
  "chapter": "1.01",
  "book": 1,
  "events": [...],
  "new_characters": [...],
  "character_updates": [...],
  "new_locations": [...],
  "new_factions": [...],
  "rolls": [...],
  "law_references": [...],
  "faction_updates": [...]
}
```

All 10 keys must be present. Empty arrays are acceptable when a chapter
genuinely has no new items in that category.

### 3.1 `events` array

Same structure as the event chapter file events (Section 2.1). This is the
source data before event IDs are assigned.

### 3.2 `new_characters`

Every character introduced for the first time in this chapter.

| Field | Type | Required | Rule |
|---|---|---|---|
| `id` | string | Yes | Canonical snake_case ID |
| `name` | string | Yes | Full display name with title |
| `aliases` | array[string] | Yes | All name variants used in text |
| `title` | string | Yes | Official title or role |
| `born` | string | Yes | `YYYY-MM-DD` if known, `"unknown"` if not |
| `status` | array[string] | Yes | Typically `["active"]` |
| `category` | array[string] | Yes | See category list below |
| `location` | string | Yes | Where they are when introduced |
| `current_task` | string | Yes | What they are doing when introduced |
| `personality` | array[string] | Yes | 4–6 traits minimum |
| `interests` | array[string] | Yes | 2–4 interests minimum |
| `speech_style` | string | Yes | How they speak (10+ words) |
| `core_characteristics` | string | Yes | 2–3 sentence summary of role/nature |
| `faction_ids` | array[string] | Yes | Known faction memberships |
| `appearance` | object | Yes | Physical description (see 3.2.1) |

#### 3.2.1 Appearance object

| Field | Type | Notes |
|---|---|---|
| `age_appearance` | string | e.g., "mid-20s", "elderly" |
| `build` | string | e.g., "lean", "stocky", "average" |
| `hair` | string | e.g., "dark", "grey", "tonsured" |
| `distinguishing_features` | string | Notable features, scars, etc. |

At minimum, `age_appearance` and `build` should be present. If the source
text describes the character's appearance, capture all details. If not
described, infer reasonable defaults from the character's age, role, and
historical context.

#### 3.2.2 Standard character categories

`royal_family`, `court_advisor`, `noble`, `military`, `religious`,
`merchant`, `foreign_royal`, `foreign_noble`, `foreign_diplomat`,
`military_order`, `scholar`, `commoner`, `spy`

#### 3.2.3 Quality check

A new character record is **incomplete** if any of these are true:
- `personality` has fewer than 4 traits
- `interests` is empty
- `speech_style` is empty or fewer than 10 words
- `core_characteristics` is empty or fewer than 20 words
- `appearance` is empty or has no subfields

### 3.3 `character_updates`

Only for characters who **materially change** during this chapter. Do not
create updates for characters who merely appear. Changes include: location
change, new task, personality development, status change, relationship shift.

| Field | Type | Required | Rule |
|---|---|---|---|
| `id` | string | Yes | Canonical character ID |
| `current_task` | string | If changed | What they are doing now |
| `location` | string | If changed | Where they are now |
| `personality` | object | If changed | `{"add": ["new_trait"]}` |
| `status` | array[string] | If changed | e.g., `["wounded"]`, `["imprisoned"]` |
| `faction_ids` | object | If changed | `{"add": ["faction_id"]}` or `{"remove": ["faction_id"]}` |

#### 3.3.1 Quality check

A chapter with 5+ events and 5+ named characters should have **at least 3
character_updates**. Events create consequences — track them.

**Good example** (from chapter 1.22):
```json
{
  "id": "infante_enrique_de_aragon",
  "current_task": "Wounded (arrow in shoulder, survivable) from ambush August 23. Counter-raiding campaign catastrophically failed (roll 6). 330 casualties. Intelligence network destroyed.",
  "location": "Loja area",
  "status": ["active", "wounded"]
}
```

**Bad example** (generic, says nothing):
```json
{
  "id": "alvaro_de_luna",
  "current_task": "Advising the king"
}
```

### 3.4 `new_locations`

Every location mentioned for the first time in this chapter.

| Field | Type | Required | Rule |
|---|---|---|---|
| `location_id` | string | Yes | Canonical snake_case ID |
| `name` | string | Yes | Full display name |
| `region` | string | Yes | Broader geographic region |
| `description` | string | Yes | 1–3 sentences; include strategic/political significance |
| `sub_locations` | array[string] | Yes | Named interior/adjacent areas from the text |

#### 3.4.1 Quality check

A location is **incomplete** if:
- `description` is empty or fewer than 30 characters
- A strategically important location (fortress, capital, port) lacks
  military/political context in description

**Good example:**
```json
{
  "location_id": "seville",
  "name": "Seville",
  "region": "Castile",
  "description": "Major Castilian trade city on the Guadalquivir. Produces ~420,000 maravedís in quarterly customs revenues. Noble feuds between Guzmán and Ponce de León families.",
  "sub_locations": ["Alcázar District", "Cathedral"]
}
```

**Bad example:**
```json
{
  "location_id": "seville",
  "name": "Seville",
  "region": "",
  "description": "",
  "sub_locations": []
}
```

### 3.5 `new_factions`

Every faction introduced for the first time in this chapter.

| Field | Type | Required | Rule |
|---|---|---|---|
| `faction_id` | string | Yes | Canonical snake_case ID |
| `name` | string | Yes | Full display name |
| `type` | string | Yes | See type list below |
| `region` | string | Yes | Geographic scope |
| `description` | string | Yes | Goals, power base, and significance (2+ sentences) |
| `leader_id` | string | Yes | Character ID of leader |
| `member_ids` | array[string] | Yes | Key member character IDs |

#### 3.5.1 Standard faction types

`political`, `military`, `religious`, `noble_house`, `military_religious`,
`economic`, `ecclesiastical`, `institutional`, `monarchy`

#### 3.5.2 Quality check

A faction is **incomplete** if:
- `description` is empty or fewer than 50 characters
- `description` does not explain the faction's goals or significance
- `leader_id` is empty
- `member_ids` is empty

### 3.6 `rolls`

Every d100 roll that occurs in this chapter's events.

| Field | Type | Required | Rule |
|---|---|---|---|
| `event_index` | integer | Yes | Index of the event containing this roll |
| `title` | string | Yes | Brief, memorable name for the roll |
| `context` | string | Yes | 1–2 sentences explaining why the roll is happening |
| `roll_type` | string | Yes | See roll types below |
| `date` | string | Yes | ISO date when roll occurs |
| `rolled` | integer | Yes | The actual d100 result (1–100) |
| `outcome_range` | string | Yes | Numeric range format: `"01-10"`, `"11-25"`, etc. |
| `outcome_label` | string | Yes | Brief label: "Campaign Failure", "Exceptional Success" |
| `outcome_detail` | string | Yes | 1–3 sentences: what specifically happened |
| `evaluation` | string | Yes | Assessment of significance and implications |
| `success_factors` | array[string] | Yes | Factors that helped (can be empty on failure) |
| `failure_factors` | array[string] | Yes | Factors that hindered (can be empty on success) |

#### 3.6.1 Standard roll types

`military`, `diplomacy`, `persuasion`, `chaos`, `travel`, `espionage`,
`religion`, `economy`, `intrigue`, `personal`

#### 3.6.2 Outcome range format

Use **numeric ranges**, not labels:

| Range | Meaning |
|---|---|
| `"01-10"` | Critical failure |
| `"11-25"` | Failure |
| `"26-40"` | Partial failure / mixed |
| `"41-60"` | Status quo / modest |
| `"61-80"` | Success |
| `"81-93"` | Major success |
| `"94-100"` | Critical success / exceptional |

**Good example:**
```json
{
  "event_index": 1,
  "title": "Enrique's Counter-Raiding Campaign",
  "context": "3,000 cavalry deployed to destroy guerrilla raiders west of Loja.",
  "roll_type": "military",
  "date": "1431-08-23",
  "rolled": 6,
  "outcome_range": "01-10",
  "outcome_label": "Campaign Failure",
  "outcome_detail": "Force ambushed in hills west of Loja. 187 dead, 143 wounded. Enrique wounded (arrow in shoulder). Intelligence network destroyed.",
  "evaluation": "Near-worst outcome. Tactical, operational, and intelligence failure on every level.",
  "success_factors": [],
  "failure_factors": ["Ambush in unfamiliar terrain", "Intelligence failure", "Guerrilla expertise"]
}
```

**Bad example (auto-generated):**
```json
{
  "event_index": 3,
  "rolled": 15,
  "title": "Cautious Acceptance",
  "context": "pose through Morocco and Constantinople campaigns, no change...",
  "roll_type": "chaos",
  "outcome_range": "failure",
  "outcome_detail": "",
  "evaluation": "",
  "success_factors": [],
  "failure_factors": []
}
```

### 3.7 `law_references`

Every law, decree, edict, treaty, or formal ruling created or modified in
this chapter.

| Field | Type | Required | Rule |
|---|---|---|---|
| `law_id` | string | Yes | ID from `laws.json` (e.g., `"law_001"`) |
| `event_index` | integer | Yes | Index of the event that enacts/modifies the law |
| `action` | string | Yes | `"enacted"`, `"modified"`, `"repealed"`, `"referenced"` |
| `summary` | string | Yes | Brief description of what the law does |

#### 3.7.1 Quality check

If a chapter's events mention a law, decree, treaty, or formal ruling, there
**must** be a corresponding `law_references` entry linking it to the event.

### 3.8 `faction_updates`

Status updates for factions whose position materially changes during this
chapter.

| Field | Type | Required | Rule |
|---|---|---|---|
| `faction_id` | string | Yes | Canonical faction ID |
| `description` | string | Yes | 2–4 sentences: current status, recent actions, outlook |

#### 3.8.1 Quality check

A chapter with significant political/military events should update at least
the primary factions involved. A battle chapter should update the military
factions. A diplomatic chapter should update the political factions.

---

## 4. Runtime Database Standards

These are the merged databases loaded by the game at runtime. They are
**generated outputs** — edit the extraction files and re-merge.

### 4.1 `characters.json`

Every character must have all 18 fields present:

| Field | Non-empty required? | Notes |
|---|---|---|
| `id` | Yes | |
| `name` | Yes | |
| `aliases` | Yes (min 1) | At least the ID itself |
| `title` | Yes | |
| `born` | Yes | Date or `"unknown"` |
| `status` | Yes (min 1) | |
| `category` | Yes (min 1) | |
| `location` | Yes | |
| `current_task` | Yes | |
| `personality` | Yes (min 4) | |
| `interests` | Yes (min 2) | |
| `speech_style` | Yes (10+ words) | |
| `core_characteristics` | Yes (20+ words) | |
| `rolled_traits` | No (can be empty) | |
| `faction_ids` | No (can be empty) | |
| `event_refs` | Yes (min 1) | |
| `appearance` | Yes (min 2 subfields) | |
| `portrait_prompt` | No (can be empty) | |

### 4.2 `locations.json`

Every location must have:
- `description`: non-empty, 30+ characters
- `event_refs`: non-empty (at least 1 event)
- `region`: non-empty

### 4.3 `factions.json`

Every faction must have:
- `description`: non-empty, 50+ characters, explains goals/significance
- `leader_id`: non-empty, valid character ID
- `member_ids`: non-empty (at least 1 member)
- `event_refs`: non-empty (at least 1 event)

### 4.4 `laws.json`

Every law must have:
- `full_text`: non-empty
- `origin_event_id`: valid event ID (not `"_pending_event_linkage"`)
- `related_events`: populated with event IDs where the law is referenced

### 4.5 `roll_history.json`

Every roll must have:
- `rolled`: non-null integer (1–100)
- `event_id`: valid event ID that exists in `events.json`
- `outcome_range`: numeric format (`"01-10"`, not `"failure"`)
- `outcome_detail`: non-empty
- `evaluation`: non-empty

---

## 5. Cross-Reference Integrity

These rules ensure data consistency across databases:

| Rule | Check |
|---|---|
| **Character-Event** | Every ID in an event's `characters` array must exist in `characters.json` |
| **Event-Character** | Every event ID in a character's `event_refs` must exist in `events.json` |
| **Roll-Event** | Every roll's `event_id` must exist in `events.json` |
| **Location-Event** | Every event ID in a location's `event_refs` must exist in `events.json` |
| **Faction-Event** | Every event ID in a faction's `event_refs` must exist in `events.json` |
| **Faction-Character** | Every ID in a faction's `member_ids` must exist in `characters.json` |
| **Law-Event** | Every law's `origin_event_id` must exist in `events.json` |
| **Alias consistency** | Character IDs in events must be canonical (not alias) per `known_aliases.json` |

---

## 6. Known Gaps (Current State)

This section tracks known deviations from the standard. Items here are
acknowledged debt, not acceptable permanent state.

### 6.1 Chapters 1.23–2.22: extraction quality

Extraction files for these 46 chapters were auto-generated by
`build_extractions.py` and are missing:

- [ ] `character_updates` — all empty (0 updates per chapter)
- [ ] `rolls` — partially captured (only `Roll NN (Label):` format; `d100 rolls (N, N)` format missed)
- [ ] `law_references` — all empty (0 law-event links)
- [ ] `new_characters` — missing `appearance`, `interests`, `speech_style`, `personality` detail
- [ ] `new_locations` — missing `description` (32 of 54 locations are stubs)
- [ ] `new_factions` — missing `description` (24 of 26 factions are stubs)
- [ ] `faction_updates` — all empty

### 6.2 Roll history

- [ ] 29 rolls (chapters 1.01–1.10) have `rolled: null` — need actual d100 values
- [ ] `outcome_range` uses label format (`"failure"`) in some entries — should be numeric (`"11-25"`)

### 6.3 Laws

- [ ] 5 laws have `origin_event_id: "_pending_event_linkage"` — need actual event IDs
- [ ] `related_events` is empty for all 46 laws

### 6.4 Characters

- [ ] 72 original characters (from 1.01–1.22) have sparse `appearance` (only 11 have any)
- [ ] 72 original characters: 50 missing `interests`, 52 missing `speech_style`

---

## 7. Validation

A validation script (`tools/validate_quality.py`) should check every rule in
this document and produce a report like:

```
=== Quality Validation Report ===

EVENTS (612)
  [PASS] All events have required fields
  [FAIL] 3 events have empty tags array
  [FAIL] 12 events have empty factions_affected (review needed)

CHARACTERS (149)
  [PASS] All characters have id, name, born
  [FAIL] 50 characters missing interests
  [FAIL] 52 characters missing speech_style
  [FAIL] 61 characters missing appearance data

LOCATIONS (54)
  [FAIL] 32 locations have empty description

FACTIONS (26)
  [FAIL] 24 factions have empty description

ROLLS (249)
  [FAIL] 29 rolls have null rolled value
  [FAIL] 11 rolls reference non-existent event IDs

LAWS (46)
  [FAIL] 5 laws have pending event linkage
  [FAIL] 46 laws have empty related_events

CROSS-REFERENCES
  [FAIL] 1 character in events not found in characters.json: muhammad_al_badisi
  [PASS] All faction member_ids exist in characters.json
```

Run this after every merge operation. No chapter is "done" until validation
passes with zero FAIL items for that chapter's data.

---

## 8. Pipeline Checklist

When processing a new chapter, every step must complete before the chapter is
marked done in `build_state.json`:

- [ ] **Event defs** exist in `tools/event_defs/chapter_X.XX_defs.json`
- [ ] **Event chapter file** assembled in `resources/data/events/chapter_X.XX.json`
- [ ] **Extraction file** created in `tools/extractions/chapter_X.XX_extracted.json`
- [ ] Extraction file has non-empty: `new_characters`, `character_updates`, `rolls` (if rolls exist), `law_references` (if laws exist)
- [ ] **Merge** completed: `python3 tools/merge_chapter.py --chapter X.XX`
- [ ] **Events rebuilt**: `python3 tools/build_events_db.py merge`
- [ ] **Validation passes**: `python3 tools/validate_quality.py --chapter X.XX`
- [ ] All character IDs use canonical form (no aliases)
- [ ] All cross-references valid

---

## 9. Document History

| Date | Change |
|---|---|
| 2026-02-20 | Initial version. Created after audit revealed quality degradation in chapters 1.23–2.22 compared to 1.01–1.22 standard. |
