
import asyncio

import esp32
from machine import Pin, deepsleep

import config


class IdleTimer:
	"""Route idle timeout to a deep sleep that wakes on the stop button."""

	def __init__(self, timeout_ms: int = config.IDLE_SLEEP_TIMEOUT_MS) -> None:
		self.timeout_ms = timeout_ms
		self.trigger = asyncio.ThreadSafeFlag()
		self._task = None

	def start(self) -> None:
		"""Start a fresh idle timeout."""
		self.cancel()
		self._task = asyncio.create_task(self._watchdog())

	def cancel(self) -> None:
		"""Cancel the timeout when the device leaves idle mode."""
		if self._task is not None:
			self._task.cancel()
			self._task = None

	async def _watchdog(self) -> None:
		await asyncio.sleep_ms(self.timeout_ms)
		self.trigger.set()

	async def enter_deep_sleep(self) -> None:
		"""Sleep until the active-low stop button is pressed."""
		wake_button = Pin(config.STOP_BUTTON_PIN, Pin.IN, Pin.PULL_UP)
		esp32.wake_on_ext0(wake_button, esp32.WAKEUP_ALL_LOW)
		deepsleep()