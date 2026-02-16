## Manages character portrait generation, caching, and retrieval.
## Handles DALL-E API calls to generate portraits from structured appearance data
## and stores them per-campaign in portraits/{character_id}/.
class_name PortraitManager
extends Node

signal portrait_ready(character_id: String, texture: ImageTexture)
signal portrait_failed(character_id: String, error: String)
signal generation_started(character_id: String)

const OPENAI_API_URL := "https://api.openai.com/v1/images/generations"
const PORTRAIT_SIZE := "1024x1024"
const PORTRAIT_MODEL := "dall-e-3"

@export var data_manager: DataManager

var openai_api_key: String = ""
var _http_request: HTTPRequest
var _pending_character_id: String = ""
var _pending_context: String = ""
var _is_generating: bool = false

## Queue for portrait generation requests: [{character_id, context}]
var _generation_queue: Array = []

## In-memory texture cache: character_id -> {context -> ImageTexture}
var _texture_cache: Dictionary = {}

## Portrait metadata: tracks generated portraits per character
## Stored as portraits_meta.json in campaign dir
var _portraits_meta: Dictionary = {}


func _ready() -> void:
	_http_request = HTTPRequest.new()
	_http_request.timeout = 120.0
	add_child(_http_request)
	_http_request.request_completed.connect(_on_generation_completed)
	_load_openai_config()


func _load_openai_config() -> void:
	if data_manager == null:
		return
	var config = data_manager.load_config()
	if config != null:
		openai_api_key = config.get("openai_api_key", "")


func save_openai_config() -> void:
	if data_manager == null:
		return
	var config = data_manager.load_config()
	if config == null:
		config = {}
	config["openai_api_key"] = openai_api_key
	data_manager.save_config(config)


func is_configured() -> bool:
	return openai_api_key != "" and openai_api_key.length() > 10


func is_generating() -> bool:
	return _is_generating


## Returns the portrait directory path for a character in the current campaign.
func _get_portrait_dir(character_id: String) -> String:
	return data_manager.get_campaign_dir().path_join("portraits").path_join(character_id)


## Returns the file path for a specific portrait variant.
func _get_portrait_path(character_id: String, context: String) -> String:
	return _get_portrait_dir(character_id).path_join("%s.png" % context)


## Loads portrait metadata from disk.
func load_portraits_meta() -> void:
	var meta = data_manager.load_json("portraits_meta.json")
	if meta != null:
		_portraits_meta = meta
	else:
		_portraits_meta = {"portraits": {}}


## Saves portrait metadata to disk.
func _save_portraits_meta() -> void:
	data_manager.save_json("portraits_meta.json", _portraits_meta)


## Checks if a portrait exists on disk for the given character and context.
func has_portrait(character_id: String, context: String = "default") -> bool:
	var path := _get_portrait_path(character_id, context)
	return FileAccess.file_exists(path)


## Gets a cached texture or loads from disk. Returns null if not available.
func get_portrait_texture(character_id: String, context: String = "default") -> ImageTexture:
	# Check memory cache first
	if _texture_cache.has(character_id) and _texture_cache[character_id].has(context):
		return _texture_cache[character_id][context]

	# Try loading from disk
	var path := _get_portrait_path(character_id, context)
	if not FileAccess.file_exists(path):
		return null

	var image := Image.new()
	var err := image.load(path)
	if err != OK:
		push_warning("PortraitManager: Failed to load portrait %s: %s" % [path, error_string(err)])
		return null

	var texture := ImageTexture.create_from_image(image)

	# Cache it
	if not _texture_cache.has(character_id):
		_texture_cache[character_id] = {}
	_texture_cache[character_id][context] = texture

	return texture


## Gets the best available portrait texture for a character.
## Tries the requested context first, then falls back to "default", then "court".
func get_best_portrait(character_id: String, preferred_context: String = "default") -> ImageTexture:
	var fallback_order := [preferred_context, "default", "court", "prayer"]
	for ctx in fallback_order:
		var tex := get_portrait_texture(character_id, ctx)
		if tex != null:
			return tex
	return null


## Returns existing portrait or queues generation if none exists.
## Call this instead of get_best_portrait when you want auto-generation.
func ensure_portrait(character_id: String, context: String = "default") -> ImageTexture:
	var tex := get_best_portrait(character_id, context)
	if tex != null:
		return tex

	# No portrait exists — queue generation if configured
	if not is_configured():
		return null

	# Check if already queued or currently generating this character
	if _pending_character_id == character_id:
		return null
	for queued in _generation_queue:
		if queued["character_id"] == character_id:
			return null

	var appearance := get_character_appearance(character_id)
	if appearance.is_empty():
		return null

	if _is_generating:
		_generation_queue.append({"character_id": character_id, "context": context})
	else:
		generate_portrait(character_id, appearance, context)

	return null


## Processes the next item in the generation queue.
func _process_generation_queue() -> void:
	if _is_generating or _generation_queue.is_empty():
		return

	var next: Dictionary = _generation_queue.pop_front()
	var char_id: String = next["character_id"]
	var context: String = next["context"]

	# Skip if portrait was generated in the meantime
	if get_best_portrait(char_id) != null:
		_process_generation_queue()
		return

	var appearance := get_character_appearance(char_id)
	if appearance.is_empty():
		_process_generation_queue()
		return

	generate_portrait(char_id, appearance, context)


## Lists all available portrait contexts for a character (from disk).
func list_character_portraits(character_id: String) -> PackedStringArray:
	var contexts: PackedStringArray = []
	var dir_path := _get_portrait_dir(character_id)
	var dir := DirAccess.open(dir_path)
	if dir == null:
		return contexts

	dir.list_dir_begin()
	var file_name := dir.get_next()
	while file_name != "":
		if file_name.ends_with(".png"):
			contexts.append(file_name.get_basename())
		file_name = dir.get_next()
	dir.list_dir_end()

	return contexts


