## Manages the active event's exchange buffer.
## Stores exchanges in active_event.json and provides the last 8 as API messages.
## This replaces the old date-scoped conversation system.
class_name ConversationBuffer
extends Node

const DEFAULT_BUFFER_SIZE := 8

@export var data_manager: DataManager

var buffer_size: int = DEFAULT_BUFFER_SIZE

# The active event's exchanges
var _exchanges: Array = []

# Current scene context
var _current_date: String = ""
var _current_location: String = ""
var _characters_present: Array = []


## Initializes the buffer by loading the active event from disk.
func initialize(date: String, location: String) -> void:
	_current_date = date
	_current_location = location
	_exchanges = []

	# Load existing active event exchanges
	if data_manager != null:
		var active = data_manager.load_json("active_event.json")
		if active != null and active.has("exchanges"):
			_exchanges = active["exchanges"]


func set_scene_context(date: String, location: String, characters: Array) -> void:
	_current_date = date
	_current_location = location
	_characters_present = characters


## Adds a player input + GM response exchange to the active event buffer.
func add_exchange(player_input: String, gm_response: String, metadata: Dictionary) -> void:
	var exchange := {
		"timestamp": Time.get_datetime_string_from_system(true),
		"player_input": player_input,
		"gm_response": gm_response,
		"summary": metadata.get("summary_update", ""),
	}

	_exchanges.append(exchange)
	_save_active_event()


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


## Returns the total number of exchanges in the active event.
func get_exchange_count() -> int:
	return _exchanges.size()


## Persists the active event's exchanges to disk.
func _save_active_event() -> void:
	if data_manager == null:
		return

	var active_event := {
		"start_date": _current_date,
		"location": _current_location,
		"characters": _characters_present,
		"exchanges": _exchanges,
	}
	data_manager.save_json("active_event.json", active_event)


## Clears the buffer.
func clear() -> void:
	_exchanges = []
