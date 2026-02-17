## Laws browser panel — placeholder until a laws database is created.
extends Control

## Font resources — set by main.gd after loading
var font_cinzel: Font
var font_almendra: Font

var _parchment_bg: TextureRect
var _message_label: Label


func _ready() -> void:
	_build_ui()


func refresh() -> void:
	pass  # Nothing to refresh yet


func _build_ui() -> void:
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_FULL_RECT)
	panel.size = size
	var panel_style := StyleBoxFlat.new()
	panel_style.bg_color = Color(0.82, 0.76, 0.66, 1.0)
	panel_style.content_margin_left = 0
	panel_style.content_margin_right = 0
	panel_style.content_margin_top = 0
	panel_style.content_margin_bottom = 0
	panel.add_theme_stylebox_override("panel", panel_style)
	add_child(panel)

	_parchment_bg = TextureRect.new()
	_parchment_bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_parchment_bg.stretch_mode = TextureRect.STRETCH_TILE
	_parchment_bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	panel.add_child(_parchment_bg)
	_load_parchment_texture()

	_message_label = Label.new()
	_message_label.text = "No laws have been enacted yet."
	_message_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_message_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_message_label.set_anchors_preset(Control.PRESET_FULL_RECT)
	_message_label.add_theme_color_override("font_color", Color(0.35, 0.30, 0.25, 0.6))
	if font_cinzel:
		_message_label.add_theme_font_override("font", font_cinzel)
	_message_label.add_theme_font_size_override("font_size", 20)
	panel.add_child(_message_label)


func _load_parchment_texture() -> void:
	for ext in ["png", "jpg", "jpeg", "webp"]:
		var path := "res://resources/images/parchment.%s" % ext
		if ResourceLoader.exists(path):
			var tex = load(path)
			if tex:
				_parchment_bg.texture = tex
				return
