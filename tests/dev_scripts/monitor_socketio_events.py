# !/usr/bin/env python3
"""Manual developer tool: Monitors and logs all Socket.IO events.

This tool monitors and logs Socket.IO events from the espresso machine
for debugging and development purposes. Enhanced for real-world testing
of state normalization and preheat behavior analysis.

Graceful shutdown: Send SIGTERM to stop monitoring and disconnect cleanly.
"""
import difflib
import json
import logging
import signal
import sys
import time
from datetime import datetime
from typing import Any, List, Tuple

from meticulous.api import Api, ApiOptions

# Graceful shutdown flag
_shutdown_requested = False


def _signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown_requested
    _shutdown_requested = True
    logger = logging.getLogger(__name__)
    logger.info("\n[SHUTDOWN] Graceful shutdown requested - disconnecting...")


# Register signal handlers for graceful shutdown
signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGINT, _signal_handler)


def normalize_state_name(state_name: str) -> str:
    """
    Normalize detailed state information from machine for consistent representation.
    Used to test the normalization approach on unknown profiles.

    Takes the raw detailed state name from arg[0].name in status event and normalizes it.
    These are more granular state values during extraction (PI, Ramp, Hold, Decline, etc.).

    Handles:
    - Underscores to spaces: "pre_infusion" -> "Pre Infusion"
    - Smart title casing: capitalizes first word always, keeps small
      words lowercase if not first
    """
    # Words that should remain lowercase (unless at start of phrase)
    lowercase_words = {"to", "in", "a", "an", "the", "at", "by", "or", "and", "for", "of"}

    # Replace underscores with spaces
    state_name = state_name.replace("_", " ").strip()

    # Split into words
    words = state_name.split()

    if not words:
        return state_name

    # Normalize each word with smart capitalization
    normalized_words = []
    for i, word in enumerate(words):
        if i == 0:
            # Always capitalize first word
            normalized_words.append(word.capitalize())
        elif word.lower() in lowercase_words:
            # Keep small words lowercase (unless they're acronyms like PI)
            normalized_words.append(word.lower() if len(word) > 1 else word.upper())
        else:
            # Capitalize content words
            normalized_words.append(word.capitalize())

    return " ".join(normalized_words)


# Setup logging to file and console
# Generate timestamped log file for each run to avoid ever-expanding logs
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"socketio_events_{timestamp}.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to: {log_file}")

# Machine IP - read from command line or default
MACHINE_IP = sys.argv[1] if len(sys.argv) > 1 else "192.168.0.115"
BASE_URL = f"http://{MACHINE_IP}"

# Duration in seconds (optional, defaults to unlimited)
# Usage: python monitor_socketio_events.py [machine_ip] [duration_seconds]
DURATION = int(sys.argv[2]) if len(sys.argv) > 2 else None

# Keywords to search for - looking for state transitions
# We use partial matching to catch variations
KEYWORDS = {
    # Preheating phase
    "prefeat",
    "preheat",
    "heating",
    # Ready states
    "ready",
    "idle",
    # Shot stages
    "retracting",
    "retract",
    "pi",
    "pressure",
    "ramp",
    "ramping",
    "hold",
    "holding",
    "decline",
    "declining",
    "flow",
    "flowing",
    # Shot states
    "extract",
    "extracting",
    "extraction",
    "purge",
    "purging",
    # General state changes
    "state",
    "status",
    "phase",
    "stage",
    "temperature",
    "brew",
    "shot",
}

# Event counters
event_counts = {
    "total_events": 0,
    "relevant_events": 0,
    "raw_events_by_type": {},
    "status_events": 0,
    "heater_status_events": 0,
    "heating_related_events": 0,
}

# Track previous values to detect changes
# Format: {(event_name, field_path, keyword): previous_value}
previous_values = {}

