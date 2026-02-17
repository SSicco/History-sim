## Characters browser panel with search, grouped list, and detail view.
## Uses parchment background with dark text and medieval fonts.
extends Control

@export var data_manager: DataManager

## Portrait manager reference — set by main.gd for loading existing portraits.
var portrait_manager: PortraitManager

## Font resources — set by main.gd after loading
var font_cinzel: Font
var font_almendra: Font
var font_almendra_bold: Font

## All characters loaded from characters.json
var _characters: Array = []

## Currently selected character dict (or null)
var _selected_character: Variant = null

## Category display order and labels
const CATEGORY_ORDER: Array = [
	"royal_family", "court_advisor", "nobility", "military", "religious",
	"iberian_royalty", "papal_court", "byzantine", "ottoman", "italian",
	"polish_hungarian", "economic", "household",
]

const CATEGORY_LABELS: Dictionary = {
	"royal_family": "Royal Family",
	"court_advisor": "Court Advisors",
	"nobility": "Nobility",
	"military": "Military",
	"religious": "Religious",
	"iberian_royalty": "Iberian Royalty",
	"papal_court": "Papal Court",
	"byzantine": "Byzantine",
	"ottoman": "Ottoman",
	"italian": "Italian",
	"polish_hungarian": "Polish & Hungarian",
	"economic": "Economic",
	"household": "Household",
}

# ─── UI Node References ──────────────────────────────────────────────────────

var _search_input: LineEdit
var _character_list: VBoxContainer
var _list_scroll: ScrollContainer
var _detail_scroll: ScrollContainer
var _detail_container: VBoxContainer
var _empty_label: Label
var _parchment_bg: TextureRect

# Portrait size constants
const PORTRAIT_WIDTH := 200
const PORTRAIT_HEIGHT := 260
const LIST_WIDTH := 280


func _ready() -> void:
	_build_ui()
	call_deferred("_load_characters")


## Loads characters from the campaign's characters.json.
func _load_characters() -> void:
	if data_manager == null:
		return

	var data = data_manager.load_json("characters.json")
	if data != null and data.has("characters"):
		_characters = data["characters"]
	else:
		_characters = []

	_populate_list()


## Refreshes the character list (call after campaign load).
func refresh() -> void:
	_load_characters()
	_selected_character = null
	_show_empty_state()


# ─── UI Construction ─────────────────────────────────────────────────────────

