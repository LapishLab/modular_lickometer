"""Route device inputs to modes and their shared stop events."""

from asyncio import ThreadSafeFlag, Event, create_task, Task

class ModeType:
	RECORDING = "recording"

class ModeDefinition:
	def __init__(self, type: str, start_trig: tuple[ThreadSafeFlag, ...], stop_trig: tuple[ThreadSafeFlag, ...]) -> None:
		self.type = type
		self.start_trig = start_trig
		self.stop_trig = stop_trig
		self.stop_event = Event()
		

class ModeHandler:
	def __init__(self, modes: tuple[ModeDefinition, ...]) -> None:
		self._modes = modes
		self._current_mode = None
		self._activation_ready = Event()
		self._watch_tasks = self._create_watchers()
		self._routing_enabled = False

	def _create_watchers(self) -> list[Task]:
		triggers = []
		for m in self._modes:
			triggers.extend(m.start_trig)
			triggers.extend(m.stop_trig)

		watchers = []
		already_watched = []
		for t in triggers:
			if t not in already_watched:
				already_watched.append(t)
				watchers.append(create_task(self._watch(t)))
		return watchers

	async def _watch(self, signal: ThreadSafeFlag) -> None:
		while True:
			await signal.wait()
			self._route(signal)

	def _route(self, trigger: ThreadSafeFlag) -> None:
		"""Route a signal to a new mode or the active mode's stop event."""
		if not self._routing_enabled:
			return
		if self._current_mode is None:
			for m in self._modes:
				if trigger in m.start_trig:
					self._current_mode = m
					self._activation_ready.set()
					return
		else:
			if trigger in self._current_mode.stop_trig:
				self._current_mode.stop_event.set()

	async def wait(self) -> ModeDefinition:
		"""Wait until an input activates a mode."""
		self._routing_enabled = True
		await self._activation_ready.wait()
		self._activation_ready.clear()

		if self._current_mode is None:
			raise RuntimeError("No active mode after activation ready. This should have been set during routing.")

		return self._current_mode

	def end_mode(self) -> None:
		"""Mark an activation complete so another mode can start."""
		self._routing_enabled = False
		if self._current_mode is not None:
			self._current_mode.stop_event.clear()
			self._current_mode = None
		
