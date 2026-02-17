## Header bar displaying current location, date, characters present, and test mode indicator.
extends PanelContainer

signal settings_requested
signal debug_requested

@export var game_state: GameStateManager

@onready var location_label: Label = %LocationLabel
@onready var date_label: Label = %DateLabel
@onready var characters_label: Label = %CharactersLabel
@onready var debug_button: Button = %DebugButton
@onready var settings_button: Button = %SettingsButton

## Test mode indicator label — created programmatically
var _test_mode_label: Label


func _ready() -> void:
	debug_button.pressed.connect(func(): debug_requested.emit())
	settings_button.pressed.connect(func(): settings_requested.emit())

	# Create test mode indicator (inserted before the debug button)
	_test_mode_label = Label.new()
	_test_mode_label.text = "[TEST MODE]"
	_test_mode_label.add_theme_color_override("font_color", Color(0.95, 0.3, 0.3, 1.0))
	_test_mode_label.add_theme_font_size_override("font_size", 14)
	_test_mode_label.visible = false
	var hbox := debug_button.get_parent()
	hbox.add_child(_test_mode_label)
	hbox.move_child(_test_mode_label, debug_button.get_index())

	if game_state:
		game_state.state_changed.connect(_update_display)
		_update_display()


func set_test_mode(enabled: bool) -> void:
	_test_mode_label.visible = enabled


func _update_display() -> void:
	if game_state == null:
		return

	location_label.text = game_state.current_location
	date_label.text = _format_date(game_state.current_date)

	if game_state.scene_characters.is_empty():
		characters_label.text = ""
		characters_label.visible = false
	else:
		var names: PackedStringArray = []
		for char_id in game_state.scene_characters:
			names.append(_format_character_name(char_id))
		characters_label.text = "Present: " + " · ".join(names)
		characters_label.visible = true


## Converts a character ID like "count_of_haro" to "Count Of Haro".
func _format_character_name(char_id: String) -> String:
	var parts := char_id.split("_")
	var formatted: PackedStringArray = []
	for part in parts:
		if part.length() > 0:
			formatted.append(part[0].to_upper() + part.substr(1))
	return " ".join(formatted)


## Formats an ISO date like "1439-09-15" to "15 September 1439".
func _format_date(iso_date: String) -> String:
	var parts := iso_date.split("-")
	if parts.size() != 3:
		return iso_date

	var year := parts[0]
	var month_num := parts[1].to_int()
	var day := parts[2].lstrip("0")
	if day == "":
		day = "0"

	var months := [
		"", "January", "February", "March", "April", "May", "June",
		"July", "August", "September", "October", "November", "December"
	]

	if month_num < 1 or month_num > 12:
		return iso_date

	return "%s %s %s" % [day, months[month_num], year]
