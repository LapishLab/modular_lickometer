import asyncio
import states
from sd import mount_data_folder
import hardware
from utilities import print_error
from experiment import run_experiment

async def main():
	await asyncio.sleep(5)
	await hardware.initialize()
	mount_data_folder()

	print("Starting Main Loop")

	states.current_status = states.Status.PENDING
	print("pending")
	while(True):
		await hardware.button_pressed.wait()
		print("Starting recording task")
		stop_event = asyncio.Event()
		asyncio.create_task(run_experiment(stop_event))
		await asyncio.sleep_ms(50)  # Ignore switch bounce before accepting another edge
		hardware.arm_button_interrupt()

		await hardware.button_pressed.wait()
		print("Indicating that recording should stop")
		stop_event.set()

		await asyncio.sleep_ms(50)  # Ignore switch bounce before accepting another edge
		hardware.arm_button_interrupt()



if __name__ == "__main__":
	asyncio.run(main())
