
def mount_data_folder():
	from config import SPI_SCK, SPI_MOSI, SPI_MISO, SD_CS, DATA_FOLDER
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
	import vfs
	vfs.mount(sd, DATA_FOLDER)