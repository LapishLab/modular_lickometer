import vfs
from config import SPI_SCK, SPI_MOSI, SPI_MISO, SD_CS, DATA_FOLDER
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

	# Initialize SPI
	print("Initializing SPI...")
	from machine import Pin, SPI
	spi = SPI(1,
		baudrate=4_000_000,
		sck=Pin(SPI_SCK),
		mosi=Pin(SPI_MOSI),
		miso=Pin(SPI_MISO))

	print("Initializing SD card...")
	from lib.sdcard import SDCard
	sd = SDCard(spi, Pin(SD_CS))

	print(f"Mounting SD card to {DATA_FOLDER}...")
	vfs.mount(sd, DATA_FOLDER)
	