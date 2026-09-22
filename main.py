import asyncio
import config
import states
from sd import mount_data_folder
import hardware
from utilities import print_error
from experiment import run_experiment
from button import DebouncedButton
from led import BLINKING_LED

async def main():
	await asyncio.sleep(5)
	led_rec = BLINKING_LED(config.LED_REC_PIN)
	led_trans = BLINKING_LED(config.LED_TRANSFER_PIN)
	led_err = BLINKING_LED(config.LED_ERROR_PIN)
	button = DebouncedButton(config.STOP_BUTTON_PIN)
	await hardware.initialize()
	mount_data_folder()

	print("Starting Main Loop")

	states.current_status = states.Status.PENDING
	print("pending")
	while(True):
		led_rec.num_flashes = 1
		await button.pressed.wait()
		led_rec.num_flashes = 0
		print("Starting recording task")
		stop_event = asyncio.Event()
		asyncio.create_task(run_experiment(stop_event))

		await button.pressed.wait()
		print("Indicating that recording should stop")
		stop_event.set()



if __name__ == "__main__":
	asyncio.run(main())
