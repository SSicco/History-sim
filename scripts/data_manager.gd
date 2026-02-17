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
	for subdir in ["portraits"]:
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


## Loads a JSON file bundled in the project (res://) — used for starter data.
func load_bundled_json(res_path: String) -> Variant:
	if not FileAccess.file_exists(res_path):
		push_error("DataManager: Bundled file not found: %s" % res_path)
		return null

	var file := FileAccess.open(res_path, FileAccess.READ)
	if file == null:
		push_error("DataManager: Failed to open bundled %s: %s" % [res_path, error_string(FileAccess.get_open_error())])
		return null

	var text := file.get_as_text()
	file.close()

	if text.is_empty():
		return null

	var json := JSON.new()
	var err := json.parse(text)
	if err != OK:
		push_error("DataManager: JSON parse error in %s at line %d: %s" % [res_path, json.get_error_line(), json.get_error_message()])
		return null

	return json.data


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


## Returns the portrait directory for a character.
func get_portrait_dir(character_id: String) -> String:
	return get_campaign_dir().path_join("portraits").path_join(character_id)


## Ensures portrait subdirectory exists for a character.
func ensure_portrait_dir(character_id: String) -> void:
	DirAccess.make_dir_recursive_absolute(get_portrait_dir(character_id))


## Lists all campaigns (subdirectories under save_data/).
func list_campaigns() -> PackedStringArray:
	var campaigns: PackedStringArray = []
	var dir := DirAccess.open(SAVE_BASE_DIR)
	if dir == null:
		return campaigns

	dir.list_dir_begin()
	var dir_name := dir.get_next()
	while dir_name != "":
		if dir.current_is_dir() and not dir_name.begins_with("."):
			campaigns.append(dir_name)
		dir_name = dir.get_next()
	dir.list_dir_end()

	return campaigns
