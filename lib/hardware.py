# Global variables
from lib.rtc import init_rtc
from machine import TouchPad, Pin
from config import I2C_SCL, I2C_SDA, TOUCH_PIN, TOUCH_PIN_2, SYNC_PIN

# Initialize hardware with error handling
clock = None
touch = None
touch2 = None
sync_out = None



async def initialize():
	global clock, touch, touch2, button, sync_out
	clock = init_rtc(scl_pin=I2C_SCL, sda_pin=I2C_SDA)
	touch = TouchPad(Pin(TOUCH_PIN))
	touch2 = TouchPad(Pin(TOUCH_PIN_2))
	sync_out = Pin(SYNC_PIN, Pin.OUT, value=0)
	