## Context Agent — Call 1 in the two-call architecture.
## Uses claude-haiku-4-5-20251001 to determine which game data the main GM needs.
## Has its own HTTPRequest node for independent API calls.
## Also handles profile refresh calls.
class_name ContextAgent
extends Node

signal context_ready(search_results: Dictionary)
signal context_skipped
signal context_failed(error: String)
signal profile_refreshed(profile_text: String)

const HAIKU_MODEL := "claude-haiku-4-5-20251001"
const API_URL := "https://api.anthropic.com/v1/messages"
const API_VERSION := "2023-06-01"
const CONTEXT_MAX_TOKENS := 500
const PROFILE_MAX_TOKENS := 800

## Budget caps for search results
const MAX_CHARACTERS := 4
const MAX_EVENTS := 6
const MAX_LAWS := 3

var api_key: String = ""
var data_manager: DataManager
var api_logger: ApiLogger

var _http_request: HTTPRequest
var _is_requesting: bool = false
var _call_type: String = ""  # "context" or "profile"
var _pending_profile_data: Dictionary = {}

## System prompt for context routing
const CONTEXT_SYSTEM_PROMPT := """You translate player intent into search queries for a historical simulation game.
The player is King Juan II of Castile (15th century). You must determine which
characters, events, and laws are relevant to the player's input.

Available search fields:
- character_search: {"keywords": [...], "ids": [...], "categories": [...], "locations": [...]}
- event_search: {"keywords": [...], "characters": [...], "types": [...],
                  "date_after": "YYYY-MM-DD", "date_before": "YYYY-MM-DD"}
- law_search: {"keywords": [...], "status": "active"|"repealed"|""}

Event types: decision, diplomatic_proposal, promise, battle, law_enacted,
  law_repealed, relationship_change, npc_action, economic_event, roll_result,
  ceremony, death, birth, marriage, treaty, betrayal, military_action,
  construction, religious_event

Character categories: royal_family, court_advisor, iberian_royalty, nobility,
  papal_court, byzantine, ottoman, italian, military, religious, economic,
  household, polish_hungarian

Respond with ONLY valid JSON. If the conversation flows naturally from recent
context and no new data is needed, respond:
{"needs_search": false}

If context is needed, respond:
{"needs_search": true, "character_search": {...}, "event_search": {...},
 "law_search": {...}, "event_detail_ids": [...]}

Rules:
- "my love", "my wife", "the queen" -> search for Juan's wife
- "my children" -> search royal_family category
- Only include event_detail_ids for events the player explicitly asks to recall in detail
- Be generous with keywords — better to find too much than miss something
- Keep searches focused. Do not search for broad topics unless the player asks broadly"""

## System prompt for profile refresh
const PROFILE_SYSTEM_PROMPT := """You maintain King Juan II's profile for a historical simulation game.
Given Juan's current profile and recent events, produce an updated profile.
The profile must include:
1. Who Juan is (titles, key traits, faith, ambitions)
2. His family (wife, children with birth dates — NOT ages)
3. His story arc (major achievements, current chapter)
4. His current situation and task
5. Key relationships and alliances

Keep it under 500 words. Use birth dates (YYYY-MM-DD), never ages.
Write in third person, present tense. Focus on what's narratively relevant NOW.

Respond with ONLY the profile text, no JSON wrapping."""


func _ready() -> void:
	_http_request = HTTPRequest.new()
	_http_request.timeout = 60.0
	add_child(_http_request)
	_http_request.request_completed.connect(_on_request_completed)


## Requests context analysis from Haiku.
## player_input: The raw player text.
## date, location: Current game state.
## sticky_char_ids, sticky_event_ids: IDs already in sticky context.
## character_index: Compact one-line-per-character index.
## event_index: Compact one-line-per-event index (last 100).
func request_context(
	player_input: String,
	date: String,
	location: String,
	sticky_char_ids: Array,
	sticky_event_ids: Array,
	character_index: String,
	event_index: String
) -> void:
	if _is_requesting:
		context_failed.emit("Context agent is already processing a request.")
		return

	if api_key == "":
		context_skipped.emit()
		return

	_call_type = "context"

	var user_content := _build_context_user_content(
		player_input, date, location,
		sticky_char_ids, sticky_event_ids,
		character_index, event_index
	)

	var body := {
		"model": HAIKU_MODEL,
		"max_tokens": CONTEXT_MAX_TOKENS,
		"system": [{"type": "text", "text": CONTEXT_SYSTEM_PROMPT}],
		"messages": [{"role": "user", "content": user_content}],
	}

	_send_request(body)


