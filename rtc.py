"""
PCF8523 Real-Time Clock (RTC) driver for MicroPython ESP32

The PCF8523 is an I2C-based RTC with built-in oscillator.
Address: 0x68 (or 0x69 with A0 pin high)

Register map:
0x00: Control_1
0x01: Control_2
0x02: Control_3
0x03: Seconds
0x04: Minutes
0x05: Hours
0x06: Days
0x07: Weekdays
0x08: Months
0x09: Years
"""

from machine import I2C, Pin
import time

class PCF8523:
    def __init__(self, i2c=None, scl_pin=6, sda_pin=5, i2c_freq=400000, addr=0x68):
        """
        Initialize PCF8523 RTC
        
        Args:
            i2c: I2C object (if None, creates one)
            scl_pin: SCL pin number (default 6)
            sda_pin: SDA pin number (default 5)
            i2c_freq: I2C frequency in Hz
            addr: I2C address (0x68 default, 0x69 with A0 high)
        """
        if i2c is None:
            self.i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin), freq=i2c_freq)
        else:
            self.i2c = i2c
        
        self.addr = addr
        self._init_rtc()
    
    def _init_rtc(self):
        """Initialize RTC - stop oscillator if running, then restart"""
        # Read Control_1 register
        ctrl1 = self._read_register(0x00)
        
        # Set oscillator stop bit
        self.i2c.writeto_mem(self.addr, 0x00, bytes([ctrl1 | 0x20]))
        time.sleep_ms(10)
        
        # Clear oscillator stop bit to start oscillator
        self.i2c.writeto_mem(self.addr, 0x00, bytes([ctrl1 & ~0x20]))
    
    def _read_register(self, reg):
        """Read a single register"""
        return self.i2c.readfrom_mem(self.addr, reg, 1)[0]
    
    def _write_register(self, reg, value):
        """Write a single register"""
        self.i2c.writeto_mem(self.addr, reg, bytes([value]))
    
    def _bcd2dec(self, bcd):
        """Convert BCD (Binary Coded Decimal) to decimal"""
        return (bcd >> 4) * 10 + (bcd & 0x0F)
    
    def _dec2bcd(self, dec):
        """Convert decimal to BCD (Binary Coded Decimal)"""
        return ((dec // 10) << 4) | (dec % 10)
    
    def get_time(self):
        """
        Read time from RTC
        
        Returns:
            tuple: (year, month, day, hour, minute, second, weekday, yearday)
            Compatible with time.struct_time
        """
        # Read all time registers (0x03 to 0x09)
        regs = self.i2c.readfrom_mem(self.addr, 0x03, 7)
        
        # Extract values (remove status bits)
        seconds = self._bcd2dec(regs[0] & 0x7F)
        minutes = self._bcd2dec(regs[1] & 0x7F)
        hours = self._bcd2dec(regs[2] & 0x3F)
        day = self._bcd2dec(regs[3] & 0x3F)
        weekday = regs[4] & 0x07
        month = self._bcd2dec(regs[5] & 0x1F)
        year = self._bcd2dec(regs[6])
        
        # Assume 20xx for years (e.g., 26 -> 2026)
        full_year = 2000 + year
        
        # Calculate yearday (day of year)
        # Simplified calculation
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if (full_year % 4 == 0 and full_year % 100 != 0) or (full_year % 400 == 0):
            days_in_month[1] = 29
        
        yearday = sum(days_in_month[:month-1]) + day
        
        return (full_year, month, day, hours, minutes, seconds, weekday, yearday)
    
    def set_time(self, year, month, day, hour, minute, second, weekday=0):
        """
        Set time on RTC
        
        Args:
            year: Full year (e.g., 2026)
            month: Month (1-12)
            day: Day (1-31)
            hour: Hour (0-23)
            minute: Minute (0-59)
            second: Second (0-59)
            weekday: Day of week (0=Monday, 1=Tuesday, ..., 6=Sunday)
        """
        # Convert to 2-digit year
        year_2digit = year % 100
        
        # Create register values
        sec_val = self._dec2bcd(second)
        min_val = self._dec2bcd(minute)
        hour_val = self._dec2bcd(hour)
        day_val = self._dec2bcd(day)
        month_val = self._dec2bcd(month)
        year_val = self._dec2bcd(year_2digit)
        
        # Write to registers
        self.i2c.writeto_mem(self.addr, 0x03, bytes([
            sec_val,
            min_val,
            hour_val,
            day_val,
            weekday & 0x07,
            month_val,
            year_val
        ]))
    
    def get_timestamp(self):
        """
        Get current time as a formatted string
        
        Returns:
            str: Formatted as "YYYY-MM-DD HH:MM:SS"
        """
        year, month, day, hour, minute, second, _, _ = self.get_time()
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            year, month, day, hour, minute, second
        )
    
    def get_timestamp_filename(self):
        """
        Get timestamp suitable for filenames
        
        Returns:
            str: Formatted as "YYYY_MM_DD_HHmmss"
        """
        year, month, day, hour, minute, second, _, _ = self.get_time()
        return "{:04d}_{:02d}_{:02d}_{:02d}{:02d}{:02d}".format(
            year, month, day, hour, minute, second
        )
    
    def is_running(self):
        """Check if RTC oscillator is running"""
        ctrl1 = self._read_register(0x00)
        return not (ctrl1 & 0x20)  # Bit 5: stop bit
    
    def sync_time(self, ntp=False):
        """
        Sync RTC with system time or NTP
        
        Args:
            ntp: If True, try to sync with NTP server (requires network)
                If False, use current MicroPython time.time()
        """
        if ntp:
            try:
                import ntptime
                ntptime.settime()
                # Now set RTC from system time
                tm = time.localtime()
                self.set_time(tm[0], tm[1], tm[2], tm[3], tm[4], tm[5])
                print("[RTC] Synced with NTP")
            except Exception as e:
                print(f"[RTC] NTP sync failed: {e}")
        else:
            # Use MicroPython system time
            tm = time.localtime()
            self.set_time(tm[0], tm[1], tm[2], tm[3], tm[4], tm[5])
            print(f"[RTC] Synced with system time: {self.get_timestamp()}")

# Global RTC instance
_rtc_instance = None

def init_rtc(scl_pin=6, sda_pin=5, i2c_freq=400000):
    """Initialize and return global RTC instance"""
    global _rtc_instance
    _rtc_instance = PCF8523(scl_pin=scl_pin, sda_pin=sda_pin, i2c_freq=i2c_freq)
    return _rtc_instance

def get_rtc():
    """Get global RTC instance"""
    global _rtc_instance
    if _rtc_instance is None:
        init_rtc()
    return _rtc_instance

