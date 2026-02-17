# CLAUDE.md — Project Instructions for Claude Code

## Project Overview
Godot 4.x (GDScript) historical simulation game — "Castile 1430". The player takes the role of Juan II of Castile. The app uses the Anthropic API for narrative generation, Stability AI for portrait generation, and a JSON-based data system for characters, events, economy, and laws.

## Git Rules (MANDATORY)

### 1. Always start from `origin/main`
Before writing ANY code, run:
```
git fetch origin main
git log --oneline -3 origin/main
```
Verify you know what the current state of `main` is. NEVER trust local `master` — it may be stale.

### 2. Feature branches fork from `origin/main`
```
git checkout -b <branch-name> origin/main
```
NEVER branch from local `master` or from another feature branch unless explicitly told to.

### 3. Verify your base before starting work
After creating or checking out your branch, confirm:
```
git log --oneline -5 HEAD
```
The top commits should match `origin/main` (plus any new work). If you see commits from old sessions (api_logger.gd, context_agent.gd, session_recorder.gd, event_diagnostics.gd, profile_manager.gd) — STOP. You are on the wrong base.

### 4. Merge back to main before declaring work complete
After pushing to a feature branch, the work is NOT available to the user until it reaches `origin/main`. Before telling the user their code is ready:
1. Merge the feature branch into main: `git checkout main && git merge <branch-name>`
2. Push main: `git push origin main`
3. Verify the push succeeded and the commit hash matches

**Never confirm "up to date" or "work is done" without verifying the commits are on `origin/main`.** If the user asks "how to pull" after you pushed to a feature branch, that is a signal you forgot to merge.

### 5. No stale branches
When work is merged to main, the feature branch should be deleted. Do not leave old branches around.

### 6. Local `master` is unreliable
The local `master` branch may be behind `origin/main` by dozens of commits. Always use `origin/main` as the reference, never local `master`.

## Architecture

### Scripts (res://scripts/)
- `main.gd` — Application controller, wires all subsystems, two-call flow orchestration
- `data_manager.gd` — JSON file I/O for all game data (class_name: DataManager)
- `game_state_manager.gd` — Campaign state, characters, events, economy
- `api_client.gd` — Anthropic API communication (Sonnet for GM calls)
- `prompt_assembler.gd` — Builds 4-layer prompts from game state + history + profile + sticky context
- `prompt_retry_manager.gd` — Two-call orchestrator: ContextAgent → GM, with retry logic
- `context_agent.gd` — Call 1: Haiku-based context routing + local search engine (class_name: ContextAgent)
- `sticky_context.gd` — Token-budgeted memory system across exchanges (class_name: StickyContext)
- `profile_manager.gd` — Juan II profile management, refreshed every 8 events (class_name: ProfileManager)
- `api_logger.gd` — Per-call cost/usage tracking with Sonnet+Haiku pricing (class_name: ApiLogger)
- `session_recorder.gd` — Full exchange recording for debugging (class_name: SessionRecorder)
- `event_diagnostics.gd` — Per-event statistics tracking (class_name: EventDiagnostics)
- `conversation_buffer.gd` — Manages conversation history (rolling 8-exchange window)
- `roll_engine.gd` — d100 dice roll system
- `portrait_manager.gd` — Stability AI portrait generation + caching (class_name: PortraitManager)
- `portrait_prompt_builder.gd` — Builds Stability AI prompts from appearance data
- `response_parser.gd` — Parses structured API responses and metadata
- `chat_panel.gd` — Narrative display with inline portrait support
- `header_bar.gd` — Location, date, characters display
- `settings_screen.gd` — API key config, campaign management
- `debug_panel.gd` — Debug prompt viewer
- `characters_panel.gd` — Characters browser tab (search, categories, detail view)
- `laws_panel.gd` — Laws browser tab (placeholder)

### Scene tree (scenes/main.tscn)
```
Main (Control)
├── DataManager, GameStateManager, ApiClient, PromptAssembler,
│   ConversationBuffer, RollEngine, PromptRetryManager, PortraitManager
├── ContextAgent, StickyContext, ProfileManager, ApiLogger,
│   SessionRecorder, EventDiagnostics
├── Layout (VBoxContainer)
│   ├── HeaderBar (PanelContainer)
│   ├── TabBar — [Narrative, Characters, Laws]
│   ├── ContentArea (HBoxContainer) — contains ChatPanel
│   ├── CharactersPanel (Control) — hidden by default
│   └── LawsPanel (Control) — hidden by default
├── SettingsScreen (PanelContainer) — overlay
└── DebugPanel (PanelContainer) — overlay, hidden by default
```

### Resources
- `resources/fonts/` — Cinzel.ttf (headers), Almendra-Regular.ttf, Almendra-Bold.ttf (body)
- `resources/images/` — Optional parchment.png background texture
- `resources/gm_prompts/` — GM prompt templates (layer1_gm_guidelines.txt, layer2_*.txt, etc.)
- `resources/data/` — Bundled starter data (characters.json, starter_events.json)
- `game_data/` — JSON reference data (characters, chapters, etc.)

### Key patterns
- Dependencies are wired in `main.gd._ready()` via property injection (not signals or autoload)
- Fonts are loaded at startup in `_load_fonts()` and passed to panels
- Tab switching toggles visibility of ContentArea vs CharactersPanel vs LawsPanel
- Campaign data is stored in `user://save_data/<campaign_name>/`
- Portrait textures are cached in memory and persisted to `portraits/<character_id>/`

## Two-Call Architecture
Every player input triggers two API calls:
1. **Call 1 — ContextAgent (Haiku):** Cheap call to `claude-haiku-4-5-20251001` that determines which characters, events, and laws the GM needs. Returns search queries executed locally.
2. **Call 2 — Main GM (Sonnet):** Full narrative call to `claude-sonnet-4-5-20250929` with 4-layer prompt (Guidelines → Call Type → Juan Profile → Scene Context).

Roll results skip Call 1 entirely and go straight to Call 2.

### Prompt Layers
- **Layer 1:** GM Guidelines (`layer1_gm_guidelines.txt`) — static, cached
- **Layer 2:** Call-type template (medieval_norms, persuasion, chaos, etc.) — cached
- **Layer 3:** Juan II Profile (refreshed every 8 events via Haiku) — cached
- **Layer 4:** Scene Context (date, location, sticky context, last 10 events, summary) — dynamic

### Sticky Context
- Token budget: 3000 tokens (4 chars = 1 token)
- Clears on: overflow, location change, session start
- Stores: characters (max 4), events (max 6), laws (max 3) from ContextAgent searches