## Generates a portrait for a character using DALL-E.
## character_id: The canonical character ID.
## appearance: The structured appearance dictionary from character data.
## context: The scene context ("default", "court", "battle", "prayer").
## character_name: Display name for metadata.
func generate_portrait(character_id: String, appearance: Dictionary, context: String = "default", _character_name: String = "") -> void:
	if not is_configured():
		portrait_failed.emit(character_id, "OpenAI API key not configured. Set it in Settings.")
		return

	if _is_generating:
		portrait_failed.emit(character_id, "A portrait generation is already in progress.")
		return

	if appearance.is_empty():
		portrait_failed.emit(character_id, "No appearance data available for %s." % character_id)
		return

	var prompt := PortraitPromptBuilder.build_prompt(appearance, context)
	if prompt == "":
		portrait_failed.emit(character_id, "Failed to build prompt for %s." % character_id)
		return

	_pending_character_id = character_id
	_pending_context = context
	_is_generating = true
	generation_started.emit(character_id)

	var headers := PackedStringArray([
		"Content-Type: application/json",
		"Authorization: Bearer %s" % openai_api_key,
	])

	var body := JSON.stringify({
		"model": PORTRAIT_MODEL,
		"prompt": prompt,
		"n": 1,
		"size": PORTRAIT_SIZE,
		"response_format": "b64_json",
	})

	var err := _http_request.request(OPENAI_API_URL, headers, HTTPClient.METHOD_POST, body)
	if err != OK:
		_is_generating = false
		portrait_failed.emit(character_id, "Failed to send portrait generation request: %s" % error_string(err))
		_process_generation_queue()


func _on_generation_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	_is_generating = false
	var char_id := _pending_character_id
	var context := _pending_context

	if result != HTTPRequest.RESULT_SUCCESS:
		portrait_failed.emit(char_id, "Network error during portrait generation (code: %d)" % result)
		_process_generation_queue()
		return

	var response_text := body.get_string_from_utf8()

	if response_code != 200:
		var error_msg := "DALL-E API error (HTTP %d)" % response_code
		var err_json := JSON.new()
		if err_json.parse(response_text) == OK and err_json.data is Dictionary:
			var err_data: Dictionary = err_json.data
			if err_data.has("error") and err_data["error"] is Dictionary:
				error_msg += ": %s" % err_data["error"].get("message", "Unknown error")
		portrait_failed.emit(char_id, error_msg)
		_process_generation_queue()
		return

	# Parse response
	var json := JSON.new()
	if json.parse(response_text) != OK:
		portrait_failed.emit(char_id, "Failed to parse DALL-E response.")
		_process_generation_queue()
		return

	var data: Dictionary = json.data
	if not data.has("data") or not data["data"] is Array or data["data"].is_empty():
		portrait_failed.emit(char_id, "DALL-E response missing image data.")
		_process_generation_queue()
		return

	var image_data: Dictionary = data["data"][0]
	var b64_string: String = image_data.get("b64_json", "")
	if b64_string == "":
		portrait_failed.emit(char_id, "DALL-E response missing base64 image data.")
		_process_generation_queue()
		return

	# Decode base64 to image
	var image_bytes := Marshalls.base64_to_raw(b64_string)
	var image := Image.new()
	var err := image.load_png_from_buffer(image_bytes)
	if err != OK:
		portrait_failed.emit(char_id, "Failed to decode portrait image: %s" % error_string(err))
		_process_generation_queue()
		return

	# Save to disk
	var portrait_dir := _get_portrait_dir(char_id)
	DirAccess.make_dir_recursive_absolute(portrait_dir)
	var save_path := _get_portrait_path(char_id, context)
	err = image.save_png(save_path)
	if err != OK:
		portrait_failed.emit(char_id, "Failed to save portrait: %s" % error_string(err))
		_process_generation_queue()
		return

	# Update metadata
	if not _portraits_meta.has("portraits"):
		_portraits_meta["portraits"] = {}
	if not _portraits_meta["portraits"].has(char_id):
		_portraits_meta["portraits"][char_id] = {}
	_portraits_meta["portraits"][char_id][context] = {
		"generated_at": Time.get_datetime_string_from_system(true),
		"model": PORTRAIT_MODEL,
		"size": PORTRAIT_SIZE,
	}
	_save_portraits_meta()

	# Create texture and cache
	var texture := ImageTexture.create_from_image(image)
	if not _texture_cache.has(char_id):
		_texture_cache[char_id] = {}
	_texture_cache[char_id][context] = texture

	print("PortraitManager: Generated portrait for %s (%s)" % [char_id, context])
	portrait_ready.emit(char_id, texture)
	_process_generation_queue()


## Clears the in-memory texture cache.
func clear_cache() -> void:
	_texture_cache.clear()


## Gets appearance data for a character from the campaign's characters.json.
func get_character_appearance(character_id: String) -> Dictionary:
	var characters_data = data_manager.load_json("characters.json")
	if characters_data == null or not characters_data.has("characters"):
		return {}

	for character in characters_data["characters"]:
		if character is Dictionary and character.get("id") == character_id:
			return character.get("appearance", {})

	return {}


## Gets the display name for a character from the campaign's characters.json.
func get_character_name(character_id: String) -> String:
	var characters_data = data_manager.load_json("characters.json")
	if characters_data == null or not characters_data.has("characters"):
		return character_id

	for character in characters_data["characters"]:
		if character is Dictionary and character.get("id") == character_id:
			return character.get("name", character_id)

	return character_id
