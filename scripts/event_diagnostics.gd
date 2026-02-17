## Tracks per-event statistics: exchange count, context pulls, costs, and end reason.
## An "event" is a sequence of exchanges between sticky context resets.
class_name EventDiagnostics
extends Node

var data_manager: DataManager

## Current event tracking
var _current_event_id: int = 0
var _event_exchange_count: int = 0
var _event_context_pulls: int = 0
var _event_cost: float = 0.0
var _event_start_time: String = ""
var _sticky_snapshots: Array = []


## Starts tracking a new event.
func begin_event() -> void:
	# Save the previous event if it had any exchanges
	if _event_exchange_count > 0:
		_save_current_event("new_event")

	_current_event_id += 1
	_event_exchange_count = 0
	_event_context_pulls = 0
	_event_cost = 0.0
	_event_start_time = Time.get_datetime_string_from_system(true)
	_sticky_snapshots = []


## Records an exchange within the current event.
func record_exchange(cost: float) -> void:
	_event_exchange_count += 1
	_event_cost += cost


## Records a context pull (search performed by ContextAgent).
func record_context_pull() -> void:
	_event_context_pulls += 1


## Records a sticky context snapshot for diagnostics.
func record_sticky_snapshot(snapshot: Dictionary) -> void:
	_sticky_snapshots.append({
		"exchange": _event_exchange_count,
		"snapshot": snapshot,
	})


## Ends the current event with a reason (overflow, location_change, session_end).
func end_event(reason: String) -> void:
	_save_current_event(reason)


## Saves the current event diagnostics to disk.
func _save_current_event(end_reason: String) -> void:
	if data_manager == null:
		return

	var event_data := {
		"event_number": _current_event_id,
		"start_time": _event_start_time,
		"end_time": Time.get_datetime_string_from_system(true),
		"end_reason": end_reason,
		"exchange_count": _event_exchange_count,
		"context_pulls": _event_context_pulls,
		"total_cost_usd": snapped(_event_cost, 0.000001),
		"sticky_snapshots": _sticky_snapshots,
	}

	var filename := "diagnostics/event_%03d.json" % _current_event_id
	data_manager.save_json(filename, event_data)


## Returns current event stats for display.
func get_current_stats() -> Dictionary:
	return {
		"event_id": _current_event_id,
		"exchanges": _event_exchange_count,
		"context_pulls": _event_context_pulls,
		"cost": snapped(_event_cost, 0.000001),
	}
