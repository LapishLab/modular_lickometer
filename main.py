import asyncio
import config
from rtc import PCF8523
import states
from sd import mount_data_folder
from utilities import print_error
from experiment import run_experiment
from button import DebouncedButton
from http_server import HTTPServer
from led import BLINKING_LED
from battery import BatteryMonitor
from machine import TouchPad, Pin
from mode_handler import ModeDefinition, ModeHandler, ModeType

async def main() -> None:
	await asyncio.sleep(5)
	led_rec = BLINKING_LED(config.LED_REC_PIN)
	led_trans = BLINKING_LED(config.LED_TRANSFER_PIN)
	led_err = BLINKING_LED(config.LED_ERROR_PIN)
	battery = BatteryMonitor(
		config.BATTERY_VOLTAGE_PIN,
		config.LOW_BATTERY_LED_PIN,
	)
	button = DebouncedButton(config.STOP_BUTTON_PIN)
	rtc = PCF8523(scl_pin=config.I2C_SCL, sda_pin=config.I2C_SDA)
	touch_array = [TouchPad(Pin(p)) for p in config.TOUCH_PINS]
	mount_data_folder()
	server = HTTPServer()
	handler = ModeHandler((
		ModeDefinition(
			mode=ModeType.RECORDING,
			start_on=(button.pressed,),
			stop_on=(button.pressed,),
		),
	))

	print("Starting Main Loop")

	while True:
		states.current_status = states.Status.PENDING
		led_rec.num_flashes = 1
		await server.start()
		activation = await handler.wait_for_mode()

		try:
			await server.stop()
			led_rec.num_flashes = 0

			if activation.mode == ModeType.RECORDING:
				await run_experiment(activation.stop_event, rtc, touch_array)
			else:
				raise ValueError("Unknown mode: {}".format(activation.mode))
		finally:
			handler.end_mode()


if __name__ == "__main__":
	asyncio.run(main())