func _build_ui() -> void:
	# Main split: left list + right detail
	var hsplit := HSplitContainer.new()
	hsplit.layout_mode = 1
	hsplit.anchors_preset = Control.PRESET_FULL_RECT
	hsplit.split_offset = LIST_WIDTH
	add_child(hsplit)

	# ── Left Panel (list) ─────────────────────────────────────────────────
	var left_panel := PanelContainer.new()
	left_panel.custom_minimum_size = Vector2(LIST_WIDTH, 0)
	left_panel.size_flags_horizontal = Control.SIZE_FILL
	var left_style := StyleBoxFlat.new()
	left_style.bg_color = Color(0.12, 0.11, 0.10, 1.0)
	left_style.content_margin_left = 0
	left_style.content_margin_right = 0
	left_style.content_margin_top = 0
	left_style.content_margin_bottom = 0
	left_panel.add_theme_stylebox_override("panel", left_style)
	hsplit.add_child(left_panel)

	var left_vbox := VBoxContainer.new()
	left_vbox.layout_mode = 2
	left_vbox.add_theme_constant_override("separation", 0)
	left_panel.add_child(left_vbox)

	# Search bar
	var search_margin := MarginContainer.new()
	search_margin.layout_mode = 2
	search_margin.add_theme_constant_override("margin_left", 10)
	search_margin.add_theme_constant_override("margin_right", 10)
	search_margin.add_theme_constant_override("margin_top", 10)
	search_margin.add_theme_constant_override("margin_bottom", 6)
	left_vbox.add_child(search_margin)

	_search_input = LineEdit.new()
	_search_input.placeholder_text = "Search characters..."
	_search_input.layout_mode = 2
	_search_input.clear_button_enabled = true
	if font_cinzel:
		_search_input.add_theme_font_override("font", font_cinzel)
	_search_input.add_theme_font_size_override("font_size", 13)
	_search_input.text_changed.connect(_on_search_changed)
	search_margin.add_child(_search_input)

	# Scrollable character list
	_list_scroll = ScrollContainer.new()
	_list_scroll.layout_mode = 2
	_list_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_list_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	left_vbox.add_child(_list_scroll)

	_character_list = VBoxContainer.new()
	_character_list.layout_mode = 2
	_character_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_character_list.add_theme_constant_override("separation", 0)
	_list_scroll.add_child(_character_list)

	# ── Right Panel (detail) ──────────────────────────────────────────────
	var right_panel := PanelContainer.new()
	right_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var right_style := StyleBoxFlat.new()
	right_style.bg_color = Color(0.82, 0.76, 0.66, 1.0)  # Fallback if no parchment
	right_style.content_margin_left = 0
	right_style.content_margin_right = 0
	right_style.content_margin_top = 0
	right_style.content_margin_bottom = 0
	right_panel.add_theme_stylebox_override("panel", right_style)
	hsplit.add_child(right_panel)

	# Parchment background (stretched)
	_parchment_bg = TextureRect.new()
	_parchment_bg.layout_mode = 1
	_parchment_bg.anchors_preset = Control.PRESET_FULL_RECT
	_parchment_bg.stretch_mode = TextureRect.STRETCH_TILE
	_parchment_bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	right_panel.add_child(_parchment_bg)
	_load_parchment_texture()

	# Detail scroll on top of parchment
	_detail_scroll = ScrollContainer.new()
	_detail_scroll.layout_mode = 2
	_detail_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_detail_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_detail_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	right_panel.add_child(_detail_scroll)

	var detail_margin := MarginContainer.new()
	detail_margin.layout_mode = 2
	detail_margin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	detail_margin.add_theme_constant_override("margin_left", 40)
	detail_margin.add_theme_constant_override("margin_right", 40)
	detail_margin.add_theme_constant_override("margin_top", 30)
	detail_margin.add_theme_constant_override("margin_bottom", 30)
	_detail_scroll.add_child(detail_margin)

	_detail_container = VBoxContainer.new()
	_detail_container.layout_mode = 2
	_detail_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_detail_container.add_theme_constant_override("separation", 16)
	detail_margin.add_child(_detail_container)

	# Empty state label (centered)
	_empty_label = Label.new()
	_empty_label.text = "Select a character from the list"
	_empty_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_empty_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_empty_label.layout_mode = 1
	_empty_label.anchors_preset = Control.PRESET_FULL_RECT
	_empty_label.add_theme_color_override("font_color", Color(0.35, 0.30, 0.25, 0.6))
	if font_cinzel:
		_empty_label.add_theme_font_override("font", font_cinzel)
	_empty_label.add_theme_font_size_override("font_size", 18)
	right_panel.add_child(_empty_label)

	_show_empty_state()


func _load_parchment_texture() -> void:
	for ext in ["png", "jpg", "jpeg", "webp"]:
		var path := "res://resources/images/parchment.%s" % ext
		if ResourceLoader.exists(path):
			var tex = load(path)
			if tex:
				_parchment_bg.texture = tex
				return


# ─── List Population ─────────────────────────────────────────────────────────

func _populate_list(filter: String = "") -> void:
	for child in _character_list.get_children():
		child.queue_free()

	var filter_lower := filter.to_lower()

	# Group characters by category
	var grouped: Dictionary = {}
	for cat in CATEGORY_ORDER:
		grouped[cat] = []
	var uncategorized: Array = []

	for character in _characters:
		var name_str: String = character.get("name", "")
		var id_str: String = character.get("id", "")

		# Apply search filter
		if filter_lower != "":
			var match_found := false
			if filter_lower in name_str.to_lower():
				match_found = true
			elif filter_lower in id_str.to_lower():
				match_found = true
			else:
				var cats: Array = character.get("category", [])
				for cat in cats:
					var label: String = CATEGORY_LABELS.get(cat, cat)
					if filter_lower in label.to_lower():
						match_found = true
						break
			if not match_found:
				continue

		# Place in first matching category
		var placed := false
		var cats: Array = character.get("category", [])
		for cat in CATEGORY_ORDER:
			if cat in cats:
				grouped[cat].append(character)
				placed = true
				break
		if not placed:
			uncategorized.append(character)

	# Build list UI
	for cat in CATEGORY_ORDER:
		var chars: Array = grouped[cat]
		if chars.is_empty():
			continue
		chars.sort_custom(func(a, b): return a.get("name", "") < b.get("name", ""))
		_add_category_header(CATEGORY_LABELS.get(cat, cat), chars.size())
		for character in chars:
			_add_character_entry(character)

	if not uncategorized.is_empty():
		uncategorized.sort_custom(func(a, b): return a.get("name", "") < b.get("name", ""))
		_add_category_header("Other", uncategorized.size())
		for character in uncategorized:
			_add_character_entry(character)


