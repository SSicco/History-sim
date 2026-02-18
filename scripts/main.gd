## Main application controller.
## Orchestrates all subsystems: game state, API communication, UI, and data persistence.
## Implements the two-call architecture: ContextAgent (Haiku) → GM (Sonnet).
extends Control

@onready var data_manager: DataManager = $DataManager
@onready var game_state: GameStateManager = $GameStateManager
@onready var api_client: ApiClient = $ApiClient
@onready var prompt_assembler: PromptAssembler = $PromptAssembler
@onready var conversation_buffer: ConversationBuffer = $ConversationBuffer
@onready var roll_engine: RollEngine = $RollEngine
@onready var retry_manager: PromptRetryManager = $PromptRetryManager
@onready var portrait_manager: PortraitManager = $PortraitManager

## New prompt engine subsystems
@onready var context_agent: ContextAgent = $ContextAgent
@onready var sticky_context: StickyContext = $StickyContext
@onready var profile_manager: ProfileManager = $ProfileManager
@onready var api_logger: ApiLogger = $ApiLogger
@onready var session_recorder: SessionRecorder = $SessionRecorder
@onready var event_diagnostics: EventDiagnostics = $EventDiagnostics

@onready var header_bar: PanelContainer = $Layout/HeaderBar
@onready var tab_bar: TabBar = %TabBar
@onready var content_area: HBoxContainer = $Layout/ContentArea
@onready var chat_panel: VBoxContainer = $Layout/ContentArea/ChatPanel
@onready var characters_panel: Control = $Layout/CharactersPanel
@onready var laws_panel: Control = $Layout/LawsPanel
@onready var engine_eval_panel: Control = $Layout/EngineEvalPanel
@onready var settings_screen: PanelContainer = $SettingsScreen
@onready var debug_panel: PanelContainer = $DebugPanel

var _campaign_loaded: bool = false
var _last_player_input: String = ""

const DEFAULT_CAMPAIGN := "castile_1430"

## Loaded font resources for medieval UI styling.
var _font_cinzel: Font
var _font_almendra: Font
var _font_almendra_bold: Font


