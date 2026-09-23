import asyncio
import config
from rtc import PCF8523
import states
from sd import mount_data_folder
from utilities import print_error
from experiment import run_experiment
from button import UserButtons
from http_server import HTTPServer
from led import Status_LEDS
from battery import BatteryMonitor
from machine import TouchPad, Pin
from mode_handler import ModeDefinition, ModeHandler, ModeType

async def main() -> None:
	await asyncio.sleep(5)
	leds = Status_LEDS()
	battery = BatteryMonitor()
	buttons = UserButtons()
	rtc = PCF8523(scl_pin=config.I2C_SCL, sda_pin=config.I2C_SDA)
	touch_array = [TouchPad(Pin(p)) for p in config.TOUCH_PINS]
	mount_data_folder()
	server = HTTPServer()
	handler = ModeHandler((
		ModeDefinition(
			mode=ModeType.RECORDING,
			start_on=(buttons.start.pressed,),
			stop_on=(buttons.stop.pressed,),
		),
	))

	print("Starting Main Loop")

	while True:
		states.current_status = states.Status.PENDING
		leds.recording.set_blinks(1)
		await server.start()
		activation = await handler.wait_for_mode()

		try:
			await server.stop()
			await leds.recording.set_constant(False)
			if activation.mode == ModeType.RECORDING:
				await leds.recording.set_constant(True)
				await run_experiment(activation.stop_event, rtc, touch_array)
			else:
				raise ValueError("Unknown mode: {}".format(activation.mode))
		finally:
			handler.end_mode()


if __name__ == "__main__":
	asyncio.run(main())
