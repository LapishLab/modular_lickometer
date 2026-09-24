from data_writer import DataWriter
from machine import TouchPad
from rtc import PCF8523
import asyncio
import config
import time
from capacitance import SipperArray

async def run_experiment(
	stop_event: asyncio.Event,
	rtc: PCF8523,
	sippers: SipperArray,
) -> None:
	print('Running experiment')
	filename = rtc.get_timestamp_filename()
	start_time = time.ticks_ms()
	writer = DataWriter(filename)

	try:
		while not stop_event.is_set():
			elapsed_ms = time.ticks_diff(time.ticks_ms(), start_time)
			left = sippers.left.read()
			right = sippers.right.read()
			writer.write((elapsed_ms, left, right))
			await asyncio.sleep_ms(config.SAMPLE_PERIOD_MS)
	finally:
		print("Recording stopped, flushing data...")
		writer.close()
		print("Data flushed, exiting recording task")
