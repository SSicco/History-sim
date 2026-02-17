## Engine evaluation dashboard.
## Reads diagnostics and API logs to show aggregate engine performance metrics.
## Accessible as the "Engine" tab in the main tab bar.
extends Control

var data_manager: DataManager
var api_logger: ApiLogger
var event_diagnostics: EventDiagnostics
var sticky_context: StickyContext
var profile_manager: ProfileManager

## Font references set by main.gd
var font_cinzel: Font
var font_almendra: Font

var _scroll: ScrollContainer
var _content: VBoxContainer
var _refresh_button: Button


func _ready() -> void:
	_build_ui()


func _build_ui() -> void:
	_scroll = ScrollContainer.new()
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(_scroll)

	_content = VBoxContainer.new()
	_content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_content.add_theme_constant_override("separation", 8)
	_scroll.add_child(_content)

	_refresh_button = Button.new()
	_refresh_button.text = "Refresh Metrics"
	_refresh_button.pressed.connect(refresh)
	_content.add_child(_refresh_button)


func refresh() -> void:
	# Clear previous content (keep refresh button)
	for child in _content.get_children():
		if child != _refresh_button:
			child.queue_free()

	# Move refresh button to bottom by re-adding after content
	_content.move_child(_refresh_button, 0)

	if data_manager == null:
		_add_section("No data manager available.")
		return

	var api_logs := _load_api_logs()
	var event_logs := _load_event_diagnostics()
	var session_logs := _load_session_recordings()

	_build_cost_section(api_logs)
	_build_context_section(session_logs)
	_build_confidence_section(session_logs)
	_build_sticky_section(event_logs)
	_build_profile_section()
	_build_retry_section(session_logs)
	_build_summary_section(api_logs, session_logs, event_logs)


# ─── Data Loading ────────────────────────────────────────────────────────

func _load_api_logs() -> Array:
	var logs: Array = []
	var log_dir := data_manager.get_campaign_dir().path_join("api_logs")
	var dir := DirAccess.open(log_dir)
	if dir == null:
		return logs

	dir.list_dir_begin()
	var fname := dir.get_next()
	while fname != "":
		if fname.ends_with(".json"):
			var log_data = data_manager.load_json("api_logs/%s" % fname)
			if log_data != null and log_data is Dictionary:
				logs.append(log_data)
		fname = dir.get_next()
	dir.list_dir_end()
	return logs


func _load_event_diagnostics() -> Array:
	var events: Array = []
	var diag_dir := data_manager.get_campaign_dir().path_join("diagnostics")
	var dir := DirAccess.open(diag_dir)
	if dir == null:
		return events

	dir.list_dir_begin()
	var fname := dir.get_next()
	while fname != "":
		if fname.begins_with("event_") and fname.ends_with(".json"):
			var evt_data = data_manager.load_json("diagnostics/%s" % fname)
			if evt_data != null and evt_data is Dictionary:
				events.append(evt_data)
		fname = dir.get_next()
	dir.list_dir_end()
	return events


func _load_session_recordings() -> Array:
	var sessions: Array = []
	var diag_dir := data_manager.get_campaign_dir().path_join("diagnostics")
	var dir := DirAccess.open(diag_dir)
	if dir == null:
		return sessions

	dir.list_dir_begin()
	var fname := dir.get_next()
	while fname != "":
		if fname.begins_with("rec_") and fname.ends_with(".json"):
			var session_data = data_manager.load_json("diagnostics/%s" % fname)
			if session_data != null and session_data is Dictionary:
				sessions.append(session_data)
		fname = dir.get_next()
	dir.list_dir_end()
	return sessions


# ─── Section Builders ────────────────────────────────────────────────────

