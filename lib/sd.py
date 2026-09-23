import vfs
from config import SD_DATA_PINS, SD_CLK, SD_CMD, SD_DETECT, DATA_FOLDER
import os

def _is_mounted(mount_point: str) -> bool:
	try:
		# An unmounted directory belongs to the same filesystem as its parent, so
		# both paths have identical filesystem statistics. A mounted SD card has
		# its own filesystem and therefore different statistics.
		path = mount_point.rstrip("/")
		parent = path.rsplit("/", 1)[0] or "/"
		return os.statvfs(path) != os.statvfs(parent)
	except OSError:
		return False

def mount_data_folder() -> None:
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
