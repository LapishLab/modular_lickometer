import asyncio
import machine
from idle_timer import IdleTimer
from rtc import get_PCF85263A_instance
from sd import mount_data_folder
from experiment import run_experiment
from button import get_UserButtons_instance
from http_server import get_HTTPServer_instance
from led import get_Status_LEDS_instance
from battery import get_BatteryMonitor_instance
from mode_handler import ModeDefinition, ModeHandler, ModeType
from capacitance import get_SipperArray_instance
from update_manager import get_UpdateManager_instance
import states

async def main() -> None:
	leds = get_Status_LEDS_instance()
	await leds.experiment.set_blinks(states.Experiment.STARTUP)
	battery = get_BatteryMonitor_instance()
	buttons = get_UserButtons_instance()
	rtc = get_PCF85263A_instance()
	sippers = get_SipperArray_instance()
	mount_data_folder()
	server = get_HTTPServer_instance()
	update_manager = get_UpdateManager_instance()
	idle_timer = IdleTimer()
	handler = ModeHandler((
		ModeDefinition(
			type=ModeType.RECORDING,
			start_trig=(buttons.start.pressed, server.start_trigger),
			stop_trig=(buttons.stop.pressed,),
		),
		ModeDefinition(
			type=ModeType.DEEP_SLEEP,
			start_trig=(idle_timer.trigger,),
			stop_trig=(),
		),
		ModeDefinition(
			type=ModeType.UPDATING,
			start_trig=(server.update_trigger,),
			stop_trig=(),
		),
	))
	print("Starting Main Loop")

	while True:
		await leds.experiment.set_blinks(states.Experiment.PENDING)
		await server.start()
		test_worker = asyncio.create_task(cap_test_loop())
		idle_timer.start()
		mode = await handler.wait()
		idle_timer.cancel()
		test_worker.cancel()
		await leds.experiment.set_blinks(states.Experiment.NONE)

		try:
			if mode.type == ModeType.RECORDING:
				await server.stop()
				await leds.experiment.set_blinks(states.Experiment.RECORDING)
				await run_experiment(mode.stop_event, rtc, sippers)
			elif mode.type == ModeType.DEEP_SLEEP:
				await server.stop()
				await idle_timer.enter_deep_sleep()
			elif mode.type == ModeType.UPDATING:
				await server.stop()
				update_manager.install()
				print("Application update installed; rebooting")
				machine.reset()
			else:
				raise ValueError("Unknown mode: {}".format(mode.type))
		finally:
			await leds.experiment.set_blinks(states.Experiment.NONE)
			handler.end_mode()


async def cap_test_loop(delay_ms: int = 200) -> None:
	sippers = get_SipperArray_instance()
	while True:
		sippers.left.read()
		sippers.right.read()
		await asyncio.sleep_ms(delay_ms)