func _ready() -> void:
	# Load medieval fonts
	_load_fonts()

	# Wire up core dependencies
	game_state.data_manager = data_manager
	api_client.data_manager = data_manager
	prompt_assembler.game_state = game_state
	prompt_assembler.conversation_buffer = conversation_buffer
	prompt_assembler.data_manager = data_manager
	conversation_buffer.data_manager = data_manager
	roll_engine.data_manager = data_manager
	roll_engine.game_state = game_state
	header_bar.game_state = game_state
	chat_panel.game_state = game_state
	portrait_manager.data_manager = data_manager

	# Wire portrait manager to chat panel
	chat_panel.portrait_manager = portrait_manager

	# Wire new prompt engine subsystems
	context_agent.data_manager = data_manager
	context_agent.api_logger = api_logger
	# StickyContext is self-contained (no dependencies to wire)
	profile_manager.data_manager = data_manager
	profile_manager.context_agent = context_agent
	api_logger.data_manager = data_manager
	session_recorder.data_manager = data_manager
	event_diagnostics.data_manager = data_manager

	# Wire subsystems into PromptAssembler
	prompt_assembler.sticky_context = sticky_context
	prompt_assembler.profile_manager = profile_manager

	# Wire retry manager dependencies (core + new subsystems)
	retry_manager.api_client = api_client
	retry_manager.prompt_assembler = prompt_assembler
	retry_manager.game_state = game_state
	retry_manager.data_manager = data_manager
	retry_manager.context_agent = context_agent
	retry_manager.sticky_context = sticky_context
	retry_manager.session_recorder = session_recorder
	retry_manager.event_diagnostics = event_diagnostics
	retry_manager.api_logger = api_logger
	retry_manager.connect_signals()

	# Wire up panels
	characters_panel.data_manager = data_manager
	characters_panel.portrait_manager = portrait_manager
	characters_panel.font_cinzel = _font_cinzel
	characters_panel.font_almendra = _font_almendra
	characters_panel.font_almendra_bold = _font_almendra_bold

	laws_panel.data_manager = data_manager
	laws_panel.font_cinzel = _font_cinzel
	laws_panel.font_almendra = _font_almendra

	engine_eval_panel.data_manager = data_manager
	engine_eval_panel.api_logger = api_logger
	engine_eval_panel.event_diagnostics = event_diagnostics
	engine_eval_panel.sticky_context = sticky_context
	engine_eval_panel.profile_manager = profile_manager
	engine_eval_panel.font_cinzel = _font_cinzel
	engine_eval_panel.font_almendra = _font_almendra

	settings_screen.data_manager = data_manager
	settings_screen.api_client = api_client
	settings_screen.portrait_manager = portrait_manager

	debug_panel.prompt_assembler = prompt_assembler
	debug_panel.game_state = game_state
	debug_panel.conversation_buffer = conversation_buffer
	debug_panel.api_client = api_client
	debug_panel.retry_manager = retry_manager

	# Connect signals — route through retry_manager instead of api_client directly
	chat_panel.message_submitted.connect(_on_player_message)
	chat_panel.roll_submitted.connect(_on_roll_submitted)
	retry_manager.response_ready.connect(_on_api_response)
	retry_manager.processing_started.connect(_on_api_request_started)
	retry_manager.processing_failed.connect(_on_api_request_failed)
	retry_manager.status_update.connect(_on_retry_status_update)
	settings_screen.settings_closed.connect(_on_settings_closed)
	settings_screen.campaign_loaded.connect(_on_load_campaign)
	settings_screen.campaign_reset_requested.connect(_on_campaign_reset)
	settings_screen.test_mode_toggled.connect(_on_test_mode_toggled)
	header_bar.settings_requested.connect(_show_settings)
	header_bar.debug_requested.connect(_toggle_debug_panel)

	# Portrait manager signals
	portrait_manager.portrait_ready.connect(_on_portrait_ready)
	portrait_manager.portrait_failed.connect(_on_portrait_failed)

	# Sticky context signals — handle event boundaries
	sticky_context.context_overflow.connect(_on_sticky_overflow)

	# Profile refresh signals
	context_agent.profile_refreshed.connect(_on_profile_refreshed)

	# Location change signal — clears sticky context
	game_state.location_changed.connect(_on_location_changed)

	# Style and connect the tab bar
	_style_tab_bar()
	tab_bar.tab_changed.connect(_on_tab_changed)

	# Apply fonts to header bar
	_apply_header_fonts()

	# Restore test mode from config
	var config = data_manager.load_config()
	if config != null and config.get("test_mode", false):
		data_manager.test_mode = true
		header_bar.set_test_mode(true)

	# Check if we have a configured API key — go straight to gameplay
	if config == null or config.get("api_key", "") == "":
		# No API key — settings screen is unavoidable
		_show_settings()
	elif config.has("last_campaign") and config["last_campaign"] != "":
		# Resume where we left off
		_try_load_campaign(config["last_campaign"])
	else:
		# API key exists but no campaign — auto-create and start playing
		_auto_create_default_campaign()


func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if settings_screen.visible:
			_on_settings_closed()
		else:
			_show_settings()
	elif event is InputEventKey and event.pressed:
		if event.keycode == KEY_F12:
			_toggle_debug_panel()
		elif event.ctrl_pressed and event.keycode == KEY_S:
			_quick_save()


func _show_settings() -> void:
	settings_screen.visible = true


func _on_settings_closed() -> void:
	if not _campaign_loaded:
		# No campaign yet — auto-create one if API key is now configured
		if api_client.is_configured():
			_auto_create_default_campaign()
		return
	settings_screen.visible = false


func _auto_create_default_campaign() -> void:
	# Check if default campaign already exists — if so, load it instead
	var campaigns := data_manager.list_campaigns()
	if campaigns.has(DEFAULT_CAMPAIGN):
		_try_load_campaign(DEFAULT_CAMPAIGN)
		return

	game_state.initialize_new_campaign(DEFAULT_CAMPAIGN)

	# Save last campaign in config
	var config = data_manager.load_config()
	if config == null:
		config = {}
	config["last_campaign"] = DEFAULT_CAMPAIGN
	data_manager.save_config(config)

	_initialize_campaign_subsystems()

	_campaign_loaded = true
	settings_screen.visible = false
	chat_panel.clear_display()
	chat_panel.append_narrative("Campaign initialized. %s — %s\n\nType your first action or describe the opening scene." % [
		game_state.current_location, _format_date_short(game_state.current_date)
	])

	# Refresh browse panels
	characters_panel.refresh()
	laws_panel.refresh()


func _on_load_campaign(campaign_name: String) -> void:
	_try_load_campaign(campaign_name)