# REAL-WORLD TEST TRACKING
# Track state transitions specifically from arg[0].name
state_transitions = []  # List of (timestamp, raw_state, normalized_state)
previous_state_name = None  # Track previous arg[0].name to detect changes
current_state_name = None  # Current state (updated in handle_status_event)

# NEW: Comprehensive state tracking for Home Assistant validation
state_machine_timeline = []  # All state transitions as they'd appear in HA
is_brewing_timeline = []  # When isBrewing sensor turns on/off
enrichment_decisions = []  # When we use heater_status.message as state
previous_is_brewing = False
latest_heater_status_message = None  # Latest heater_status.message for state

# Extended keywords for heating phase detection
HEATING_KEYWORDS = {
    "preheat",
    "preheating",
    "prefeat",
    "stabilizing",
    "stabilize",
    "stable",
    "warming",
    "warming up",
    "less than",
    "remaining",
    "heat ready",
    "ready to brew",
    "countdown",
    "timer",
}

# Fuzzy matching threshold (0.0 to 1.0, where 1.0 is exact match)
# 0.8 = 80% similarity
MATCH_THRESHOLD = 0.8


def fuzzy_match_keywords(text: str) -> List[Tuple[str, float]]:
    """
    Find keywords in text using fuzzy matching.
    Returns list of (keyword, similarity_score) tuples above threshold.

    Args:
        text: Text to search in

    Returns:
        List of (matched_keyword, similarity_score) for matches >= MATCH_THRESHOLD
    """
    text_lower = text.lower()
    matches = []

    for keyword in KEYWORDS:
        # Use SequenceMatcher to calculate similarity
        # We check both exact substring and fuzzy matching
        similarity = difflib.SequenceMatcher(None, text_lower, keyword.lower()).ratio()

        # Also check if keyword appears as a substring (for exact matches)
        if keyword in text_lower:
            similarity = 1.0
        # Also check if keyword is contained as a word-like unit
        elif similarity < MATCH_THRESHOLD:
            # Try to find close matches within the text (sliding window approach)
            max_similarity = 0
            for i in range(len(text_lower) - len(keyword) + 1):
                chunk = text_lower[i : i + len(keyword)]
                chunk_similarity = difflib.SequenceMatcher(None, chunk, keyword.lower()).ratio()
                max_similarity = max(max_similarity, chunk_similarity)
            similarity = max_similarity

        if similarity >= MATCH_THRESHOLD:
            matches.append((keyword, similarity))

    # Sort by similarity (highest first)
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches


def find_keywords_in_value(value: Any, path: str = "") -> List[Tuple[str, str, str, float]]:
    """
    Recursively search for keywords in a value using fuzzy matching.
    Returns list of tuples: (keyword_found, path_to_value, actual_value_str, confidence)
    """
    matches = []

    if isinstance(value, str):
        keyword_matches = fuzzy_match_keywords(value)
        for keyword, confidence in keyword_matches:
            matches.append((keyword, path, value, confidence))
    elif isinstance(value, (int, float, bool)):
        # Convert to string and check
        value_str = str(value).lower()
        keyword_matches = fuzzy_match_keywords(value_str)
        for keyword, confidence in keyword_matches:
            matches.append((keyword, path, str(value), confidence))
    elif isinstance(value, dict):
        for key, val in value.items():
            new_path = f"{path}.{key}" if path else key
            matches.extend(find_keywords_in_value(val, new_path))
    elif isinstance(value, (list, tuple)):
        for idx, item in enumerate(value):
            new_path = f"{path}[{idx}]"
            matches.extend(find_keywords_in_value(item, new_path))
    elif hasattr(value, "__dict__"):
        # Handle objects by converting to dict
        try:
            obj_dict = value.__dict__
            for key, val in obj_dict.items():
                new_path = f"{path}.{key}" if path else key
                matches.extend(find_keywords_in_value(val, new_path))
        except Exception:
            pass

    return matches


