## Orchestrates the reflection → fetch → GM call → retry flow.
## Sits between main.gd and api_client to add context-aware retries.
##
## Flow:
##   1. Player input arrives
##   2. If events exist: reflection call asks "which past events do you need?"
##   3. Fetch full event data for the returned IDs
##   4. Main GM call with enriched context
##   5. If GM signals missing_context and fixable: retry (up to 3 attempts)
##   6. Final attempt uses graceful in-fiction degradation for remaining gaps
class_name PromptRetryManager
extends Node

signal response_ready(narrative: String, metadata: Dictionary)
signal processing_started
signal processing_failed(error_message: String)
signal status_update(message: String)

enum State { IDLE, REFLECTING, GM_CALLING, RE_REFLECTING, FINALIZING }

const MAX_ATTEMPTS := 3
const REFLECTION_MAX_TOKENS := 300

## Call types that skip the reflection step entirely (context is already established).
const SKIP_REFLECTION_TYPES := ["roll_result", "chapter_start", "year_end"]

var api_client: ApiClient
var prompt_assembler: PromptAssembler
var game_state: GameStateManager
var data_manager: DataManager

var _state: int = State.IDLE
var _attempt: int = 0
var _player_input: String = ""
var _event_index: Array = []
var _enrichment_text: String = ""
var _missing_hints: Array = []


func connect_signals() -> void:
	api_client.raw_response_received.connect(_on_raw_response)
	api_client.response_received.connect(_on_gm_response)
	api_client.request_failed.connect(_on_request_failed)


## Rebuilds the compact event index from events.json.
## Call this before processing input (events may have been added since last call).
func build_event_index() -> void:
	var events_data = data_manager.load_json("events.json")
	_event_index = []
	if events_data == null:
		return
	for evt in events_data.get("events", []):
		_event_index.append({
			"id": evt.get("event_id", ""),
			"date": evt.get("date", ""),
			"type": evt.get("type", ""),
			"recap": evt.get("summary", ""),
			"characters": evt.get("characters", []),
		})


## Entry point: called by main.gd when the player submits a message.
func handle_player_input(text: String) -> void:
	if _state != State.IDLE:
		processing_failed.emit("Already processing a request.")
		return

	_player_input = text
	_attempt = 0
	_enrichment_text = ""
	_missing_hints = []

	processing_started.emit()
	build_event_index()

	# Decide whether to do a reflection call or go straight to GM
	var call_type := game_state.current_call_type
	var skip_reflection := call_type in SKIP_REFLECTION_TYPES or _event_index.is_empty()

	if skip_reflection:
		_start_gm_call()
	else:
		_start_reflection()


## Starts the reflection call to identify which past events are needed.
func _start_reflection() -> void:
	_state = State.REFLECTING
	_attempt += 1
	status_update.emit("Consulting memory... (attempt %d/%d)" % [_attempt, MAX_ATTEMPTS])

	var index_text := _build_event_index_text()
	var prompt := prompt_assembler.assemble_reflection_prompt(
		_player_input, index_text, _missing_hints
	)
	api_client.send_raw_message(prompt["system"], prompt["messages"], REFLECTION_MAX_TOKENS)


## Starts a re-reflection with hints about what was missing last time.
func _start_re_reflection() -> void:
	_state = State.RE_REFLECTING
	_attempt += 1
	status_update.emit("Broadening search... (attempt %d/%d)" % [_attempt, MAX_ATTEMPTS])

	var index_text := _build_event_index_text()
	var prompt := prompt_assembler.assemble_reflection_prompt(
		_player_input, index_text, _missing_hints
	)
	api_client.send_raw_message(prompt["system"], prompt["messages"], REFLECTION_MAX_TOKENS)


## Starts the main GM call (normal or enriched).
func _start_gm_call() -> void:
	if _attempt == 0:
		_attempt = 1

	var is_final := (_attempt >= MAX_ATTEMPTS)

	if _enrichment_text == "" and _missing_hints.is_empty():
		# No enrichment needed — use standard prompt
		_state = State.GM_CALLING
		status_update.emit("Composing response...")
		var prompt := prompt_assembler.assemble_prompt(_player_input)
		api_client.send_message(prompt["system"], prompt["messages"], prompt["max_tokens"])
	else:
		# Use enriched prompt
		_state = State.FINALIZING if is_final else State.GM_CALLING
		var label := "Final attempt..." if is_final else "Composing response... (attempt %d/%d)" % [_attempt, MAX_ATTEMPTS]
		status_update.emit(label)
		var prompt := prompt_assembler.assemble_enriched_prompt(
			_player_input, _enrichment_text, is_final, _missing_hints
		)
		api_client.send_message(prompt["system"], prompt["messages"], prompt["max_tokens"])


