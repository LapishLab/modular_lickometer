"""Manually exercise every function in the native ``touch_control`` module.

Run this script on an ESP32-S3 containing the custom MicroPython firmware. Do
not run it during an experiment. It restores readable tuning settings, leaves
the hardware filter disabled, and restores the timeout to its ESP-IDF default.

This verifies that each wrapper can be called and returns the expected Python
type. It does not prove that every setting has the intended electrical effect.
"""

import time
from machine import Pin, TouchPad

import touch_control

TOUCH_PINS = (7, 5, 6, 4)
TEST_CHANNEL = TOUCH_PINS[0]
FILTER_SETTLE_MS = 100


def require(condition: bool, message: str) -> None:
    """Raise an assertion with a useful message when a check fails."""
    if not condition:
        raise AssertionError(message)


def require_int(value: object, name: str) -> None:
    """Require an integer result, excluding booleans."""
    require(type(value) is int, "%s returned %r, not int" % (name, value))


def require_bool(value: object, name: str) -> None:
    """Require a boolean result."""
    require(type(value) is bool, "%s returned %r, not bool" % (name, value))


def require_int_tuple(value: object, length: int, name: str) -> None:
    """Require a tuple of a specified number of integers."""
    if type(value) is not tuple:
        raise AssertionError("%s returned %r, not tuple" % (name, value))
    require(len(value) == length, "%s returned the wrong tuple length" % name)
    for item in value:
        require_int(item, name)


def pass_test(name: str) -> None:
    """Print one successful API check."""
    print("PASS:", name)


def main() -> None:
    """Initialize touch sensing and exercise the complete native API."""
    # Keep all TouchPad instances alive for the duration of the test. Creating
    # the first one initializes the shared ESP-IDF touch driver.
    pads = tuple(TouchPad(Pin(pin)) for pin in TOUCH_PINS)
    require(len(pads) == len(TOUCH_PINS), "TouchPad initialization failed")
    pass_test("TouchPad initialization")

    timeout_default = touch_control.TIMEOUT_THRESHOLD_DEFAULT
    require_int(timeout_default, "TIMEOUT_THRESHOLD_DEFAULT")
    require(timeout_default == 0x3FFFFF, "unexpected timeout default")
    pass_test("module constants")

    original_cycles = touch_control.get_charge_discharge_times()
    require_int(original_cycles, "get_charge_discharge_times")
    pass_test("get_charge_discharge_times")

    original_interval = touch_control.get_measurement_interval()
    require_int(original_interval, "get_measurement_interval")
    pass_test("get_measurement_interval")

    original_count_mode = touch_control.get_count_mode(TEST_CHANNEL)
    require_int_tuple(original_count_mode, 2, "get_count_mode")
    pass_test("get_count_mode")

    original_voltage = touch_control.get_voltage()
    require_int_tuple(original_voltage, 3, "get_voltage")
    pass_test("get_voltage")

    original_idle_connection = touch_control.get_idle_connection()
    require_int(original_idle_connection, "get_idle_connection")
    pass_test("get_idle_connection")

    original_filter_config = touch_control.get_filter_config()
    require_int_tuple(original_filter_config, 5, "get_filter_config")
    pass_test("get_filter_config")

    try:
        result = touch_control.set_timeout(False, 0)
        require(result is None, "set_timeout did not return None")
        pass_test("set_timeout")

        result = touch_control.resume()
        require(result is None, "resume did not return None")
        pass_test("resume")

        result = touch_control.set_charge_discharge_times(original_cycles)
        require(result is None, "set_charge_discharge_times did not return None")
        require(
            touch_control.get_charge_discharge_times() == original_cycles,
            "charge/discharge cycle setting did not round-trip",
        )
        pass_test("set_charge_discharge_times")

        result = touch_control.set_measurement_interval(original_interval)
        require(result is None, "set_measurement_interval did not return None")
        require(
            touch_control.get_measurement_interval() == original_interval,
            "measurement interval did not round-trip",
        )
        pass_test("set_measurement_interval")

        result = touch_control.set_count_mode(
            TEST_CHANNEL,
            original_count_mode[0],
            original_count_mode[1],
        )
        require(result is None, "set_count_mode did not return None")
        require(
            touch_control.get_count_mode(TEST_CHANNEL) == original_count_mode,
            "count mode did not round-trip",
        )
        pass_test("set_count_mode")

        result = touch_control.set_voltage(
            original_voltage[0],
            original_voltage[1],
            original_voltage[2],
        )
        require(result is None, "set_voltage did not return None")
        require(
            touch_control.get_voltage() == original_voltage,
            "voltage setting did not round-trip",
        )
        pass_test("set_voltage")

        result = touch_control.set_idle_connection(original_idle_connection)
        require(result is None, "set_idle_connection did not return None")
        require(
            touch_control.get_idle_connection() == original_idle_connection,
            "idle connection did not round-trip",
        )
        pass_test("set_idle_connection")

        current_channel = touch_control.current_channel()
        require_int(current_channel, "current_channel")
        require(0 <= current_channel <= 14, "current_channel is out of range")
        pass_test("current_channel")

        in_progress = touch_control.measurement_in_progress()
        require_bool(in_progress, "measurement_in_progress")
        pass_test("measurement_in_progress")

        status = touch_control.interrupt_status()
        require_int(status, "interrupt_status")
        pass_test("interrupt_status")

        result = touch_control.clear_interrupts(touch_control.INTERRUPT_TIMEOUT)
        require(result is None, "clear_interrupts did not return None")
        pass_test("clear_interrupts")

        result = touch_control.configure_filter(
            touch_control.FILTER_IIR_16,
            0,
            0,
            4,
            touch_control.SMOOTH_IIR_2,
        )
        require(result is None, "configure_filter did not return None")
        expected_filter = (
            touch_control.FILTER_IIR_16,
            0,
            0,
            4,
            touch_control.SMOOTH_IIR_2,
        )
        require(
            touch_control.get_filter_config() == expected_filter,
            "filter configuration did not round-trip",
        )
        pass_test("configure_filter")

        result = touch_control.enable_filter()
        require(result is None, "enable_filter did not return None")
        time.sleep_ms(FILTER_SETTLE_MS)
        pass_test("enable_filter")

        for channel in TOUCH_PINS:
            smooth_value = touch_control.read_smooth(channel)
            require_int(smooth_value, "read_smooth")
            require(smooth_value >= 0, "read_smooth returned a negative value")
        pass_test("read_smooth")

        result = touch_control.disable_filter()
        require(result is None, "disable_filter did not return None")
        pass_test("disable_filter")
    finally:
        # The timeout enable state and filter enable state have no public
        # getters, so leave them in known states. Restore all readable values.
        touch_control.disable_filter()
        touch_control.configure_filter(
            original_filter_config[0],
            original_filter_config[1],
            original_filter_config[2],
            original_filter_config[3],
            original_filter_config[4],
        )
        touch_control.set_idle_connection(original_idle_connection)
        touch_control.set_voltage(
            original_voltage[0],
            original_voltage[1],
            original_voltage[2],
        )
        touch_control.set_count_mode(
            TEST_CHANNEL,
            original_count_mode[0],
            original_count_mode[1],
        )
        touch_control.set_measurement_interval(original_interval)
        touch_control.set_charge_discharge_times(original_cycles)
        touch_control.set_timeout(True, timeout_default)

    print("All touch_control API checks passed.")
    print("Hardware filter is disabled; timeout is restored to the default.")


main()
