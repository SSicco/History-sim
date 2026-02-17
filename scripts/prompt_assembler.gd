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
var _reflection_template: String = ""

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
	_reflection_template = _load_resource_text("res://resources/gm_prompts/layer0_reflection.txt")

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
	var system_blocks := _build_system_blocks(call_type, player_input)
	var messages := _build_messages(player_input)
	var max_tokens: int = MAX_TOKENS.get(call_type, 400)

	return {
		"system": system_blocks,
		"messages": messages,
		"max_tokens": max_tokens,
	}


## Builds the system content blocks with cache control markers.
func _build_system_blocks(call_type: String, player_input: String = "") -> Array:
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
	var scene_context := _build_scene_context(player_input)
	if scene_context != "":
		blocks.append({
			"type": "text",
			"text": scene_context,
			"cache_control": {"type": "ephemeral"},
		})

	return blocks


## Builds scene-specific context from game data.
## Scans player_input for character mentions and includes their data automatically.
func _build_scene_context(player_input: String = "") -> String:
	var parts: PackedStringArray = []

	# Current situation
	parts.append("═══ CURRENT SITUATION ═══")
	parts.append("Date: %s" % game_state.current_date)
	parts.append("Location: %s" % game_state.current_location)
	parts.append("")

	var characters_data = data_manager.load_json("characters.json")
	var all_characters: Array = []
	if characters_data != null and characters_data.has("characters"):
		all_characters = characters_data["characters"]

	# Characters in scene
	if not game_state.scene_characters.is_empty():
		parts.append("═══ CHARACTERS PRESENT ═══")
		if not all_characters.is_empty():
			for char_id in game_state.scene_characters:
				var char_info = _find_character(all_characters, char_id)
				if char_info != null:
					parts.append(_format_character_context(char_info))
					parts.append("")
		else:
			for char_id in game_state.scene_characters:
				parts.append("- %s" % char_id)
		parts.append("")

	# Characters referenced in player input but not already in scene
	if player_input != "" and not all_characters.is_empty():
		var referenced := _resolve_mentioned_characters(player_input, all_characters)
		# Filter out characters already in scene
		var new_refs: Array = []
		for char_info in referenced:
			if not game_state.scene_characters.has(char_info.get("id", "")):
				new_refs.append(char_info)
		if not new_refs.is_empty():
			parts.append("═══ CHARACTERS REFERENCED BY PLAYER ═══")
			for char_info in new_refs:
				parts.append(_format_character_context(char_info))
				parts.append("")
			parts.append("")

	# Running scene summary
	if game_state.running_summary != "":
		parts.append("═══ CURRENT SCENE SO FAR ═══")
		parts.append(game_state.running_summary.strip_edges())
		parts.append("")

	return "\n".join(parts)


func _find_character(characters: Array, char_id: String) -> Variant:
	for c in characters:
		if c is Dictionary and c.get("id") == char_id:
			return c
	return null


## Scans player input for character name/alias mentions.
## Returns an array of character dictionaries that were referenced.
func _resolve_mentioned_characters(player_input: String, all_characters: Array) -> Array:
	var input_lower := player_input.to_lower()
	var matched: Array = []
	var matched_ids: Dictionary = {}  # Prevent duplicates

	for c in all_characters:
		if not c is Dictionary:
			continue
		var char_id: String = c.get("id", "")
		if matched_ids.has(char_id):
			continue

		# Check character name
		var char_name: String = c.get("name", "")
		if char_name != "" and input_lower.contains(char_name.to_lower()):
			matched.append(c)
			matched_ids[char_id] = true
			continue

		# Check aliases
		var aliases: Array = c.get("aliases", [])
		var found := false
		for alias in aliases:
			if alias is String and alias != "":
				# Match alias as a word boundary: convert underscores to spaces for matching
				var alias_readable := alias.replace("_", " ").to_lower()
				if input_lower.contains(alias_readable):
					matched.append(c)
					matched_ids[char_id] = true
					found = true
					break
		if found:
			continue

		# Check title (partial match on significant parts)
		var title: String = c.get("title", "")
		if title != "" and title.length() > 4 and input_lower.contains(title.to_lower()):
			matched.append(c)
			matched_ids[char_id] = true

	return matched


func _format_character_context(char_data: Dictionary) -> String:
	var lines: PackedStringArray = []
	lines.append("### %s" % char_data.get("name", char_data.get("id", "Unknown")))

	if char_data.get("title", "") != "":
		lines.append("Title: %s" % char_data["title"])
	if char_data.get("born", "0000-00-00") != "0000-00-00":
		lines.append("Born: %s" % char_data["born"])
	if char_data.get("location", "") != "":
		lines.append("Location: %s" % char_data["location"])
	if char_data.get("current_task", "") != "":
		lines.append("Current Task: %s" % char_data["current_task"])
	if char_data.has("personality") and not char_data["personality"].is_empty():
		lines.append("Personality: %s" % ", ".join(PackedStringArray(char_data["personality"])))
	if char_data.has("interests") and not char_data["interests"].is_empty():
		lines.append("Interests:")
		for interest in char_data["interests"]:
			lines.append("  - %s" % interest)
	if char_data.get("speech_style", "") != "":
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


