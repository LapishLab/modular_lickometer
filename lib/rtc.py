"""PCF85263A real-time clock driver for MicroPython on ESP32-S3."""

from machine import I2C, Pin
import time


class PCF85263A:
    """Access the calendar clock in an NXP PCF85263A over I2C."""

    _DEFAULT_ADDRESS = 0x51

    _REG_HUNDREDTHS = 0x00
    _REG_SECONDS = 0x01
    _REG_STOP_ENABLE = 0x2E

    _SECONDS_OS = 0x80
    _STOP = 0x01
    _CLOCK_PRESCALER_RESET = 0xA4

    def __init__(
        self,
        i2c: I2C | None = None,
        scl_pin: int = 6,
        sda_pin: int = 5,
        i2c_freq: int = 400000,
        addr: int = _DEFAULT_ADDRESS,
    ) -> None:
        """Initialize the RTC, creating I2C bus 0 when one is not supplied."""
        if i2c is None:
            self.i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=i2c_freq)
        else:
            self.i2c = i2c

        self.addr = addr

    def _read_register(self, reg: int) -> int:
        """Read one register."""
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]

    def _write_register(self, reg: int, value: int) -> None:
        """Write one register."""
        self.i2c.writeto_mem(self.addr, reg, bytes((value,)))

    def _bcd2dec(self, bcd: int) -> int:
        """Convert binary-coded decimal to an integer."""
        return (bcd >> 4) * 10 + (bcd & 0x0F)

    def _dec2bcd(self, dec: int) -> int:
        """Convert an integer to binary-coded decimal."""
        return ((dec // 10) << 4) | (dec % 10)

    def get_time(self) -> tuple:
        """Return (year, month, day, hour, minute, second, weekday, yearday)."""
        # Reading any time register freezes a coherent snapshot of all counters.
        regs = self.i2c.readfrom_mem(self.addr, self._REG_HUNDREDTHS, 8)

        seconds = self._bcd2dec(regs[1] & 0x7F)
        minutes = self._bcd2dec(regs[2] & 0x7F)
        hours = self._bcd2dec(regs[3] & 0x3F)
        day = self._bcd2dec(regs[4] & 0x3F)
        weekday = regs[5] & 0x07
        month = self._bcd2dec(regs[6] & 0x1F)
        year = 2000 + self._bcd2dec(regs[7])

        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0:
            days_in_month[1] = 29
        yearday = sum(days_in_month[:month - 1]) + day

        return (year, month, day, hours, minutes, seconds, weekday, yearday)

    def set_time(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        second: int,
        weekday: int = 0,
    ) -> None:
        """Set the calendar clock using a full year and a zero-based weekday."""
        if not 2000 <= year <= 2099:
            raise ValueError("year must be between 2000 and 2099")
        if not 1 <= month <= 12:
            raise ValueError("month must be between 1 and 12")
        if not 1 <= day <= 31:
            raise ValueError("day must be between 1 and 31")
        if not 0 <= hour <= 23:
            raise ValueError("hour must be between 0 and 23")
        if not 0 <= minute <= 59:
            raise ValueError("minute must be between 0 and 59")
        if not 0 <= second <= 59:
            raise ValueError("second must be between 0 and 59")
        if not 0 <= weekday <= 6:
            raise ValueError("weekday must be between 0 and 6")

        registers = bytes((
            0,
            self._dec2bcd(second),
            self._dec2bcd(minute),
            self._dec2bcd(hour),
            self._dec2bcd(day),
            weekday,
            self._dec2bcd(month),
            self._dec2bcd(year % 100),
        ))

        # Stop the counters and reset the clock prescaler before updating the
        # complete time block, as required by the PCF85263A write sequence.
        self.i2c.writeto_mem(
            self.addr,
            self._REG_STOP_ENABLE,
            bytes((self._STOP, self._CLOCK_PRESCALER_RESET)),
        )
        try:
            self.i2c.writeto_mem(self.addr, self._REG_HUNDREDTHS, registers)
        finally:
            self._write_register(self._REG_STOP_ENABLE, 0)

    def get_timestamp(self) -> str:
        """Return the current time formatted as YYYY-MM-DD HH:MM:SS."""
        year, month, day, hour, minute, second, _, _ = self.get_time()
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            year, month, day, hour, minute, second
        )

    def get_timestamp_filename(self) -> str:
        """Return the current time formatted for a recording filename."""
        year, month, day, hour, minute, second, _, _ = self.get_time()
        return "{:04d}_{:02d}_{:02d}_{:02d}{:02d}{:02d}".format(
            year, month, day, hour, minute, second
        )

    def is_running(self) -> bool:
        """Return whether the counters are enabled and the oscillator is valid."""
        stop_enabled = self._read_register(self._REG_STOP_ENABLE) & self._STOP
        oscillator_stopped = self._read_register(self._REG_SECONDS) & self._SECONDS_OS
        return not stop_enabled and not oscillator_stopped

    def sync_time(self, ntp: bool = False) -> None:
        """Set the external RTC from NTP or the MicroPython system clock."""
        if ntp:
            import ntptime
            ntptime.settime()

        current = time.localtime()
        self.set_time(
            current[0],
            current[1],
            current[2],
            current[3],
            current[4],
            current[5],
            current[6],
        )
        print("[RTC] Synced with system time: {}".format(self.get_timestamp()))
