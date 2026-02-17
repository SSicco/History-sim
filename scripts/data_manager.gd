## Handles all JSON file I/O for game data.
## Reads and writes characters, events, economy, laws, conversations, etc.
## Supports test mode: when enabled, all I/O goes to a test_data/ subdirectory.
class_name DataManager
extends Node

signal test_mode_changed(enabled: bool)

const SAVE_BASE_DIR := "user://save_data"

var campaign_name: String = ""
var test_mode: bool = false


func get_campaign_dir() -> String:
	var base := SAVE_BASE_DIR.path_join(campaign_name)
	if test_mode:
		return base.path_join("test_data")
	return base


## Returns the real campaign dir (ignoring test_mode), used for reading
## bundled/reference data even while in test mode.
func get_real_campaign_dir() -> String:
	return SAVE_BASE_DIR.path_join(campaign_name)


func ensure_campaign_dirs() -> void:
	var base := get_campaign_dir()
	for subdir in ["portraits", "conversations", "chapter_summaries", "api_logs", "diagnostics"]:
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


## Deletes all files in the campaign directory (wipe & rebuild).
## If in test mode, only deletes the test_data/ subdirectory.
func delete_campaign_data() -> void:
	var target_dir := get_campaign_dir()
	_delete_dir_recursive(target_dir)


## Deletes the test_data/ subdirectory for the current campaign.
func delete_test_data() -> void:
	var test_dir := get_real_campaign_dir().path_join("test_data")
	_delete_dir_recursive(test_dir)


## Enables or disables test mode. Persists to config.
func set_test_mode(enabled: bool) -> void:
	test_mode = enabled
	var config = load_config()
	if config == null:
		config = {}
	config["test_mode"] = enabled
	save_config(config)
	test_mode_changed.emit(enabled)


## Recursively deletes a directory and all its contents.
func _delete_dir_recursive(path: String) -> void:
	var dir := DirAccess.open(path)
	if dir == null:
		return

	dir.list_dir_begin()
	var name := dir.get_next()
	while name != "":
		if name == "." or name == "..":
			name = dir.get_next()
			continue
		var full_path := path.path_join(name)
		if dir.current_is_dir():
			_delete_dir_recursive(full_path)
		else:
			dir.remove(name)
		name = dir.get_next()
	dir.list_dir_end()

	# Remove the now-empty directory itself
	var parent_path := path.get_base_dir()
	var dir_name := path.get_file()
	var parent := DirAccess.open(parent_path)
	if parent != null:
		parent.remove(dir_name)