func _try_load_campaign(campaign_name: String) -> void:
	if game_state.load_campaign(campaign_name):
		conversation_buffer.initialize(
			game_state.current_date,
			game_state.current_location
		)

		# Save as last campaign
		var config = data_manager.load_config()
		if config == null:
			config = {}
		config["last_campaign"] = campaign_name
		data_manager.save_config(config)

		# Load portrait metadata and clear texture cache for new campaign
		portrait_manager.clear_cache()
		portrait_manager.load_portraits_meta()

		# Initialize prompt engine subsystems
		_initialize_campaign_subsystems()

		_campaign_loaded = true
		settings_screen.visible = false

		# Refresh browse panels
		characters_panel.refresh()
		laws_panel.refresh()

		# Restore conversation display
		chat_panel.clear_display()
		var exchanges := conversation_buffer.get_all_exchanges()
		for exchange in exchanges:
			chat_panel.append_narrative(
				"[color=#7eb8da][b]Juan II:[/b] %s[/color]" % exchange.get("player_input", "")
			)
			chat_panel.append_narrative(exchange.get("gm_response", ""))

		if exchanges.is_empty():
			chat_panel.append_narrative("Campaign loaded. %s — %s" % [
				game_state.current_location,
				_format_date_short(game_state.current_date),
			])
	else:
		push_warning("Failed to load campaign '%s', creating default." % campaign_name)
		_auto_create_default_campaign()


func _on_campaign_reset() -> void:
	# Wipe the current campaign data and re-initialize from bundled starter data
	data_manager.campaign_name = DEFAULT_CAMPAIGN
	data_manager.delete_campaign_data()
	game_state.initialize_new_campaign(DEFAULT_CAMPAIGN)

	var config = data_manager.load_config()
	if config == null:
		config = {}
	config["last_campaign"] = DEFAULT_CAMPAIGN
	data_manager.save_config(config)

	_initialize_campaign_subsystems()

	_campaign_loaded = true
	chat_panel.clear_display()
	chat_panel.append_narrative("Campaign reset. %s — %s\n\nAll test data cleared. Type your first action." % [
		game_state.current_location, _format_date_short(game_state.current_date)
	])

	characters_panel.refresh()
	laws_panel.refresh()


func _on_test_mode_toggled(enabled: bool) -> void:
	data_manager.set_test_mode(enabled)
	header_bar.set_test_mode(enabled)

	if enabled:
		# Initialize test data directory with copies of current real data
		data_manager.ensure_campaign_dirs()
		# Copy essential files from real campaign to test dir if they don't exist
		var test_state = data_manager.load_json("game_state.json")
		if test_state == null:
			# First time entering test mode — copy real state
			var was_test := data_manager.test_mode
			data_manager.test_mode = false
			var real_state = data_manager.load_json("game_state.json")
			var real_events = data_manager.load_json("events.json")
			var real_chars = data_manager.load_json("characters.json")
			var real_active = data_manager.load_json("active_event.json")
			data_manager.test_mode = was_test

			if real_state != null:
				data_manager.save_json("game_state.json", real_state)
			if real_events != null:
				data_manager.save_json("events.json", real_events)
			if real_chars != null:
				data_manager.save_json("characters.json", real_chars)
			if real_active != null:
				data_manager.save_json("active_event.json", real_active)

	# Reload campaign in the new mode
	_try_load_campaign(DEFAULT_CAMPAIGN)
	chat_panel._append_system_text("Test mode %s." % ("enabled" if enabled else "disabled"))


## Initializes prompt engine subsystems for the current campaign.
func _initialize_campaign_subsystems() -> void:
	# Sync API key to context agent
	var config = data_manager.load_config()
	if config != null:
		context_agent.api_key = config.get("api_key", "")

	# Load/initialize profile
	profile_manager.load_profile()

	# Load portrait metadata
	portrait_manager.load_portraits_meta()

	# Reset sticky context and diagnostics
	sticky_context.clear()
	api_logger.reset_session()
	event_diagnostics.begin_event()


func _on_player_message(text: String) -> void:
	if not api_client.is_configured():
		chat_panel.show_error("API key not configured. Press Escape to open Settings.")
		return

	# Ensure context agent has API key
	if context_agent.api_key == "":
		var config = data_manager.load_config()
		if config != null:
			context_agent.api_key = config.get("api_key", "")

	_last_player_input = text
	retry_manager.handle_player_input(text)


func _on_roll_submitted(value: int) -> void:
	roll_engine.submit_roll(str(value))

	# Send the roll result through the retry manager
	var roll_message := "d100 roll result: %d" % value
	_last_player_input = roll_message
	retry_manager.handle_player_input(roll_message)


func _on_api_request_started() -> void:
	chat_panel.set_waiting(true)