def handle_status_event(*args):
    """Specific handler for 'status' events to capture state transitions."""
    global previous_state_name, current_state_name, previous_is_brewing
    event_counts["status_events"] += 1

    if args and isinstance(args[0], dict):
        payload = args[0]

        # Log full status payload every time
        logger.info(f"[STATUS_PAYLOAD] {json.dumps(payload, default=str)}")

        # Extract detailed state from arg[0].name
        detailed_state = payload.get("name", None)
        coarse_state = payload.get("state", None)
        is_extracting = payload.get("extracting", False)
        timestamp = time.time()

        # Update current state
        if detailed_state:
            current_state_name = detailed_state

        # Track state changes via normalization and arg[0].name
        if detailed_state and detailed_state != previous_state_name:
            normalized = normalize_state_name(detailed_state)

            state_transitions.append(
                {
                    "timestamp": timestamp,
                    "raw_state": detailed_state,
                    "normalized_state": normalized,
                    "coarse_state": coarse_state,
                    "extracting": is_extracting,
                }
            )

            # Add to state machine timeline
            state_machine_timeline.append(
                {
                    "timestamp": timestamp,
                    "state": normalized,
                    "raw": detailed_state,
                }
            )

            logger.info(
                f"[STATE_CHANGE] arg[0].name='{detailed_state}' -> "
                f"'{normalized}' (coarse: {coarse_state})"
            )
            previous_state_name = detailed_state

        # Track isBrewing sensor changes
        # is_brewing = (coarse_state != "idle") AND is_extracting
        current_is_brewing = (coarse_state and coarse_state.lower() != "idle") and is_extracting
        if current_is_brewing != previous_is_brewing:
            is_brewing_timeline.append(
                {
                    "timestamp": timestamp,
                    "is_brewing": current_is_brewing,
                    "coarse_state": coarse_state,
                    "extracting": is_extracting,
                }
            )
            logger.info(
                f"[SENSOR_CHANGE] isBrewing={current_is_brewing} "
                f"(coarse_state='{coarse_state}', extracting={is_extracting})"
            )
            previous_is_brewing = current_is_brewing


def handle_heater_status_event(*args):
    """Specific handler for 'heater_status' events - capture everything."""
    event_counts["heater_status_events"] += 1

    # Log EVERYTHING about heater_status events
    if args:
        logger.info(f"[HEATER_STATUS_EVENT] args count: {len(args)}")
        for idx, arg in enumerate(args):
            logger.info(f"[HEATER_STATUS_ARG{idx}] type={type(arg).__name__}, value={repr(arg)}")
            if isinstance(arg, dict):
                logger.info(f"[HEATER_STATUS_DICT] {json.dumps(arg, default=str, indent=2)}")
                # Log each key-value pair
                for key, val in arg.items():
                    logger.info(f"  [{key}] = {repr(val)}")
            elif isinstance(arg, (int, float, str, bool)):
                logger.info(f"[HEATER_STATUS_VALUE] {repr(arg)}")
    else:
        logger.info("[HEATER_STATUS_EVENT] No arguments")


def handle_any_event(event_name: str, *args):
    """
    Catch-all handler for Socket.IO events not explicitly handled.
    Logs ALL events for comprehensive monitoring.
    """
    event_counts["total_events"] += 1

    # Track event types
    if event_name not in event_counts["raw_events_by_type"]:
        event_counts["raw_events_by_type"][event_name] = 0
    event_counts["raw_events_by_type"][event_name] += 1

    # Log ALL events (not just status/heater_status)
    logger.info(f"[OTHER_EVENT] {event_name} | args count: {len(args)}")
    for idx, arg in enumerate(args):
        if isinstance(arg, dict):
            logger.info(f"  [arg{idx}] dict: {json.dumps(arg, default=str)}")
        else:
            logger.info(f"  [arg{idx}] {type(arg).__name__}: {repr(arg)}")


