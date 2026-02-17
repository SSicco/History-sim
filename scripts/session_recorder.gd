## Records everything about every exchange for full debugging capability.
## Captures: Haiku prompts/responses, search results, sticky snapshots,
## Sonnet prompts/responses (all 4 layers), token usage, and costs.
class_name SessionRecorder
extends Node

var data_manager: DataManager

## Current session data
var _session_id: String = ""
var _session_start: String = ""
var _exchanges: Array = []
var _current_exchange: Dictionary = {}


func _ready() -> void:
	_session_id = "rec_%s" % Time.get_datetime_string_from_system(true).replace(":", "-")
	_session_start = Time.get_datetime_string_from_system(true)


## Begins recording a new exchange.
func begin_exchange(player_input: String) -> void:
	_current_exchange = {
		"exchange_number": _exchanges.size() + 1,
		"timestamp": Time.get_datetime_string_from_system(true),
		"player_input": player_input,
		"context_agent": {},
		"search_results": {},
		"sticky_snapshot": {},
		"gm_prompt": {},
		"gm_response": {},
		"token_usage": {},
		"cost": 0.0,
	}


## Records the Context Agent (Haiku) call details.
func record_context_call(system_prompt: String, user_content: String, raw_response: String, usage: Dictionary) -> void:
	_current_exchange["context_agent"] = {
		"system_prompt_length": system_prompt.length(),
		"system_prompt_tokens": ceili(system_prompt.length() / 4.0),
		"user_content": user_content.left(500),
		"raw_response": raw_response,
		"usage": usage.duplicate(true),
	}


## Records search results from the local search engine.
func record_search_results(characters: Array, events: Array, laws: Array) -> void:
	_current_exchange["search_results"] = {
		"characters_found": characters.size(),
		"events_found": events.size(),
		"laws_found": laws.size(),
		"character_ids": characters.map(func(c): return c.get("id", "") if c is Dictionary else ""),
		"event_ids": events.map(func(e): return e.get("event_id", "") if e is Dictionary else ""),
	}


## Records the sticky context snapshot before the GM call.
func record_sticky_snapshot(snapshot: Dictionary) -> void:
	_current_exchange["sticky_snapshot"] = snapshot


## Records the GM prompt details (all 4 layers).
func record_gm_prompt(system_blocks: Array, messages: Array, max_tokens: int) -> void:
	var layer_info: Array = []
	for i in range(system_blocks.size()):
		var block: Dictionary = system_blocks[i]
		var text: String = block.get("text", "")
		layer_info.append({
			"layer": i + 1,
			"char_count": text.length(),
			"token_estimate": ceili(text.length() / 4.0),
			"preview": text.left(100) + "..." if text.length() > 100 else text,
		})

	_current_exchange["gm_prompt"] = {
		"layer_count": system_blocks.size(),
		"layers": layer_info,
		"message_count": messages.size(),
		"max_tokens": max_tokens,
		"total_system_chars": layer_info.reduce(func(acc, l): return acc + l["char_count"], 0),
	}


## Records the GM response and parsed results.
func record_gm_response(raw_response: String, narrative: String, metadata: Dictionary, usage: Dictionary) -> void:
	_current_exchange["gm_response"] = {
		"raw_length": raw_response.length(),
		"narrative_length": narrative.length(),
		"metadata": metadata.duplicate(true),
		"usage": usage.duplicate(true),
	}


## Records total cost for this exchange.
func record_exchange_cost(cost: float) -> void:
	_current_exchange["cost"] = snapped(cost, 0.000001)


## Finalizes the current exchange and adds it to the session.
func finish_exchange() -> void:
	_exchanges.append(_current_exchange.duplicate(true))
	_current_exchange = {}
	_save_session()


## Saves the full session recording to disk.
func _save_session() -> void:
	if data_manager == null:
		return

	var session_data := {
		"session_id": _session_id,
		"session_start": _session_start,
		"exchange_count": _exchanges.size(),
		"exchanges": _exchanges,
	}
	data_manager.save_json("diagnostics/%s.json" % _session_id, session_data)


## Generates a human-readable report of the session.
func save_report() -> void:
	if data_manager == null or _exchanges.is_empty():
		return

	var lines: PackedStringArray = []
	lines.append("═══ SESSION REPORT ═══")
	lines.append("Session: %s" % _session_id)
	lines.append("Started: %s" % _session_start)
	lines.append("Exchanges: %d" % _exchanges.size())
	lines.append("")

	var total_cost := 0.0
	for i in range(_exchanges.size()):
		var ex: Dictionary = _exchanges[i]
		lines.append("--- Exchange %d ---" % (i + 1))
		lines.append("Player: %s" % ex.get("player_input", "").left(100))

		var ctx: Dictionary = ex.get("context_agent", {})
		if not ctx.is_empty():
			lines.append("Context Agent: %s" % ctx.get("raw_response", "").left(100))

		var gm: Dictionary = ex.get("gm_prompt", {})
		lines.append("GM Prompt: %d layers, %d system chars" % [
			gm.get("layer_count", 0),
			gm.get("total_system_chars", 0),
		])

		var resp: Dictionary = ex.get("gm_response", {})
		lines.append("GM Response: %d chars narrative" % resp.get("narrative_length", 0))

		var cost: float = ex.get("cost", 0.0)
		total_cost += cost
		lines.append("Cost: $%.6f" % cost)
		lines.append("")

	lines.append("Total Session Cost: $%.6f" % total_cost)

	var report_text := "\n".join(lines)
	var path := "diagnostics/%s_REPORT.txt" % _session_id

	# Write as raw text, not JSON
	if data_manager != null:
		var full_path: String = data_manager.get_campaign_dir().path_join(path)
		var dir_path := full_path.get_base_dir()
		DirAccess.make_dir_recursive_absolute(dir_path)
		var file := FileAccess.open(full_path, FileAccess.WRITE)
		if file != null:
			file.store_string(report_text)
			file.close()
