# Global variables
from lib.rtc import init_rtc
from machine import TouchPad, Pin
from config import I2C_SCL, I2C_SDA, RGB_PIN, RGB_PWR_PIN, TOUCH_PIN, TOUCH_PIN_2, STOP_BUTTON_PIN, SYNC_PIN
import states
from Led import LED
import asyncio

# Initialize hardware with error handling
led = None
clock = None
touch = None
touch2 = None
button = None
sync_out = None
button_pressed = asyncio.ThreadSafeFlag()
_button_interrupt_armed = False


def _handle_button_interrupt(pin):
	"""Signal a button press without doing any work in interrupt context."""
	global _button_interrupt_armed
	if _button_interrupt_armed:
		_button_interrupt_armed = False
		button_pressed.set()


def arm_button_interrupt():
	"""Allow the next falling edge to be handled."""
	global _button_interrupt_armed
	_button_interrupt_armed = True

async def initialize():
	global led, clock, touch, touch2, button, sync_out
	led = LED(RGB_PWR_PIN, RGB_PIN, get_state=lambda: states.current_status)
	clock = init_rtc(scl_pin=I2C_SCL, sda_pin=I2C_SDA)
	touch = TouchPad(Pin(TOUCH_PIN))
	touch2 = TouchPad(Pin(TOUCH_PIN_2))
	button = Pin(STOP_BUTTON_PIN, Pin.IN, Pin.PULL_UP)
	arm_button_interrupt()
	button.irq(
		trigger=Pin.IRQ_FALLING,
		handler=_handle_button_interrupt,
		hard=True,
	)
	sync_out = Pin(SYNC_PIN, Pin.OUT, value=0)
	