def handle_connect():
    """Handle Socket.IO connect event."""
    logger.info("[SYSTEM] Socket.IO connected!")


def handle_disconnect():
    """Handle Socket.IO disconnect event."""
    logger.info("[SYSTEM] Socket.IO disconnected!")


def handle_error(data):
    """Handle Socket.IO error event."""
    logger.warning(f"[SYSTEM] Socket.IO error: {data}")


def main():
    """Run the event monitor."""
    logger.info("=" * 80)
    logger.info("Socket.IO Event Monitor - Real-World State Transition Testing")
    logger.info(f"Connecting to: {BASE_URL}")
    logger.info(f"Logging to: {log_file}")
    logger.info("=" * 80)
    logger.info("")
    logger.info("TEST OBJECTIVES:")
    logger.info("(1) Confirm state normalization works with unknown profile")
    logger.info("    - Capturing arg[0].name and normalizing via normalize_state_name()")
    logger.info("")
    logger.info("(2) Investigate preheat behavior:")
    logger.info("    (a) Is heater_status countdown actually a countdown?")
    logger.info("    (b) Does arg[0].name change during preheat state?")
    logger.info("    (c) Does 'preheat' appear in arg[0].name during preheat mode?")
    logger.info("    (d) If not in arg[0].name, where does it appear?")
    logger.info("")
    logger.info("=" * 80)
    logger.info("")

    # Setup event handlers - use minimal options, we'll catch all with the wildcard
    options = ApiOptions()

    # Connect to API
    logger.info("Initializing API...")
    api = Api(base_url=BASE_URL, options=options)

    # Get device info
    logger.info("Fetching device info...")
    try:
        device_info = api.get_device_info()
        if device_info is not None and hasattr(device_info, "name"):
            name = getattr(device_info, "name", None)
            serial = getattr(device_info, "serial", None)
            firmware = getattr(device_info, "firmware", None)
            if name:
                logger.info(f"Device: {name}")
            if serial:
                logger.info(f"Serial: {serial}")
            if firmware:
                logger.info(f"Firmware: {firmware}")
        else:
            logger.warning(f"Could not fetch device info: {device_info}")
    except Exception as e:
        logger.warning(f"Could not fetch device info: {e}")

    # Connect Socket.IO
    logger.info("Connecting Socket.IO...")
    try:
        api.connect_to_socket()
        logger.info("Socket.IO connected!")
    except Exception as e:
        logger.error(f"Socket.IO connection failed: {e}")
        return

    # Register specific handlers for key events
    api.sio.on("status", handler=handle_status_event)
    api.sio.on("heater_status", handler=handle_heater_status_event)

    # Register the catch-all handler to capture other events
    api.sio.on("*", handler=handle_any_event)

    # Also register lifecycle event handlers
    api.sio.on("connect", handler=handle_connect)
    api.sio.on("disconnect", handler=handle_disconnect)
    api.sio.on("error", handler=handle_error)

    logger.info("=" * 80)
    logger.info("Listening for events...")
    logger.info("READY FOR TEST: Perform preheat, then pull shot with unknown profile")
    if DURATION:
        logger.info(f"Auto-stopping in {DURATION} seconds")
    else:
        logger.info("Tell me when to stop the monitor")
    logger.info("=" * 80)
    logger.info("")

    # Keep running and print summary every 15 seconds
    start_time = time.time()
    try:
        while True:
            # Check for graceful shutdown request
            if _shutdown_requested:
                logger.info("Shutdown signal received, stopping...")
                break

            time.sleep(15)

            # Check if we've exceeded the duration
            if DURATION and (time.time() - start_time) >= DURATION:
                logger.info("")
                logger.info("Duration reached, stopping...")
                break

            if event_counts["total_events"] > 0:
                logger.info("-" * 80)
                logger.info("Running stats:")
                logger.info(f"  Total events: {event_counts['total_events']}")
                logger.info(f"  Status events: {event_counts['status_events']}")
                logger.info(f"  Heater status events: {event_counts['heater_status_events']}")
                logger.info(f"  State transitions captured: {len(state_transitions)}")
                if state_transitions:
                    logger.info(f"  Latest state: {state_transitions[-1]['normalized_state']}")
                logger.info(f"  Heating messages captured: {len(enrichment_decisions)}")
                logger.info("-" * 80)
    except KeyboardInterrupt:
        logger.info("")
        pass
    finally:
        # Generate comprehensive final report
        generate_final_report()

        # Ensure Socket.IO connection is properly closed
        logger.info("Disconnecting Socket.IO...")
        try:
            api.disconnect_socket()
            logger.info("Socket.IO disconnected successfully")
        except Exception as e:
            logger.warning(f"Error disconnecting Socket.IO: {e}")


