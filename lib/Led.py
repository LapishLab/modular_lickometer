from machine import Pin, PWM
import asyncio

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
		self.num_flashes = 0 # 0 means never turn on, -1 means stay on, >0 means flash that many times 
		
		self.task = asyncio.create_task(self.blink_loop())
	
	async def blink_loop(self) -> None:
		while True:
			if self.num_flashes == -1:
				self.PWM.duty_u16(self.intensity)
			elif self.num_flashes == 0:
				self.PWM.duty_u16(0)
			elif self.num_flashes > 0:
				for _ in range(self.num_flashes):
					self.PWM.duty_u16(self.intensity)
					await asyncio.sleep_ms(self.FLASH_ON)
					self.PWM.duty_u16(0)
					await asyncio.sleep_ms(self.FLASH_OFF)
			await asyncio.sleep_ms(self.PAUSE_OFF)
