from machine import Pin, PWM
import asyncio
import config
class Status_LEDS:
	"""Class to manage the status LEDs on the device."""
	def __init__(self) -> None:
		self.recording = BLINKING_LED(config.LED_REC_PIN)
		self.transfer = BLINKING_LED(config.LED_TRANSFER_PIN)
		self.error = BLINKING_LED(config.LED_ERROR_PIN)

class BLINKING_LED:
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

	def set_blinks(self, num_flashes: int) -> None:
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