func _build_cost_section(api_logs: Array) -> void:
	_add_header("Cost & Token Usage")

	if api_logs.is_empty():
		_add_line("No API calls recorded yet.")
		return

	var total_cost := 0.0
	var total_input := 0
	var total_output := 0
	var total_cache_read := 0
	var total_cache_write := 0
	var sonnet_calls := 0
	var haiku_calls := 0
	var sonnet_cost := 0.0
	var haiku_cost := 0.0

	for log_entry in api_logs:
		var cost: float = log_entry.get("cost_usd", 0.0)
		total_cost += cost
		var usage: Dictionary = log_entry.get("usage", {})
		total_input += usage.get("input_tokens", 0)
		total_output += usage.get("output_tokens", 0)
		total_cache_read += usage.get("cache_read_tokens", 0)
		total_cache_write += usage.get("cache_write_tokens", 0)

		var model: String = log_entry.get("model", "")
		if model.contains("haiku"):
			haiku_calls += 1
			haiku_cost += cost
		else:
			sonnet_calls += 1
			sonnet_cost += cost

	var avg_cost := total_cost / api_logs.size() if not api_logs.is_empty() else 0.0
	var cache_rate := 0.0
	var total_all_input := total_input + total_cache_read + total_cache_write
	if total_all_input > 0:
		cache_rate = (float(total_cache_read) / total_all_input) * 100.0

	_add_line("Total cost: $%.4f" % total_cost)
	_add_line("Total calls: %d (Sonnet: %d, Haiku: %d)" % [api_logs.size(), sonnet_calls, haiku_calls])
	_add_line("Avg cost per call: $%.6f" % avg_cost)
	_add_line("Sonnet total: $%.4f  |  Haiku total: $%.4f" % [sonnet_cost, haiku_cost])
	_add_separator()
	_add_line("Input tokens: %s  |  Output tokens: %s" % [_fmt_num(total_input), _fmt_num(total_output)])
	_add_line("Cache read: %s  |  Cache write: %s" % [_fmt_num(total_cache_read), _fmt_num(total_cache_write)])
	_add_line("Cache hit rate: %.1f%%" % cache_rate)


func _build_context_section(session_logs: Array) -> void:
	_add_header("Context Agent Performance")

	var exchanges := _extract_all_exchanges(session_logs)
	if exchanges.is_empty():
		_add_line("No session recordings found.")
		return

	var total_searches := 0
	var total_chars_found := 0
	var total_events_found := 0
	var total_laws_found := 0
	var searches_with_results := 0

	for ex in exchanges:
		var search: Dictionary = ex.get("search_results", {})
		if search.is_empty():
			continue
		total_searches += 1
		var chars: int = search.get("characters_found", 0)
		var evts: int = search.get("events_found", 0)
		var laws: int = search.get("laws_found", 0)
		total_chars_found += chars
		total_events_found += evts
		total_laws_found += laws
		if chars > 0 or evts > 0 or laws > 0:
			searches_with_results += 1

	var hit_rate := (float(searches_with_results) / total_searches * 100.0) if total_searches > 0 else 0.0

	_add_line("Total context searches: %d" % total_searches)
	_add_line("Searches with results: %d (%.1f%%)" % [searches_with_results, hit_rate])
	_add_line("Avg characters per search: %.1f" % (float(total_chars_found) / maxi(total_searches, 1)))
	_add_line("Avg events per search: %.1f" % (float(total_events_found) / maxi(total_searches, 1)))
	_add_line("Avg laws per search: %.1f" % (float(total_laws_found) / maxi(total_searches, 1)))


