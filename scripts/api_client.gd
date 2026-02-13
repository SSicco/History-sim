## HTTP client for the Anthropic Claude API.
## Handles sending messages, retry logic, and response parsing.
class_name ApiClient
extends Node

signal response_received(narrative: String, metadata: Dictionary)
signal request_started
signal request_failed(error_message: String)


const API_URL := "https://api.anthropic.com/v1/messages"
const API_VERSION := "2023-06-01"
const MAX_RETRIES := 3
const RETRY_DELAYS := [2.0, 5.0, 15.0]

@export var data_manager: DataManager

var api_key: String = ""
var model: String = "claude-sonnet-4-5-20250514"
var _http_request: HTTPRequest
var _retry_count: int = 0
var _pending_body: Dictionary = {}
var _is_requesting: bool = false


func _ready() -> void:
	_http_request = HTTPRequest.new()
	_http_request.timeout = 120.0
	add_child(_http_request)
	_http_request.request_completed.connect(_on_request_completed)
	_load_api_config()


func _load_api_config() -> void:
	if data_manager == null:
		return
	var config = data_manager.load_config()
	if config != null:
		api_key = config.get("api_key", "")
		model = config.get("model", "claude-sonnet-4-5-20250514")


func save_api_config() -> void:
	if data_manager == null:
		return
	var config = data_manager.load_config()
	if config == null:
		config = {}
	config["api_key"] = api_key
	config["model"] = model
	data_manager.save_config(config)


func is_configured() -> bool:
	return api_key != "" and api_key.length() > 10


func is_requesting() -> bool:
	return _is_requesting


## Sends a message to the Claude API.
## system_blocks: Array of system content blocks (with optional cache_control)
## messages: Array of message objects ({role, content})
## max_tokens: Maximum response tokens
func send_message(system_blocks: Array, messages: Array, max_tokens: int = 400) -> void:
	if not is_configured():
		request_failed.emit("API key not configured. Please set your API key in Settings.")
		return

	if _is_requesting:
		request_failed.emit("A request is already in progress.")
		return

	_pending_body = {
		"model": model,
		"max_tokens": max_tokens,
		"system": system_blocks,
		"messages": messages,
	}

	_retry_count = 0
	_is_requesting = true
	request_started.emit()
	_do_request()


func _do_request() -> void:
	var headers := PackedStringArray([
		"Content-Type: application/json",
		"x-api-key: %s" % api_key,
		"anthropic-version: %s" % API_VERSION,
		"anthropic-beta: prompt-caching-2024-07-31",
	])

	var body := JSON.stringify(_pending_body)
	var err := _http_request.request(API_URL, headers, HTTPClient.METHOD_POST, body)
	if err != OK:
		_handle_error("Failed to send HTTP request: %s" % error_string(err))


func _on_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS:
		_handle_error("Network error (result code: %d). Your message is saved." % result)
		return

	var response_text := body.get_string_from_utf8()

	if response_code == 429:
		_handle_error("API rate limited. Retrying...")
		return

	if response_code != 200:
		var error_msg := "API error (HTTP %d)" % response_code
		# Try to extract error message from response
		var err_json := JSON.new()
		if err_json.parse(response_text) == OK and err_json.data is Dictionary:
			var err_data: Dictionary = err_json.data
			if err_data.has("error") and err_data["error"] is Dictionary:
				error_msg += ": %s" % err_data["error"].get("message", "Unknown error")
		_handle_error(error_msg)
		return

	# Parse successful response
	var json := JSON.new()
	if json.parse(response_text) != OK:
		_handle_error("Failed to parse API response JSON.")
		return

	var data: Dictionary = json.data
	if not data.has("content") or not data["content"] is Array or data["content"].is_empty():
		_handle_error("API response missing content.")
		return

	var content_text := ""
	for block in data["content"]:
		if block is Dictionary and block.get("type") == "text":
			content_text += block["text"]

	_is_requesting = false
	_retry_count = 0

	# Parse the response to separate narrative from metadata
	var parsed := ResponseParser.parse_response(content_text)
	response_received.emit(parsed["narrative"], parsed["metadata"])


func _handle_error(message: String) -> void:
	if _retry_count < MAX_RETRIES:
		var delay: float = RETRY_DELAYS[_retry_count]
		_retry_count += 1
		push_warning("ApiClient: %s — retrying in %.0fs (attempt %d/%d)" % [message, delay, _retry_count, MAX_RETRIES])
		get_tree().create_timer(delay).timeout.connect(_do_request)
	else:
		_is_requesting = false
		_retry_count = 0
		request_failed.emit(message)


func cancel_request() -> void:
	if _is_requesting:
		_http_request.cancel_request()
		_is_requesting = false
		_retry_count = 0