func _add_category_header(label: String, count: int) -> void:
	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(0, 12)
	_character_list.add_child(spacer)

	var header := Label.new()
	header.text = "  %s  (%d)" % [label.to_upper(), count]
	header.layout_mode = 2
	header.add_theme_color_override("font_color", Color(0.75, 0.65, 0.45, 1.0))
	if font_cinzel:
		header.add_theme_font_override("font", font_cinzel)
	header.add_theme_font_size_override("font_size", 12)
	_character_list.add_child(header)

	var sep := HSeparator.new()
	sep.add_theme_constant_override("separation", 2)
	var sep_style := StyleBoxFlat.new()
	sep_style.bg_color = Color(0.5, 0.43, 0.33, 0.3)
	sep_style.content_margin_top = 1
	sep_style.content_margin_bottom = 1
	sep.add_theme_stylebox_override("separator", sep_style)
	_character_list.add_child(sep)


func _add_character_entry(character: Dictionary) -> void:
	var btn := Button.new()
	btn.text = "  %s" % character.get("name", character.get("id", "Unknown"))
	btn.layout_mode = 2
	btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
	btn.clip_text = true

	var normal_style := StyleBoxFlat.new()
	normal_style.bg_color = Color(0, 0, 0, 0)
	normal_style.content_margin_left = 8
	normal_style.content_margin_right = 4
	normal_style.content_margin_top = 4
	normal_style.content_margin_bottom = 4
	btn.add_theme_stylebox_override("normal", normal_style)

	var hover_style := StyleBoxFlat.new()
	hover_style.bg_color = Color(0.75, 0.65, 0.45, 0.15)
	hover_style.content_margin_left = 8
	hover_style.content_margin_right = 4
	hover_style.content_margin_top = 4
	hover_style.content_margin_bottom = 4
	btn.add_theme_stylebox_override("hover", hover_style)

	var pressed_style := StyleBoxFlat.new()
	pressed_style.bg_color = Color(0.75, 0.65, 0.45, 0.3)
	pressed_style.content_margin_left = 8
	pressed_style.content_margin_right = 4
	pressed_style.content_margin_top = 4
	pressed_style.content_margin_bottom = 4
	btn.add_theme_stylebox_override("pressed", pressed_style)

	btn.add_theme_color_override("font_color", Color(0.85, 0.80, 0.72, 1.0))
	btn.add_theme_color_override("font_hover_color", Color(1.0, 0.95, 0.85, 1.0))
	if font_almendra:
		btn.add_theme_font_override("font", font_almendra)
	btn.add_theme_font_size_override("font_size", 14)

	# Dim deceased characters
	var status_arr: Array = character.get("status", [])
	if "deceased" in status_arr:
		btn.add_theme_color_override("font_color", Color(0.55, 0.50, 0.45, 0.7))

	btn.pressed.connect(_on_character_selected.bind(character))
	_character_list.add_child(btn)


func _on_search_changed(new_text: String) -> void:
	_populate_list(new_text)


# ─── Detail View ─────────────────────────────────────────────────────────────

func _show_empty_state() -> void:
	_detail_scroll.visible = false
	_empty_label.visible = true


func _on_character_selected(character: Dictionary) -> void:
	_selected_character = character
	_empty_label.visible = false
	_detail_scroll.visible = true
	_build_detail_view(character)


