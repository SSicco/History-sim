## Manages King Juan II's profile (Layer 3 of the prompt system).
## Stored in juan_profile.txt as JSON with profile_text, last_refresh_event_count, last_updated.
## Refreshed every 8 events via a Haiku call through the ContextAgent.
class_name ProfileManager
extends Node

const REFRESH_INTERVAL := 8  # Refresh every 8 logged events

var data_manager: DataManager
var context_agent: ContextAgent

## Current profile state
var _profile_text: String = ""
var _last_refresh_event_count: int = 0
var _total_event_count: int = 0


## Loads the profile from disk, or initializes with the bootstrap template.
func load_profile() -> void:
	if data_manager == null:
		_profile_text = get_initial_template()
		return

	var profile_data = data_manager.load_json("juan_profile.txt")
	if profile_data != null and profile_data is Dictionary:
		_profile_text = profile_data.get("profile_text", get_initial_template())
		_last_refresh_event_count = profile_data.get("last_refresh_event_count", 0)
		_total_event_count = _last_refresh_event_count
	else:
		_profile_text = get_initial_template()
		save_profile()


## Saves the current profile to disk.
func save_profile() -> void:
	if data_manager == null:
		return

	var profile_data := {
		"profile_text": _profile_text,
		"last_refresh_event_count": _last_refresh_event_count,
		"last_updated": Time.get_datetime_string_from_system(true),
	}
	data_manager.save_json("juan_profile.txt", profile_data)


## Returns the current profile text for prompt injection.
func get_profile_text() -> String:
	return _profile_text


## Called when new events are logged. Checks if a refresh is needed.
## Returns true if a refresh was triggered.
func on_events_logged(new_event_count: int) -> bool:
	_total_event_count += new_event_count

	var events_since_refresh := _total_event_count - _last_refresh_event_count
	if events_since_refresh >= REFRESH_INTERVAL:
		_trigger_refresh()
		return true

	return false


## Triggers a profile refresh via the ContextAgent's Haiku call.
func _trigger_refresh() -> void:
	if context_agent == null or data_manager == null:
		return

	# Get the last 8 events
	var events_data = data_manager.load_json("events.json")
	var recent_events: Array = []
	if events_data != null and events_data.has("events"):
		var all_events: Array = events_data["events"]
		var start_idx := maxi(0, all_events.size() - 8)
		recent_events = all_events.slice(start_idx)

	# Get royal family characters
	var royal_family := _get_royal_family()

	# Get current date from events
	var current_date := ""
	if not recent_events.is_empty():
		current_date = recent_events.back().get("date", "")

	context_agent.request_profile_refresh(
		_profile_text,
		recent_events,
		current_date,
		royal_family
	)


## Called when the ContextAgent returns a refreshed profile.
func apply_refresh(new_profile_text: String) -> void:
	_profile_text = new_profile_text
	_last_refresh_event_count = _total_event_count
	save_profile()


## Gets royal family characters from the database.
func _get_royal_family() -> Array:
	if data_manager == null:
		return []

	var characters_data = data_manager.load_json("characters.json")
	if characters_data == null or not characters_data.has("characters"):
		return []

	var royal: Array = []
	for c in characters_data["characters"]:
		if c is Dictionary:
			var cats: Array = c.get("category", [])
			if "royal_family" in cats:
				royal.append(c)

	return royal


## Initial bootstrap profile for new campaigns.
static func get_initial_template() -> String:
	return """Juan II of Castile, born March 6, 1405, is the reigning King of Castile and León. He ascended to the throne as an infant and has ruled under regencies for most of his life. Now twenty-four years old, he seeks to establish his personal authority over a kingdom dominated by powerful nobles.

FAMILY:
- Wife: María of Aragón (born 1396-09-14), Queen consort. Their marriage ties Castile to the Crown of Aragón.
- Son: Enrique, Prince of Asturias (born 1425-01-05), heir to the throne.
- Daughter: Catalina (born 1422-10-04).

STORY ARC:
Juan's reign has been shaped by the tension between royal authority and noble power. His chief minister, Álvaro de Luna, Constable of Castile, wields enormous influence — a source of both strength and resentment among the grandes. The Infantes of Aragón, Juan's cousins, have repeatedly challenged his authority from their bases in Aragón and Navarre.

CURRENT SITUATION:
The year is 1430. Juan holds court in Valladolid, the political heart of Castile. The kingdom faces pressure from multiple directions: the ongoing frontier with Granada, the ambitions of the Aragonese Infantes, and the ever-present jockeying among Castilian nobles for royal favor and territorial advantage.

KEY RELATIONSHIPS:
- Álvaro de Luna: Chief minister and closest confidant. Polarizing figure at court.
- Count of Haro: Powerful northern noble, wary of Luna's influence.
- Archbishop of Toledo: Head of the Castilian Church, political actor in his own right.
- Juan of Navarre: Cousin and rival, King of Navarre, leader of the Aragonese faction."""
