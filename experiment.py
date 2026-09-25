from data_writer import DataWriter
from machine import TouchPad
from rtc import PCF85263A
import asyncio
from config import SAMPLE_PERIOD_MS
from time import ticks_diff, ticks_ms
from capacitance import SipperArray

async def run_experiment(
	stop_event: asyncio.Event,
	rtc: PCF85263A,
	sippers: SipperArray,
) -> None:
	print('Running experiment')
	filename = rtc.get_timestamp_filename()
	start_time = ticks_ms()
	writer = DataWriter(filename)

	try:
		while not stop_event.is_set():
			now = ticks_ms()
			elapsed_ms = ticks_diff(now, start_time)
			(l, l_ref) = sippers.left.read()
			(r, r_ref) = sippers.right.read()
			writer.write((elapsed_ms, l, l_ref, r, r_ref))
			remaing_ms = SAMPLE_PERIOD_MS - ticks_diff(ticks_ms(), now)
			await asyncio.sleep_ms(remaing_ms)
	finally:
		print("Recording stopped, flushing data...")
		writer.close()
		print("Data flushed, exiting recording task")