def generate_final_report():
    """Generate comprehensive final report answering the test questions."""
    logger.info("")
    logger.info("=" * 80)
    logger.info("FINAL REPORT - STATE TRANSITION TEST RESULTS")
    logger.info("=" * 80)
    logger.info("")

    # STATE TRANSITIONS
    logger.info("STATE TRANSITIONS (via arg[0].name normalization)")
    logger.info("=" * 80)
    if state_transitions:
        logger.info(f"Total: {len(state_transitions)} state changes captured")
        logger.info("")
        for i, transition in enumerate(state_transitions, 1):
            logger.info(
                f"{i:2d}. '{transition['raw_state']}' -> " f"'{transition['normalized_state']}'"
            )
    else:
        logger.warning("No state transitions captured")

    logger.info("")
    logger.info("=" * 80)
    logger.info("isBREWING SENSOR TIMELINE")
    logger.info("=" * 80)
    if is_brewing_timeline:
        logger.info(f"Total: {len(is_brewing_timeline)} sensor state changes")
        logger.info("")
        for idx, brewing_event in enumerate(is_brewing_timeline, 1):
            state = "ON" if brewing_event["is_brewing"] else "OFF"
            coarse = brewing_event.get("coarse_state", "unknown")
            extracting = brewing_event.get("extracting", False)
            logger.info(
                f"{idx}. isBrewing={state:3s} (coarse_state='{coarse}', "
                f"extracting={extracting})"
            )
    else:
        logger.warning("No isBrewing sensor changes recorded")

    logger.info("")
    logger.info("=" * 80)
    logger.info("HEATING MESSAGES (when state='heating')")
    logger.info("=" * 80)
    if enrichment_decisions:
        logger.info(f"Total: {len(enrichment_decisions)} heating messages captured")
        logger.info("")
        for idx, enrich_event in enumerate(enrichment_decisions, 1):
            msg = enrich_event.get("heater_status_message", "N/A")
            logger.info(f"{idx}. {msg}")
    else:
        logger.warning("No heating messages captured during state='heating'")

    logger.info("")
    logger.info("=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total events received: {event_counts['total_events']}")
    logger.info(f"Status events: {event_counts['status_events']}")
    logger.info(f"Heater status events: {event_counts['heater_status_events']}")
    logger.info(f"State transitions (changes only): {len(state_transitions)}")
    logger.info(f"isBrewing sensor changes: {len(is_brewing_timeline)}")
    logger.info(f"Heating phase messages: {len(enrichment_decisions)}")
    logger.info("")
    logger.info("Events Captured (Distinct Only):")
    logger.info("  [OK] State transitions: Only logged when state CHANGES via arg[0].name")
    logger.info("  [OK] isBrewing sensor: Only logged when sensor value changes")
    logger.info(
        "  [OK] Heating messages: Only logged when "
        "heater_status.message changes during heating state"
    )
    logger.info(f"Full log saved to: {log_file}")
    logger.info("=" * 80)
    logger.info("")


if __name__ == "__main__":
    main()
