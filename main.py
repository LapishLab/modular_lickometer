import config
import time
import _thread


def main():
	print("Starting Main Loop")
	while(True):
		time.sleep(1)
		# print("loop")
		if config.button.value() == 0: # Is the button pressed?
			print("Button Pressed")
			if not config.is_recording:
				print("Starting Recording Thread")
				config.is_recording = True
				# run_experiment()
				_thread.start_new_thread(run_experiment, ("Core1", 1))
				# config.led.set_status("Recording")
				time.sleep(1) # debounce
			else:
				print("Indicating that recording should stop")
				config.is_recording = False
				time.sleep(5) # let it finish up
				# led.set_status("Transferring")
				# transfer_data()
				# led.set_status("Idle")


from data_writer import DataWriter
def run_experiment(core, core_str):
	print('Running experiment')
	# Create Data writer
	with open('name.txt', 'r') as f:
		name = f.readline().strip()
	now = config.clock.get_timestamp_filename()
	filename = f'{now}_{name}.csv'
	writer = DataWriter(filename)

	while(config.is_recording):
		c = config.touch.read()
		t = config.clock.get_timestamp()
		writer.write(t,c)
		time.sleep_ms(config.SAMPLE_PERIOD_MS)
	print("Recording stopped, flushing data...")
	writer.flush()


if __name__ == "__main__":
	main();