## Requests a profile refresh from Haiku.
func request_profile_refresh(current_profile: String, recent_events: Array, date: String, royal_family: Array) -> void:
	if _is_requesting:
		return

	_call_type = "profile"

	var user_content := _build_profile_user_content(current_profile, recent_events, date, royal_family)

	var body := {
		"model": HAIKU_MODEL,
		"max_tokens": PROFILE_MAX_TOKENS,
		"system": [{"type": "text", "text": PROFILE_SYSTEM_PROMPT}],
		"messages": [{"role": "user", "content": user_content}],
	}

	_pending_profile_data = {
		"date": date,
	}

	_send_request(body)


func _send_request(body: Dictionary) -> void:
	_is_requesting = true

	var headers := PackedStringArray([
		"Content-Type: application/json",
		"x-api-key: %s" % api_key,
		"anthropic-version: %s" % API_VERSION,
	])

	var body_str := JSON.stringify(body)
	var err := _http_request.request(API_URL, headers, HTTPClient.METHOD_POST, body_str)
	if err != OK:
		_is_requesting = false
		if _call_type == "context":
			context_failed.emit("Failed to send context request: %s" % error_string(err))
		elif _call_type == "profile":
			push_warning("ContextAgent: Profile refresh request failed: %s" % error_string(err))


func _on_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	_is_requesting = false

	if result != HTTPRequest.RESULT_SUCCESS or response_code != 200:
		if _call_type == "context":
			# Graceful degradation: skip context search on failure
			push_warning("ContextAgent: Request failed (result=%d, code=%d), skipping context" % [result, response_code])
			context_skipped.emit()
		elif _call_type == "profile":
			push_warning("ContextAgent: Profile refresh failed (result=%d, code=%d)" % [result, response_code])
		return

	var response_text := body.get_string_from_utf8()
	var json := JSON.new()
	if json.parse(response_text) != OK:
		if _call_type == "context":
			context_skipped.emit()
		return

	var data: Dictionary = json.data
	if not data.has("content") or not data["content"] is Array or data["content"].is_empty():
		if _call_type == "context":
			context_skipped.emit()
		return

	var content_text := ""
	for block in data["content"]:
		if block is Dictionary and block.get("type") == "text":
			content_text += block["text"]

	# Log usage
	var usage: Dictionary = data.get("usage", {})
	if api_logger != null:
		api_logger.log_call({
			"model": HAIKU_MODEL,
			"call_type": "context_agent" if _call_type == "context" else "profile_refresh",
			"request_summary": "Context routing" if _call_type == "context" else "Profile refresh",
			"response_summary": content_text.left(100),
		}, usage)

	if _call_type == "context":
		_handle_context_response(content_text, usage)
	elif _call_type == "profile":
		_handle_profile_response(content_text)


func _handle_context_response(content_text: String, _usage: Dictionary) -> void:
	var parsed := _parse_context_json(content_text)
	if parsed.is_empty():
		context_skipped.emit()
		return

	if not parsed.get("needs_search", false):
		context_skipped.emit()
		return

	# Execute local searches and return results
	var results := _execute_searches(parsed)
	context_ready.emit(results)


func _handle_profile_response(content_text: String) -> void:
	var profile_text := content_text.strip_edges()
	if profile_text != "":
		profile_refreshed.emit(profile_text)


## Parses the Haiku response JSON, stripping code fences if present.
func _parse_context_json(text: String) -> Dictionary:
	var cleaned := text.strip_edges()

	# Strip markdown code fences
	if cleaned.begins_with("```"):
		var first_newline := cleaned.find("\n")
		if first_newline != -1:
			cleaned = cleaned.substr(first_newline + 1)
		var last_fence := cleaned.rfind("```")
		if last_fence != -1:
			cleaned = cleaned.left(last_fence)
		cleaned = cleaned.strip_edges()

	var json := JSON.new()
	if json.parse(cleaned) != OK:
		push_warning("ContextAgent: Failed to parse response JSON: %s" % cleaned.left(200))
		return {}

	if json.data is Dictionary:
		return json.data

	return {}


## Executes local searches based on Haiku's queries against cached game data.
func _execute_searches(queries: Dictionary) -> Dictionary:
	var results := {
		"characters": [],
		"events": [],
		"laws": [],
		"event_detail_ids": queries.get("event_detail_ids", []),
	}

	# Character search
	if queries.has("character_search"):
		results["characters"] = _search_characters(queries["character_search"])

	# Event search
	if queries.has("event_search"):
		results["events"] = _search_events(queries["event_search"])

	# Law search
	if queries.has("law_search"):
		results["laws"] = _search_laws(queries["law_search"])

	return results


