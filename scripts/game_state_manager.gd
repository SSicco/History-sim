## Core game state management.
## Tracks current date, location, scene characters, and orchestrates
## save/load operations across all data systems.
## Date and location are always derived from the last event in events.json.
class_name GameStateManager
extends Node

signal state_changed
signal date_changed(new_date: String)
signal location_changed(new_location: String)
signal scene_characters_changed(characters: Array)
signal roll_requested(roll_type: String)
signal roll_completed

@export var data_manager: DataManager

var current_date: String = ""
var current_location: String = ""
var current_chapter: int = 1
var chapter_title: String = ""
var scene_characters: Array = []
var awaiting_roll: bool = false
var roll_type: String = ""  # "persuasion", "chaos", or ""
var last_save_time: String = ""
var running_summary: String = ""

# Track which call type to use for prompt assembly
var current_call_type: String = "narrative"  # narrative, persuasion, chaos, roll_result, year_end, battle

# Event count for profile refresh tracking
var logged_event_count: int = 0


func _ready() -> void:
	if data_manager == null:
		push_error("GameStateManager: DataManager not assigned")


func initialize_new_campaign(campaign_name: String) -> void:
	data_manager.campaign_name = campaign_name
	data_manager.ensure_campaign_dirs()

	scene_characters = []
	awaiting_roll = false
	roll_type = ""
	running_summary = ""
	current_call_type = "narrative"
	logged_event_count = 0

	# Load starter data from bundled resources
	var starter_characters = data_manager.load_bundled_json("res://resources/data/characters.json")
	if starter_characters != null:
		data_manager.save_json("characters.json", starter_characters)
		print("Campaign init: loaded %d characters" % starter_characters.get("characters", []).size())
	else:
		data_manager.save_json("characters.json", {"characters": []})
		push_warning("Campaign init: no starter characters found, starting empty")

	var starter_events = data_manager.load_bundled_json("res://resources/data/starter_events.json")
	if starter_events != null:
		data_manager.save_json("events.json", starter_events)
		print("Campaign init: loaded %d events" % starter_events.get("events", []).size())
	else:
		data_manager.save_json("events.json", {"events": [], "next_id": 1})
		push_warning("Campaign init: no starter events found, starting empty")

	# Derive date and location from the last event
	_derive_state_from_data()

	# Initialize remaining data files as empty
	data_manager.save_json("factions.json", {"factions": []})
	data_manager.save_json("laws.json", {"laws": []})
	data_manager.save_json("timeline.json", {"scheduled_events": [], "past_events": []})
	data_manager.save_json("roll_history.json", {"rolls": []})
	data_manager.save_json("economy.json", {
		"current_year": int(current_date.left(4)) if current_date.length() >= 4 else 1433,
		"currency": "maravedís",
		"regions": [],
		"treasury": {
			"opening_balance": 0,
			"total_revenue": 0,
			"total_expenses": 0,
			"closing_balance": 0,
			"expense_breakdown": {}
		}
	})

	save_game_state()
	state_changed.emit()


func load_campaign(campaign_name: String) -> bool:
	data_manager.campaign_name = campaign_name
	var state = data_manager.load_json("game_state.json")
	if state == null:
		push_error("GameStateManager: No game_state.json found for campaign '%s'" % campaign_name)
		return false

	current_date = state.get("current_date", "")
	current_location = state.get("current_location", "")
	current_chapter = state.get("current_chapter", 1)
	chapter_title = state.get("chapter_title", "")
	scene_characters = state.get("scene_characters", [])
	awaiting_roll = state.get("awaiting_roll", false)
	roll_type = state.get("roll_type", "")
	last_save_time = state.get("last_save", "")
	running_summary = state.get("running_summary", "")
	current_call_type = state.get("current_call_type", "narrative")
	logged_event_count = state.get("logged_event_count", 0)

	# Sanitize stale call types from legacy saves
	if current_call_type == "chapter_start":
		current_call_type = "narrative"
	if not awaiting_roll and current_call_type == "roll_result":
		current_call_type = "narrative"

	# Always derive date/location from the last event — this is authoritative
	_derive_state_from_data()

	state_changed.emit()
	return true


