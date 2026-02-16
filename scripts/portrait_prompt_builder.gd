## Builds DALL-E image generation prompts from structured character appearance data.
## Composes prompts for different contexts (court, battle, default) and age variations.
class_name PortraitPromptBuilder
extends RefCounted


## Context presets for different scene types.
const CONTEXT_PRESETS := {
	"default": {
		"clothing_field": "default_clothing",
		"background": "",
		"pose": "portrait from the chest up, facing slightly to the side",
	},
	"court": {
		"clothing_field": "court_clothing",
		"background": "ornate medieval court chamber, tapestries, candlelight",
		"pose": "formal portrait, dignified bearing, facing the viewer",
	},
	"battle": {
		"clothing_field": "battle_clothing",
		"background": "battlefield, banners in wind, dramatic sky",
		"pose": "commanding stance, alert expression",
	},
	"prayer": {
		"clothing_field": "default_clothing",
		"background": "dimly lit chapel, stained glass, candlelight",
		"pose": "contemplative expression, hands clasped or at rest",
	},
}


## Builds a DALL-E prompt from structured appearance data and a context.
## appearance: Dictionary with structured appearance fields.
## context: One of "default", "court", "battle", "prayer".
## age_override: Optional age description to override the stored one (for aging).
## Returns the prompt string ready for DALL-E.
static func build_prompt(appearance: Dictionary, context: String = "default", age_override: String = "") -> String:
	if appearance.is_empty():
		return ""

	var preset: Dictionary = CONTEXT_PRESETS.get(context, CONTEXT_PRESETS["default"])
	var parts: PackedStringArray = []

	# Art style (lead with this for DALL-E)
	var art_style: String = appearance.get("art_style", "medieval oil portrait, realistic detail")
	parts.append(art_style)

	# Pose
	parts.append(preset["pose"])

	# Gender and age
	var gender: String = appearance.get("gender", "")
	var age_desc: String = age_override if age_override != "" else appearance.get("age_description", "")
	if gender != "" and age_desc != "":
		parts.append("%s, %s" % [gender, age_desc])
	elif gender != "":
		parts.append(gender)

	# Physical description
	var build: String = appearance.get("build", "")
	if build != "":
		parts.append(build)

	var hair: String = appearance.get("hair", "")
	if hair != "":
		parts.append(hair)

	var eyes: String = appearance.get("eyes", "")
	if eyes != "":
		parts.append(eyes)

	var skin: String = appearance.get("skin", "")
	if skin != "":
		parts.append(skin)

	var facial: String = appearance.get("facial_features", "")
	if facial != "":
		parts.append(facial)

	var marks: String = appearance.get("distinguishing_marks", "")
	if marks != "":
		parts.append(marks)

	# Clothing — use context-appropriate clothing, fall back to default
	var clothing_field: String = preset["clothing_field"]
	var clothing: String = appearance.get(clothing_field, "")
	if clothing == "":
		clothing = appearance.get("default_clothing", "")
	if clothing != "":
		parts.append("wearing %s" % clothing)

	# Background
	var bg: String = preset["background"]
	if bg != "":
		parts.append(bg)

	return ", ".join(parts)


## Builds a prompt for a specific age, keeping all other appearance fields the same.
## Useful for showing characters at different life stages.
static func build_aged_prompt(appearance: Dictionary, age: int, context: String = "default") -> String:
	var age_desc := "%d years old" % age
	return build_prompt(appearance, context, age_desc)


## Returns a list of available contexts for a character based on their appearance data.
## Only includes contexts where the character has appropriate clothing defined.
static func get_available_contexts(appearance: Dictionary) -> PackedStringArray:
	var contexts: PackedStringArray = ["default"]

	if appearance.get("court_clothing", "") != "":
		contexts.append("court")
	if appearance.get("battle_clothing", "") != "":
		contexts.append("battle")

	# Prayer is always available (uses default clothing)
	contexts.append("prayer")

	return contexts


## Generates a short description suitable for alt-text or tooltips.
static func build_description(appearance: Dictionary, character_name: String) -> String:
	var age: String = appearance.get("age_description", "")
	var hair: String = appearance.get("hair", "")
	var eyes: String = appearance.get("eyes", "")

	var parts: PackedStringArray = []
	parts.append(character_name)
	if age != "":
		parts.append(age)
	if hair != "":
		parts.append(hair)
	if eyes != "":
		parts.append(eyes)

	return ", ".join(parts)