func _build_detail_view(character: Dictionary) -> void:
	for child in _detail_container.get_children():
		child.queue_free()

	var dark_text := Color(0.15, 0.12, 0.08, 1.0)
	var muted_text := Color(0.35, 0.30, 0.22, 1.0)
	var accent_text := Color(0.45, 0.30, 0.15, 1.0)

	# ── Portrait + Name header ────────────────────────────────────────────
	var header_hbox := HBoxContainer.new()
	header_hbox.layout_mode = 2
	header_hbox.add_theme_constant_override("separation", 24)
	_detail_container.add_child(header_hbox)

	# Portrait area
	var portrait_container := VBoxContainer.new()
	portrait_container.custom_minimum_size = Vector2(PORTRAIT_WIDTH, 0)
	portrait_container.add_theme_constant_override("separation", 0)
	header_hbox.add_child(portrait_container)

	var portrait_frame := PanelContainer.new()
	portrait_frame.custom_minimum_size = Vector2(PORTRAIT_WIDTH, PORTRAIT_HEIGHT)
	var frame_style := StyleBoxFlat.new()
	frame_style.bg_color = Color(0.65, 0.58, 0.48, 0.3)
	frame_style.border_color = Color(0.45, 0.38, 0.28, 0.6)
	frame_style.set_border_width_all(2)
	frame_style.set_corner_radius_all(4)
	frame_style.content_margin_left = 4
	frame_style.content_margin_right = 4
	frame_style.content_margin_top = 4
	frame_style.content_margin_bottom = 4
	portrait_frame.add_theme_stylebox_override("panel", frame_style)
	portrait_container.add_child(portrait_frame)

	# Load portrait via PortraitManager (read-only, no generation)
	var portrait_tex := _load_portrait(character.get("id", ""))
	if portrait_tex:
		var tex_rect := TextureRect.new()
		tex_rect.texture = portrait_tex
		tex_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tex_rect.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		tex_rect.layout_mode = 2
		tex_rect.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		tex_rect.size_flags_vertical = Control.SIZE_EXPAND_FILL
		portrait_frame.add_child(tex_rect)
	else:
		var placeholder := Control.new()
		placeholder.layout_mode = 2
		placeholder.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		placeholder.size_flags_vertical = Control.SIZE_EXPAND_FILL
		portrait_frame.add_child(placeholder)

	# Name + title area
	var name_vbox := VBoxContainer.new()
	name_vbox.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_vbox.add_theme_constant_override("separation", 8)
	header_hbox.add_child(name_vbox)

	var name_spacer_top := Control.new()
	name_spacer_top.custom_minimum_size = Vector2(0, 20)
	name_vbox.add_child(name_spacer_top)

	# Character name
	var name_label := RichTextLabel.new()
	name_label.bbcode_enabled = true
	name_label.fit_content = true
	name_label.scroll_active = false
	name_label.layout_mode = 2
	name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var char_name: String = character.get("name", "Unknown")
	if font_cinzel:
		name_label.add_theme_font_override("bold_font", font_cinzel)
		name_label.add_theme_font_override("normal_font", font_cinzel)
	name_label.add_theme_font_size_override("normal_font_size", 26)
	name_label.add_theme_font_size_override("bold_font_size", 26)
	name_label.add_theme_color_override("default_color", dark_text)
	name_label.text = "[b]%s[/b]" % char_name
	name_vbox.add_child(name_label)

	# Title
	var title_str: String = character.get("title", "")
	if title_str != "":
		var title_label := Label.new()
		title_label.text = title_str
		title_label.add_theme_color_override("font_color", accent_text)
		if font_almendra:
			title_label.add_theme_font_override("font", font_almendra)
		title_label.add_theme_font_size_override("font_size", 16)
		title_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		name_vbox.add_child(title_label)

	# Status
	var status_arr: Array = character.get("status", [])
	if not status_arr.is_empty():
		for status_val in status_arr:
			var badge := Label.new()
			badge.text = "  %s  " % str(status_val).capitalize()
			if font_cinzel:
				badge.add_theme_font_override("font", font_cinzel)
			badge.add_theme_font_size_override("font_size", 11)
			badge.add_theme_color_override("font_color", Color(0.3, 0.25, 0.18, 1.0))
			name_vbox.add_child(badge)

	# Location
	var location: String = character.get("location", "")
	if location != "":
		var loc_label := Label.new()
		loc_label.text = location
		loc_label.add_theme_color_override("font_color", muted_text)
		if font_almendra:
			loc_label.add_theme_font_override("font", font_almendra)
		loc_label.add_theme_font_size_override("font_size", 14)
		loc_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		name_vbox.add_child(loc_label)

	# ── Divider ───────────────────────────────────────────────────────────
	_add_ornamental_divider(_detail_container)

	# ── Birth ─────────────────────────────────────────────────────────────
	var born: String = character.get("born", "")
	if born != "":
		_add_section_header("Born", _detail_container)
		_add_section_body(_format_birth_date(born), _detail_container)

	# ── Personality ───────────────────────────────────────────────────────
	var personality: Array = character.get("personality", [])
	if not personality.is_empty():
		_add_section_header("Personality", _detail_container)
		_add_section_body(" · ".join(PackedStringArray(personality)), _detail_container)

	# ── Current Task ──────────────────────────────────────────────────────
	var task: String = character.get("current_task", "")
	if task != "":
		_add_section_header("Current Task", _detail_container)
		_add_section_body(task, _detail_container)

	# ── Interests ─────────────────────────────────────────────────────────
	var interests: Array = character.get("interests", [])
	if not interests.is_empty():
		_add_section_header("Interests", _detail_container)
		_add_section_body(" · ".join(PackedStringArray(interests)), _detail_container)

	# ── Speech Style ──────────────────────────────────────────────────────
	var speech: String = character.get("speech_style", "")
	if speech != "":
		_add_section_header("Speech Style", _detail_container)
		_add_section_body(speech, _detail_container)

	# ── Red Lines ─────────────────────────────────────────────────────────
	var red_lines: Array = character.get("red_lines", [])
	if not red_lines.is_empty():
		_add_section_header("Red Lines", _detail_container)
		var lines_text := ""
		for rl in red_lines:
			lines_text += "• %s\n" % str(rl)
		_add_section_body(lines_text.strip_edges(), _detail_container)

	# ── Key Events ────────────────────────────────────────────────────────
	var events: Array = character.get("event_refs", [])
	if not events.is_empty():
		_add_section_header("Key Events", _detail_container)
		var events_text := ""
		for evt in events:
			events_text += "• %s\n" % str(evt)
		_add_section_body(events_text.strip_edges(), _detail_container)

	# Bottom padding
	var bottom_spacer := Control.new()
	bottom_spacer.custom_minimum_size = Vector2(0, 40)
	_detail_container.add_child(bottom_spacer)

	_detail_scroll.scroll_vertical = 0