func save_game_state() -> void:
	last_save_time = Time.get_datetime_string_from_system(true)
	var state := {
		"current_date": current_date,
		"current_location": current_location,
		"current_chapter": current_chapter,
		"chapter_title": chapter_title,
		"scene_characters": scene_characters,
		"awaiting_roll": awaiting_roll,
		"roll_type": roll_type,
		"last_save": last_save_time,
		"running_summary": running_summary,
		"current_call_type": current_call_type,
		"logged_event_count": logged_event_count,
	}
	data_manager.save_json("game_state.json", state)


func update_from_metadata(metadata: Dictionary) -> void:
	var changed := false

	if metadata.has("scene_characters"):
		var new_chars: Array = metadata["scene_characters"]
		if new_chars != scene_characters:
			scene_characters = new_chars
			scene_characters_changed.emit(scene_characters)
			changed = true

	if metadata.has("location") and metadata["location"] != current_location:
		current_location = metadata["location"]
		location_changed.emit(current_location)
		changed = true

	if metadata.has("date") and metadata["date"] != current_date:
		current_date = metadata["date"]
		date_changed.emit(current_date)
		changed = true

	if metadata.has("awaiting_roll"):
		var was_awaiting := awaiting_roll
		awaiting_roll = metadata["awaiting_roll"]
		if metadata.has("roll_type") and metadata["roll_type"] != null:
			roll_type = metadata["roll_type"]
		else:
			roll_type = ""

		if awaiting_roll and not was_awaiting:
			current_call_type = roll_type if roll_type != "" else "narrative"
			roll_requested.emit(roll_type)
		elif not awaiting_roll and was_awaiting:
			current_call_type = "narrative"
			roll_completed.emit()
		changed = true

	if metadata.has("summary_update") and metadata["summary_update"] != "":
		running_summary += "\n" + metadata["summary_update"]
		changed = true

	# Auto-log events from metadata
	if metadata.has("events") and metadata["events"] is Array and not metadata["events"].is_empty():
		_auto_log_events(metadata["events"])
		logged_event_count += metadata["events"].size()
		changed = true

	if changed:
		save_game_state()
		state_changed.emit()


func _auto_log_events(new_events: Array) -> void:
	var events_data = data_manager.load_json("events.json")
	if events_data == null:
		events_data = {"events": [], "next_id": 1}

	for evt in new_events:
		var event_id: int = events_data.get("next_id", 1)
		var event_entry := {
			"event_id": "evt_%04d" % event_id,
			"date": current_date,
			"type": evt.get("type", "decision"),
			"summary": evt.get("summary", ""),
			"characters": evt.get("characters", []),
			"factions_affected": evt.get("factions_affected", []),
			"location": current_location,
			"tags": evt.get("tags", []),
			"status": evt.get("status", "resolved"),
		}
		events_data["events"].append(event_entry)
		events_data["next_id"] = event_id + 1

	data_manager.save_json("events.json", events_data)


func set_call_type(call_type: String) -> void:
	current_call_type = call_type
	save_game_state()


func submit_roll(value: int) -> void:
	if not awaiting_roll:
		return

	# Log the roll
	var roll_data = data_manager.load_json("roll_history.json")
	if roll_data == null:
		roll_data = {"rolls": []}

	roll_data["rolls"].append({
		"date": current_date,
		"roll_type": roll_type,
		"value": value,
		"timestamp": Time.get_datetime_string_from_system(true),
	})
	data_manager.save_json("roll_history.json", roll_data)

	# Update state — the roll result call type keeps the same skill context
	current_call_type = "roll_result"
	awaiting_roll = false
	save_game_state()
	roll_completed.emit()
	state_changed.emit()


## Derives current date and location from the last event in events.json.
## This is the authoritative source for game timeline position.
func _derive_state_from_data() -> void:
	var events_data = data_manager.load_json("events.json")
	if events_data == null or not events_data.has("events"):
		return
	var events: Array = events_data["events"]
	if events.is_empty():
		return

	var last_event: Dictionary = events.back()
	var evt_date: String = last_event.get("date", "")
	var evt_location: String = last_event.get("location", "")

	if evt_date != "":
		if evt_date != current_date:
			current_date = evt_date
	if evt_location != "":
		if evt_location != current_location:
			current_location = evt_location
