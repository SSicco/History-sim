## Laws browser panel with search, grouped list, and detail view.
## Uses parchment background with dark text and medieval fonts.
extends Control

@export var data_manager: DataManager

## Font resources — set by main.gd after loading
var font_cinzel: Font
var font_almendra: Font

## All laws loaded from laws.json
var _laws: Array = []

## Currently selected law dict (or null)
var _selected_law: Variant = null

## Scope display order and labels
const SCOPE_ORDER: Array = [
	"castile", "aragon", "papal", "byzantine", "constantinople",
	"military_orders", "international",
]

const SCOPE_LABELS: Dictionary = {
	"castile": "Crown of Castile",
	"aragon": "Crown of Aragon",
	"papal": "Papal Decrees",
	"byzantine": "Byzantine Empire",
	"constantinople": "Constantinople",
	"military_orders": "Military Orders",
	"international": "International",
}

# ─── UI Node References ──────────────────────────────────────────────────────

var _search_input: LineEdit
var _law_list: VBoxContainer
var _list_scroll: ScrollContainer
var _detail_scroll: ScrollContainer
var _detail_container: VBoxContainer
var _empty_label: Label
var _parchment_bg: TextureRect

const LIST_WIDTH := 300


func _ready() -> void:
	_build_ui()
	call_deferred("_load_laws")


## Loads laws from the campaign's laws.json.
func _load_laws() -> void:
	if data_manager == null:
		return

	var data = data_manager.load_json("laws.json")
	if data != null and data.has("laws"):
		_laws = data["laws"]
	else:
		_laws = []

	_populate_list()


## Refreshes the law list (call after campaign load).
func refresh() -> void:
	_load_laws()
	_selected_law = null
	_show_empty_state()


# ─── UI Construction ─────────────────────────────────────────────────────────

