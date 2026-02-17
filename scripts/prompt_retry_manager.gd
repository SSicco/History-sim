## Orchestrates the two-call flow: ContextAgent (Haiku) → GM (Sonnet).
## Integrates with the ContextAgent for Call 1 and ApiClient for Call 2.
## Handles retry logic when the GM signals missing_context.
##
## Flow:
##   1. Player input arrives
##   2. ContextAgent (Haiku) determines which data is needed → local search → sticky context
##   3. PromptAssembler builds 4-layer prompt
##   4. Main GM call (Sonnet) with full context
##   5. If GM signals missing_context and fixable: retry (up to 3 attempts)
##   6. Final attempt uses graceful in-fiction degradation for remaining gaps
class_name PromptRetryManager
extends Node

signal response_ready(narrative: String, metadata: Dictionary)
signal processing_started
signal processing_failed(error_message: String)
signal status_update(message: String)

enum State { IDLE, CONTEXT_AGENT, GM_CALLING, RE_REFLECTING, FINALIZING }

const MAX_ATTEMPTS := 3
const REFLECTION_MAX_TOKENS := 300

## Call types that skip the context agent step entirely.
const SKIP_CONTEXT_TYPES := ["roll_result", "year_end"]

var api_client: ApiClient
var prompt_assembler: PromptAssembler
var game_state: GameStateManager
var data_manager: DataManager

## New subsystems
var context_agent: ContextAgent
var sticky_context: StickyContext
var session_recorder: SessionRecorder
var event_diagnostics: EventDiagnostics
var api_logger: ApiLogger

var _state: int = State.IDLE
var _attempt: int = 0
var _player_input: String = ""
var _enrichment_text: String = ""
var _missing_hints: Array = []


func connect_signals() -> void:
	api_client.response_received.connect(_on_gm_response)
	api_client.request_failed.connect(_on_request_failed)
	api_client.usage_reported.connect(_on_usage_reported)

	# Legacy reflection signals (kept for backward compat, but ContextAgent is primary)
	api_client.raw_response_received.connect(_on_raw_response)

	# Connect ContextAgent signals
	if context_agent != null:
		context_agent.context_ready.connect(_on_context_ready)
		context_agent.context_skipped.connect(_on_context_skipped)
		context_agent.context_failed.connect(_on_context_failed)


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

	# Begin session recording
	if session_recorder != null:
		session_recorder.begin_exchange(text)

	# Increment sticky context exchange counter
	if sticky_context != null:
		sticky_context.increment_exchange()

	# Decide whether to use ContextAgent or go straight to GM
	var call_type := game_state.current_call_type
	var skip_context := call_type in SKIP_CONTEXT_TYPES

	if skip_context or context_agent == null:
		_start_gm_call()
	else:
		_start_context_agent()


## Starts the ContextAgent (Call 1 — Haiku).
func _start_context_agent() -> void:
	_state = State.CONTEXT_AGENT
	_attempt += 1
	status_update.emit("Analyzing context...")

	var character_index := context_agent.build_character_index()
	var event_index := context_agent.build_event_index()

	var sticky_char_ids: Array = []
	var sticky_event_ids: Array = []
	if sticky_context != null:
		sticky_char_ids = sticky_context.get_character_ids()
		sticky_event_ids = sticky_context.get_event_ids()

	context_agent.request_context(
		_player_input,
		game_state.current_date,
		game_state.current_location,
		sticky_char_ids,
		sticky_event_ids,
		character_index,
		event_index
	)


## Called when ContextAgent returns search results.
func _on_context_ready(search_results: Dictionary) -> void:
	if _state != State.CONTEXT_AGENT:
		return

	# Add search results to sticky context
	if sticky_context != null:
		var characters: Array = search_results.get("characters", [])
		var events: Array = search_results.get("events", [])
		var laws: Array = search_results.get("laws", [])

		var overflowed := false
		if not characters.is_empty():
			overflowed = sticky_context.add_characters(characters) or overflowed
		if not events.is_empty():
			overflowed = sticky_context.add_events(events) or overflowed
		if not laws.is_empty():
			overflowed = sticky_context.add_laws(laws) or overflowed

		# Handle event detail recall
		var detail_ids: Array = search_results.get("event_detail_ids", [])
		for evt_id in detail_ids:
			var conversations := _load_event_conversations(evt_id)
			if not conversations.is_empty():
				sticky_context.add_event_detail(evt_id, conversations)

		# Record search results for diagnostics
		if session_recorder != null:
			session_recorder.record_search_results(characters, events, laws)
		if event_diagnostics != null:
			event_diagnostics.record_context_pull()

		# Handle overflow — triggers new event boundary
		if overflowed:
			sticky_context.clear()
			if event_diagnostics != null:
				event_diagnostics.end_event("overflow")
				event_diagnostics.begin_event()

		# Record sticky snapshot
		if session_recorder != null:
			session_recorder.record_sticky_snapshot(sticky_context.get_snapshot())
		if event_diagnostics != null:
			event_diagnostics.record_sticky_snapshot(sticky_context.get_snapshot())

	_start_gm_call()


