from machine import Pin
import asyncio

import config
class UserButtons:	
	def __init__(self) -> None:
		self.start = DebouncedButton(config.START_BUTTON_PIN)
		self.stop = DebouncedButton(config.STOP_BUTTON_PIN)

class DebouncedButton:
	"""A falling-edge button whose debounce state is self-contained."""

	def __init__(self, pin_number: int, debounce_ms: int = 50) -> None:
		self._pin = Pin(pin_number, Pin.IN, Pin.PULL_UP)
		self._debounce_ms = debounce_ms
		self._interrupt = asyncio.ThreadSafeFlag()
		self.pressed = asyncio.ThreadSafeFlag()

		self._pin.irq(
			trigger=Pin.IRQ_FALLING,
			handler=lambda p:self._interrupt.set(),
		)
		self._debounce_task = asyncio.create_task(self._process_interrupts())

	async def _process_interrupts(self) -> None:
		while True:
			await self._interrupt.wait()
			self.pressed.set()
			await asyncio.sleep_ms(self._debounce_ms)
			self._interrupt.clear()
