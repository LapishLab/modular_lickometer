from data_writer import DataWriter
import asyncio
import states
import hardware
import config
import time
from utilities import print_error
from tcp import connect_to_server_and_send_file



async def run_experiment(stop_event):
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

	while not stop_event.is_set():
		c = hardware.touch.read()
		c2 = hardware.touch2.read()
		hardware.sync_out.value(1 if sample_index % pattern_samples < high_samples else 0)
		sample_index += 1
		elapsed_ms = time.ticks_diff(time.ticks_ms(), start_time)
		t = elapsed_ms / 1000.0
		writer.write(t, c, c2)
		await asyncio.sleep_ms(config.SAMPLE_PERIOD_MS)
	print("Recording stopped, flushing data...")
	writer.close()
	print("Data flushed, exiting recording task")
	states.current_status = states.Status.DATA_TRANSFER 
	await connect_to_server_and_send_file(file_path=file_path)
	states.current_status = states.Status.PENDING