# ─── Detail View Helpers ─────────────────────────────────────────────────────

func _add_section_header(title: String, parent: Control) -> void:
	var label := Label.new()
	label.text = title.to_upper()
	label.layout_mode = 2
	label.add_theme_color_override("font_color", Color(0.45, 0.35, 0.22, 1.0))
	if font_cinzel:
		label.add_theme_font_override("font", font_cinzel)
	label.add_theme_font_size_override("font_size", 13)
	parent.add_child(label)


func _add_section_body(text: String, parent: Control) -> void:
	var label := Label.new()
	label.text = text
	label.layout_mode = 2
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.add_theme_color_override("font_color", Color(0.18, 0.15, 0.10, 1.0))
	if font_almendra:
		label.add_theme_font_override("font", font_almendra)
	label.add_theme_font_size_override("font_size", 15)
	parent.add_child(label)


func _add_ornamental_divider(parent: Control) -> void:
	var margin := MarginContainer.new()
	margin.layout_mode = 2
	margin.add_theme_constant_override("margin_top", 4)
	margin.add_theme_constant_override("margin_bottom", 4)
	parent.add_child(margin)

	var sep := HSeparator.new()
	var sep_style := StyleBoxFlat.new()
	sep_style.bg_color = Color(0.45, 0.38, 0.28, 0.4)
	sep_style.content_margin_top = 1
	sep_style.content_margin_bottom = 1
	sep.add_theme_stylebox_override("separator", sep_style)
	margin.add_child(sep)


func _format_birth_date(born_str: String) -> String:
	if born_str.begins_with("~"):
		return "circa %s" % born_str.substr(1)

	var parts := born_str.split("-")
	if parts.size() != 3:
		return born_str

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
		return born_str

	return "%s %s %s" % [day, months[month_num], year]


# ─── Portrait Loading ────────────────────────────────────────────────────────

func _load_portrait(character_id: String) -> Texture2D:
	if character_id == "":
		return null

	# Use PortraitManager if available (uses its cache and fallback logic)
	if portrait_manager != null:
		return portrait_manager.get_best_portrait(character_id)

	# Fallback: load directly from disk
	if data_manager == null:
		return null

	var portrait_dir := data_manager.get_campaign_dir().path_join("portraits").path_join(character_id)
	for filename in ["default.png", "court.png", "battle.png", "prayer.png"]:
		var path := portrait_dir.path_join(filename)
		if FileAccess.file_exists(path):
			var image := Image.new()
			var err := image.load(path)
			if err == OK:
				return ImageTexture.create_from_image(image)

	return null
