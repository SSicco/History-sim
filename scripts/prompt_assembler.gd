## Builds the layered prompt structure for API calls.
## Assembles system blocks (Layer 1 + Layer 2 + Layer 3) and messages
## based on the current game state and call type.
class_name PromptAssembler
extends Node

@export var game_state: GameStateManager
@export var conversation_buffer: ConversationBuffer
@export var data_manager: DataManager

# Loaded prompt templates
var _layer1_guidelines: String = ""
var _layer2_templates: Dictionary = {}  # call_type -> template text

# Max tokens by call type
const MAX_TOKENS := {
	"narrative": 400,
	"persuasion": 1500,
	"chaos": 1500,
	"roll_result": 600,
	"chapter_start": 1000,
	"year_end": 2000,
	"battle": 800,
}


func _ready() -> void:
	_load_prompt_templates()


func _load_prompt_templates() -> void:
	_layer1_guidelines = _load_resource_text("res://resources/gm_prompts/layer1_gm_guidelines.txt")

	var template_files := {
		"narrative": "res://resources/gm_prompts/layer2_medieval_norms.txt",
		"persuasion": "res://resources/gm_prompts/layer2_persuasion.txt",
		"chaos": "res://resources/gm_prompts/layer2_chaos.txt",
		"chapter_start": "res://resources/gm_prompts/layer2_chapter_start.txt",
		"year_end": "res://resources/gm_prompts/layer2_year_end.txt",
	}

	for call_type in template_files:
		var text := _load_resource_text(template_files[call_type])
		if text != "":
			_layer2_templates[call_type] = text


func _load_resource_text(path: String) -> String:
	if not FileAccess.file_exists(path):
		push_warning("PromptAssembler: Template not found: %s" % path)
		return ""
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return ""
	var text := file.get_as_text()
	file.close()
	return text


## Assembles the full prompt for the current game state.
## Returns {"system": Array, "messages": Array, "max_tokens": int}
func assemble_prompt(player_input: String) -> Dictionary:
	var call_type := game_state.current_call_type
	var system_blocks := _build_system_blocks(call_type)
	var messages := _build_messages(player_input)
	var max_tokens: int = MAX_TOKENS.get(call_type, 400)

	return {
		"system": system_blocks,
		"messages": messages,
		"max_tokens": max_tokens,
	}


## Builds the system content blocks with cache control markers.
func _build_system_blocks(call_type: String) -> Array:
	var blocks: Array = []

	# Layer 1 — GM Guidelines (always present, cached)
	if _layer1_guidelines != "":
		blocks.append({
			"type": "text",
			"text": _layer1_guidelines,
			"cache_control": {"type": "ephemeral"},
		})

	# Layer 2 — Call-type specific content (cached)
	var layer2_key := call_type
	# For roll_result, reuse the skill that generated the table
	if call_type == "roll_result":
		# Use the roll_type from game state to determine which skill to load
		if game_state.roll_type == "persuasion":
			layer2_key = "persuasion"
		elif game_state.roll_type == "chaos":
			layer2_key = "chaos"
		else:
			layer2_key = "narrative"

	if _layer2_templates.has(layer2_key):
		blocks.append({
			"type": "text",
			"text": _layer2_templates[layer2_key],
			"cache_control": {"type": "ephemeral"},
		})

	# Layer 3 — Scene context (cached, updates at scene changes)
	var scene_context := _build_scene_context()
	if scene_context != "":
		blocks.append({
			"type": "text",
			"text": scene_context,
			"cache_control": {"type": "ephemeral"},
		})

	return blocks


## Builds scene-specific context from game data.
func _build_scene_context() -> String:
	var parts: PackedStringArray = []

	# Current situation
	parts.append("═══ CURRENT SITUATION ═══")
	parts.append("Date: %s" % game_state.current_date)
	parts.append("Location: %s" % game_state.current_location)
	parts.append("Chapter %d: %s" % [game_state.current_chapter, game_state.chapter_title])
	parts.append("")

	# Characters in scene
	if not game_state.scene_characters.is_empty():
		parts.append("═══ CHARACTERS PRESENT ═══")
		var characters_data = data_manager.load_json("characters.json")
		if characters_data != null and characters_data.has("characters"):
			for char_id in game_state.scene_characters:
				var char_info = _find_character(characters_data["characters"], char_id)
				if char_info != null:
					parts.append(_format_character_context(char_info))
					parts.append("")
		else:
			for char_id in game_state.scene_characters:
				parts.append("- %s" % char_id)
		parts.append("")

	# Running chapter summary
	if game_state.running_summary != "":
		parts.append("═══ CHAPTER SUMMARY SO FAR ═══")
		parts.append(game_state.running_summary.strip_edges())
		parts.append("")

	return "\n".join(parts)


func _find_character(characters: Array, char_id: String) -> Variant:
	for c in characters:
		if c is Dictionary and c.get("id") == char_id:
			return c
	return null


func _format_character_context(char_data: Dictionary) -> String:
	var lines: PackedStringArray = []
	lines.append("### %s" % char_data.get("name", char_data.get("id", "Unknown")))

	if char_data.has("title"):
		lines.append("Title: %s" % char_data["title"])
	if char_data.has("age"):
		lines.append("Age: %s" % str(char_data["age"]))
	if char_data.has("location"):
		lines.append("Location: %s" % char_data["location"])
	if char_data.has("current_task"):
		lines.append("Current Task: %s" % char_data["current_task"])
	if char_data.has("personality"):
		lines.append("Personality: %s" % ", ".join(PackedStringArray(char_data["personality"])))
	if char_data.has("interests"):
		lines.append("Interests:")
		for interest in char_data["interests"]:
			lines.append("  - %s" % interest)
	if char_data.has("red_lines"):
		lines.append("Red Lines:")
		for red_line in char_data["red_lines"]:
			lines.append("  - %s" % red_line)
	if char_data.has("speech_style"):
		lines.append("Speech Style: %s" % char_data["speech_style"])

	# Load relevant events for this character
	if char_data.has("event_refs") and not char_data["event_refs"].is_empty():
		var events_data = data_manager.load_json("events.json")
		if events_data != null and events_data.has("events"):
			lines.append("Recent Events:")
			for evt_id in char_data["event_refs"].slice(-5):  # Last 5 events
				var evt = _find_event(events_data["events"], evt_id)
				if evt != null:
					lines.append("  - [%s] %s" % [evt.get("date", "?"), evt.get("summary", "")])

	return "\n".join(lines)


func _find_event(events: Array, event_id: String) -> Variant:
	for e in events:
		if e is Dictionary and e.get("event_id") == event_id:
			return e
	return null


## Builds the messages array: conversation history + new player input.
func _build_messages(player_input: String) -> Array:
	var messages := conversation_buffer.get_api_messages()

	# Add the new player input
	messages.append({
		"role": "user",
		"content": player_input,
	})

	return messages


## Returns the max_tokens value for a given call type.
func get_max_tokens(call_type: String) -> int:
	return MAX_TOKENS.get(call_type, 400)
