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

class DebouncedButton:
	"""A falling-edge button whose debounce state is self-contained."""

	def __init__(self, pin_number, debounce_ms=50):
		self._pin = Pin(pin_number, Pin.IN, Pin.PULL_UP)
		self._debounce_ms = debounce_ms
		self._interrupt = asyncio.ThreadSafeFlag()
		self.pressed = asyncio.ThreadSafeFlag()

		self._pin.irq(
			trigger=Pin.IRQ_FALLING,
			handler=lambda p:self._interrupt.set(),
			hard=True,
		)
		self._debounce_task = asyncio.create_task(self._process_interrupts())

	async def _process_interrupts(self):
		while True:
			await self._interrupt.wait()
			self.pressed.set()
			await asyncio.sleep_ms(self._debounce_ms)
			self._interrupt.clear()

async def initialize():
	global led, clock, touch, touch2, button, sync_out
	led = LED(RGB_PWR_PIN, RGB_PIN, get_state=lambda: states.current_status)
	clock = init_rtc(scl_pin=I2C_SCL, sda_pin=I2C_SDA)
	touch = TouchPad(Pin(TOUCH_PIN))
	touch2 = TouchPad(Pin(TOUCH_PIN_2))
	button = DebouncedButton(STOP_BUTTON_PIN)
	sync_out = Pin(SYNC_PIN, Pin.OUT, value=0)
	