# ─── Local Search Engine ─────────────────────────────────────────────

## Searches characters with scoring.
func _search_characters(query: Dictionary) -> Array:
	if data_manager == null:
		return []

	var characters_data = data_manager.load_json("characters.json")
	if characters_data == null or not characters_data.has("characters"):
		return []

	var all_chars: Array = characters_data["characters"]
	var keywords: Array = query.get("keywords", [])
	var ids: Array = query.get("ids", [])
	var categories: Array = query.get("categories", [])
	var locations: Array = query.get("locations", [])

	var scored: Array = []

	for c in all_chars:
		if not c is Dictionary:
			continue

		var score := 0
		var char_id: String = c.get("id", "")
		var char_name: String = c.get("name", "").to_lower()
		var char_title: String = c.get("title", "").to_lower()
		var char_task: String = c.get("current_task", "").to_lower()
		var char_cats: Array = c.get("category", [])
		var char_loc: String = c.get("location", "").to_lower()

		# Direct ID match
		if char_id in ids:
			score += 50

		# Keyword matches
		for kw in keywords:
			var kw_lower: String = str(kw).to_lower()
			if char_name.contains(kw_lower):
				score += 20
			if char_title.contains(kw_lower):
				score += 10
			if char_task.contains(kw_lower):
				score += 5

		# Category match
		for cat in categories:
			if cat in char_cats:
				score += 8

		# Location match
		for loc in locations:
			if char_loc.contains(str(loc).to_lower()):
				score += 12

		if score > 0:
			scored.append({"score": score, "data": c})

	# Sort by score descending
	scored.sort_custom(func(a, b): return a["score"] > b["score"])

	# Return top MAX_CHARACTERS
	var results: Array = []
	for i in range(mini(scored.size(), MAX_CHARACTERS)):
		results.append(scored[i]["data"])

	return results


## Searches events with scoring.
func _search_events(query: Dictionary) -> Array:
	if data_manager == null:
		return []

	var events_data = data_manager.load_json("events.json")
	if events_data == null or not events_data.has("events"):
		return []

	var all_events: Array = events_data["events"]
	var keywords: Array = query.get("keywords", [])
	var characters: Array = query.get("characters", [])
	var types: Array = query.get("types", [])
	var date_after: String = query.get("date_after", "")
	var date_before: String = query.get("date_before", "")

	var scored: Array = []

	for evt in all_events:
		if not evt is Dictionary:
			continue

		# Date range hard filters
		var evt_date: String = evt.get("date", "")
		if date_after != "" and evt_date < date_after:
			continue
		if date_before != "" and evt_date > date_before:
			continue

		var score := 0
		var summary: String = evt.get("summary", "").to_lower()
		var evt_chars: Array = evt.get("characters", [])
		var evt_type: String = evt.get("type", "")

		# Keyword in summary
		for kw in keywords:
			if summary.contains(str(kw).to_lower()):
				score += 10

		# Character ID match
		for char_id in characters:
			if char_id in evt_chars:
				score += 15

		# Event type match
		if evt_type in types:
			score += 8

		# Recency bonus
		if evt_date != "":
			score += 1

		if score > 0:
			scored.append({"score": score, "date": evt_date, "data": evt})

	# Sort by score descending, then date descending for ties
	scored.sort_custom(func(a, b):
		if a["score"] != b["score"]:
			return a["score"] > b["score"]
		return a["date"] > b["date"]
	)

	# Return top MAX_EVENTS
	var results: Array = []
	for i in range(mini(scored.size(), MAX_EVENTS)):
		results.append(scored[i]["data"])

	return results


## Searches laws with scoring.
func _search_laws(query: Dictionary) -> Array:
	if data_manager == null:
		return []

	var laws_data = data_manager.load_json("laws.json")
	if laws_data == null or not laws_data.has("laws"):
		return []

	var all_laws: Array = laws_data["laws"]
	var keywords: Array = query.get("keywords", [])
	var status_filter: String = query.get("status", "")

	var scored: Array = []

	for law in all_laws:
		if not law is Dictionary:
			continue

		# Status hard filter
		if status_filter != "" and law.get("status", "") != status_filter:
			continue

		var score := 0
		var title: String = law.get("title", "").to_lower()
		var summary: String = law.get("summary", "").to_lower()

		for kw in keywords:
			var kw_lower: String = str(kw).to_lower()
			if title.contains(kw_lower):
				score += 15
			if summary.contains(kw_lower):
				score += 10

		if score > 0:
			scored.append({"score": score, "data": law})

	scored.sort_custom(func(a, b): return a["score"] > b["score"])

	var results: Array = []
	for i in range(mini(scored.size(), MAX_LAWS)):
		results.append(scored[i]["data"])

	return results


