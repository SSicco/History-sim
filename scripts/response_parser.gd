## Parses Claude API responses, separating narrative text from the JSON metadata block.
## The metadata block is expected at the end of the response, wrapped in ```json``` fences.
class_name ResponseParser
extends RefCounted

## Default empty metadata returned when none is found in the response.
static var EMPTY_METADATA := {
	"scene_characters": [],
	"location": "",
	"date": "",
	"awaiting_roll": false,
	"roll_type": null,
	"summary_update": "",
	"dialogue": [],
	"juan_acted": false,
	"confidence": 1.0,
	"missing_context": [],
}


## Parses a full response string into narrative text and metadata dictionary.
## Returns {"narrative": String, "metadata": Dictionary}
static func parse_response(response_text: String) -> Dictionary:
	var narrative := ""
	var metadata: Dictionary = EMPTY_METADATA.duplicate(true)

	# Look for the last ```json ... ``` block in the response
	var json_block_start := response_text.rfind("```json")
	if json_block_start == -1:
		# No metadata block found — entire response is narrative
		return {"narrative": response_text.strip_edges(), "metadata": metadata}

	# Extract narrative (everything before the json block)
	narrative = response_text.left(json_block_start).strip_edges()

	# Extract the JSON content between ```json and ```
	var json_content_start := json_block_start + "```json".length()
	var json_block_end := response_text.find("```", json_content_start)
	if json_block_end == -1:
		# Malformed block — closing ``` not found, try to parse anyway
		json_block_end = response_text.length()

	var json_str := response_text.substr(json_content_start, json_block_end - json_content_start).strip_edges()

	# Parse JSON
	var json := JSON.new()
	var err := json.parse(json_str)
	if err != OK:
		push_warning("ResponseParser: Failed to parse metadata JSON at line %d: %s" % [json.get_error_line(), json.get_error_message()])
		return {"narrative": narrative, "metadata": metadata}

	if json.data is Dictionary:
		var parsed: Dictionary = json.data
		# Merge parsed data with defaults so all expected keys exist
		for key in EMPTY_METADATA:
			if parsed.has(key):
				metadata[key] = parsed[key]

	return {"narrative": narrative, "metadata": metadata}


## Extracts dialogue speaker information from metadata for portrait display.
## Returns an array of {speaker: String, type: String} dictionaries.
static func get_dialogue_speakers(metadata: Dictionary) -> Array:
	return metadata.get("dialogue", [])


## Checks if the response indicates Juan acted (which violates Rule 3).
## This is a self-check flag Claude includes in its metadata.
static func check_juan_acted(metadata: Dictionary) -> bool:
	return metadata.get("juan_acted", false)
