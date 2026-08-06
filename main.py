import time
import _thread
import states
from sd import mount_data_folder
import hardware
from utilities import print_error
from experiment import try_experiment

def main():
	time.sleep(5)
	try:
		do_everything()
	except Exception as e:
		states.current_status = states.Status.ERROR_GENERAL
		while True:
			print_error("An unknown error occurred somewhere in do_everything", e)
			time.sleep(1) # Halt further execution on  error
	
def do_everything():
	hardware.initialize()	
	try:
		mount_data_folder()
	except Exception as e:
		states.current_status = states.Status.ERROR_SD
		while True:
			print_error("Failed to mount data folder", e)
			time.sleep(100)

	print("Starting Main Loop")

	states.current_status = states.Status.PENDING
	print("pending")
	while(True):
		time.sleep(.001)
		try:
			check_button()
		except Exception as e:
			states.current_status = states.Status.ERROR_BUTTON
			while True:
				print_error("A button error occurred", e)
				time.sleep(1) # Halt further execution on unexpected error


def check_button():
	# print("loop")
	if hardware.button.value() == 0: # Is the button pressed?
		print("Button Pressed")
		if states.current_status == states.Status.PENDING:
			print("Starting Recording Thread")
			states.current_status = states.Status.RECORDING
			states.keep_recording = True
			# run_experiment()
			_thread.start_new_thread(try_experiment, ("Core1", 1))
			# config.led.set_status("Recording")
			time.sleep(1) # debounce
		else:
			print("Indicating that recording should stop")
			states.current_status = states.Status.STOPPING_RECORDING
			states.keep_recording = False
			while states.current_status is not states.Status.PENDING:
				time.sleep(1)  # Wait for recording thread to finish
			# led.set_status("Transferring")
			# transfer_data()
			# led.set_status("Idle")



if __name__ == "__main__":
	main()