func _build_confidence_section(session_logs: Array) -> void:
	_add_header("GM Confidence & Missing Context")

	var exchanges := _extract_all_exchanges(session_logs)
	if exchanges.is_empty():
		_add_line("No session recordings found.")
		return

	var total_responses := 0
	var total_confidence := 0.0
	var low_confidence_count := 0
	var missing_context_count := 0
	var missing_items: Dictionary = {}  # type -> count

	for ex in exchanges:
		var gm: Dictionary = ex.get("gm_response", {})
		if gm.is_empty():
			continue
		var metadata: Dictionary = gm.get("metadata", {})
		if metadata.is_empty():
			continue

		total_responses += 1

		var confidence: float = metadata.get("confidence", 1.0)
		total_confidence += confidence
		if confidence < 0.8:
			low_confidence_count += 1

		var missing: Array = metadata.get("missing_context", [])
		if not missing.is_empty():
			missing_context_count += 1
			for item in missing:
				if item is Dictionary:
					var mtype: String = item.get("type", "unknown")
					missing_items[mtype] = missing_items.get(mtype, 0) + 1

	var avg_confidence := total_confidence / maxi(total_responses, 1)
	var missing_rate := (float(missing_context_count) / maxi(total_responses, 1)) * 100.0

	_add_line("Total GM responses: %d" % total_responses)
	_add_line("Average confidence: %.2f" % avg_confidence)
	_add_line("Low confidence (<0.8): %d (%.1f%%)" % [low_confidence_count, float(low_confidence_count) / maxi(total_responses, 1) * 100.0])
	_add_line("Responses with missing context: %d (%.1f%%)" % [missing_context_count, missing_rate])

	if not missing_items.is_empty():
		_add_line("")
		_add_line("Missing context breakdown:")
		for mtype in missing_items:
			_add_line("  %s: %d" % [mtype, missing_items[mtype]])


func _build_sticky_section(event_logs: Array) -> void:
	_add_header("Sticky Context & Events")

	if event_logs.is_empty():
		_add_line("No event diagnostics recorded.")
		return

	var total_events := event_logs.size()
	var total_exchanges := 0
	var total_context_pulls := 0
	var total_event_cost := 0.0
	var overflow_count := 0
	var location_change_count := 0

	for evt in event_logs:
		total_exchanges += evt.get("exchange_count", 0)
		total_context_pulls += evt.get("context_pulls", 0)
		total_event_cost += evt.get("total_cost_usd", 0.0)
		var reason: String = evt.get("end_reason", "")
		if reason == "overflow":
			overflow_count += 1
		elif reason == "location_change":
			location_change_count += 1

	var avg_exchanges := float(total_exchanges) / maxi(total_events, 1)
	var avg_pulls := float(total_context_pulls) / maxi(total_events, 1)

	_add_line("Total event segments: %d" % total_events)
	_add_line("Avg exchanges per event: %.1f" % avg_exchanges)
	_add_line("Avg context pulls per event: %.1f" % avg_pulls)
	_add_line("Context overflows: %d" % overflow_count)
	_add_line("Location changes: %d" % location_change_count)
	_add_line("Avg cost per event: $%.6f" % (total_event_cost / maxi(total_events, 1)))

	# Current sticky context stats
	if sticky_context != null:
		var snapshot: Dictionary = sticky_context.get_snapshot()
		var token_count: int = snapshot.get("estimated_tokens", 0)
		var budget: int = 3000
		var fill_pct := (float(token_count) / budget) * 100.0
		var chars_dict: Dictionary = snapshot.get("characters", {})
		var events_dict: Dictionary = snapshot.get("events", {})
		var laws_dict: Dictionary = snapshot.get("laws", {})
		_add_line("")
		_add_line("Current sticky context: %d/%d tokens (%.0f%% full)" % [token_count, budget, fill_pct])
		_add_line("Characters loaded: %d  |  Events: %d  |  Laws: %d" % [
			chars_dict.size(), events_dict.size(), laws_dict.size(),
		])


func _build_profile_section() -> void:
	_add_header("Profile Manager")

	if profile_manager == null:
		_add_line("Profile manager not available.")
		return

	var profile_text := profile_manager.get_profile_text()
	var profile_length := profile_text.length()
	var token_est := ceili(profile_length / 4.0)

	_add_line("Profile length: %d chars (~%d tokens)" % [profile_length, token_est])

	if data_manager != null:
		var profile_data = data_manager.load_json("juan_profile.txt")
		if profile_data != null and profile_data is Dictionary:
			var last_refresh: int = profile_data.get("last_refresh_event_count", 0)
			var last_updated: String = profile_data.get("last_updated", "never")
			_add_line("Last refresh at event count: %d" % last_refresh)
			_add_line("Last updated: %s" % last_updated)

	# Show how stale the profile is
	if data_manager != null:
		var state = data_manager.load_json("game_state.json")
		if state != null:
			var logged: int = state.get("logged_event_count", 0)
			var profile_data = data_manager.load_json("juan_profile.txt")
			var last_refresh: int = 0
			if profile_data != null and profile_data is Dictionary:
				last_refresh = profile_data.get("last_refresh_event_count", 0)
			var events_since := logged - last_refresh
			_add_line("Events since last refresh: %d (refreshes every %d)" % [events_since, 8])


