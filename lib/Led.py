from machine import Pin, PWM
import asyncio
from config import LED_REC_PIN, LED_TRANSFER_PIN, LED_ERROR_PIN

_instance_Status_LEDS = None
def get_Status_LEDS_instance() -> Status_LEDS:
    """Global access point that instantiates ONLY when called."""
    global _instance_Status_LEDS
    if _instance_Status_LEDS is None:
        _instance_Status_LEDS = Status_LEDS()
    return _instance_Status_LEDS

class Status_LEDS:
	"""Class to manage the status LEDs on the device."""
	def __init__(self) -> None:
		self.experiment = Blinking_LED(LED_REC_PIN)
		self.wireless = Blinking_LED(LED_TRANSFER_PIN)
		self.error = Blinking_LED(LED_ERROR_PIN)

class Blinking_LED:
	def __init__(self, pin: int) -> None:
		"""
		Initialize single LED
		
		Args:
			pin: GPIO pin
			get_state: Callable function that returns [color, num_flashes]
		"""
		self.PWM = PWM(Pin(pin))
		self.PWM.freq(1000)
		self.PWM.duty_u16(0)  # Start with LED off
		
		# Timing constants (in milliseconds)
		self.FLASH_ON = 100
		self.FLASH_OFF = 100
		self.PAUSE_OFF = 1000
		self.intensity = int(0.5 * 2**16)
		self.num_flashes = 1
		self.task = None
	
	async def blink_loop(self) -> None:
		while True:
			if self.num_flashes >0:
				for _ in range(self.num_flashes):
					self.PWM.duty_u16(self.intensity)
					await asyncio.sleep_ms(self.FLASH_ON)
					self.PWM.duty_u16(0)
					await asyncio.sleep_ms(self.FLASH_OFF)
			await asyncio.sleep_ms(self.PAUSE_OFF)

	async def set_blinks(self, num_flashes: int) -> None:
		if num_flashes==0:
			await self.set_constant(False)
		elif num_flashes==-1:
			await self.set_constant(True)
		elif num_flashes>0:
			self.num_flashes = num_flashes
			if self.task is None:
				self.task = asyncio.create_task(self.blink_loop())

	async def set_constant(self, on: bool) -> None:
		if self.task is not None:
			self.task.cancel()
			try:
				await self.task
			except asyncio.CancelledError:
				self.task = None
		self.PWM.duty_u16(self.intensity if on else 0)
