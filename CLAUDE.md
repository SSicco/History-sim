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

### 4. No stale branches
When work is merged to main, the feature branch should be deleted. Do not leave old branches around.

### 5. Local `master` is unreliable
The local `master` branch may be behind `origin/main` by dozens of commits. Always use `origin/main` as the reference, never local `master`.

## Architecture

### Scripts (res://scripts/)
- `main.gd` — Application controller, wires all subsystems
- `data_manager.gd` — JSON file I/O for all game data (class_name: DataManager)
- `game_state_manager.gd` — Campaign state, characters, events, economy
- `api_client.gd` — Anthropic API communication
- `prompt_assembler.gd` — Builds prompts from game state + history
- `prompt_retry_manager.gd` — Handles retries and validation of API responses
- `conversation_buffer.gd` — Manages conversation history
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
- `game_data/` — JSON reference data (characters, chapters, etc.)

### Key patterns
- Dependencies are wired in `main.gd._ready()` via property injection (not signals or autoload)
- Fonts are loaded at startup in `_load_fonts()` and passed to panels
- Tab switching toggles visibility of ContentArea vs CharactersPanel vs LawsPanel
- Campaign data is stored in `user://save_data/<campaign_name>/`
- Portrait textures are cached in memory and persisted to `portraits/<character_id>/`

## Scripts that DO NOT exist (and never should)
These were part of an old, divergent branch and are NOT in the real codebase:
- ~~api_logger.gd~~ — Does not exist
- ~~context_agent.gd~~ — Does not exist
- ~~session_recorder.gd~~ — Does not exist
- ~~event_diagnostics.gd~~ — Does not exist
- ~~profile_manager.gd~~ — Does not exist

If you see references to any of these, you are working from an outdated base. Stop and re-read the Git Rules above.