## Builds a compact character index for the reflection prompt.
func _build_character_index() -> String:
	var characters_data = data_manager.load_json("characters.json")
	if characters_data == null or not characters_data.has("characters"):
		return "(no characters in database)"

	var all_chars: Array = characters_data["characters"]
	if all_chars.is_empty():
		return "(no characters in database)"

	var lines: PackedStringArray = []
	for c in all_chars:
		if not c is Dictionary:
			continue
		var char_id: String = c.get("id", "")
		var name: String = c.get("name", char_id)
		var title: String = c.get("title", "")
		var location: String = c.get("location", "")
		lines.append("[%s] %s | %s | %s" % [char_id, name, title, location])

	return "\n".join(lines)


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


## Assembles the reflection prompt that asks which past events are needed.
## Returns {"system": Array, "messages": Array, "max_tokens": int}
func assemble_reflection_prompt(player_input: String, event_index_text: String, missing_hints: Array) -> Dictionary:
	var system_blocks: Array = []

	if _reflection_template != "":
		var prompt_text := _reflection_template
		prompt_text = prompt_text.replace("{event_index}", event_index_text)
		prompt_text = prompt_text.replace("{character_index}", _build_character_index())
		prompt_text = prompt_text.replace("{date}", game_state.current_date)
		prompt_text = prompt_text.replace("{location}", game_state.current_location)
		prompt_text = prompt_text.replace("{characters}", ", ".join(PackedStringArray(game_state.scene_characters)))

		# Build retry hints if this is a re-reflection
		var retry_hints_text := ""
		if not missing_hints.is_empty():
			var hint_lines: PackedStringArray = []
			hint_lines.append("═══ RETRY GUIDANCE ═══")
			hint_lines.append("The previous response indicated missing context for:")
			for hint in missing_hints:
				if hint is Dictionary:
					hint_lines.append("- [%s] %s" % [hint.get("type", "unknown"), hint.get("description", "")])
			hint_lines.append("")
			hint_lines.append("Broaden your search. Look for related events, adjacent")
			hint_lines.append("timestamps, and connected characters that might fill these gaps.")
			retry_hints_text = "\n".join(hint_lines)
		prompt_text = prompt_text.replace("{retry_hints}", retry_hints_text)

		system_blocks.append({
			"type": "text",
			"text": prompt_text,
		})

	var messages: Array = [{
		"role": "user",
		"content": player_input,
	}]

	return {
		"system": system_blocks,
		"messages": messages,
		"max_tokens": 300,
	}


## Assembles the full GM prompt enriched with retrieved event data.
## enrichment_text: Full text of events fetched from the reflection step.
## is_final_attempt: If true, adds graceful degradation instructions.
## missing_hints: Context gaps from previous attempt (used for final attempt guidance).
func assemble_enriched_prompt(player_input: String, enrichment_text: String, is_final_attempt: bool, missing_hints: Array) -> Dictionary:
	var call_type := game_state.current_call_type
	var system_blocks := _build_system_blocks(call_type, player_input)
	var messages := _build_messages(player_input)
	var max_tokens: int = MAX_TOKENS.get(call_type, 400)

	# Inject retrieved events as additional context
	if enrichment_text != "":
		system_blocks.append({
			"type": "text",
			"text": enrichment_text,
		})

	# On final attempt with known gaps, add graceful degradation guidance
	if is_final_attempt and not missing_hints.is_empty():
		system_blocks.append({
			"type": "text",
			"text": _build_final_attempt_guidance(missing_hints),
		})

	return {
		"system": system_blocks,
		"messages": messages,
		"max_tokens": max_tokens,
	}


## Builds instructions for the final attempt when context gaps remain.
func _build_final_attempt_guidance(missing_hints: Array) -> String:
	var lines: PackedStringArray = []
	lines.append("═══ RESPONSE GUIDANCE — FINAL ATTEMPT ═══")
	lines.append("Some context could not be retrieved. The following gaps remain:")
	for hint in missing_hints:
		if hint is Dictionary:
			lines.append("- %s" % hint.get("description", "unknown gap"))
	lines.append("")
	lines.append("You MUST still produce a complete, immersive response.")
	lines.append("For any details you cannot confirm from the provided data,")
	lines.append("characters should naturally express uncertainty in-fiction:")
	lines.append("- Fuzzy memory: \"I believe it was... though the details escape me, Your Majesty\"")
	lines.append("- Partial recall: Get confirmed details right, hedge gracefully on the rest")
	lines.append("- Deflection: \"That was some time ago — perhaps the chancellor's records would say precisely\"")
	lines.append("- Honest gaps: \"Forgive me, Sire, the specifics of that matter...\"")
	lines.append("")
	lines.append("NEVER fabricate specific dates, names, or agreements not in the provided context.")
	lines.append("Better to be honestly vague than confidently wrong.")
	return "\n".join(lines)