## Called when ContextAgent determines no new context is needed.
func _on_context_skipped() -> void:
	if _state != State.CONTEXT_AGENT:
		return
	_start_gm_call()


## Called when ContextAgent fails.
func _on_context_failed(_error: String) -> void:
	if _state != State.CONTEXT_AGENT:
		return
	# Graceful degradation: proceed without new context
	push_warning("PromptRetryManager: Context agent failed, proceeding without new context")
	_start_gm_call()


## Starts the main GM call (Call 2 — Sonnet).
func _start_gm_call() -> void:
	if _attempt == 0:
		_attempt = 1

	var is_final := (_attempt >= MAX_ATTEMPTS)

	if _enrichment_text == "" and _missing_hints.is_empty():
		# Standard prompt (context is in sticky, assembled by PromptAssembler)
		_state = State.GM_CALLING
		status_update.emit("Composing response...")
		var prompt := prompt_assembler.assemble_prompt(_player_input)

		# Record GM prompt for diagnostics
		if session_recorder != null:
			session_recorder.record_gm_prompt(prompt["system"], prompt["messages"], prompt["max_tokens"])

		api_client.send_message(prompt["system"], prompt["messages"], prompt["max_tokens"])
	else:
		# Enriched prompt (legacy retry path)
		_state = State.FINALIZING if is_final else State.GM_CALLING
		var label := "Final attempt..." if is_final else "Composing response... (attempt %d/%d)" % [_attempt, MAX_ATTEMPTS]
		status_update.emit(label)
		var prompt := prompt_assembler.assemble_enriched_prompt(
			_player_input, _enrichment_text, is_final, _missing_hints
		)

		if session_recorder != null:
			session_recorder.record_gm_prompt(prompt["system"], prompt["messages"], prompt["max_tokens"])

		api_client.send_message(prompt["system"], prompt["messages"], prompt["max_tokens"])


# ─── Signal handlers ───────────────────────────────────────────────────

## Legacy handler for reflection responses (raw mode).
func _on_raw_response(text: String) -> void:
	if _state != State.RE_REFLECTING:
		return

	# Parse reflection response → event IDs and character IDs
	var result := _parse_reflection_response(text)
	var event_enrichment := _fetch_full_events(result["event_ids"])
	var char_enrichment := _fetch_full_characters(result["character_ids"])

	var parts: PackedStringArray = []
	if event_enrichment != "":
		parts.append(event_enrichment)
	if char_enrichment != "":
		parts.append(char_enrichment)
	_enrichment_text = "\n\n".join(parts)
	_start_gm_call()


## Tracks API usage for logging.
var _last_usage: Dictionary = {}
var _last_raw_response: String = ""

func _on_usage_reported(usage: Dictionary, raw_response: String) -> void:
	_last_usage = usage
	_last_raw_response = raw_response

	# Log to ApiLogger
	if api_logger != null:
		api_logger.log_call({
			"model": api_client.model,
			"call_type": game_state.current_call_type,
			"request_summary": _player_input.left(80),
			"response_summary": raw_response.left(100),
		}, usage)


func _on_gm_response(narrative: String, metadata: Dictionary) -> void:
	if _state != State.GM_CALLING and _state != State.FINALIZING:
		response_ready.emit(narrative, metadata)
		return

	# Record GM response for diagnostics
	if session_recorder != null:
		session_recorder.record_gm_response(_last_raw_response, narrative, metadata, _last_usage)

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
		var remaining: Array = []
		for item in missing:
			if item is Dictionary and item.get("type", "") != "character_unknown":
				remaining.append(item)
		_missing_hints = remaining
		has_fixable = false
		for item in remaining:
			if item is Dictionary and item.get("fixable", false):
				has_fixable = true
				break

	if _missing_hints.is_empty() and char_context != "":
		status_update.emit("Characters found, retrying...")
		_start_gm_call()
	elif has_fixable:
		_start_re_reflection()
	else:
		_attempt = MAX_ATTEMPTS
		_state = State.FINALIZING
		status_update.emit("Final attempt with graceful degradation...")
		var prompt := prompt_assembler.assemble_enriched_prompt(
			_player_input, _enrichment_text, true, _missing_hints
		)
		api_client.send_message(prompt["system"], prompt["messages"], prompt["max_tokens"])


func _on_request_failed(error_message: String) -> void:
	match _state:
		State.CONTEXT_AGENT:
			push_warning("PromptRetryManager: Context agent failed (%s), falling back" % error_message)
			_start_gm_call()
		State.RE_REFLECTING:
			push_warning("PromptRetryManager: Re-reflection failed (%s), falling back" % error_message)
			_enrichment_text = ""
			_start_gm_call()
		State.GM_CALLING, State.FINALIZING:
			_state = State.IDLE
			if session_recorder != null:
				session_recorder.finish_exchange()
			processing_failed.emit(error_message)
		_:
			_state = State.IDLE
			processing_failed.emit(error_message)


