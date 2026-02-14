## Main application controller.
## Orchestrates all subsystems: game state, API communication, UI, and data persistence.
extends Control

@onready var data_manager: DataManager = $DataManager
@onready var game_state: GameStateManager = $GameStateManager
@onready var api_client: ApiClient = $ApiClient
@onready var prompt_assembler: PromptAssembler = $PromptAssembler
@onready var conversation_buffer: ConversationBuffer = $ConversationBuffer
@onready var roll_engine: RollEngine = $RollEngine
@onready var retry_manager: PromptRetryManager = $PromptRetryManager

@onready var header_bar: PanelContainer = $Layout/HeaderBar
@onready var chat_panel: VBoxContainer = $Layout/ContentArea/ChatPanel
@onready var settings_screen: PanelContainer = $SettingsScreen
@onready var debug_panel: PanelContainer = $DebugPanel

var _campaign_loaded: bool = false
var _last_player_input: String = ""


func _ready() -> void:
	# Wire up dependencies
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

	# Wire retry manager dependencies
	retry_manager.api_client = api_client
	retry_manager.prompt_assembler = prompt_assembler
	retry_manager.game_state = game_state
	retry_manager.data_manager = data_manager
	retry_manager.connect_signals()

	settings_screen.data_manager = data_manager
	settings_screen.api_client = api_client

	debug_panel.prompt_assembler = prompt_assembler
	debug_panel.game_state = game_state
	debug_panel.conversation_buffer = conversation_buffer
	debug_panel.api_client = api_client

	# Connect signals — route through retry_manager instead of api_client directly
	chat_panel.message_submitted.connect(_on_player_message)
	chat_panel.roll_submitted.connect(_on_roll_submitted)
	retry_manager.response_ready.connect(_on_api_response)
	retry_manager.processing_started.connect(_on_api_request_started)
	retry_manager.processing_failed.connect(_on_api_request_failed)
	retry_manager.status_update.connect(_on_retry_status_update)
	settings_screen.settings_closed.connect(_on_settings_closed)
	settings_screen.campaign_started.connect(_on_new_campaign)
	settings_screen.campaign_loaded.connect(_on_load_campaign)
	header_bar.settings_requested.connect(_show_settings)
	header_bar.debug_requested.connect(_toggle_debug_panel)

	# Check if we have a configured API key and campaign
	var config = data_manager.load_config()
	if config == null or config.get("api_key", "") == "":
		_show_settings()
	elif config.has("last_campaign") and config["last_campaign"] != "":
		_try_load_campaign(config["last_campaign"])
	else:
		_show_settings()


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
		# Can't close settings without a campaign loaded
		return
	settings_screen.visible = false


func _on_new_campaign(campaign_name: String) -> void:
	var start_date: String = settings_screen.get_start_date()
	game_state.initialize_new_campaign(campaign_name, start_date, "Valladolid, Royal Palace")
	conversation_buffer.initialize(start_date, "Valladolid, Royal Palace", 1)

	# Save last campaign in config
	var config = data_manager.load_config()
	if config == null:
		config = {}
	config["last_campaign"] = campaign_name
	data_manager.save_config(config)

	_campaign_loaded = true
	settings_screen.visible = false
	chat_panel.clear_display()
	chat_panel.append_narrative("A new campaign begins. The year is %s. You are Juan II of Castile.\n\nType your first action or describe the opening scene." % start_date.left(4))


func _on_load_campaign(campaign_name: String) -> void:
	_try_load_campaign(campaign_name)


func _try_load_campaign(campaign_name: String) -> void:
	if game_state.load_campaign(campaign_name):
		conversation_buffer.initialize(
			game_state.current_date,
			game_state.current_location,
			game_state.current_chapter
		)

		# Save as last campaign
		var config = data_manager.load_config()
		if config == null:
			config = {}
		config["last_campaign"] = campaign_name
		data_manager.save_config(config)

		_campaign_loaded = true
		settings_screen.visible = false

		# Restore conversation display
		chat_panel.clear_display()
		var exchanges := conversation_buffer.get_all_exchanges()
		for exchange in exchanges:
			chat_panel.append_narrative(
				"[color=#7eb8da][b]Juan II:[/b] %s[/color]" % exchange.get("player_input", "")
			)
			chat_panel.append_narrative(exchange.get("gm_response", ""))

		if exchanges.is_empty():
			chat_panel.append_narrative("Campaign loaded. Chapter %d: %s\n\n%s" % [
				game_state.current_chapter,
				game_state.chapter_title,
				game_state.current_location,
			])
	else:
		chat_panel.show_error("Failed to load campaign '%s'." % campaign_name)
		_show_settings()


func _on_player_message(text: String) -> void:
	if not api_client.is_configured():
		chat_panel.show_error("API key not configured. Press Escape to open Settings.")
		return

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

	# Display the narrative
	chat_panel.append_narrative(narrative)

	# Update game state from metadata
	game_state.update_from_metadata(metadata)

	# Update conversation buffer context
	conversation_buffer.set_scene_context(
		game_state.current_date,
		game_state.current_location,
		game_state.current_chapter,
		game_state.scene_characters
	)

	# Archive the exchange
	conversation_buffer.add_exchange(_last_player_input, narrative, metadata)

	# Auto-save
	game_state.save_game_state()


func _on_api_request_failed(error_message: String) -> void:
	chat_panel.set_waiting(false)
	chat_panel.show_error(error_message)


func _on_retry_status_update(message: String) -> void:
	chat_panel.set_thinking_text(message)


func _toggle_debug_panel() -> void:
	if debug_panel.visible:
		debug_panel.visible = false
	else:
		debug_panel.show_prompt()


func _quick_save() -> void:
	if _campaign_loaded:
		game_state.save_game_state()
		chat_panel._append_system_text("Game saved.")
