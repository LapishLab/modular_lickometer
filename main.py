import asyncio
import states
from sd import mount_data_folder
import hardware
from utilities import print_error
from experiment import try_experiment

async def main():
	await asyncio.sleep(5)
	try:
		await do_everything()
	except Exception as e:
		states.current_status = states.Status.ERROR_GENERAL
		while True:
			print_error("An unknown error occurred somewhere in do_everything", e)
			await asyncio.sleep(1) # Halt further execution on error
	
async def do_everything():
	await hardware.initialize()
	try:
		mount_data_folder()
	except Exception as e:
		states.current_status = states.Status.ERROR_SD
		while True:
			print_error("Failed to mount data folder", e)
			await asyncio.sleep(100)

	print("Starting Main Loop")

	states.current_status = states.Status.PENDING
	print("pending")
	while(True):
		await asyncio.sleep_ms(1)
		try:
			await check_button()
		except Exception as e:
			states.current_status = states.Status.ERROR_BUTTON
			while True:
				print_error("A button error occurred", e)
				await asyncio.sleep(1) # Halt further execution on unexpected error


async def check_button():
	# print("loop")
	if hardware.button.value() == 0: # Is the button pressed?
		print("Button Pressed")
		if states.current_status == states.Status.PENDING:
			print("Starting recording task")
			states.current_status = states.Status.RECORDING
			states.keep_recording = True
			asyncio.create_task(try_experiment())
			# config.led.set_status("Recording")
			await asyncio.sleep(1) # debounce
		else:
			print("Indicating that recording should stop")
			states.current_status = states.Status.STOPPING_RECORDING
			states.keep_recording = False
			while states.current_status is not states.Status.PENDING:
				await asyncio.sleep(1)  # Wait for the recording task to finish
			# led.set_status("Transferring")
			# transfer_data()
			# led.set_status("Idle")



if __name__ == "__main__":
	asyncio.run(main())