func _build_ui() -> void:
	# Main split: left list + right detail
	var hsplit := HSplitContainer.new()
	hsplit.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
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
	left_vbox.add_theme_constant_override("separation", 0)
	left_panel.add_child(left_vbox)

	# Search bar
	var search_margin := MarginContainer.new()
	search_margin.add_theme_constant_override("margin_left", 10)
	search_margin.add_theme_constant_override("margin_right", 10)
	search_margin.add_theme_constant_override("margin_top", 10)
	search_margin.add_theme_constant_override("margin_bottom", 6)
	left_vbox.add_child(search_margin)

	_search_input = LineEdit.new()
	_search_input.placeholder_text = "Search laws..."
	_search_input.clear_button_enabled = true
	if font_cinzel:
		_search_input.add_theme_font_override("font", font_cinzel)
	_search_input.add_theme_font_size_override("font_size", 13)
	_search_input.text_changed.connect(_on_search_changed)
	search_margin.add_child(_search_input)

	# Scrollable law list
	_list_scroll = ScrollContainer.new()
	_list_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_list_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	left_vbox.add_child(_list_scroll)

	_law_list = VBoxContainer.new()
	_law_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_law_list.add_theme_constant_override("separation", 0)
	_list_scroll.add_child(_law_list)

	# ── Right Panel (detail) ──────────────────────────────────────────────
	var right_panel := PanelContainer.new()
	right_panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	var right_style := StyleBoxFlat.new()
	right_style.bg_color = Color(0.82, 0.76, 0.66, 1.0)
	right_style.content_margin_left = 0
	right_style.content_margin_right = 0
	right_style.content_margin_top = 0
	right_style.content_margin_bottom = 0
	right_panel.add_theme_stylebox_override("panel", right_style)
	hsplit.add_child(right_panel)

	# Parchment background
	_parchment_bg = TextureRect.new()
	_parchment_bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_parchment_bg.stretch_mode = TextureRect.STRETCH_TILE
	_parchment_bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	right_panel.add_child(_parchment_bg)
	_load_parchment_texture()

	# Detail scroll on top of parchment
	_detail_scroll = ScrollContainer.new()
	_detail_scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_detail_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_detail_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	right_panel.add_child(_detail_scroll)

	var detail_margin := MarginContainer.new()
	detail_margin.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	detail_margin.add_theme_constant_override("margin_left", 40)
	detail_margin.add_theme_constant_override("margin_right", 40)
	detail_margin.add_theme_constant_override("margin_top", 30)
	detail_margin.add_theme_constant_override("margin_bottom", 30)
	_detail_scroll.add_child(detail_margin)

	_detail_container = VBoxContainer.new()
	_detail_container.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_detail_container.add_theme_constant_override("separation", 16)
	detail_margin.add_child(_detail_container)

	# Empty state label
	_empty_label = Label.new()
	_empty_label.text = "Select a law from the list"
	_empty_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_empty_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_empty_label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
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
	for child in _law_list.get_children():
		child.queue_free()

	var filter_lower := filter.to_lower()

	# Group laws by scope
	var grouped: Dictionary = {}
	for scope in SCOPE_ORDER:
		grouped[scope] = []
	var uncategorized: Array = []

	for law in _laws:
		# Apply search filter
		if filter_lower != "":
			var match_found := false
			if filter_lower in law.get("title", "").to_lower():
				match_found = true
			elif filter_lower in law.get("summary", "").to_lower():
				match_found = true
			else:
				var tags: Array = law.get("tags", [])
				for tag in tags:
					if filter_lower in str(tag).to_lower():
						match_found = true
						break
			if not match_found:
				continue

		# Place in scope group
		var scope: String = law.get("scope", "")
		if scope in grouped:
			grouped[scope].append(law)
		else:
			uncategorized.append(law)

	# Build list UI
	for scope in SCOPE_ORDER:
		var laws_in_scope: Array = grouped[scope]
		if laws_in_scope.is_empty():
			continue
		laws_in_scope.sort_custom(func(a, b): return a.get("date_enacted", "") < b.get("date_enacted", ""))
		_add_scope_header(SCOPE_LABELS.get(scope, scope), laws_in_scope.size())
		for law in laws_in_scope:
			_add_law_entry(law)

	if not uncategorized.is_empty():
		uncategorized.sort_custom(func(a, b): return a.get("date_enacted", "") < b.get("date_enacted", ""))
		_add_scope_header("Other", uncategorized.size())
		for law in uncategorized:
			_add_law_entry(law)


func _add_scope_header(label: String, count: int) -> void:
	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(0, 12)
	_law_list.add_child(spacer)

	var header := Label.new()
	header.text = "  %s  (%d)" % [label.to_upper(), count]
	header.add_theme_color_override("font_color", Color(0.75, 0.65, 0.45, 1.0))
	if font_cinzel:
		header.add_theme_font_override("font", font_cinzel)
	header.add_theme_font_size_override("font_size", 12)
	_law_list.add_child(header)

	var sep := HSeparator.new()
	sep.add_theme_constant_override("separation", 2)
	var sep_style := StyleBoxFlat.new()
	sep_style.bg_color = Color(0.5, 0.43, 0.33, 0.3)
	sep_style.content_margin_top = 1
	sep_style.content_margin_bottom = 1
	sep.add_theme_stylebox_override("separator", sep_style)
	_law_list.add_child(sep)


func _add_law_entry(law: Dictionary) -> void:
	var btn := Button.new()
	var date_short := _format_year(law.get("date_enacted", ""))
	btn.text = "  %s  %s" % [date_short, law.get("title", "Unknown")]
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

	# Dim repealed/suspended laws
	var status: String = law.get("status", "active")
	if status == "repealed":
		btn.add_theme_color_override("font_color", Color(0.55, 0.50, 0.45, 0.7))
	elif status == "suspended":
		btn.add_theme_color_override("font_color", Color(0.70, 0.60, 0.45, 0.8))

	btn.pressed.connect(_on_law_selected.bind(law))
	_law_list.add_child(btn)


func _on_search_changed(new_text: String) -> void:
	_populate_list(new_text)


