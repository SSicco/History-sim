# TASK: Convert chapter2.txt → chapter_02_02.json

## RULES — READ THESE FIRST

- **DO NOT** read CONVENTIONS.md. Everything you need is in THIS document.
- **DO NOT** create a todo list. Just start writing the file.
- **DO NOT** read chapter2.txt in small chunks. Read it in 4 parallel reads of ~450 lines each (1-450, 451-900, 901-1350, 1351-1787).
- **DO NOT** give progress reports. Write the file.
- **DO** read `chapter2.txt` and the reference JSON in parallel, then immediately start writing.
- **DO** write the entire `chapter_02_02.json` file in ONE Write tool call.
- **DO** commit and push when done.

**Your entire workflow should be: Read source files → Write JSON → Commit → Push. That's it.**

---

## What You Are Doing

Convert the narrative in `/home/user/History-sim/chapter2.txt` into a structured JSON file at:

```
/home/user/History-sim/resources/data/chapter_02_02.json
```

The `resources/data/` directory already exists.

---

## Output File Structure

```json
{
  "chapter": "2.2",
  "title": "Strategic Counsel",
  "date_range": "1433-04-25 / 1433-05-28",
  "encounters": [
    {
      "id": "evt_1433_00011",
      "type": "diplomatic_proposal",
      "date": "1433-04-25",
      "end_date": null,
      "location": "Rome, Vatican Private Chamber",
      "participants": ["juan_ii", "eugenius_iv", "giordano_orsini"],
      "exchanges": [
        { "speaker": "narrator", "text": "..." },
        { "speaker": "eugenius_iv", "text": "..." },
        { "speaker": "juan_ii", "text": "..." }
      ],
      "roll": null,
      "recap": "One-sentence summary of what happened."
    }
  ]
}
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `chapter` | string | Always `"2.2"` |
| `title` | string | Always `"Strategic Counsel"` |
| `date_range` | string | Always `"1433-04-25 / 1433-05-28"` |
| `encounters` | array | List of encounter objects (see below) |

### Encounter Object

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Event ID: `evt_1433_XXXXX`. Starts at `00011` (chapter 2.1 used 00001-00010) |
| `type` | string | One of the canonical event types listed below |
| `date` | string | ISO date `YYYY-MM-DD` |
| `end_date` | string or null | ISO date if event spans multiple days, otherwise `null` |
| `location` | string | Format: `"City, Specific Place"` |
| `participants` | array[string] | Character IDs of everyone present (see Character ID table) |
| `exchanges` | array[object] | Array of `{"speaker": "...", "text": "..."}` objects |
| `roll` | object or null | If a d100 roll occurs: `{"table_id": "roll_ch2_2_NNN", "value": NN, "outcome": "Short label"}`. If no roll: `null` |
| `recap` | string | One-sentence summary of the encounter |

### Exchange Object

| Field | Type | Description |
|-------|------|-------------|
| `speaker` | string | Either `"narrator"` for narration/description, or a character ID for dialogue |
| `text` | string | The narration or dialogue text. Preserve the original text from the source. |

### Roll Object (when present)

| Field | Type | Description |
|-------|------|-------------|
| `table_id` | string | Format: `roll_ch2_2_NNN` where NNN is 001, 002, etc. |
| `value` | integer | The actual number rolled |
| `outcome` | string | Short label of the outcome (e.g., "Alarm - Firm Rejection") |

---

## Canonical Event Types

Use these values for the `type` field:

| Type | Use For |
|------|---------|
| `diplomatic_proposal` | Treaties, alliances, negotiations |
| `decision` | Player decisions with consequences |
| `military_action` | Troop movements, sieges, mobilization |
| `religious_event` | Church events, councils, reforms |
| `ceremony` | Coronations, weddings, funerals |
| `npc_action` | NPC-initiated actions |
| `roll_result` | Outcome of d100 rolls |
| `relationship_change` | Shifts in character relationships |

---

## Character ID Reference

These are the character IDs to use in `participants` and `speaker` fields:

| Character | ID | Notes |
|-----------|----|-------|
| King Juan II of Castile | `juan_ii` | The player character |
| Pope Eugenius IV | `eugenius_iv` | |
| Cardinal Giordano Orsini | `giordano_orsini` | |
| Captain Fernán Alonso de Robles | `fernan_alonso_de_robles` | |
| Marco Tornesi | `marco_tornesi` | Italian guide |
| Brother Guillem | `brother_guillem` | Benedictine spiritual counsel |
| Emperor Sigismund | `sigismund` | Holy Roman Emperor-Elect, King of Hungary and Bohemia |
| Metropolitan Bessarion of Nicaea | `bessarion` | Byzantine delegation |
| Metropolitan Isidore of Kiev | `isidore` | Byzantine delegation |
| Abbott Rodrigo González | `rodrigo_gonzalez` | Chief of Castilian delegation at Basel |
| Bishop Alfonso de Cartagena | `alfonso_de_cartagena` | Castilian delegation |
| Fray Hernando de Talavera | `hernando_de_talavera` | Juan's confessor |
| Narrator | `narrator` | For all narration, description, GM text |

---

## Encounter Breakdown

**There are 11 encounters.** Here they are with their IDs and key details:

### Encounter 1: `evt_1433_00011` — Papal Dinner: Theological Positions
- **type:** `diplomatic_proposal`
- **date:** `1433-04-25`
- **location:** `"Rome, Vatican Private Chamber"`
- **participants:** `["juan_ii", "eugenius_iv", "giordano_orsini"]`
- **roll:** `null`
- **What happens:** The Pope and Orsini read Juan's delegation's theological document. Discussion of Hussite reforms (communion in both kinds, vernacular preaching), Bohemian property distinction, and papal vs conciliar authority. The Pope questions how Juan reconciles faith with acknowledging Church errors.
- **Source lines:** ~20–88
- **recap:** Pope Eugenius IV and Cardinal Orsini review the Castilian theological positions on Hussite reforms, finding the distinction between genuine reform and Bohemian property theft strategically powerful but questioning the theological implications.

### Encounter 2: `evt_1433_00012` — Juan Proposes Pope Attend Basel
- **type:** `diplomatic_proposal`
- **date:** `1433-04-25`
- **location:** `"Rome, Vatican Private Chamber"`
- **participants:** `["juan_ii", "eugenius_iv", "giordano_orsini"]`
- **roll:** `{"table_id": "roll_ch2_2_001", "value": 33, "outcome": "Alarm - Firm Rejection"}`
- **What happens:** Juan suggests the Pope accompany him to Basel with 800 crusaders for protection. The Pope is alarmed — firmly explains why this is impossible (would validate conciliar supremacy, precedent of armed escort, Rome would fall). Cardinal Orsini supports the Pope's position. The Pope redirects: Juan should go to Basel as an independent monarch, not as papal escort.
- **Source lines:** ~89–182
- **recap:** Juan naively proposes the Pope attend Basel under crusader escort; the Pope firmly rejects this as politically catastrophic but redirects Juan to attend as an independent Christian monarch with moral authority from the Reconquista.

### Encounter 3: `evt_1433_00013` — Juan's Vision for Christendom
- **type:** `diplomatic_proposal`
- **date:** `1433-04-25`
- **location:** `"Rome, Vatican Private Chamber"`
- **participants:** `["juan_ii", "eugenius_iv", "giordano_orsini"]`
- **roll:** `{"table_id": "roll_ch2_2_002", "value": 83, "outcome": "Inspired"}`
- **What happens:** Juan articulates a broader vision: reform addresses conciliarist concerns about corruption, expose Bohemian nobles as thieves hiding behind theology, redirect Christendom's energy toward the Ottoman threat and aiding Constantinople. The Pope is genuinely inspired for the first time in three years but raises obstacles: the Filioque dispute, Byzantine distrust, the authority question, Ottoman military logistics.
- **Source lines:** ~183–311
- **recap:** Juan presents an inspired vision of ending Hussite heresy through genuine reform, exposing Bohemian noble theft, and redirecting Christendom against the Ottoman threat, genuinely inspiring the Pope while prompting serious discussion of the theological and logistical obstacles ahead.

### Encounter 4: `evt_1433_00014` — Sequential Strategy Discussion
- **type:** `diplomatic_proposal`
- **date:** `1433-04-25`
- **location:** `"Rome, Vatican Private Chamber"`
- **participants:** `["juan_ii", "eugenius_iv", "giordano_orsini"]`
- **roll:** `{"table_id": "roll_ch2_2_003", "value": 41, "outcome": "Questioning - Probes Assumptions"}`
- **What happens:** Juan proposes resolving the Hussite question first, then turning to the Ottomans. The Pope questions each step's feasibility: Bohemian nobles defeated five crusades, Hussite resolution has eluded the Church for 18 years, Constantinople may not have time to wait. Demands specifics on actual plans.
- **Source lines:** ~357–448
- **recap:** Juan proposes a sequential strategy of resolving the Hussite conflict before aiding Constantinople, but the Pope probes hard on the feasibility of each step, demanding specifics about military enforcement and timelines.

### Encounter 5: `evt_1433_00015` — Juan's Humility and Personal Revelation
- **type:** `diplomatic_proposal`
- **date:** `1433-04-25`
- **location:** `"Rome, Vatican Private Chamber"`
- **participants:** `["juan_ii", "eugenius_iv", "giordano_orsini"]`
- **roll:** `{"table_id": "roll_ch2_2_004", "value": 92, "outcome": "Profound Trust"}`
- **What happens:** Juan admits his limitations, acknowledges he cannot march to Bohemia without the Emperor's support, reveals Isabel is pregnant and he must return home for the birth. The Pope is profoundly moved. The testing ends and shifts to partnership: the Pope offers letters of introduction, strategic advice, and complete trust. Discussion of timing (leave before Emperor arrives), logistics (50 crusaders travel with Juan, 750 remain at San Paolo fuori le Mura near Rome), Juan's approach to the Byzantine delegation (listen to fears first).
- **Source lines:** ~449–621
- **recap:** Juan reveals his limitations and promise to return to his pregnant wife, profoundly moving the Pope, who shifts from testing to full partnership and offers letters of introduction, strategic counsel, and complete trust for Juan's journey to Basel.

### Encounter 6: `evt_1433_00016` — Journey North from Rome
- **type:** `military_action`
- **date:** `1433-04-27`
- **end_date:** `1433-05-13`
- **location:** `"Rome to Trent, Alpine Road"`
- **participants:** `["juan_ii", "fernan_alonso_de_robles", "marco_tornesi", "brother_guillem"]`
- **roll:** `null`
- **What happens:** Juan departs Rome with 50 crusaders, traveling through Tuscany, past Florence, through Bologna, into the Alpine foothills. Five weeks of travel condensed into narrative summary.
- **Source lines:** ~623–677
- **recap:** Juan and fifty crusaders depart Rome and travel north through Italy toward Basel, carrying papal letters of introduction and safe conduct.

### Encounter 7: `evt_1433_00017` — Sigismund's Letter Exchange
- **type:** `diplomatic_proposal`
- **date:** `1433-05-14`
- **end_date:** `1433-05-15`
- **location:** `"Trent, Inn"`
- **participants:** `["juan_ii", "sigismund", "fernan_alonso_de_robles"]`
- **roll:** `{"table_id": "roll_ch2_2_005", "value": 42, "outcome": "Message Exchange Only"}`
- **What happens:** Juan's riders locate Sigismund near Verona. The Emperor cannot delay his journey to Rome for coronation, but sends a detailed letter with counsel on Bohemia: warns that Bohemian nobles are not monolithic, that Hussite military tactics humbled traditional cavalry, and urges Juan to meet him at Basel. Juan writes a respectful reply acknowledging the Emperor's superior experience, requesting free passage conditionally, and mentioning his pregnant wife.
- **Source lines:** ~638–728
- **recap:** Juan's riders intercept Emperor Sigismund near Verona, resulting in a substantive letter exchange where the Emperor offers detailed counsel on Bohemia and promises to seek Juan out personally at Basel.

### Encounter 8: `evt_1433_00018` — Sigismund's Enthusiastic Reply
- **type:** `diplomatic_proposal`
- **date:** `1433-05-20`
- **location:** `"Zurich, Road"`
- **participants:** `["juan_ii", "sigismund", "fernan_alonso_de_robles", "marco_tornesi", "brother_guillem"]`
- **roll:** `{"table_id": "roll_ch2_2_006", "value": 97, "outcome": "Strong Preliminary Endorsement"}`
- **What happens:** Sigismund writes back personally (not through a secretary). He is deeply impressed—recognizes Juan as different from other kings. Will not grant blanket free passage, but invites detailed discussion at Basel. The P.S. about daughters is warmly personal. Captain Robles and others note this is a soldier's letter to a soldier.
- **Source lines:** ~789–834
- **recap:** Emperor Sigismund sends a remarkably personal reply recognizing Juan as a potential true ally, offering conditional support and promising to seek him out at Basel for substantive strategic discussions.

### Encounter 9: `evt_1433_00019` — Arrival at Basel
- **type:** `ceremony`
- **date:** `1433-05-28`
- **location:** `"Basel, City Gates"`
- **participants:** `["juan_ii", "fernan_alonso_de_robles", "bessarion", "isidore", "rodrigo_gonzalez", "alfonso_de_cartagena"]`
- **roll:** `{"table_id": "roll_ch2_2_007", "value": 43, "outcome": "Neutral Reception"}`
- **What happens:** Juan arrives at Basel. The Byzantine delegation (Bessarion and Isidore) comes to the gates first, asking direct questions about his intentions. Juan deflects — tells them these matters require private discussion, gives a brief public address to all delegations, and asks people to schedule meetings through his commanders. The reception is neutral: no enemies made, but no friends either. Brother Guillem is sent after the Byzantines to clarify that his brevity was discretion, not dismissal.
- **Source lines:** ~835–980
- **recap:** Juan arrives at Basel to a neutral reception; the Byzantine delegation greets him at the gates with urgent questions, but Juan deflects to private meetings, making no enemies but no friends in his cautious public debut.

### Encounter 10: `evt_1433_00020` — Confession with Fray Hernando
- **type:** `religious_event`
- **date:** `1433-05-28`
- **location:** `"Basel, Merchant's House, Private Study"`
- **participants:** `["juan_ii", "hernando_de_talavera"]`
- **roll:** `{"table_id": "roll_ch2_2_008", "value": 6, "outcome": "Devastating Alarm"}`
- **What happens:** Juan confesses to Fray Hernando. He admits pride, ambition, mixed motives regarding Naples, and guilt about pressing Isabel for another pregnancy despite the risk. Fray Hernando is devastated (roll 6) — he identifies a pattern of messianic rationalization: Juan uses love for his family to justify continental warfare and uses humility to mask certainty. The confessor denies absolution, saying Juan cannot yet see his own sin. He gives Juan three questions as penance to pray on for three days. Juan begs for guidance and the Fray relents slightly, providing the questions and a daily practice (cathedral prayer each morning before any meetings).
- **Source lines:** ~1017–1547
- **Three questions given as penance:**
  1. What would faithful kingship look like if you only ever ruled Castile?
  2. Are you protecting people as they wish, or as you have decided they need?
  3. If you died tomorrow and God asked why you risked Isabel's life, what would you say?
- **recap:** Juan's confession to Fray Hernando takes a devastating turn when the confessor identifies a dangerous pattern of messianic rationalization in Juan's thinking, denying absolution and assigning three soul-searching questions as penance.

### Encounter 11: `evt_1433_00021` — Prayer with Abbott Rodrigo
- **type:** `religious_event`
- **date:** `1433-05-28`
- **location:** `"Basel, Merchant's House, Private Study"`
- **participants:** `["juan_ii", "rodrigo_gonzalez"]`
- **roll:** `null`
- **What happens:** Juan asks Abbott Rodrigo to pray with him before discussing Council business. The elderly Abbott leads them in prayer for wisdom, humility, and guidance. Juan prays privately for Isabel's safe delivery. The chapter ends with them rising from prayer, ready to discuss Basel's political landscape, but with Fray Hernando's three questions weighing on Juan's soul.
- **Source lines:** ~1548–1677
- **recap:** Juan and Abbott Rodrigo share a moment of prayer, asking God for wisdom and guidance, before preparing to discuss the Council's political landscape, closing the chapter with Fray Hernando's unanswered questions weighing heavily on Juan's soul.

---

## How to Handle the Source Text

The source file `chapter2.txt` (1787 lines) is a raw chat transcript from a roleplay session. It contains:

1. **Narrator/GM text** → Use as `"speaker": "narrator"` exchanges
2. **Character dialogue** (in quotes or spoken text) → Use as `"speaker": "character_id"` exchanges
3. **Player input** (Juan's actions/speech, written informally) → Rewrite as proper dialogue for `"speaker": "juan_ii"` OR as narrator text describing his actions
4. **GM meta-commentary** (d100 tables, analysis, roll results, dates) → **SKIP THESE.** Do not include table definitions, success/failure analysis, "Show more" markers, or real-world dates (e.g., "14 nov 2025") in the JSON.
5. **"read NPC guide.md" / "Draft a d100 table"** → Player instructions to the GM. **SKIP THESE.**

### Key Rule for Exchanges

- Include the substantive narrative and dialogue. Condense where needed but preserve the story.
- Each exchange should be a coherent paragraph or speech.
- Narrator exchanges cover scene descriptions, actions, transitions.
- Character exchanges are dialogue only.
- Juan's informal player input should be cleaned up into proper dialogue or narrated action. For example:
  - Player wrote: `"Of course father. Thank you for explaining it to me"`
  - JSON should be: `{"speaker": "juan_ii", "text": "Of course, Holy Father. Thank you for explaining it to me. I was merely inquiring, not seeking to pressure your person in any direction."}`

---

## Git Instructions

1. Branch: `claude/convert-chapter2-json-YC3L8` (should already be checked out)
2. File path: `resources/data/chapter_02_02.json`
3. Commit message: `Add chapter 2.2 (Strategic Counsel) JSON conversion`
4. Push: `git push -u origin claude/convert-chapter2-json-YC3L8`

---

## Checklist

```
[ ] Read chapter2.txt (4 parallel reads)
[ ] Read reference JSON (git show remotes/origin/claude/convert-chapter-to-json-DYLts:resources/data/chapter_02_01.json | head -80)
[ ] Write resources/data/chapter_02_02.json in ONE Write call
[ ] git add resources/data/chapter_02_02.json
[ ] git commit
[ ] git push -u origin claude/convert-chapter2-json-YC3L8
```

**Total time target: Just do it. No planning. No reporting. Read, write, commit, push.**
