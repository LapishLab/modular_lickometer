from data_writer import DataWriter
import asyncio
import config
import time

async def run_experiment(stop_event, rtc, touch_array):
	print('Running experiment')
	filename = rtc.get_timestamp_filename()
	start_time = time.ticks_ms()
	writer = DataWriter(filename)

	try:
		while not stop_event.is_set():
			capsense_values = [touch.read() for touch in touch_array]
			elapsed_ms = time.ticks_diff(time.ticks_ms(), start_time)
			t = elapsed_ms / 1000.0
			writer.write(t, capsense_values)
			await asyncio.sleep_ms(config.SAMPLE_PERIOD_MS)
	finally:
		print("Recording stopped, flushing data...")
		writer.close()
		print("Data flushed, exiting recording task")