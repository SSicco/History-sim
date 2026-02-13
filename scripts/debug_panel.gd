## Debug panel showing the full prompt structure in collapsible sections.
## Toggle with F12 or the Debug button in the header bar.
extends PanelContainer

var prompt_assembler: PromptAssembler
var game_state: GameStateManager
var conversation_buffer: ConversationBuffer
var api_client: ApiClient

var _sections_container: VBoxContainer
var _sections: Array = []  # [{button, content, label, expanded}]
var _token_label: Label


func _ready() -> void:
	visible = false
	_build_ui()


func _build_ui() -> void:
	# Full screen overlay
	set_anchors_preset(Control.PRESET_FULL_RECT)

	# Dark background
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.08, 0.08, 0.1, 0.97)
	style.border_color = Color(0.3, 0.3, 0.35, 1.0)
	style.set_border_width_all(1)
	add_theme_stylebox_override("panel", style)

	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 24)
	margin.add_theme_constant_override("margin_top", 16)
	margin.add_theme_constant_override("margin_right", 24)
	margin.add_theme_constant_override("margin_bottom", 16)
	add_child(margin)

	var outer_vbox := VBoxContainer.new()
	outer_vbox.add_theme_constant_override("separation", 8)
	margin.add_child(outer_vbox)

	# Title bar
	var title_bar := HBoxContainer.new()
	title_bar.add_theme_constant_override("separation", 12)
	outer_vbox.add_child(title_bar)

	var title := Label.new()
	title.text = "PROMPT DEBUG VIEW"
	title.add_theme_font_size_override("font_size", 20)
	title.add_theme_color_override("font_color", Color(0.9, 0.75, 0.4))
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_bar.add_child(title)

	_token_label = Label.new()
	_token_label.add_theme_color_override("font_color", Color(0.6, 0.7, 0.6))
	_token_label.add_theme_font_size_override("font_size", 14)
	title_bar.add_child(_token_label)

	var collapse_all_btn := Button.new()
	collapse_all_btn.text = "Collapse All"
	collapse_all_btn.pressed.connect(_collapse_all)
	title_bar.add_child(collapse_all_btn)

	var expand_all_btn := Button.new()
	expand_all_btn.text = "Expand All"
	expand_all_btn.pressed.connect(_expand_all)
	title_bar.add_child(expand_all_btn)

	var close_btn := Button.new()
	close_btn.text = "Close [F12]"
	close_btn.pressed.connect(func(): visible = false)
	title_bar.add_child(close_btn)

	# Separator
	var sep := HSeparator.new()
	outer_vbox.add_child(sep)

	# Scroll area for sections
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	outer_vbox.add_child(scroll)

	_sections_container = VBoxContainer.new()
	_sections_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_sections_container.add_theme_constant_override("separation", 4)
	scroll.add_child(_sections_container)


## Populates the panel with the current prompt data and shows it.
func show_prompt() -> void:
	# Clear previous sections
	_sections.clear()
	for child in _sections_container.get_children():
		child.queue_free()

	# Need to wait a frame for queue_free to process
	await get_tree().process_frame

	# Get prompt data from assembler
	var debug_data := _gather_prompt_data()
	var total_chars := 0

	# Build sections
	for section in debug_data:
		_add_section(section["label"], section["content"], section.get("collapsed", false))
		total_chars += section["content"].length()

	# Rough token estimate (~4 chars per token)
	_token_label.text = "~%d chars | ~%d tokens (est.)" % [total_chars, total_chars / 4]

	visible = true