# ─── Index Builders ──────────────────────────────────────────────────

## Builds a compact character index: one line per character.
## Format: id | name | title | location | status
func build_character_index() -> String:
	if data_manager == null:
		return "(no characters)"

	var characters_data = data_manager.load_json("characters.json")
	if characters_data == null or not characters_data.has("characters"):
		return "(no characters)"

	var all_chars: Array = characters_data["characters"]
	if all_chars.is_empty():
		return "(no characters)"

	var lines: PackedStringArray = []
	for c in all_chars:
		if not c is Dictionary:
			continue
		var status_arr: Array = c.get("status", ["active"])
		var status_str: String = ", ".join(PackedStringArray(status_arr)) if not status_arr.is_empty() else "active"
		lines.append("%s | %s | %s | %s | %s" % [
			c.get("id", ""),
			c.get("name", ""),
			c.get("title", ""),
			c.get("location", ""),
			status_str,
		])

	return "\n".join(lines)


## Builds a compact event index: one line per event (last 100).
## Format: event_id | date | type | summary (max 80 chars) | characters
func build_event_index() -> String:
	if data_manager == null:
		return "(no events)"

	var events_data = data_manager.load_json("events.json")
	if events_data == null or not events_data.has("events"):
		return "(no events)"

	var all_events: Array = events_data["events"]
	if all_events.is_empty():
		return "(no events)"

	# Last 100 events
	var start_idx := maxi(0, all_events.size() - 100)
	var recent := all_events.slice(start_idx)

	var lines: PackedStringArray = []
	for evt in recent:
		if not evt is Dictionary:
			continue
		var summary: String = evt.get("summary", "")
		if summary.length() > 80:
			summary = summary.left(80) + "..."
		var chars := ", ".join(PackedStringArray(evt.get("characters", [])))
		lines.append("%s | %s | %s | %s | %s" % [
			evt.get("event_id", ""),
			evt.get("date", ""),
			evt.get("type", ""),
			summary,
			chars,
		])

	return "\n".join(lines)


# ─── User Content Builders ───────────────────────────────────────────

func _build_context_user_content(
	player_input: String,
	date: String,
	location: String,
	sticky_char_ids: Array,
	sticky_event_ids: Array,
	character_index: String,
	event_index: String
) -> String:
	var parts: PackedStringArray = []
	parts.append('Player input: "%s"' % player_input)
	parts.append("Current date: %s" % date)
	parts.append("Current location: %s" % location)
	parts.append("")
	parts.append("Already in context (do not re-search):")
	parts.append("- Characters: %s" % (", ".join(PackedStringArray(sticky_char_ids)) if not sticky_char_ids.is_empty() else "(none)"))
	parts.append("- Events: %s" % (", ".join(PackedStringArray(sticky_event_ids)) if not sticky_event_ids.is_empty() else "(none)"))
	parts.append("")
	parts.append("CHARACTER INDEX:")
	parts.append(character_index)
	parts.append("")
	parts.append("EVENT INDEX (last 100):")
	parts.append(event_index)

	return "\n".join(parts)


func _build_profile_user_content(current_profile: String, recent_events: Array, date: String, royal_family: Array) -> String:
	var parts: PackedStringArray = []
	parts.append("Current date: %s" % date)
	parts.append("")
	parts.append("CURRENT PROFILE:")
	parts.append(current_profile)
	parts.append("")
	parts.append("RECENT EVENTS (last 8):")
	for evt in recent_events:
		if evt is Dictionary:
			parts.append("[%s] %s — %s" % [
				evt.get("date", "?"),
				evt.get("type", "?"),
				evt.get("summary", ""),
			])
	parts.append("")
	parts.append("ROYAL FAMILY:")
	for member in royal_family:
		if member is Dictionary:
			parts.append("- %s (%s), born %s" % [
				member.get("name", "?"),
				member.get("title", "?"),
				member.get("born", "?"),
			])

	return "\n".join(parts)