# ─── Signal handlers ───────────────────────────────────────────────────

func _on_raw_response(text: String) -> void:
	if _state != State.REFLECTING and _state != State.RE_REFLECTING:
		return

	# Parse reflection response → list of event IDs
	var needed_ids := _parse_reflection_response(text)
	_enrichment_text = _fetch_full_events(needed_ids)
	_start_gm_call()


func _on_gm_response(narrative: String, metadata: Dictionary) -> void:
	if _state != State.GM_CALLING and _state != State.FINALIZING:
		# Not our call — shouldn't happen with proper wiring, but pass through
		response_ready.emit(narrative, metadata)
		return

	var missing: Array = metadata.get("missing_context", [])

	# Happy path: no gaps, or this is the final attempt — done
	if missing.is_empty() or _attempt >= MAX_ATTEMPTS:
		_finish(narrative, metadata)
		return

	# Classify missing items as fixable vs unfixable
	var has_fixable := false
	for item in missing:
		if item is Dictionary and item.get("fixable", false):
			has_fixable = true
			break

	_missing_hints = missing

	# Resolve character_unknown gaps directly from the database
	var char_context := _resolve_missing_characters(missing)
	if char_context != "":
		if _enrichment_text != "":
			_enrichment_text += "\n\n" + char_context
		else:
			_enrichment_text = char_context
		# Remove resolved character hints so they don't trigger another retry
		var remaining: Array = []
		for item in missing:
			if item is Dictionary and item.get("type", "") != "character_unknown":
				remaining.append(item)
		_missing_hints = remaining
		# Check if there are still fixable gaps (non-character)
		has_fixable = false
		for item in remaining:
			if item is Dictionary and item.get("fixable", false):
				has_fixable = true
				break

	if _missing_hints.is_empty() and char_context != "":
		# All gaps were character_unknown and we resolved them — retry with enriched context
		status_update.emit("Characters found, retrying...")
		_start_gm_call()
	elif has_fixable:
		# There are fixable gaps — retry with a broader reflection
		_start_re_reflection()
	else:
		# All gaps are unfixable (outside simulation data) — skip to final attempt
		_attempt = MAX_ATTEMPTS
		_state = State.FINALIZING
		status_update.emit("Final attempt with graceful degradation...")
		var prompt := prompt_assembler.assemble_enriched_prompt(
			_player_input, _enrichment_text, true, _missing_hints
		)
		api_client.send_message(prompt["system"], prompt["messages"], prompt["max_tokens"])


func _on_request_failed(error_message: String) -> void:
	match _state:
		State.REFLECTING, State.RE_REFLECTING:
			# Reflection failed — fall back to a normal GM call without enrichment
			push_warning("PromptRetryManager: Reflection failed (%s), falling back to direct call" % error_message)
			_enrichment_text = ""
			_start_gm_call()
		State.GM_CALLING, State.FINALIZING:
			_state = State.IDLE
			processing_failed.emit(error_message)
		_:
			_state = State.IDLE
			processing_failed.emit(error_message)


func _finish(narrative: String, metadata: Dictionary) -> void:
	_state = State.IDLE
	response_ready.emit(narrative, metadata)


# ─── Helpers ────────────────────────────────────────────────────────────

## Builds a compact text index of all events for the reflection prompt.
func _build_event_index_text() -> String:
	if _event_index.is_empty():
		return "(no events recorded yet)"
	var lines: PackedStringArray = []
	for evt in _event_index:
		var chars := ", ".join(PackedStringArray(evt.get("characters", [])))
		lines.append("[%s] %s | %s | %s | chars: %s" % [
			evt["id"], evt["date"], evt["type"], evt["recap"], chars
		])
	return "\n".join(lines)