# ─── Detail View ─────────────────────────────────────────────────────────────

func _show_empty_state() -> void:
	_detail_scroll.visible = false
	_empty_label.visible = true


func _on_law_selected(law: Dictionary) -> void:
	_selected_law = law
	_empty_label.visible = false
	_detail_scroll.visible = true
	_build_detail_view(law)


func _build_detail_view(law: Dictionary) -> void:
	for child in _detail_container.get_children():
		child.queue_free()

	var dark_text := Color(0.15, 0.12, 0.08, 1.0)
	var muted_text := Color(0.35, 0.30, 0.22, 1.0)
	var accent_text := Color(0.45, 0.30, 0.15, 1.0)

	# ── Title ─────────────────────────────────────────────────────────────
	var title_label := RichTextLabel.new()
	title_label.bbcode_enabled = true
	title_label.fit_content = true
	title_label.scroll_active = false
	title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if font_cinzel:
		title_label.add_theme_font_override("bold_font", font_cinzel)
		title_label.add_theme_font_override("normal_font", font_cinzel)
	title_label.add_theme_font_size_override("normal_font_size", 24)
	title_label.add_theme_font_size_override("bold_font_size", 24)
	title_label.add_theme_color_override("default_color", dark_text)
	title_label.text = "[b]%s[/b]" % law.get("title", "Unknown")
	_detail_container.add_child(title_label)

	# ── Status + Scope badges ─────────────────────────────────────────────
	var badge_hbox := HBoxContainer.new()
	badge_hbox.add_theme_constant_override("separation", 12)
	_detail_container.add_child(badge_hbox)

	var status: String = law.get("status", "active")
	var status_badge := Label.new()
	status_badge.text = status.to_upper()
	if font_cinzel:
		status_badge.add_theme_font_override("font", font_cinzel)
	status_badge.add_theme_font_size_override("font_size", 11)
	match status:
		"active":
			status_badge.add_theme_color_override("font_color", Color(0.20, 0.45, 0.20, 1.0))
		"repealed":
			status_badge.add_theme_color_override("font_color", Color(0.55, 0.20, 0.20, 1.0))
		"suspended":
			status_badge.add_theme_color_override("font_color", Color(0.55, 0.45, 0.15, 1.0))
	badge_hbox.add_child(status_badge)

	var scope_str: String = SCOPE_LABELS.get(law.get("scope", ""), law.get("scope", ""))
	var scope_badge := Label.new()
	scope_badge.text = scope_str
	scope_badge.add_theme_color_override("font_color", muted_text)
	if font_cinzel:
		scope_badge.add_theme_font_override("font", font_cinzel)
	scope_badge.add_theme_font_size_override("font_size", 11)
	badge_hbox.add_child(scope_badge)

	# ── Metadata ──────────────────────────────────────────────────────────
	var meta_lines: PackedStringArray = []
	var date_str := _format_date(law.get("date_enacted", ""))
	if date_str != "":
		meta_lines.append("Enacted: %s" % date_str)
	var location: String = law.get("location", "")
	if location != "":
		meta_lines.append("Location: %s" % location)
	var proposed: String = law.get("proposed_by", "")
	if proposed != "":
		meta_lines.append("Proposed by: %s" % _format_character_id(proposed))
	var enacted: String = law.get("enacted_by", "")
	if enacted != "" and enacted != proposed:
		meta_lines.append("Enacted by: %s" % _format_character_id(enacted))

	if not meta_lines.is_empty():
		var meta_label := Label.new()
		meta_label.text = "\n".join(meta_lines)
		meta_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		meta_label.add_theme_color_override("font_color", muted_text)
		if font_almendra:
			meta_label.add_theme_font_override("font", font_almendra)
		meta_label.add_theme_font_size_override("font_size", 14)
		_detail_container.add_child(meta_label)

	# ── Tags ──────────────────────────────────────────────────────────────
	var tags: Array = law.get("tags", [])
	if not tags.is_empty():
		var tags_label := Label.new()
		tags_label.text = " · ".join(PackedStringArray(tags))
		tags_label.add_theme_color_override("font_color", accent_text)
		if font_cinzel:
			tags_label.add_theme_font_override("font", font_cinzel)
		tags_label.add_theme_font_size_override("font_size", 11)
		_detail_container.add_child(tags_label)

	# ── Divider ───────────────────────────────────────────────────────────
	_add_ornamental_divider(_detail_container)

	# ── Summary ───────────────────────────────────────────────────────────
	var summary: String = law.get("summary", "")
	if summary != "":
		_add_section_header("Summary", _detail_container)
		var summary_label := Label.new()
		summary_label.text = summary
		summary_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		summary_label.add_theme_color_override("font_color", dark_text)
		if font_almendra:
			summary_label.add_theme_font_override("font", font_almendra)
		summary_label.add_theme_font_size_override("font_size", 15)
		_detail_container.add_child(summary_label)

	# ── Full Text ─────────────────────────────────────────────────────────
	var full_text: String = law.get("full_text", "")
	if full_text != "":
		_add_ornamental_divider(_detail_container)
		_add_section_header("Full Text", _detail_container)
		var text_label := RichTextLabel.new()
		text_label.bbcode_enabled = false
		text_label.fit_content = true
		text_label.scroll_active = false
		text_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		text_label.add_theme_color_override("default_color", Color(0.20, 0.17, 0.12, 1.0))
		if font_almendra:
			text_label.add_theme_font_override("normal_font", font_almendra)
		text_label.add_theme_font_size_override("normal_font_size", 14)
		text_label.text = full_text
		_detail_container.add_child(text_label)

	# ── Effectiveness Modifiers ───────────────────────────────────────────
	var modifiers: Array = law.get("effectiveness_modifiers", [])
	if not modifiers.is_empty():
		_add_ornamental_divider(_detail_container)
		_add_section_header("Effectiveness History", _detail_container)
		for mod in modifiers:
			var mod_text := "[%s] %s — %s" % [
				mod.get("date", "?"),
				mod.get("type", "?").capitalize(),
				mod.get("summary", ""),
			]
			_add_section_body(mod_text, _detail_container)

	# ── Related Events ────────────────────────────────────────────────────
	var related: Array = law.get("related_events", [])
	if not related.is_empty():
		_add_ornamental_divider(_detail_container)
		_add_section_header("Related Events", _detail_container)
		for rel in related:
			var rel_text := "[%s] %s — %s" % [
				rel.get("date", "?"),
				rel.get("relationship", "?").capitalize(),
				rel.get("summary", ""),
			]
			_add_section_body(rel_text, _detail_container)

	# Bottom padding
	var bottom_spacer := Control.new()
	bottom_spacer.custom_minimum_size = Vector2(0, 40)
	_detail_container.add_child(bottom_spacer)

	_detail_scroll.scroll_vertical = 0


# ─── Detail View Helpers ─────────────────────────────────────────────────────

func _add_section_header(title: String, parent: Control) -> void:
	var label := Label.new()
	label.text = title.to_upper()
	label.add_theme_color_override("font_color", Color(0.45, 0.35, 0.22, 1.0))
	if font_cinzel:
		label.add_theme_font_override("font", font_cinzel)
	label.add_theme_font_size_override("font_size", 13)
	parent.add_child(label)


func _add_section_body(text: String, parent: Control) -> void:
	var label := Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.add_theme_color_override("font_color", Color(0.18, 0.15, 0.10, 1.0))
	if font_almendra:
		label.add_theme_font_override("font", font_almendra)
	label.add_theme_font_size_override("font_size", 15)
	parent.add_child(label)


func _add_ornamental_divider(parent: Control) -> void:
	var margin := MarginContainer.new()
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


func _format_year(iso_date: String) -> String:
	var parts := iso_date.split("-")
	if parts.size() >= 1:
		return parts[0]
	return ""


func _format_character_id(char_id: String) -> String:
	return char_id.replace("_", " ").capitalize()
