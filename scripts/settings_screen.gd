## Settings screen for API key entry, model selection, and campaign management.
extends PanelContainer

signal settings_closed
signal campaign_started(campaign_name: String)
signal campaign_loaded(campaign_name: String)

@export var data_manager: DataManager
@export var api_client: ApiClient

@onready var api_key_input: LineEdit = %ApiKeyInput
@onready var model_option: OptionButton = %ModelOption
@onready var save_settings_button: Button = %SaveSettingsButton
@onready var status_label: Label = %StatusLabel
@onready var campaign_name_input: LineEdit = %CampaignNameInput
@onready var new_campaign_button: Button = %NewCampaignButton
@onready var campaign_list: ItemList = %CampaignList
@onready var load_campaign_button: Button = %LoadCampaignButton
@onready var close_button: Button = %CloseButton
@onready var start_date_input: LineEdit = %StartDateInput

const MODELS := [
	["claude-sonnet-4-5-20250514", "Claude Sonnet 4.5 (Recommended)"],
	["claude-sonnet-4-20250514", "Claude Sonnet 4"],
	["claude-opus-4-20250514", "Claude Opus 4"],
	["claude-haiku-4-5-20250929", "Claude Haiku 4.5"],
]


func _ready() -> void:
	save_settings_button.pressed.connect(_on_save_settings)
	new_campaign_button.pressed.connect(_on_new_campaign)
	load_campaign_button.pressed.connect(_on_load_campaign)
	close_button.pressed.connect(_on_close)

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

	var saved_date: String = config.get("default_start_date", "1430-01-01")
	start_date_input.text = saved_date


func _on_save_settings() -> void:
	var key_text := api_key_input.text.strip_edges()

	# Only update key if it looks like a new key (not our masked version)
	if key_text != "" and not key_text.contains("..."):
		api_client.api_key = key_text

	var model_idx := model_option.selected
	if model_idx >= 0 and model_idx < MODELS.size():
		api_client.model = MODELS[model_idx][0]

	api_client.save_api_config()

	status_label.text = "Settings saved."
	# Clear status after a delay
	get_tree().create_timer(3.0).timeout.connect(func(): status_label.text = "")


func _on_new_campaign() -> void:
	var name := campaign_name_input.text.strip_edges()
	if name == "":
		status_label.text = "Please enter a campaign name."
		return

	# Sanitize name for filesystem
	var safe_name := name.replace(" ", "_").to_lower()
	for ch in [".", "/", "\\", ":", "*", "?", "\"", "<", ">", "|"]:
		safe_name = safe_name.replace(ch, "")

	if safe_name == "":
		status_label.text = "Invalid campaign name."
		return

	var start_date := start_date_input.text.strip_edges()
	if start_date == "":
		start_date = "1430-01-01"

	campaign_started.emit(safe_name)
	_refresh_campaign_list()


func _on_load_campaign() -> void:
	var selected := campaign_list.get_selected_items()
	if selected.is_empty():
		status_label.text = "Select a campaign to load."
		return

	var name := campaign_list.get_item_text(selected[0])
	campaign_loaded.emit(name)


func _on_close() -> void:
	settings_closed.emit()


func _refresh_campaign_list() -> void:
	campaign_list.clear()
	if data_manager == null:
		return

	var campaigns := data_manager.list_campaigns()
	for c in campaigns:
		campaign_list.add_item(c)


func get_start_date() -> String:
	var date: String = start_date_input.text.strip_edges()
	if date == "":
		return "1430-01-01"
	return date