## Parses the reflection call response into a list of event IDs.
## Handles JSON arrays, objects with event_ids key, and code fences.
func _parse_reflection_response(text: String) -> Array:
	var cleaned := text.strip_edges()

	# Strip code fences if present
	if cleaned.begins_with("```"):
		var first_newline := cleaned.find("\n")
		if first_newline != -1:
			cleaned = cleaned.substr(first_newline + 1)
		var last_fence := cleaned.rfind("```")
		if last_fence != -1:
			cleaned = cleaned.left(last_fence)
		cleaned = cleaned.strip_edges()

	var json := JSON.new()
	var err := json.parse(cleaned)
	if err != OK:
		push_warning("PromptRetryManager: Failed to parse reflection response: %s" % cleaned.left(200))
		return []

	if json.data is Array:
		return json.data
	elif json.data is Dictionary and json.data.has("event_ids"):
		return json.data["event_ids"]

	push_warning("PromptRetryManager: Unexpected reflection format: %s" % cleaned.left(200))
	return []


## Resolves character_unknown missing context hints by searching the character database.
## Returns formatted character context text, or "" if no characters were found.
func _resolve_missing_characters(missing_hints: Array) -> String:
	var char_descriptions: PackedStringArray = []
	for item in missing_hints:
		if item is Dictionary and item.get("type", "") == "character_unknown":
			var desc: String = item.get("description", "")
			if desc != "":
				char_descriptions.append(desc)

	if char_descriptions.is_empty():
		return ""

	var characters_data = data_manager.load_json("characters.json")
	if characters_data == null or not characters_data.has("characters"):
		return ""

	var all_characters: Array = characters_data["characters"]
	var matched_ids: Dictionary = {}
	var matched: Array = []

	for desc in char_descriptions:
		var desc_lower: String = desc.to_lower()
		for c in all_characters:
			if not c is Dictionary:
				continue
			var char_id: String = c.get("id", "")
			if matched_ids.has(char_id):
				continue

			# Check name
			var char_name: String = c.get("name", "")
			if char_name != "" and desc_lower.contains(char_name.to_lower()):
				matched.append(c)
				matched_ids[char_id] = true
				continue

			# Check aliases
			for alias in c.get("aliases", []):
				if alias is String and alias != "":
					var alias_readable := alias.replace("_", " ").to_lower()
					if desc_lower.contains(alias_readable):
						matched.append(c)
						matched_ids[char_id] = true
						break

	if matched.is_empty():
		return ""

	var lines: PackedStringArray = []
	lines.append("═══ RETRIEVED CHARACTERS ═══")
	lines.append("The following characters were identified from the database.")

	for c in matched:
		lines.append("")
		lines.append("### %s" % c.get("name", c.get("id", "Unknown")))
		if c.get("title", "") != "":
			lines.append("Title: %s" % c["title"])
		if c.get("born", "") != "" and c.get("born", "") != "0000-00-00":
			lines.append("Born: %s" % c["born"])
		if c.get("location", "") != "":
			lines.append("Location: %s" % c["location"])
		if c.get("current_task", "") != "":
			lines.append("Current Task: %s" % c["current_task"])
		if c.has("personality") and not c["personality"].is_empty():
			lines.append("Personality: %s" % ", ".join(PackedStringArray(c["personality"])))
		if c.get("speech_style", "") != "":
			lines.append("Speech Style: %s" % c["speech_style"])

	lines.append("")
	lines.append("(%d characters resolved)" % matched.size())
	return "\n".join(lines)


## Fetches full event data for the given IDs and formats it as context text.
func _fetch_full_events(event_ids: Array) -> String:
	if event_ids.is_empty():
		return ""

	var events_data = data_manager.load_json("events.json")
	if events_data == null:
		return ""

	var all_events: Array = events_data.get("events", [])
	var lines: PackedStringArray = []
	lines.append("═══ RETRIEVED MEMORY (Past Events) ═══")
	lines.append("The following events were identified as relevant to the current exchange.")

	var found_count := 0
	for evt_id in event_ids:
		for evt in all_events:
			if evt.get("event_id") == evt_id:
				lines.append("")
				lines.append("--- %s [%s] ---" % [evt.get("event_id", "?"), evt.get("date", "?")])
				lines.append("Type: %s" % evt.get("type", "unknown"))
				lines.append("Location: %s" % evt.get("location", "unknown"))
				var chars := ", ".join(PackedStringArray(evt.get("characters", [])))
				lines.append("Characters: %s" % chars)
				lines.append("Summary: %s" % evt.get("summary", ""))
				var tags: Array = evt.get("tags", [])
				if not tags.is_empty():
					lines.append("Tags: %s" % ", ".join(PackedStringArray(tags)))
				found_count += 1
				break

	if found_count == 0:
		return ""

	lines.append("")
	lines.append("(%d events retrieved out of %d requested)" % [found_count, event_ids.size()])
	return "\n".join(lines)
