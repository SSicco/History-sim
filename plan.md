# Plan: Data Quality Remediation

**Goal:** Bring all databases for chapters 1.01–2.22 up to the standard
defined in `QUALITY_STANDARD.md`.

**Status:** In progress (Phase 1)

---

## Current State

### What works
- 612 events across 68 chapters, all with full exchanges
- 149 characters in `characters.json`
- Pipeline: `event_defs` → `assemble_chapter` → `build_events_db` → `build_extractions` → `merge_chapter` → `enrich_characters`
- Automatic character enrichment (location, current_task, personality) runs after every merge

### What's broken
Two tiers of quality exist. Chapters 1.01–1.22 were hand-crafted with rich
extraction files. Chapters 1.23–2.22 were auto-generated with sparse stubs.
The quality standard was never written down, so the gap went unnoticed.

### Gap inventory

| Gap | Scope | Severity |
|---|---|---|
| Empty `character_updates` in extraction files | 46 chapters (1.23–2.22) | High |
| Missing roll data (d100 format not parsed) | ~17 chapters | High |
| 29 rolls with `rolled: null` | Chapters 1.01–1.10 | Medium |
| Roll `outcome_range` uses labels not numbers | ~120 rolls | Medium |
| Empty `law_references` in extractions | 46 chapters | Medium |
| 5 laws with `_pending_event_linkage` | laws.json | Medium |
| All 46 laws have empty `related_events` | laws.json | Medium |
| 24/26 factions have no description | factions.json | High |
| 32/54 locations have no description | locations.json | High |
| Empty `faction_updates` in extractions | 46 chapters | Medium |
| 72 original characters missing appearance | characters.json | Medium |
| 72 original characters missing interests (50) and speech_style (52) | characters.json | Medium |
| 77 generated characters missing appearance detail | characters.json | Medium |

---

## Remediation Phases

### Phase 1 — Validation tooling

**Build `tools/validate_quality.py`** so we can measure progress and prevent
regression. Without this, we're flying blind.

The script checks every rule in `QUALITY_STANDARD.md` and produces a report
with PASS/FAIL per rule, counts, and specific violations. It should support:

```bash
python3 tools/validate_quality.py              # Full report
python3 tools/validate_quality.py --chapter 1.23  # Single chapter
python3 tools/validate_quality.py --summary    # Counts only
```

**Checks to implement:**

Events:
- [ ] All 14 required fields present
- [ ] `characters` array non-empty, all IDs exist in characters.json
- [ ] `tags` array non-empty
- [ ] `exchanges` array has 2+ entries
- [ ] `location` is specific (contains comma or sub-location)
- [ ] Character IDs are canonical (not aliases)

Characters:
- [ ] All 18 fields present
- [ ] `personality` has 4+ traits
- [ ] `interests` has 2+ items
- [ ] `speech_style` has 10+ words
- [ ] `core_characteristics` has 20+ words
- [ ] `appearance` has 2+ subfields
- [ ] `event_refs` non-empty

Locations:
- [ ] `description` has 30+ characters
- [ ] `event_refs` non-empty
- [ ] `region` non-empty

Factions:
- [ ] `description` has 50+ characters
- [ ] `leader_id` is valid character ID
- [ ] `member_ids` non-empty, all valid

Rolls:
- [ ] `rolled` is non-null integer 1–100
- [ ] `event_id` exists in events.json
- [ ] `outcome_range` is numeric format ("01-10", not "failure")
- [ ] `outcome_detail` non-empty
- [ ] `evaluation` non-empty

Laws:
- [ ] `origin_event_id` is valid (not `_pending_event_linkage`)
- [ ] `full_text` non-empty
- [ ] `related_events` non-empty

Cross-references:
- [ ] All character IDs in events exist in characters.json
- [ ] All event IDs in character event_refs exist in events.json
- [ ] All roll event_ids exist in events.json
- [ ] All faction member_ids exist in characters.json
- [ ] All law origin_event_ids exist in events.json

**Deliverable:** `tools/validate_quality.py` with baseline report saved.

---

### Phase 2 — Automated fixes (no human judgment needed)

These are mechanical fixes that scripts can handle reliably.

#### 2a. Roll `outcome_range` normalization

Convert label-format ranges to numeric format in `roll_history.json`:

| Current | Target |
|---|---|
| `"critical_failure"` | `"01-10"` |
| `"failure"` | `"11-25"` |
| `"partial_failure"` | `"26-40"` |
| `"status_quo"` | `"41-60"` |
| `"success"` | `"61-80"` |
| `"major_success"` | `"81-93"` |
| `"critical_success"` | `"94-100"` |

