## Manages the conversation history buffer.
## Keeps a rolling window of recent exchanges for API calls while archiving
## older exchanges to the narrative archive.
class_name ConversationBuffer
extends Node

const DEFAULT_BUFFER_SIZE := 8

@export var data_manager: DataManager

var buffer_size: int = DEFAULT_BUFFER_SIZE

# The active exchanges being sent to the API
var _exchanges: Array = []

# Current conversation date for archiving
var _current_date: String = ""
var _current_location: String = ""
var _current_chapter: int = 1
var _characters_present: Array = []


func initialize(date: String, location: String, chapter: int) -> void:
	_current_date = date
	_current_location = location
	_current_chapter = chapter
	_exchanges = []

	# Try to load existing conversation for this date
	if data_manager != null:
		var existing = data_manager.load_conversation(date)
		if existing != null and existing.has("exchanges"):
			_exchanges = existing["exchanges"]


func set_scene_context(date: String, location: String, chapter: int, characters: Array) -> void:
	if date != _current_date:
		# Date changed — archive current and start new
		_save_current_conversation()
		_current_date = date
		_exchanges = []

	_current_location = location
	_current_chapter = chapter
	_characters_present = characters


## Adds a player input + GM response exchange to the buffer.
func add_exchange(player_input: String, gm_response: String, metadata: Dictionary) -> void:
	var exchange := {
		"exchange_id": "exch_%d" % (Time.get_ticks_msec()),
		"timestamp": Time.get_datetime_string_from_system(true),
		"player_input": player_input,
		"gm_response": gm_response,
		"event_refs": [],
		"metadata": metadata,
	}

	# Link event refs if metadata contains events
	if metadata.has("events"):
		for evt in metadata["events"]:
			if evt.has("event_id"):
				exchange["event_refs"].append(evt["event_id"])

	_exchanges.append(exchange)
	_save_current_conversation()


## Returns the recent exchanges formatted as API messages.
## Each exchange becomes a user message + assistant message pair.
func get_api_messages() -> Array:
	var messages: Array = []
	var recent := _get_recent_exchanges()

	for exchange in recent:
		messages.append({
			"role": "user",
			"content": exchange["player_input"],
		})
		messages.append({
			"role": "assistant",
			"content": exchange["gm_response"],
		})

	return messages


## Returns only the most recent buffer_size exchanges.
func _get_recent_exchanges() -> Array:
	if _exchanges.size() <= buffer_size:
		return _exchanges.duplicate()
	return _exchanges.slice(_exchanges.size() - buffer_size)


## Returns all exchanges for display purposes.
func get_all_exchanges() -> Array:
	return _exchanges.duplicate()


## Returns the total number of exchanges in the current conversation.
func get_exchange_count() -> int:
	return _exchanges.size()


func _save_current_conversation() -> void:
	if data_manager == null or _current_date == "":
		return

	var conversation := {
		"date": _current_date,
		"location": _current_location,
		"chapter": _current_chapter,
		"characters_present": _characters_present,
		"exchanges": _exchanges,
	}
	data_manager.save_conversation(_current_date, conversation)


## Clears the buffer (used when starting a new chapter or loading a different date).
func clear() -> void:
	_save_current_conversation()
	_exchanges = []
