import config
import time
import _thread
import os
import states
from states import Status
from sd import mount_data_folder
import hardware
from utilities import print_error

def main():
	time.sleep(5)
	try:
		do_everything()
	except Exception as e:
		states.current_status = Status.ERROR_GENERAL
		while True:
			print_error("An unexpected error occurred", e)
			time.sleep(1) # Halt further execution on unexpected error
	
def do_everything():
	hardware.initialize()	
	try:
		mount_data_folder()
	except Exception as e:
		states.current_status = Status.ERROR_SD
		while True:
			print_error("Failed to mount data folder", e)
			time.sleep(100)
		return

	print("Starting Main Loop")

	states.current_status = Status.PENDING
	print("pending")
	while(True):
		time.sleep(1)
		try:
			check_button()
		except Exception as e:
			states.current_status = Status.ERROR_BUTTON
			while True:
				print_error("A button error occurred", e)
				time.sleep(1) # Halt further execution on unexpected error



def check_button():
	# print("loop")
	if hardware.button.value() == 0: # Is the button pressed?
		print("Button Pressed")
		if states.current_status == Status.PENDING:
			print("Starting Recording Thread")
			states.current_status = Status.RECORDING
			# run_experiment()
			_thread.start_new_thread(try_experiment, ("Core1", 1))
			# config.led.set_status("Recording")
			time.sleep(1) # debounce
		else:
			print("Indicating that recording should stop")
			states.current_status = Status.STOPPING_RECORDING
			while states.current_status == Status.STOPPING_RECORDING:
				time.sleep(1)  # Wait for recording thread to finish
			# led.set_status("Transferring")
			# transfer_data()
			# led.set_status("Idle")


from data_writer import DataWriter
def try_experiment(core, core_str):
	try:
		run_experiment(core, core_str)
	except Exception as e:
		states.current_status = Status.ERROR_RUN_EXPERIMENT
		while True:
			print_error("An unexpected error occurred", e)
			time.sleep(1) # Halt further execution on unexpected error


def run_experiment(core, core_str):
	print('Running experiment')
	# Create Data writer
	with open('name.txt', 'r') as f:
		name = f.readline().strip()
	now = hardware.clock.get_timestamp_filename()
	filename = f'{now}_{name}.csv'
	writer = DataWriter(filename)

	while(states.current_status == Status.RECORDING):
		c = hardware.touch.read()
		t = hardware.clock.get_timestamp()
		writer.write(t,c)
		time.sleep_ms(config.SAMPLE_PERIOD_MS)
	print("Recording stopped, flushing data...")
	writer.flush()
	print("Data flushed, exiting thread")
	states.current_status = Status.PENDING


if __name__ == "__main__":
	main()