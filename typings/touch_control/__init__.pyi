"""Native ESP32-S3 touch measurement controls compiled into custom firmware."""

TIMEOUT_THRESHOLD_DEFAULT: int

COUNT_SLOPE_0: int
COUNT_SLOPE_1: int
COUNT_SLOPE_2: int
COUNT_SLOPE_3: int
COUNT_SLOPE_4: int
COUNT_SLOPE_5: int
COUNT_SLOPE_6: int
COUNT_SLOPE_7: int

INITIAL_LEVEL_LOW: int
INITIAL_LEVEL_HIGH: int
INITIAL_LEVEL_FLOAT: int

VOLTAGE_HIGH_2V4: int
VOLTAGE_HIGH_2V5: int
VOLTAGE_HIGH_2V6: int
VOLTAGE_HIGH_2V7: int
VOLTAGE_LOW_0V5: int
VOLTAGE_LOW_0V6: int
VOLTAGE_LOW_0V7: int
VOLTAGE_LOW_0V8: int
VOLTAGE_ATTENUATION_1V5: int
VOLTAGE_ATTENUATION_1V0: int
VOLTAGE_ATTENUATION_0V5: int
VOLTAGE_ATTENUATION_0V0: int

IDLE_HIGH_Z: int
IDLE_GROUND: int

INTERRUPT_DONE: int
INTERRUPT_ACTIVE: int
INTERRUPT_INACTIVE: int
INTERRUPT_SCAN_DONE: int
INTERRUPT_TIMEOUT: int

FILTER_IIR_4: int
FILTER_IIR_8: int
FILTER_IIR_16: int
FILTER_IIR_32: int
FILTER_IIR_64: int
FILTER_IIR_128: int
FILTER_IIR_256: int
FILTER_JITTER: int
SMOOTH_OFF: int
SMOOTH_IIR_2: int
SMOOTH_IIR_4: int
SMOOTH_IIR_8: int


def set_timeout(enabled: bool, threshold: int) -> None:
    """Configure the shared measurement timeout."""
    ...


def resume() -> None:
    """Resume scanning after a measurement timeout."""
    ...


def set_charge_discharge_times(cycles: int) -> None:
    """Set the number of charge/discharge cycles per measurement."""
    ...


def get_charge_discharge_times() -> int:
    """Return the number of charge/discharge cycles per measurement."""
    ...


def set_measurement_interval(interval: int) -> None:
    """Set the interval between measurements in RTC_SLOW clock cycles."""
    ...


def get_measurement_interval() -> int:
    """Return the interval between measurements."""
    ...


def set_count_mode(channel: int, slope: int, initial_level: int) -> None:
    """Set charge-current slope and initial voltage for one channel."""
    ...


def get_count_mode(channel: int) -> tuple[int, int]:
    """Return (slope, initial_level) for one channel."""
    ...


def set_voltage(high: int, low: int, attenuation: int) -> None:
    """Set the shared high, low, and attenuation voltage options."""
    ...


def get_voltage() -> tuple[int, int, int]:
    """Return (high, low, attenuation)."""
    ...


def set_idle_connection(connection: int) -> None:
    """Select high-impedance or ground for inactive channels."""
    ...


def get_idle_connection() -> int:
    """Return the inactive-channel connection setting."""
    ...


def current_channel() -> int:
    """Return the channel currently being measured."""
    ...


def measurement_in_progress() -> bool:
    """Return whether a touch measurement is underway."""
    ...


def interrupt_status() -> int:
    """Return the touch interrupt status bit mask."""
    ...


def clear_interrupts(mask: int) -> None:
    """Clear the selected touch interrupt status bits."""
    ...


def configure_filter(
    mode: int,
    debounce_count: int,
    noise_threshold: int,
    jitter_step: int,
    smooth_level: int,
) -> None:
    """Configure the ESP32-S3 touch hardware filter."""
    ...


def get_filter_config() -> tuple[int, int, int, int, int]:
    """Return (mode, debounce_count, noise_threshold, jitter_step, smooth_level)."""
    ...


def enable_filter() -> None:
    """Enable hardware filtering."""
    ...


def disable_filter() -> None:
    """Disable hardware filtering."""
    ...


def read_smooth(channel: int) -> int:
    """Read a channel's filtered value."""
    ...
