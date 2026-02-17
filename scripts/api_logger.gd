## Logs every API call with model, usage breakdown, and cost calculation.
## Persists logs to api_logs/ directory in the campaign folder.
class_name ApiLogger
extends Node

var data_manager: DataManager

## Pricing table (per million tokens)
const PRICING := {
	"claude-sonnet-4-5-20250929": {
		"input": 3.00,
		"output": 15.00,
		"cache_write": 3.75,
		"cache_read": 0.30,
	},
	"claude-haiku-4-5-20251001": {
		"input": 0.80,
		"output": 4.00,
		"cache_write": 1.00,
		"cache_read": 0.08,
	},
}

## Running totals for the current session
var _session_total_cost: float = 0.0
var _session_call_count: int = 0


## Logs an API call with full usage details.
## usage: Dictionary from the API response with input_tokens, output_tokens, etc.
## call_info: Dictionary with model, call_type, request_summary, response_summary.
func log_call(call_info: Dictionary, usage: Dictionary) -> void:
	var model: String = call_info.get("model", "unknown")
	var call_type: String = call_info.get("call_type", "unknown")

	var input_tokens: int = usage.get("input_tokens", 0)
	var output_tokens: int = usage.get("output_tokens", 0)

	# Cache usage is nested under cache_creation and cache_read_input
	var cache_write_tokens: int = 0
	var cache_read_tokens: int = 0
	if usage.has("cache_creation_input_tokens"):
		cache_write_tokens = usage["cache_creation_input_tokens"]
	if usage.has("cache_read_input_tokens"):
		cache_read_tokens = usage["cache_read_input_tokens"]

	var cost := _calculate_cost(model, input_tokens, output_tokens, cache_write_tokens, cache_read_tokens)

	_session_total_cost += cost
	_session_call_count += 1

	var log_entry := {
		"timestamp": Time.get_datetime_string_from_system(true),
		"model": model,
		"call_type": call_type,
		"usage": {
			"input_tokens": input_tokens,
			"output_tokens": output_tokens,
			"cache_write_tokens": cache_write_tokens,
			"cache_read_tokens": cache_read_tokens,
		},
		"cost_usd": snapped(cost, 0.000001),
		"request_summary": call_info.get("request_summary", ""),
		"response_summary": call_info.get("response_summary", ""),
	}

	_persist_log(log_entry)


## Calculates cost in USD for a single API call.
func _calculate_cost(model: String, input_tokens: int, output_tokens: int, cache_write_tokens: int, cache_read_tokens: int) -> float:
	var prices: Dictionary = PRICING.get(model, PRICING.get("claude-sonnet-4-5-20250929"))

	var cost := 0.0
	cost += (input_tokens / 1_000_000.0) * prices["input"]
	cost += (output_tokens / 1_000_000.0) * prices["output"]
	cost += (cache_write_tokens / 1_000_000.0) * prices["cache_write"]
	cost += (cache_read_tokens / 1_000_000.0) * prices["cache_read"]

	return cost


## Persists a log entry to the api_logs/ directory.
func _persist_log(entry: Dictionary) -> void:
	if data_manager == null:
		return

	var timestamp: String = entry.get("timestamp", "")
	var call_num: String = "%03d" % _session_call_count
	var filename := "api_logs/%s_%s.json" % [timestamp.replace(":", "-"), call_num]
	data_manager.save_json(filename, entry)


## Returns session totals for display.
func get_session_stats() -> Dictionary:
	return {
		"total_cost_usd": snapped(_session_total_cost, 0.000001),
		"call_count": _session_call_count,
	}


## Resets session totals (e.g., when loading a new campaign).
func reset_session() -> void:
	_session_total_cost = 0.0
	_session_call_count = 0
