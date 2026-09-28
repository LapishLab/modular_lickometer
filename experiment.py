from data_writer import DataWriter
from rtc import PCF85263A
import asyncio
from config import SAMPLE_PERIOD_MS
from time import ticks_diff, ticks_us
from capacitance import SipperArray

async def run_experiment(
	stop_event: asyncio.Event,
	rtc: PCF85263A,
	sippers: SipperArray,
) -> None:
	print('Running experiment')
	filename = rtc.get_timestamp_filename()
	timer_start = ticks_us()
	writer = DataWriter(filename)

	try:
		while not stop_event.is_set():
			timer_stop = ticks_us()
			(l, l_ref) = sippers.left.read()
			(r, r_ref) = sippers.right.read()
			elapsed_ms = ticks_diff(timer_stop, timer_start)
			writer.write((elapsed_ms, l, l_ref, r, r_ref))
			timer_start = timer_stop
			loop_ms = ticks_diff(ticks_us(), timer_stop) // 1000
			await asyncio.sleep_ms(SAMPLE_PERIOD_MS - loop_ms)
	finally:
		print("Recording stopped, flushing data...")
		writer.close()
		print("Data flushed, exiting recording task")
