from data_writer import DataWriter
from machine import TouchPad
from rtc import PCF8523
import asyncio
import config
import time

async def run_experiment(
	stop_event: asyncio.Event,
	rtc: PCF8523,
	touch_array: list[TouchPad],
) -> None:
	print('Running experiment')
	filename = rtc.get_timestamp_filename()
	start_time = time.ticks_ms()
	writer = DataWriter(filename)

	try:
		while not stop_event.is_set():
			capsense_values: list[int] = [touch.read() for touch in touch_array]
			elapsed_ms = time.ticks_diff(time.ticks_ms(), start_time)
			writer.write(elapsed_ms, capsense_values)
			await asyncio.sleep_ms(config.SAMPLE_PERIOD_MS)
	finally:
		print("Recording stopped, flushing data...")
		writer.close()
		print("Data flushed, exiting recording task")
