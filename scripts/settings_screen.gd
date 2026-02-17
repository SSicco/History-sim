## Settings screen for API key entry, model selection, test mode, and campaign management.
extends PanelContainer

signal settings_closed
signal campaign_loaded(campaign_name: String)
signal campaign_reset_requested
signal test_mode_toggled(enabled: bool)

@export var data_manager: DataManager
@export var api_client: ApiClient

## Set by main.gd for portrait API key management
var portrait_manager: PortraitManager

@onready var api_key_input: LineEdit = %ApiKeyInput
@onready var model_option: OptionButton = %ModelOption
@onready var openai_key_input: LineEdit = %OpenAIKeyInput
@onready var save_settings_button: Button = %SaveSettingsButton
@onready var status_label: Label = %StatusLabel
@onready var campaign_list: ItemList = %CampaignList
@onready var load_campaign_button: Button = %LoadCampaignButton
@onready var close_button: Button = %CloseButton
@onready var test_mode_check: CheckButton = %TestModeCheck
@onready var clear_test_button: Button = %ClearTestButton
@onready var reset_campaign_button: Button = %ResetCampaignButton

const MODELS := [
	["claude-sonnet-4-5-20250929", "Claude Sonnet 4.5 (Recommended)"],
	["claude-sonnet-4-20250514", "Claude Sonnet 4"],
	["claude-opus-4-20250514", "Claude Opus 4"],
	["claude-haiku-4-5-20251001", "Claude Haiku 4.5"],
]


func _ready() -> void:
	save_settings_button.pressed.connect(_on_save_settings)
	load_campaign_button.pressed.connect(_on_load_campaign)
	close_button.pressed.connect(_on_close)
	test_mode_check.toggled.connect(_on_test_mode_toggled)
	clear_test_button.pressed.connect(_on_clear_test_data)
	reset_campaign_button.pressed.connect(_on_reset_campaign)

	# Populate model options
	for m in MODELS:
		model_option.add_item(m[1])

	_load_settings()
	_refresh_campaign_list()


func _load_settings() -> void:
	if data_manager == null:
		return

	var config = data_manager.load_config()
	if config == null:
		return

	var saved_key: String = config.get("api_key", "")
	if saved_key != "":
		# Mask the key for display
		api_key_input.text = saved_key.left(8) + "..." + saved_key.right(4)
		api_key_input.placeholder_text = "API key configured (enter new to replace)"
	else:
		api_key_input.placeholder_text = "sk-ant-..."

	var saved_model: String = config.get("model", MODELS[0][0])
	for i in range(MODELS.size()):
		if MODELS[i][0] == saved_model:
			model_option.selected = i
			break

	# Load Stability AI key
	var saved_stability_key: String = config.get("stability_api_key", config.get("openai_api_key", ""))
	if saved_stability_key != "":
		openai_key_input.text = saved_stability_key.left(8) + "..." + saved_stability_key.right(4)
		openai_key_input.placeholder_text = "Stability AI key configured (enter new to replace)"
	else:
		openai_key_input.placeholder_text = "sk-..."

	# Load test mode state
	test_mode_check.button_pressed = config.get("test_mode", false)


func _on_save_settings() -> void:
	var key_text := api_key_input.text.strip_edges()

	# Only update key if it looks like a new key (not our masked version)
	if key_text != "" and not key_text.contains("..."):
		api_client.api_key = key_text

	var model_idx := model_option.selected
	if model_idx >= 0 and model_idx < MODELS.size():
		api_client.model = MODELS[model_idx][0]

	api_client.save_api_config()

	# Save Stability AI key for portrait generation
	var stability_key_text := openai_key_input.text.strip_edges()
	if stability_key_text != "" and not stability_key_text.contains("...") and portrait_manager != null:
		portrait_manager.stability_api_key = stability_key_text
		portrait_manager.save_api_config()

	status_label.text = "Settings saved."
	# Clear status after a delay
	get_tree().create_timer(3.0).timeout.connect(func(): status_label.text = "")


func _on_load_campaign() -> void:
	var selected := campaign_list.get_selected_items()
	if selected.is_empty():
		status_label.text = "Select a campaign to load."
		return

	var campaign_text: String = campaign_list.get_item_text(selected[0])
	campaign_loaded.emit(campaign_text)


func _on_test_mode_toggled(enabled: bool) -> void:
	test_mode_toggled.emit(enabled)
	if enabled:
		status_label.text = "Test mode enabled. Data writes go to test_data/."
	else:
		status_label.text = "Test mode disabled. Using live data."
	get_tree().create_timer(3.0).timeout.connect(func(): status_label.text = "")


func _on_clear_test_data() -> void:
	if data_manager == null:
		return
	data_manager.delete_test_data()
	status_label.text = "Test data cleared."
	get_tree().create_timer(3.0).timeout.connect(func(): status_label.text = "")


func _on_reset_campaign() -> void:
	campaign_reset_requested.emit()
	status_label.text = "Campaign data reset to starter database."
	get_tree().create_timer(3.0).timeout.connect(func(): status_label.text = "")


func _on_close() -> void:
	settings_closed.emit()


func _refresh_campaign_list() -> void:
	campaign_list.clear()
	if data_manager == null:
		return

	var campaigns := data_manager.list_campaigns()
	for c in campaigns:
		campaign_list.add_item(c)
