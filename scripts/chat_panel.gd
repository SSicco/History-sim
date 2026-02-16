## Main chat panel handling narrative display and player input.
## Supports inline character portraits next to dialogue.
extends VBoxContainer

signal message_submitted(text: String)
signal roll_submitted(value: int)

@export var game_state: GameStateManager

@onready var narrative_display: RichTextLabel = %NarrativeDisplay
@onready var input_field: TextEdit = %InputField
@onready var send_button: Button = %SendButton
@onready var roll_container: HBoxContainer = %RollContainer
@onready var roll_input: LineEdit = %RollInput
@onready var roll_button: Button = %RollButton
@onready var roll_label: Label = %RollLabel
@onready var thinking_indicator: Label = %ThinkingIndicator

var _is_waiting: bool = false

## Reference to portrait manager, set by main.gd
var portrait_manager: PortraitManager

## Portrait display size in pixels for inline chat portraits
const PORTRAIT_INLINE_SIZE := 48


func _ready() -> void:
	send_button.pressed.connect(_on_send_pressed)
	roll_button.pressed.connect(_on_roll_pressed)
	input_field.gui_input.connect(_on_input_gui_input)
	roll_input.text_submitted.connect(_on_roll_text_submitted)

	roll_container.visible = false
	thinking_indicator.visible = false

	if game_state:
		game_state.roll_requested.connect(_on_roll_requested)
		game_state.roll_completed.connect(_on_roll_completed)


func _on_input_gui_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_ENTER and not event.shift_pressed:
			get_viewport().set_input_as_handled()
			_on_send_pressed()


func _on_send_pressed() -> void:
	if _is_waiting:
		return

	var text := input_field.text.strip_edges()
	if text == "":
		return

	# Display player input in the narrative with portrait
	_append_player_text(text)
	input_field.text = ""
	message_submitted.emit(text)


func _on_roll_pressed() -> void:
	_submit_roll_value()


func _on_roll_text_submitted(_text: String) -> void:
	_submit_roll_value()


func _submit_roll_value() -> void:
	var text := roll_input.text.strip_edges()
	if text == "":
		return

	if not text.is_valid_int():
		_append_system_text("Please enter a number between 1 and 100.")
		return

	var value := text.to_int()
	if value < 1 or value > 100:
		_append_system_text("Roll must be between 1 and 100.")
		return

	roll_input.text = ""
	_append_system_text("d100 Roll: %d" % value)
	roll_submitted.emit(value)


func _on_roll_requested(roll_type_name: String) -> void:
	roll_container.visible = true
	var type_display := roll_type_name.capitalize() if roll_type_name != "" else "d100"
	roll_label.text = "%s Roll:" % type_display
	roll_input.grab_focus()


func _on_roll_completed() -> void:
	roll_container.visible = false


## Appends narrative text from the GM to the display.
## If dialogue metadata is provided, inserts portraits next to speaker lines.
func append_narrative(text: String, dialogue: Array = []) -> void:
	if narrative_display.text != "":
		narrative_display.append_text("\n\n")

	if dialogue.is_empty() or portrait_manager == null:
		# No dialogue metadata — display as plain narrative
		narrative_display.append_text("[color=#d4c5a9]%s[/color]" % _escape_bbcode(text))
	else:
		# Parse narrative and insert portraits before speaker dialogue lines
		_append_narrative_with_portraits(text, dialogue)

	_scroll_to_bottom()


## Appends the player's input to the display with optional portrait.
func _append_player_text(text: String) -> void:
	if narrative_display.text != "":
		narrative_display.append_text("\n\n")

	_insert_portrait("juan_ii")
	narrative_display.append_text("[color=#7eb8da][b]Juan II:[/b] %s[/color]" % _escape_bbcode(text))
	_scroll_to_bottom()


## Appends system messages (errors, roll results, etc.).
func _append_system_text(text: String) -> void:
	if narrative_display.text != "":
		narrative_display.append_text("\n\n")
	narrative_display.append_text("[color=#a0a0a0][i]%s[/i][/color]" % _escape_bbcode(text))
	_scroll_to_bottom()