func _on_api_response(narrative: String, metadata: Dictionary) -> void:
	chat_panel.set_waiting(false)

	# Extract dialogue metadata for portrait display
	var dialogue: Array = ResponseParser.get_dialogue_speakers(metadata)

	# Display the narrative with portrait support
	chat_panel.append_narrative(narrative, dialogue)

	# Update game state from metadata (includes event auto-logging)
	game_state.update_from_metadata(metadata)

	# Update conversation buffer context
	conversation_buffer.set_scene_context(
		game_state.current_date,
		game_state.current_location,
		game_state.scene_characters
	)

	# Archive the exchange
	conversation_buffer.add_exchange(_last_player_input, narrative, metadata)

	# Check if profile refresh needed (every 8 events)
	if metadata.has("events") and metadata["events"] is Array:
		profile_manager.on_events_logged(metadata["events"].size())

	# Auto-save
	game_state.save_game_state()


func _on_api_request_failed(error_message: String) -> void:
	chat_panel.set_waiting(false)
	chat_panel.show_error(error_message)


func _on_retry_status_update(message: String) -> void:
	chat_panel.set_thinking_text(message)


func _on_portrait_ready(character_id: String, _texture: ImageTexture) -> void:
	chat_panel._append_system_text("Portrait generated for %s." % portrait_manager.get_character_name(character_id))


func _on_portrait_failed(character_id: String, error_msg: String) -> void:
	push_warning("Portrait generation failed for %s: %s" % [character_id, error_msg])


# ─── Event Boundary Handlers ────────────────────────────────────────────

func _on_sticky_overflow() -> void:
	chat_panel._append_system_text("[New event — context reset]")
	event_diagnostics.end_event("overflow")
	event_diagnostics.begin_event()


func _on_location_changed(_new_location: String) -> void:
	sticky_context.clear()
	event_diagnostics.end_event("location_change")
	event_diagnostics.begin_event()


func _on_profile_refreshed(profile_text: String) -> void:
	profile_manager.apply_refresh(profile_text)


# ─── Tab Navigation ──────────────────────────────────────────────────────────

func _on_tab_changed(tab_index: int) -> void:
	content_area.visible = (tab_index == 0)
	characters_panel.visible = (tab_index == 1)
	laws_panel.visible = (tab_index == 2)
	engine_eval_panel.visible = (tab_index == 3)

	# Auto-refresh the engine eval panel when switching to it
	if tab_index == 3:
		engine_eval_panel.refresh()


# ─── Font Loading ────────────────────────────────────────────────────────────

func _load_fonts() -> void:
	var cinzel_path := "res://resources/fonts/Cinzel.ttf"
	var almendra_path := "res://resources/fonts/Almendra-Regular.ttf"
	var almendra_bold_path := "res://resources/fonts/Almendra-Bold.ttf"

	if ResourceLoader.exists(cinzel_path):
		_font_cinzel = load(cinzel_path)
	if ResourceLoader.exists(almendra_path):
		_font_almendra = load(almendra_path)
	if ResourceLoader.exists(almendra_bold_path):
		_font_almendra_bold = load(almendra_bold_path)


func _style_tab_bar() -> void:
	if _font_cinzel:
		tab_bar.add_theme_font_override("font", _font_cinzel)
	tab_bar.add_theme_font_size_override("font_size", 14)
	tab_bar.add_theme_color_override("font_selected_color", Color(0.95, 0.90, 0.78, 1.0))
	tab_bar.add_theme_color_override("font_unselected_color", Color(0.6, 0.55, 0.48, 1.0))
	tab_bar.add_theme_color_override("font_hovered_color", Color(0.85, 0.78, 0.65, 1.0))


func _apply_header_fonts() -> void:
	if _font_cinzel == null:
		return
	for node in header_bar.get_node("MarginContainer/HBoxContainer").get_children():
		if node is Label:
			node.add_theme_font_override("font", _font_cinzel)
		elif node is Button:
			node.add_theme_font_override("font", _font_cinzel)


func _toggle_debug_panel() -> void:
	if debug_panel.visible:
		debug_panel.visible = false
	else:
		debug_panel.show_prompt()


func _quick_save() -> void:
	if _campaign_loaded:
		game_state.save_game_state()
		chat_panel._append_system_text("Game saved.")


## Formats a date string for display in system messages.
func _format_date_short(iso_date: String) -> String:
	var parts := iso_date.split("-")
	if parts.size() != 3:
		return iso_date
	return "%s/%s/%s" % [parts[2], parts[1], parts[0]]
