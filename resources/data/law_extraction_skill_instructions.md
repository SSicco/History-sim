# Law Extraction Skill — Instructions

This document describes how to build a Claude Code skill that reads all `law_enacted` events from the game data and outputs structured law JSON files following the schema in CONVENTIONS.md Section 8.

---

## What the Skill Does

The skill reads the game's event data (starter_events.json and chapter detail files), identifies all `law_enacted` events, groups them into distinct laws, and outputs one JSON file per law into `resources/data/laws/`.

---

## Input Files

The skill needs access to these files:

| File | Purpose |
|------|---------|
| `resources/data/starter_events.json` | Summary view — identifies all events with `"type": "law_enacted"` and their event IDs, dates, characters, locations |
| `resources/data/chapter_02_*.json` | Detail view — full exchanges, roll data, and recaps for each event. Use these to write `full_text` and `summary` fields |
| `resources/data/roll_tables.json` | Roll table definitions — maps d100 values to outcome ranges. Use when a law's origin event has an associated roll |
| `resources/data/characters.json` | Character database — resolve character names to IDs for `proposed_by` and `enacted_by` |
| `CONVENTIONS.md` | Section 8 defines the law JSON schema. The skill output must conform exactly to this schema |

---

## Output

- **Directory:** `resources/data/laws/`
- **One file per law:** `law_001.json`, `law_002.json`, etc.
- **Additionally:** `resources/data/laws/_index.json` — a manifest listing all generated laws with their `law_id`, `title`, and `origin_event_id` for quick reference

### Index File Format

```json
{
  "generated": "2026-02-17",
  "count": 15,
  "laws": [
    {
      "law_id": "law_001",
      "title": "Papal Decree of Honours and Grants",
      "origin_event_id": "evt_1433_00009",
      "scope": "papal",
      "status": "active"
    }
  ]
}
```

---

## Processing Rules

### 1. Identify all law_enacted events

Scan `starter_events.json` for every event where `"type": "law_enacted"`. Record their `event_id`, `date`, `characters`, `location`, and `summary`.

### 2. Group events into distinct laws

Multiple `law_enacted` events can represent a single law. Apply these grouping rules:

| Condition | Result |
|-----------|--------|
| Same date + same location + same participants + same topic | **One law.** Use the final event as `origin_event_id`. Earlier events go in `related_events` with relationship `"referenced"` or `"amended"` |
| Explicitly references a prior law (e.g., "finalizes the Constitution...") | **Amendment modifier** on the original law, not a new law. Add to the original law's `effectiveness_modifiers` with type `"decree"` |
| Different jurisdiction (papal bull vs royal edict vs imperial chrysobull) | **Always separate laws**, even if enacted on the same day |
| Same topic but different dates / clearly a new legislative act | **Separate law** |

### 3. Determine fields for each law

For each grouped law:

| Field | How to determine |
|-------|-----------------|
| `law_id` | Assign sequentially: `law_001`, `law_002`, etc., in chronological order by `date_enacted` |
| `title` | Derive from the event summary. Use the formal name if one exists in the narrative (e.g., "Charter of the Imperial Tagmata", "La Dote de la Reina Isabel"). Otherwise compose a short descriptive title |
| `full_text` | Write the decree text in period-appropriate language. Use the chapter detail exchanges as source material — extract or compose the actual words of the law as they would have been proclaimed. This should read like a 15th-century legal document, 2-5 sentences |
| `date_enacted` | The date of the canonical event |
| `location` | From the event's location field |
| `proposed_by` | The character who proposed or drafted the law. Determine from the event summary and exchanges. Use character ID format |
| `enacted_by` | The authority who formally enacts it. Usually `"juan_ii"` for Castilian laws, `"pope_eugenius_iv"` for papal bulls, `"john_viii"` for Byzantine chrysobulls |
| `status` | `"active"` unless a later `law_repealed` event exists for this law |
| `scope` | Determine from jurisdiction (see CONVENTIONS.md Section 8 scope values) |
| `tags` | 2-4 category tags from the event's content |
| `origin_event_id` | The canonical event ID (final event in a group) |
| `effectiveness_modifiers` | Start empty `[]` — these will be populated during gameplay as rolls and events occur. **Exception:** if the chapter detail data includes a `roll` object for the law's origin event, include that as the first modifier with type `"roll"` and write a contextual summary of the roll's narrative outcome |
| `related_events` | Include any grouped drafting events here. Also scan other events near the same date that reference the same topic (e.g., enforcement events, reactions) |
| `repeal` | `null` unless a `law_repealed` event exists |

### 4. Write full_text guidelines

The `full_text` field is the most important creative output. It should:

- Read like an actual 15th-century legal proclamation
- Use formal language appropriate to the issuing authority (royal decree style for Castilian laws, papal bull style for church decrees, imperial chrysobull style for Byzantine edicts)
- Be 2-5 sentences — the substance of the law, not a full legal document
- Start with the authority formula (e.g., "By royal decree of His Majesty Juan II..." or "We, Eugenius, Bishop, Servant of the Servants of God...")
- State the operative provisions clearly
- Draw from the event's exchanges in the chapter detail files for specific language

### 5. Character ID resolution

When determining `proposed_by` and `enacted_by`, convert character names to their IDs using the rules in CONVENTIONS.md Section 1. Cross-reference against `characters.json` to ensure the ID exists. If a character isn't in the database, use the ID format anyway and note it for later addition.

---

## Example Output

### law_001.json

```json
{
  "law_id": "law_001",
  "title": "Papal Decree of Honours and Grants",
  "full_text": "We, Eugenius, Bishop, Servant of the Servants of God, do hereby decree before twenty-three Cardinals assembled: that Juan, King of Castile, is released from his crusade oath with highest honours; that the Military Orders of Santiago, Calatrava, and Alcántara are granted to the Crown of Castile in perpetuity; that the claim of Alfonso of Aragon to the throne of Naples is endorsed by the Holy See; and that Juan shall speak at Basel bearing the full confidence of the Apostolic Chair.",
  "date_enacted": "1433-04-24",
  "location": "Rome, Vatican Audience Chamber",
  "proposed_by": "juan_ii",
  "enacted_by": "pope_eugenius_iv",
  "status": "active",
  "scope": "papal",
  "tags": ["military_orders", "diplomatic", "religious"],
  "origin_event_id": "evt_1433_00009",
  "effectiveness_modifiers": [],
  "related_events": [],
  "repeal": null
}
```

---

## Validation Checklist

Before outputting each law file, verify:

- [ ] `law_id` is unique and follows `law_XXX` format
- [ ] `origin_event_id` matches a real event in `starter_events.json`
- [ ] `proposed_by` and `enacted_by` use valid character ID format (lowercase, underscores, no accents)
- [ ] `date_enacted` is ISO 8601
- [ ] `location` uses `"City, Place"` format
- [ ] `scope` is one of the defined values
- [ ] `status` is `"active"`, `"repealed"`, or `"suspended"`
- [ ] `full_text` reads like a period-appropriate legal document, not a modern summary
- [ ] `effectiveness_modifiers` entries have `event_id`, `date`, `type`, and `summary`
- [ ] `related_events` entries have `event_id`, `date`, `relationship`, and `summary`
- [ ] No numeric effectiveness scores anywhere — all descriptions are contextual narrative
- [ ] Grouped events are not duplicated as separate laws