func _finish(narrative: String, metadata: Dictionary) -> void:
	# Calculate cost and record
	if session_recorder != null and api_logger != null:
		session_recorder.record_exchange_cost(api_logger.get_session_stats()["total_cost_usd"])
		session_recorder.finish_exchange()

	if event_diagnostics != null and api_logger != null:
		event_diagnostics.record_exchange(api_logger.get_session_stats()["total_cost_usd"])

	_state = State.IDLE
	response_ready.emit(narrative, metadata)


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


# ─── Helpers ────────────────────────────────────────────────────────────

## Loads conversation exchanges for a specific event's date.
func _load_event_conversations(event_id: String) -> Array:
	if data_manager == null:
		return []

	# Find the event to get its date
	var events_data = data_manager.load_json("events.json")
	if events_data == null:
		return []

	var target_date := ""
	for evt in events_data.get("events", []):
		if evt is Dictionary and evt.get("event_id") == event_id:
			target_date = evt.get("date", "")
			break

	if target_date == "":
		return []

	# Load conversations for that date
	var conv_data = data_manager.load_json("conversations/%s.json" % target_date)
	if conv_data == null or not conv_data.has("exchanges"):
		# Fall back to active_event.json
		var active = data_manager.load_json("active_event.json")
		if active != null and active.has("exchanges"):
			# Return last 3 exchanges as fallback
			var exchanges: Array = active["exchanges"]
			var start_idx := maxi(0, exchanges.size() - 3)
			return exchanges.slice(start_idx)
		return []

	# Look for exchanges referencing this event
	var matching: Array = []
	for exchange in conv_data["exchanges"]:
		if exchange is Dictionary:
			var refs: Array = exchange.get("event_refs", [])
			if event_id in refs:
				matching.append(exchange)

	# Fall back to last 3 exchanges from that day
	if matching.is_empty():
		var exchanges: Array = conv_data["exchanges"]
		var start_idx := maxi(0, exchanges.size() - 3)
		return exchanges.slice(start_idx)

	return matching


## Builds a compact text index of all events for the reflection prompt.
func _build_event_index_text() -> String:
	var events_data = data_manager.load_json("events.json")
	if events_data == null:
		return "(no events recorded yet)"

	var all_events: Array = events_data.get("events", [])
	if all_events.is_empty():
		return "(no events recorded yet)"

	var lines: PackedStringArray = []
	for evt in all_events:
		var chars := ", ".join(PackedStringArray(evt.get("characters", [])))
		lines.append("[%s] %s | %s | %s | chars: %s" % [
			evt.get("event_id", ""), evt.get("date", ""), evt.get("type", ""),
			evt.get("summary", ""), chars
		])
	return "\n".join(lines)


func _parse_reflection_response(text: String) -> Dictionary:
	var cleaned := text.strip_edges()
	var empty_result := {"event_ids": [], "character_ids": []}

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
		return empty_result

	if json.data is Array:
		return {"event_ids": json.data, "character_ids": []}

	if json.data is Dictionary:
		return {
			"event_ids": json.data.get("event_ids", []),
			"character_ids": json.data.get("character_ids", []),
		}

	return empty_result


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

			var char_name: String = c.get("name", "")
			if char_name != "" and desc_lower.contains(char_name.to_lower()):
				matched.append(c)
				matched_ids[char_id] = true
				continue

			for alias in c.get("aliases", []):
				if alias is String and alias != "":
					var alias_readable: String = alias.replace("_", " ").to_lower()
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


func _fetch_full_characters(character_ids: Array) -> String:
	if character_ids.is_empty():
		return ""

	var characters_data = data_manager.load_json("characters.json")
	if characters_data == null or not characters_data.has("characters"):
		return ""

	var all_characters: Array = characters_data["characters"]
	var lines: PackedStringArray = []
	lines.append("═══ RETRIEVED CHARACTERS ═══")

	var found_count := 0
	for char_id in character_ids:
		for c in all_characters:
			if c is Dictionary and c.get("id") == char_id:
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
				found_count += 1
				break

	if found_count == 0:
		return ""

	return "\n".join(lines)


func _fetch_full_events(event_ids: Array) -> String:
	if event_ids.is_empty():
		return ""

	var events_data = data_manager.load_json("events.json")
	if events_data == null:
		return ""

	var all_events: Array = events_data.get("events", [])
	var lines: PackedStringArray = []
	lines.append("═══ RETRIEVED MEMORY (Past Events) ═══")

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
				found_count += 1
				break

	if found_count == 0:
		return ""

	return "\n".join(lines)
