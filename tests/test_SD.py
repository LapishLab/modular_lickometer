from config import SD_DATA_PINS, SD_CLK, SD_CMD, SD_DETECT

try:
	from machine import Pin, SDCard
	import os

	print("Modules imported (machine.SDCard, os)")
	detect = Pin(SD_DETECT, Pin.IN, Pin.PULL_UP)
	print(
		f"Card detect (GPIO {SD_DETECT}, active low): {detect.value()} "
		f"({'inserted' if not detect.value() else 'not inserted'})"
	)

	try:
		print(
			f"Initializing 4-bit SDIO "
			f"(CLK={SD_CLK}, CMD={SD_CMD}, DATA={SD_DATA_PINS})..."
		)
		sd = SDCard(
			slot=1,
			width=4,
			sck=SD_CLK,
			cmd=SD_CMD,
			data=SD_DATA_PINS,
			cd=detect,
		)
		print("SD card initialized")

		try:
			os.mount(sd, "/data")
			print("SD card mounted to /data")
			print(f"Files on SD card: {os.listdir('/data')}")
		except OSError as e:
			print(f"Mount failed: {e}")
			print("The card may already be mounted or have a filesystem issue.")
	except Exception as e:
		print(f"SDIO initialization failed: {e}")
		print("Check that the card is inserted and the SDIO pins are connected correctly.")
except ImportError as e:
	print(f"Import failed: {e}")

print("\n" + "=" * 50)
print("DIAGNOSTICS COMPLETE")
print("=" * 50)
