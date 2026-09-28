import asyncio
import config
from rtc import PCF85263A
from sd import mount_data_folder
from utilities import print_error
from experiment import run_experiment
from button import UserButtons
from http_server import HTTPServer
from led import Status_LEDS
from battery import BatteryMonitor
from mode_handler import ModeDefinition, ModeHandler, ModeType
from capacitance import SipperArray
import states

async def main() -> None:
	await asyncio.sleep(5)
	leds = Status_LEDS()
	await leds.experiment.set_blinks(states.Experiment.STARTUP)
	battery = BatteryMonitor()
	buttons = UserButtons()
	rtc = PCF85263A(scl_pin=config.I2C_SCL, sda_pin=config.I2C_SDA)
	sippers = SipperArray()
	mount_data_folder()
	server = HTTPServer(battery=battery, led=leds.wireless, error=leds.error)
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
