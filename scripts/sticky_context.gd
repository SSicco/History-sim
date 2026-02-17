## Persistent context memory that survives across exchanges within an event boundary.
## Stores characters, events, and laws retrieved by the ContextAgent.
## Clears on event boundaries (sticky overflow, location change, session start).
class_name StickyContext
extends Node

signal context_overflow
signal context_cleared

## Token budget: 3000 tokens, estimated at 4 chars = 1 token.
const TOKEN_BUDGET := 3000
const CHARS_PER_TOKEN := 4

## Stored data keyed by ID
var _characters: Dictionary = {}  # character_id -> character dict
var _events: Dictionary = {}      # event_id -> {record, detail, conversations}
var _laws: Dictionary = {}        # law_id -> law dict

## Pull log for diagnostics
var _pull_log: Array = []

## Exchange counter
var _exchange_count: int = 0


func get_exchange_count() -> int:
	return _exchange_count


func increment_exchange() -> void:
	_exchange_count += 1


## Returns IDs of characters already in sticky context.
func get_character_ids() -> Array:
	return _characters.keys()


## Returns IDs of events already in sticky context.
func get_event_ids() -> Array:
	return _events.keys()


## Returns IDs of laws already in sticky context.
func get_law_ids() -> Array:
	return _laws.keys()


## Adds characters to sticky context. Returns true if overflow occurred.
func add_characters(characters: Array) -> bool:
	for c in characters:
		if c is Dictionary and c.has("id"):
			_characters[c["id"]] = c
			_pull_log.append({
				"exchange": _exchange_count,
				"type": "character",
				"id": c["id"],
				"tokens": _estimate_tokens(c),
			})
	return _check_overflow()


## Adds events to sticky context. Returns true if overflow occurred.
func add_events(events: Array) -> bool:
	for evt in events:
		if evt is Dictionary and evt.has("event_id"):
			_events[evt["event_id"]] = {
				"record": evt,
				"detail": false,
				"conversations": [],
			}
			_pull_log.append({
				"exchange": _exchange_count,
				"type": "event",
				"id": evt["event_id"],
				"tokens": _estimate_tokens(evt),
			})
	return _check_overflow()


## Adds event detail (conversation exchanges) to an existing event in sticky.
func add_event_detail(event_id: String, conversations: Array) -> void:
	if _events.has(event_id):
		_events[event_id]["detail"] = true
		_events[event_id]["conversations"] = conversations


## Adds laws to sticky context. Returns true if overflow occurred.
func add_laws(laws: Array) -> bool:
	for law in laws:
		if law is Dictionary and law.has("law_id"):
			_laws[law["law_id"]] = law
			_pull_log.append({
				"exchange": _exchange_count,
				"type": "law",
				"id": law["law_id"],
				"tokens": _estimate_tokens(law),
			})
	return _check_overflow()


## Estimates the total token usage of all sticky content.
func estimate_total_tokens() -> int:
	var total_chars := 0
	for c in _characters.values():
		total_chars += _dict_char_count(c)
	for evt in _events.values():
		total_chars += _dict_char_count(evt.get("record", {}))
		for conv in evt.get("conversations", []):
			total_chars += _dict_char_count(conv)
	for law in _laws.values():
		total_chars += _dict_char_count(law)
	return ceili(float(total_chars) / CHARS_PER_TOKEN)


## Checks if token budget is exceeded. Emits context_overflow if so.
func _check_overflow() -> bool:
	if estimate_total_tokens() > TOKEN_BUDGET:
		context_overflow.emit()
		return true
	return false


## Clears all sticky context and resets exchange counter.
func clear() -> void:
	_characters.clear()
	_events.clear()
	_laws.clear()
	_pull_log.clear()
	_exchange_count = 0
	context_cleared.emit()


## Returns true if sticky context has any data.
func has_data() -> bool:
	return not _characters.is_empty() or not _events.is_empty() or not _laws.is_empty()


## Returns a snapshot of all sticky data for diagnostics.
func get_snapshot() -> Dictionary:
	return {
		"characters": _characters.duplicate(true),
		"events": _events.duplicate(true),
		"laws": _laws.duplicate(true),
		"pull_log": _pull_log.duplicate(true),
		"exchange_count": _exchange_count,
		"estimated_tokens": estimate_total_tokens(),
	}


## Returns the pull log for diagnostics.
func get_pull_log() -> Array:
	return _pull_log.duplicate(true)


## Formats sticky context for injection into the GM prompt (Layer 4).
func format_for_prompt() -> String:
	var parts: PackedStringArray = []

	# Characters
	if not _characters.is_empty():
		parts.append("═══ RELEVANT CHARACTERS ═══")
		for char_id in _characters:
			var c: Dictionary = _characters[char_id]
			parts.append("")
			parts.append("### %s" % c.get("name", c.get("id", "Unknown")))
			if c.get("title", "") != "":
				parts.append("Title: %s" % c["title"])
			if c.get("born", "") != "" and c.get("born", "") != "0000-00-00":
				parts.append("Born: %s" % c["born"])
			if c.get("location", "") != "":
				parts.append("Location: %s" % c["location"])
			if c.get("current_task", "") != "":
				parts.append("Current Task: %s" % c["current_task"])
			if c.has("personality") and c["personality"] is Array and not c["personality"].is_empty():
				parts.append("Personality: %s" % ", ".join(PackedStringArray(c["personality"])))
			if c.get("speech_style", "") != "":
				parts.append("Speech Style: %s" % c["speech_style"])
			if c.has("red_lines") and c["red_lines"] is Array and not c["red_lines"].is_empty():
				parts.append("Red Lines: %s" % ", ".join(PackedStringArray(c["red_lines"])))
		parts.append("")

	# Events
	if not _events.is_empty():
		parts.append("═══ RELEVANT PAST EVENTS ═══")
		for event_id in _events:
			var evt_data: Dictionary = _events[event_id]
			var record: Dictionary = evt_data.get("record", {})
			var chars_str := ", ".join(PackedStringArray(record.get("characters", [])))
			parts.append("[%s] %s — %s (characters: %s)" % [
				record.get("date", "?"),
				record.get("type", "?"),
				record.get("summary", ""),
				chars_str,
			])
			# Include conversation detail if available
			if evt_data.get("detail", false):
				for conv in evt_data.get("conversations", []):
					parts.append("  Player: %s" % conv.get("player_input", ""))
					var response: String = conv.get("gm_response", "")
					if response.length() > 200:
						response = response.left(200) + "..."
					parts.append("  GM: %s" % response)
		parts.append("")

	# Laws
	if not _laws.is_empty():
		parts.append("═══ RELEVANT LAWS ═══")
		for law_id in _laws:
			var law: Dictionary = _laws[law_id]
			parts.append("[%s] %s — %s (status: %s)" % [
				law.get("date", "?"),
				law.get("title", law_id),
				law.get("summary", ""),
				law.get("status", "active"),
			])
		parts.append("")

	return "\n".join(parts)


## Estimates token count for a single item.
func _estimate_tokens(data: Variant) -> int:
	return ceili(float(_dict_char_count(data)) / CHARS_PER_TOKEN)


## Counts total characters in a dictionary's string values (recursive).
func _dict_char_count(data: Variant) -> int:
	if data is String:
		return data.length()
	if data is Dictionary:
		var count := 0
		for key in data:
			count += str(key).length() + _dict_char_count(data[key])
		return count
	if data is Array:
		var count := 0
		for item in data:
			count += _dict_char_count(item)
		return count
	return str(data).length()