## Gathers all prompt sections with labels for display.
func _gather_prompt_data() -> Array:
	var sections: Array = []
	var call_type: String = game_state.current_call_type if game_state else "narrative"
	var max_tokens: int = prompt_assembler.MAX_TOKENS.get(call_type, 400)

	# Section: Config / Meta
	var model_name: String = api_client.model if api_client else "(unknown)"
	var meta_lines := PackedStringArray([
		"Model: %s" % model_name,
		"Call Type: %s" % call_type,
		"Max Tokens: %d" % max_tokens,
		"Buffer Size: %d exchanges" % conversation_buffer.buffer_size,
	])
	if game_state and game_state.awaiting_roll:
		meta_lines.append("Awaiting Roll: true (type: %s)" % game_state.roll_type)
	sections.append({
		"label": "Config / Call Type",
		"content": "\n".join(meta_lines),
		"collapsed": false,
	})

	# Section: Layer 1 — GM Guidelines
	if prompt_assembler._layer1_guidelines != "":
		var text: String = prompt_assembler._layer1_guidelines
		sections.append({
			"label": "Layer 1 — GM Guidelines (%d chars)" % text.length(),
			"content": text,
			"collapsed": true,
		})

	# Section: Layer 2 — Call-type template
	var layer2_key := call_type
	if call_type == "roll_result":
		if game_state.roll_type == "persuasion":
			layer2_key = "persuasion"
		elif game_state.roll_type == "chaos":
			layer2_key = "chaos"
		else:
			layer2_key = "narrative"

	if prompt_assembler._layer2_templates.has(layer2_key):
		var text: String = prompt_assembler._layer2_templates[layer2_key]
		sections.append({
			"label": "Layer 2 — %s (%d chars)" % [layer2_key.capitalize(), text.length()],
			"content": text,
			"collapsed": true,
		})

	# Section: Layer 3 — Scene Context
	var scene_context: String = prompt_assembler._build_scene_context()
	if scene_context != "":
		sections.append({
			"label": "Layer 3 — Scene Context (%d chars)" % scene_context.length(),
			"content": scene_context,
			"collapsed": false,
		})

	# Section: Messages (conversation history)
	var messages: Array = conversation_buffer.get_api_messages()
	if not messages.is_empty():
		var msg_parts := PackedStringArray()
		for i in range(messages.size()):
			var msg: Dictionary = messages[i]
			var role: String = msg.get("role", "?").to_upper()
			var content: String = msg.get("content", "")
			msg_parts.append("--- [%s] (message %d) ---\n%s" % [role, i + 1, content])
		sections.append({
			"label": "Messages — Conversation Buffer (%d messages)" % messages.size(),
			"content": "\n\n".join(msg_parts),
			"collapsed": false,
		})
	else:
		sections.append({
			"label": "Messages — Conversation Buffer (empty)",
			"content": "(no conversation history yet)",
			"collapsed": false,
		})

	return sections


func _add_section(label: String, content: String, collapsed: bool = false) -> void:
	var section_vbox := VBoxContainer.new()
	section_vbox.add_theme_constant_override("separation", 2)
	_sections_container.add_child(section_vbox)

	# Header button
	var btn := Button.new()
	btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
	btn.text = ("%s %s" % ["▶" if collapsed else "▼", label])
	var btn_style := StyleBoxFlat.new()
	btn_style.bg_color = Color(0.15, 0.15, 0.2, 1.0)
	btn_style.set_content_margin_all(8)
	btn_style.set_corner_radius_all(3)
	btn.add_theme_stylebox_override("normal", btn_style)
	var btn_hover := StyleBoxFlat.new()
	btn_hover.bg_color = Color(0.2, 0.2, 0.28, 1.0)
	btn_hover.set_content_margin_all(8)
	btn_hover.set_corner_radius_all(3)
	btn.add_theme_stylebox_override("hover", btn_hover)
	btn.add_theme_color_override("font_color", Color(0.85, 0.8, 0.65))
	section_vbox.add_child(btn)

	# Content area
	var content_margin := MarginContainer.new()
	content_margin.add_theme_constant_override("margin_left", 16)
	content_margin.add_theme_constant_override("margin_right", 8)
	content_margin.add_theme_constant_override("margin_top", 4)
	content_margin.add_theme_constant_override("margin_bottom", 4)
	content_margin.visible = not collapsed
	section_vbox.add_child(content_margin)

	var text_display := RichTextLabel.new()
	text_display.bbcode_enabled = true
	text_display.fit_content = true
	text_display.scroll_active = false
	text_display.selection_enabled = true
	text_display.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text_display.add_theme_font_size_override("normal_font_size", 13)
	text_display.text = "[color=#90a890]%s[/color]" % _escape_bbcode(content)
	content_margin.add_child(text_display)

	# Bottom separator
	var sep := HSeparator.new()
	section_vbox.add_child(sep)

	var section_data := {
		"button": btn,
		"content": content_margin,
		"label": label,
		"expanded": not collapsed,
	}
	_sections.append(section_data)

	btn.pressed.connect(func():
		section_data["expanded"] = not section_data["expanded"]
		content_margin.visible = section_data["expanded"]
		btn.text = "%s %s" % ["▼" if section_data["expanded"] else "▶", label]
	)


func _collapse_all() -> void:
	for section in _sections:
		section["expanded"] = false
		section["content"].visible = false
		section["button"].text = "▶ " + section["label"]


func _expand_all() -> void:
	for section in _sections:
		section["expanded"] = true
		section["content"].visible = true
		section["button"].text = "▼ " + section["label"]


func _escape_bbcode(text: String) -> String:
	return text.replace("[", "[lb]")
