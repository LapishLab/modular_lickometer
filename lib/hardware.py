# Global variables
from lib.rtc import init_rtc
from machine import TouchPad, Pin
from config import I2C_SCL, I2C_SDA, RGB_PIN, RGB_PWR_PIN, TOUCH_PIN, STOP_BUTTON_PIN, SYNC_PIN
import states
from Led import LED
import time

# Initialize hardware with error handling
led = None
clock = None
touch = None
button = None
sync_out = None

def initialize():
	global led, clock, touch, button, sync_out
	try:
		led = LED(RGB_PWR_PIN, RGB_PIN, get_state=lambda: states.current_status)
	except Exception as e:
		print(f"LED initialization failed: {e}")
		states.current_status = states.Status.ERROR_LED
		while True: time.sleep(1)  # Halt further execution if LED fails to initialize

	try:
		clock = init_rtc(scl_pin=I2C_SCL, sda_pin=I2C_SDA)
	except Exception as e:
		print(f"Clock/RTC initialization failed: {e}")
		states.current_status = states.Status.ERROR_RTC
		while True: time.sleep(1)  # Halt further execution if RTC fails to initialize

	try:
		touch = TouchPad(Pin(TOUCH_PIN))
	except Exception as e:
		print(f"Touch initialization failed: {e}")
		states.current_status = states.Status.ERROR_TOUCH
		while True: time.sleep(1)  # Halt further execution if touch fails to initialize

	try:
		button = Pin(STOP_BUTTON_PIN, Pin.IN, Pin.PULL_UP)
	except Exception as e:
		print(f"Button initialization failed: {e}")
		states.current_status = states.Status.ERROR_BUTTON
		while True: time.sleep(1)  # Halt further execution if button fails to initialize

	try:
		sync_out = Pin(SYNC_PIN, Pin.OUT, value=0)
	except Exception as e:
		print(f"Sync output pin initialization failed: {e}")
		states.current_status = states.Status.ERROR_RUN_EXPERIMENT
		while True: time.sleep(1)  # Halt further execution if the output pin fails to initialize
