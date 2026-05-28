# Global variables
from lib.rtc import init_rtc
from machine import TouchPad, Pin
from config import I2C_SCL, I2C_SDA, RGB_PIN, RGB_PWR_PIN, TOUCH_PIN, STOP_BUTTON_PIN
import states
from Led import LED
led = LED(RGB_PWR_PIN, RGB_PIN, get_state=lambda: states.current_status)  # Pass getter function to read current state
clock = init_rtc(scl_pin=I2C_SCL, sda_pin=I2C_SDA)
touch = TouchPad(Pin(TOUCH_PIN))
button = Pin(STOP_BUTTON_PIN, Pin.IN, Pin.PULL_UP)