func _build_retry_section(session_logs: Array) -> void:
	_add_header("Retry & Re-reflection")

	var exchanges := _extract_all_exchanges(session_logs)
	if exchanges.is_empty():
		_add_line("No session recordings found.")
		return

	var total := exchanges.size()
	var with_context_agent := 0
	var with_search_results := 0

	for ex in exchanges:
		var ctx: Dictionary = ex.get("context_agent", {})
		if not ctx.is_empty():
			with_context_agent += 1
		var search: Dictionary = ex.get("search_results", {})
		if not search.is_empty():
			with_search_results += 1

	_add_line("Total exchanges recorded: %d" % total)
	_add_line("With context agent call: %d (%.1f%%)" % [with_context_agent, float(with_context_agent) / maxi(total, 1) * 100.0])
	_add_line("With search results: %d (%.1f%%)" % [with_search_results, float(with_search_results) / maxi(total, 1) * 100.0])


func _build_summary_section(api_logs: Array, session_logs: Array, event_logs: Array) -> void:
	_add_header("Summary")

	var total_api_calls := api_logs.size()
	var total_sessions := session_logs.size()
	var total_events := event_logs.size()

	var total_exchanges := 0
	for session in session_logs:
		total_exchanges += session.get("exchange_count", 0)

	_add_line("API calls logged: %d" % total_api_calls)
	_add_line("Session recordings: %d" % total_sessions)
	_add_line("Event segments: %d" % total_events)
	_add_line("Player exchanges: %d" % total_exchanges)

	# Database stats
	if data_manager != null:
		var events_data = data_manager.load_json("events.json")
		if events_data != null:
			var event_count: int = events_data.get("events", []).size()
			var next_id: int = events_data.get("next_id", 0)
			_add_line("Events in database: %d (next_id: %d)" % [event_count, next_id])

		var chars_data = data_manager.load_json("characters.json")
		if chars_data != null:
			var char_count: int = chars_data.get("characters", []).size()
			_add_line("Characters in database: %d" % char_count)


# ─── UI Helpers ──────────────────────────────────────────────────────────

func _add_header(text: String) -> void:
	var sep := HSeparator.new()
	_content.add_child(sep)

	var label := Label.new()
	label.text = text
	if font_cinzel != null:
		label.add_theme_font_override("font", font_cinzel)
	label.add_theme_font_size_override("font_size", 18)
	label.add_theme_color_override("font_color", Color(0.933, 0.898, 0.839, 1.0))
	_content.add_child(label)


func _add_section(text: String) -> void:
	var label := Label.new()
	label.text = text
	label.add_theme_color_override("font_color", Color(0.7, 0.7, 0.7, 1.0))
	_content.add_child(label)


func _add_line(text: String) -> void:
	var label := Label.new()
	label.text = text
	if font_almendra != null:
		label.add_theme_font_override("font", font_almendra)
	label.add_theme_font_size_override("font_size", 14)
	label.add_theme_color_override("font_color", Color(0.831, 0.773, 0.663, 1.0))
	_content.add_child(label)


func _add_separator() -> void:
	var sep := HSeparator.new()
	sep.add_theme_constant_override("separation", 4)
	_content.add_child(sep)


func _extract_all_exchanges(session_logs: Array) -> Array:
	var all: Array = []
	for session in session_logs:
		var exchanges: Array = session.get("exchanges", [])
		all.append_array(exchanges)
	return all


func _fmt_num(n: int) -> String:
	var s := str(n)
	var result := ""
	var count := 0
	for i in range(s.length() - 1, -1, -1):
		if count > 0 and count % 3 == 0:
			result = "," + result
		result = s[i] + result
		count += 1
	return result
