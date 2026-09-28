import asyncio
from rtc import get_PCF85263A_instance
from sd import mount_data_folder
from utilities import print_error
from experiment import run_experiment
from button import get_UserButtons_instance
from http_server import get_HTTPServer_instance
from led import get_Status_LEDS_instance
from battery import get_BatteryMonitor_instance
from mode_handler import ModeDefinition, ModeHandler, ModeType
from capacitance import get_SipperArray_instance
import states

async def main() -> None:
	await asyncio.sleep(5)
	leds = get_Status_LEDS_instance()
	await leds.experiment.set_blinks(states.Experiment.STARTUP)
	battery = get_BatteryMonitor_instance()
	buttons = get_UserButtons_instance()
	rtc = get_PCF85263A_instance()
	sippers = get_SipperArray_instance()
	mount_data_folder()
	server = get_HTTPServer_instance()
	handler = ModeHandler((
		ModeDefinition(
			type=ModeType.RECORDING,
			start_trig=(buttons.start.pressed,),
			stop_trig=(buttons.stop.pressed,),
		),
	))

	print("Starting Main Loop")

	while True:
		await leds.experiment.set_blinks(states.Experiment.PENDING)
		await server.start()
		mode = await handler.wait()
		await leds.experiment.set_blinks(states.Experiment.NONE)

		try:
			await server.stop()
			if mode.type == ModeType.RECORDING:
				await leds.experiment.set_blinks(states.Experiment.RECORDING)
				await run_experiment(mode.stop_event, rtc, sippers)
			else:
				raise ValueError("Unknown mode: {}".format(mode.type))
		finally:
			await leds.experiment.set_blinks(states.Experiment.NONE)
			handler.end_mode()


if __name__ == "__main__":
	asyncio.run(main())