## Inserts a portrait image inline if available for the character.
func _insert_portrait(character_id: String) -> void:
	if portrait_manager == null:
		return

	var texture := portrait_manager.ensure_portrait(character_id)
	if texture == null:
		return

	# Resize for inline display
	var image := texture.get_image()
	if image == null:
		return

	image = image.duplicate()
	image.resize(PORTRAIT_INLINE_SIZE, PORTRAIT_INLINE_SIZE, Image.INTERPOLATE_LANCZOS)
	var inline_texture := ImageTexture.create_from_image(image)

	narrative_display.add_image(inline_texture, PORTRAIT_INLINE_SIZE, PORTRAIT_INLINE_SIZE)
	narrative_display.append_text(" ")


## Appends narrative with portrait images inserted before dialogue lines.
## Parses the narrative text to find lines that start with character names
## and inserts the appropriate portrait before each one.
func _append_narrative_with_portraits(text: String, dialogue: Array) -> void:
	# Build a lookup of speaker_id -> display name from dialogue metadata
	var speaker_names: Dictionary = {}  # display_name_lower -> character_id
	for entry in dialogue:
		if entry is Dictionary and entry.has("speaker"):
			var speaker_id: String = entry["speaker"]
			var display_name := _format_speaker_name(speaker_id)
			speaker_names[display_name.to_lower()] = speaker_id

	# Split narrative into lines and check each for dialogue
	var lines := text.split("\n")
	var first_line := true

	for line in lines:
		if not first_line:
			narrative_display.append_text("\n")
		first_line = false

		var found_speaker := false
		# Check if this line starts with a known speaker name
		var trimmed := line.strip_edges()
		for display_name_lower in speaker_names:
			# Match patterns like "Name:" or "**Name:**" or "Name said"
			if trimmed.to_lower().begins_with(display_name_lower):
				var after := trimmed.substr(display_name_lower.length()).strip_edges()
				if after.begins_with(":") or after.begins_with("said") or after.begins_with("spoke") or after.begins_with("replied") or after.begins_with("asked") or after.begins_with("whispered"):
					var char_id: String = speaker_names[display_name_lower]
					_insert_portrait(char_id)
					found_speaker = true
					break

		if not found_speaker:
			# Also check for quoted dialogue markers like *"Name speaks"*
			for display_name_lower in speaker_names:
				if display_name_lower in trimmed.to_lower():
					# Just insert portrait if name is mentioned in a dialogue context
					var char_id: String = speaker_names[display_name_lower]
					if "\"" in trimmed or "\u201c" in trimmed or "\u201d" in trimmed or "spoke" in trimmed.to_lower() or "said" in trimmed.to_lower():
						_insert_portrait(char_id)
						found_speaker = true
						break

		narrative_display.append_text("[color=#d4c5a9]%s[/color]" % _escape_bbcode(line))


## Converts a character_id to a display name for matching against narrative text.
func _format_speaker_name(char_id: String) -> String:
	# Try getting proper name from portrait manager
	if portrait_manager != null:
		var char_name := portrait_manager.get_character_name(char_id)
		if char_name != char_id:
			# Extract just the first name for matching
			# "King Juan II of Castile" -> try matching "Juan"
			var name_parts := char_name.split(" ")
			# Skip title words
			for part in name_parts:
				if part.to_lower() not in ["king", "queen", "prince", "princess", "don", "doña", "fray", "bishop", "count", "duke", "sir", "ser", "lord", "lady", "of", "de", "the"]:
					return part

	# Fallback: convert ID to title case
	var fallback_parts := char_id.split("_")
	var formatted: PackedStringArray = []
	for part in fallback_parts:
		if part.length() > 0:
			formatted.append(part[0].to_upper() + part.substr(1))
	return " ".join(formatted)


func show_error(error_text: String) -> void:
	_append_system_text("Error: %s" % error_text)


func set_waiting(waiting: bool) -> void:
	_is_waiting = waiting
	send_button.disabled = waiting
	input_field.editable = not waiting
	thinking_indicator.visible = waiting
	if waiting:
		thinking_indicator.text = "The court awaits..."


func set_thinking_text(text: String) -> void:
	thinking_indicator.text = text


func clear_display() -> void:
	narrative_display.clear()


func _scroll_to_bottom() -> void:
	await get_tree().process_frame
	var scroll: VScrollBar = narrative_display.get_v_scroll_bar()
	if scroll:
		scroll.value = scroll.max_value


func _escape_bbcode(text: String) -> String:
	return text.replace("[", "[lb]")
