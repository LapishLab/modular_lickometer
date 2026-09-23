import vfs
from config import SD_DATA_PINS, SD_CLK, SD_CMD, SD_DETECT, DATA_FOLDER
import os

def _is_mounted(mount_point):
	# Check if the mount point exists and is a directory
	# TODO: This could be misleading if the directory exists, but the SD card is not actually mounted.
	try:
		# Get file/directory status bits
		mode = os.stat(mount_point)[0]
		
		# In MicroPython, directory mode bits usually match standard S_IFDIR (0x4000)
		# Check if the path is a directory (0x4000) rather than a regular file (0x8000)
		return bool(mode & 0x4000)
	except OSError:
		# Path does not exist
		return False

def mount_data_folder():
	if _is_mounted(DATA_FOLDER):
		print(f"Data folder already exists: {DATA_FOLDER}.")
		return

	print("Initializing SD card in 4-bit SDIO mode...")
	from machine import Pin, SDCard
	card_detect = Pin(SD_DETECT, Pin.IN, Pin.PULL_UP)
	if card_detect.value():
		raise OSError("No SD card inserted")

	sd = SDCard(
		slot=1,
		width=4,
		sck=SD_CLK,
		cmd=SD_CMD,
		data=SD_DATA_PINS,
		cd=card_detect,
	)

	print(f"Mounting SD card to {DATA_FOLDER}...")
	vfs.mount(sd, DATA_FOLDER)
