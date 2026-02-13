## Handles d100 roll input validation and history logging.
class_name RollEngine
extends Node

signal roll_submitted(value: int)
signal roll_invalid(reason: String)

@export var data_manager: DataManager
@export var game_state: GameStateManager


## Validates and submits a d100 roll value.
func submit_roll(input: String) -> void:
	var trimmed := input.strip_edges()

	if not trimmed.is_valid_int():
		roll_invalid.emit("Please enter a number between 1 and 100.")
		return

	var value := trimmed.to_int()
	if value < 1 or value > 100:
		roll_invalid.emit("Roll must be between 1 and 100. You entered: %d" % value)
		return

	# Delegate to game state for logging and state update
	game_state.submit_roll(value)
	roll_submitted.emit(value)


## Returns the roll history for display.
func get_roll_history() -> Array:
	if data_manager == null:
		return []

	var roll_data = data_manager.load_json("roll_history.json")
	if roll_data == null:
		return []

	return roll_data.get("rolls", [])


## Returns the most recent roll entry, or null.
func get_last_roll() -> Variant:
	var history := get_roll_history()
	if history.is_empty():
		return null
	return history[-1]
