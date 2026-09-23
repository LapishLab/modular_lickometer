"""Route device inputs to modes and their shared stop events."""

from asyncio import ThreadSafeFlag, Event, create_task

class ModeType:
	RECORDING = "recording"

class ModeDefinition:
	def __init__(self, mode: str, start_on: tuple, stop_on: tuple) -> None:
		self.mode = mode
		self.start_on = start_on
		self.stop_on = stop_on


class ModeActivation:
	def __init__(self, definition: ModeDefinition) -> None:
		self.mode = definition.mode
		self.stop_event = Event()
		self._definition = definition


class ModeHandler:
	def __init__(self, definitions: tuple) -> None:
		self._definitions = definitions
		self._ready_for_event = False
		self._current_activation = None
		self._activation_ready = Event()
		self._watch_tasks = self._create_watch_tasks()

	def _create_watch_tasks(self) -> list:
		all_signals = []
		for mode_def in self._definitions:
			all_signals.extend(mode_def.start_on)
			all_signals.extend(mode_def.stop_on)

		watch_tasks = []
		already_watched = []
		for signal in all_signals:
			if not self._contains(already_watched, signal):
				already_watched.append(signal)
				watch_tasks.append(
					create_task(self._watch(signal))
				)

		return watch_tasks

	async def _watch(self, signal: ThreadSafeFlag) -> None:
		while True:
			await signal.wait()
			self._route(signal)

	def _route(self, signal: ThreadSafeFlag) -> None:
		"""Route a signal to a new mode or the active mode's stop event."""
		if not self._ready_for_event:
			return
		
		if self._current_activation is None:
			for mode_def in self._definitions:
				if self._contains(mode_def.start_on, signal):
					self._current_activation = ModeActivation(mode_def)
					self._activation_ready.set()
					return
		else:
			if self._contains(self._current_activation._definition.stop_on, signal):
				self._current_activation.stop_event.set()
			else:
				print("Ignoring input while in {}".format(self._current_activation.mode))
			return

	def _contains(self, signals: list | tuple, target: object) -> bool:
		return any(target is signal for signal in signals)

	async def wait_for_mode(self) -> ModeActivation:
		"""Wait until an input activates a mode."""
		self._ready_for_event = True
		await self._activation_ready.wait()
		self._activation_ready.clear()

		if self._current_activation is None:
			raise RuntimeError("No active mode after activation ready. This should have been set during routing.")

		return self._current_activation

	def end_mode(self) -> None:
		"""Mark an activation complete so another mode can start."""
		self._current_activation = None
		self._ready_for_event = False
		
