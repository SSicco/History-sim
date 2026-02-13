## Main chat panel handling narrative display and player input.
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

	# Display player input in the narrative
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
func append_narrative(text: String) -> void:
	if narrative_display.text != "":
		narrative_display.append_text("\n\n")
	narrative_display.append_text("[color=#d4c5a9]%s[/color]" % _escape_bbcode(text))
	_scroll_to_bottom()


## Appends the player's input to the display.
func _append_player_text(text: String) -> void:
	if narrative_display.text != "":
		narrative_display.append_text("\n\n")
	narrative_display.append_text("[color=#7eb8da][b]Juan II:[/b] %s[/color]" % _escape_bbcode(text))
	_scroll_to_bottom()


## Appends system messages (errors, roll results, etc.).
func _append_system_text(text: String) -> void:
	if narrative_display.text != "":
		narrative_display.append_text("\n\n")
	narrative_display.append_text("[color=#a0a0a0][i]%s[/i][/color]" % _escape_bbcode(text))
	_scroll_to_bottom()


func show_error(error_text: String) -> void:
	_append_system_text("Error: %s" % error_text)


func set_waiting(waiting: bool) -> void:
	_is_waiting = waiting
	send_button.disabled = waiting
	input_field.editable = not waiting
	thinking_indicator.visible = waiting


func clear_display() -> void:
	narrative_display.clear()


func _scroll_to_bottom() -> void:
	await get_tree().process_frame
	var scroll := narrative_display.get_v_scroll_bar()
	if scroll:
		scroll.value = scroll.max_value


func _escape_bbcode(text: String) -> String:
	return text.replace("[", "[lb]")
