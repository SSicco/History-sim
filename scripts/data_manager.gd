## Handles all JSON file I/O for game data.
## Reads and writes characters, events, economy, laws, conversations, etc.
class_name DataManager
extends Node

const SAVE_BASE_DIR := "user://save_data"

var campaign_name: String = ""


func get_campaign_dir() -> String:
	return SAVE_BASE_DIR.path_join(campaign_name)


func ensure_campaign_dirs() -> void:
	var base := get_campaign_dir()
	for subdir in ["conversations", "chapter_summaries", "portraits"]:
		DirAccess.make_dir_recursive_absolute(base.path_join(subdir))


## Saves a dictionary as JSON to a file within the campaign directory.
func save_json(filename: String, data: Variant) -> Error:
	var path := get_campaign_dir().path_join(filename)
	var dir_path := path.get_base_dir()
	DirAccess.make_dir_recursive_absolute(dir_path)

	var json_string := JSON.stringify(data, "\t")
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		push_error("DataManager: Failed to open %s for writing: %s" % [path, error_string(FileAccess.get_open_error())])
		return FileAccess.get_open_error()

	file.store_string(json_string)
	file.close()
	return OK


## Loads a JSON file from the campaign directory. Returns null on failure.
func load_json(filename: String) -> Variant:
	var path := get_campaign_dir().path_join(filename)
	if not FileAccess.file_exists(path):
		return null

	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		push_error("DataManager: Failed to open %s for reading: %s" % [path, error_string(FileAccess.get_open_error())])
		return null

	var text := file.get_as_text()
	file.close()

	if text.is_empty():
		return null

	var json := JSON.new()
	var err := json.parse(text)
	if err != OK:
		push_error("DataManager: JSON parse error in %s at line %d: %s" % [path, json.get_error_line(), json.get_error_message()])
		return null

	return json.data


## Saves a conversation log for a specific in-game date.
func save_conversation(date_str: String, data: Dictionary) -> Error:
	return save_json("conversations/%s.json" % date_str, data)


## Loads a conversation log for a specific in-game date.
func load_conversation(date_str: String) -> Variant:
	return load_json("conversations/%s.json" % date_str)


## Returns a list of all conversation date strings available.
func list_conversation_dates() -> PackedStringArray:
	var dates: PackedStringArray = []
	var dir_path := get_campaign_dir().path_join("conversations")
	var dir := DirAccess.open(dir_path)
	if dir == null:
		return dates

	dir.list_dir_begin()
	var file_name := dir.get_next()
	while file_name != "":
		if file_name.ends_with(".json"):
			dates.append(file_name.get_basename())
		file_name = dir.get_next()
	dir.list_dir_end()

	dates.sort()
	return dates


## Saves a chapter summary.
func save_chapter_summary(chapter_num: int, data: Dictionary) -> Error:
	return save_json("chapter_summaries/chapter_%02d.json" % chapter_num, data)


## Loads a chapter summary.
func load_chapter_summary(chapter_num: int) -> Variant:
	return load_json("chapter_summaries/chapter_%02d.json" % chapter_num)


## Saves the app-level config (API key, model preferences).
## This is stored outside the campaign directory.
func save_config(data: Dictionary) -> Error:
	var path := "user://config.json"
	var json_string := JSON.stringify(data, "\t")
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	file.store_string(json_string)
	file.close()
	return OK


## Loads the app-level config.
func load_config() -> Variant:
	var path := "user://config.json"
	if not FileAccess.file_exists(path):
		return null

	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return null

	var text := file.get_as_text()
	file.close()

	if text.is_empty():
		return null

	var json := JSON.new()
	var err := json.parse(text)
	if err != OK:
		return null

	return json.data


## Lists all campaigns (subdirectories under save_data/).
func list_campaigns() -> PackedStringArray:
	var campaigns: PackedStringArray = []
	var dir := DirAccess.open(SAVE_BASE_DIR)
	if dir == null:
		return campaigns

	dir.list_dir_begin()
	var name := dir.get_next()
	while name != "":
		if dir.current_is_dir() and not name.begins_with("."):
			campaigns.append(name)
		name = dir.get_next()
	dir.list_dir_end()

	return campaigns
