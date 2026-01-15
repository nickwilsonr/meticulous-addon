# Test Suite Structure for Meticulous Espresso Add-on


This directory contains all tests and developer scripts for the add-on, organized by function:


## Integration Tests (`integration/`)
- End-to-end, API, and persistence tests
- Validate the add-on as a whole, including API calls, config, and sensor state
- Example files:
	- `test_addon_integration.py`
	- `test_sensor_population.py`
	- `test_pymeticulous_030_updates.py`


## Unit Tests (`unit/`)
- Isolated logic and handler tests
- Validate individual functions, command handlers, and error handling
- Example files:
  - `test_mqtt_commands.py`
## Manual/Dev Scripts

### `dev_scripts/`
- Developer scripts for manual or ad-hoc testing (not run by automated test suite)
- Example: `test_socketio_events.py` (Socket.IO event monitor)

### `manual/`
- Manual API endpoint test scripts
- Example: `test_profiles_endpoint.py`, `test_correct_endpoint.py`

## Running All Tests


Use the provided `run_tests.py` script to run all unit and integration tests:

```sh
python tests/run_tests.py
```

Or run a specific test file with unittest:

```sh
python -m unittest tests/integration/test_addon_integration.py
python -m unittest tests/unit/test_mqtt_commands.py
```

## Adding New Tests
- Place new integration (system-level) tests in `integration/`
- Place new unit (logic/handler) tests in `unit/`
- Use the provided examples as templates
