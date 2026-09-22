from data_writer import DataWriter
import asyncio
import states
import hardware
import config
import time
from utilities import print_error
from tcp import connect_to_server_and_send_file

async def try_experiment():
	try:
		await run_experiment()
	except Exception as e:
		states.current_status = states.Status.ERROR_RUN_EXPERIMENT
		while True:
			print_error("An unknown error occurred in run_experiment", e)
			await asyncio.sleep(1) # Halt further execution on unexpected error


async def run_experiment():
	print('Running experiment')
	high_samples = 1000
	low_samples = 500
	pattern_samples = high_samples + low_samples
	sample_index = 0
	# Create Data writer
	with open('name.txt', 'r') as f:
		name = f.readline().strip()
	now = hardware.clock.get_timestamp_filename()
	file_path = f"{config.DATA_FOLDER}/{now}_{name}.csv"
	start_time = time.ticks_ms()
	writer = DataWriter(file_path, header="timestamp,touch_value_1,touch_value_2")

	try:
		while(states.keep_recording):
			c = hardware.touch.read()
			c2 = hardware.touch2.read()
			hardware.sync_out.value(
				1 if sample_index % pattern_samples < high_samples else 0
			)
			sample_index += 1
			elapsed_ms = time.ticks_diff(time.ticks_ms(), start_time)
			t = elapsed_ms / 1000.0
			writer.write(t, c, c2)
			await asyncio.sleep_ms(config.SAMPLE_PERIOD_MS)
	finally:
		hardware.sync_out.value(0)
	print("Recording stopped, flushing data...")
	writer.close()
	print("Data flushed, exiting recording task")
	states.current_status = states.Status.DATA_TRANSFER 
	await connect_to_server_and_send_file(file_path=file_path)
	states.current_status = states.Status.PENDING