**Approach:** Script reads `roll_history.json`, maps labels to ranges, writes
back. For rolls that also have a `rolled` value, verify the range matches.

#### 2b. Roll format extraction (d100 pattern)

Add a second pattern to `build_extractions.py` that matches:
`d100 rolls (12, 35, 40, 78)` — the format used in chapters 1.24–1.41.

**Approach:** Add regex pattern, re-run extraction for affected chapters, re-merge.

#### 2c. Law-event linkage

Match each law's `origin_event_id` to an actual event by:
1. Date matching (law's `date_enacted` vs event dates)
2. Character matching (law's `proposed_by`/`enacted_by` vs event characters)
3. Content matching (law title/summary keywords vs event summary)

**Approach:** Script reads laws.json and events.json, scores matches, assigns
the best match. Review borderline cases manually.

#### 2d. Cross-reference rebuild

Rebuild `event_refs` arrays for locations and factions by scanning all events:
- For each event, add its ID to the matching location's and factions' `event_refs`

**Approach:** Already done by merge_chapter, but verify completeness.

**Deliverable:** All automated fixes applied, validation report updated.

---

### Phase 3 — Extraction enrichment (needs source text analysis)

This is the main body of work. The event chapter files contain full exchange
text (player/GM conversations). This text contains character descriptions,
roll contexts, faction developments, and law discussions — but this
information was never extracted into the extraction files for chapters
1.23–2.22.

#### Source material available

For every chapter in scope, we have:
- `resources/data/events/chapter_X.XX.json` — full events with exchanges
- `tools/preprocessed/chapter_X.XX_preprocessed.json` — cleaned messages
- `tools/event_defs/chapter_X.XX_defs.json` — event boundaries

The exchange text is the richest source. A typical GM response is 500–2000
words of detailed narrative including character descriptions, political
analysis, military details, and roll outcomes.

#### 3a. Build `tools/extract_from_exchanges.py`

A new script that reads a chapter's event file (with exchanges) and generates
enriched extraction data. This replaces the current `build_extractions.py`
output with much richer data derived from the actual narrative text.

**What it extracts:**

From **GM narration** in exchanges:
- **Character descriptions** → `new_characters.appearance`, `speech_style`
- **Character actions/changes** → `character_updates` (task, location, status)
- **Roll mechanics** → `rolls` with full context, outcome detail, evaluation
- **Location descriptions** → `new_locations.description`, `sub_locations`
- **Faction developments** → `faction_updates` with status narratives
- **Legal actions** → `law_references` linking laws to events

**Extraction approach (per chapter):**

1. Read the chapter event file
2. For each event, read all GM exchanges
3. For known patterns, extract structured data:
   - Roll results: `Roll NN (Label):` and `d100 rolls (N, N, N)` patterns
   - Character introductions: first mention of a character name with
     descriptive context → appearance, personality hints
   - Location introductions: first detailed description of a place
   - Status changes: "wounded", "imprisoned", "died", "arrived at", etc.
   - Law/decree text: formal proclamations, edicts, treaties
4. Write enriched extraction file

**What this script does NOT do:**
- Deep narrative interpretation (who is lying, hidden motivations)
- Relationship inference (allies, enemies)
- Personality synthesis from dialogue patterns

Those require human judgment or LLM analysis and are deferred to Phase 4.

**Approach:** Build the script, run it per chapter, review output, merge.
Process in batches of ~10 chapters.

#### 3b. Chapter-by-chapter extraction review

For each batch of chapters, the extraction output should be reviewed to:
- Verify character_updates are accurate (not hallucinated from pattern matching)
- Confirm roll data matches the actual narrative
- Check location descriptions capture strategic significance
- Ensure faction updates reflect actual political changes

This is the step where human oversight catches extraction errors.

#### 3c. Backfill original characters (1.01–1.22)

72 characters from the original pipeline are missing `appearance`, `interests`,
and `speech_style`. These characters appear in events that have full exchange
text. The same extraction approach works:

1. For each character missing data, find their events
2. Read the exchange text from those events
3. Extract appearance descriptions, stated interests, dialogue patterns
4. Update the character record

**Deliverable:** All 68 chapters have complete extraction files. All characters
have appearance, interests, speech_style populated.

---

### Phase 4 — Faction and location descriptions

After Phase 3, we'll have per-chapter faction_updates and location data from
exchanges. This phase synthesizes that into the runtime databases.

#### 4a. Faction descriptions

For each of the 24 stub factions:
1. Collect all events where the faction appears (from `event_refs`)
2. Read the exchange text from key events
3. Write a 2–4 sentence description covering: goals, power base, key members,
   current status as of chapter 2.22

**Priority order** (by event count):
1. The Papacy (31 events)
2. Military Orders (13 events)
3. Council of Basel (6 events)
4. Kingdom of Granada (4 events)
5. French Faction (3 events)
6. Remaining 19 factions

#### 4b. Location descriptions

For each of the 32 stub locations:
1. Find events at that location
2. Read exchange text for descriptive passages
3. Write a 1–3 sentence description covering: what the place is, why it
   matters, any strategic/political significance

**Priority order** (by event count):
1. Vatican (21 events)
2. Alhama de Granada (7 events)
3. Remaining 30 locations

**Deliverable:** All factions and locations have substantive descriptions.

---

### Phase 5 — Law cross-referencing

#### 5a. Fix pending event linkages

5 laws have `origin_event_id: "_pending_event_linkage"`. For each:
1. Read the law's date, proposer, and content
2. Search events.json for matching events
3. Assign the correct event ID

#### 5b. Populate `related_events`

For all 46 laws:
1. Search event summaries and exchange text for references to the law
2. Add matching event IDs to the law's `related_events` array

**Deliverable:** All laws linked to originating and related events.

---

### Phase 6 — Final validation and cleanup

1. Run `validate_quality.py` — all checks must pass
2. Rebuild events.json: `python3 tools/build_events_db.py merge`
3. Run `verify_databases.py` for cross-reference integrity
4. Archive old `plan.md` content (move to `archive/`)
5. Update `CLAUDE.md` with current pipeline documentation
6. Update `build_state.json` to reflect completion

**Deliverable:** Zero FAIL items in validation report. All databases at
quality standard.

---

## Work Estimates

| Phase | Chapters | Approach | Size |
|---|---|---|---|
| Phase 1: Validation script | — | Build tool | Small |
| Phase 2: Automated fixes | All | Script | Small |
| Phase 3a: Exchange extraction tool | — | Build tool | Medium |
| Phase 3b: Run extraction + review | 46 chapters | Batch process | Large |
| Phase 3c: Backfill original characters | 72 characters | Script + review | Medium |
| Phase 4: Faction + location descriptions | 56 items | Write from events | Medium |
| Phase 5: Law cross-references | 46 laws | Script + review | Small |
| Phase 6: Final validation | All | Run tools | Small |

**Critical path:** Phase 1 → Phase 2 → Phase 3a → Phase 3b (largest block)
→ Phase 4 → Phase 6

Phases 4 and 5 can run in parallel once Phase 3 is done.

---

## Pipeline Flow (Updated)

```
Source material (Claude chat exports)
    ↓  tools/preprocess_chapter.py
Preprocessed messages (tools/preprocessed/)
    ↓  tools/assemble_chapter.py (+ event_defs)
Event chapter files (resources/data/events/chapter_*.json)
    ↓  tools/build_events_db.py assign-ids
Event IDs assigned
    ↓  tools/extract_from_exchanges.py        ← NEW (Phase 3a)
Enriched extraction files (tools/extractions/)
    ↓  tools/merge_chapter.py
All databases updated
    ↓  tools/enrich_characters.py
Character state derived from events
    ↓  tools/build_events_db.py merge
events.json rebuilt
    ↓  tools/validate_quality.py              ← NEW (Phase 1)
Quality report
```

---

## Rules for Future Work

1. **No chapter is "done" until `validate_quality.py` passes for it.**
   This is the single gate that prevents quality regression.

2. **`plan.md` is the living tracker.** Update it when work completes. Check
   items off. Add new gaps as discovered.

3. **`QUALITY_STANDARD.md` is the spec.** If the standard needs to change,
   change the document first, then update the validation script, then update
   the data. Never silently lower the bar.

4. **Extraction files are the source of truth for enrichment data.** Do not
   manually edit `characters.json`, `locations.json`, etc. Edit the extraction
   file and re-merge.

5. **Every merge runs enrichment + validation.** The pipeline must catch
   problems at merge time, not later.

---

## Changelog

| Date | Change |
|---|---|
| 2026-02-20 | Rewrote plan.md. Old version (single-source-of-truth plan) is obsolete — that work was completed. New version tracks quality remediation. |
