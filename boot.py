# SD card initialization and mounting.

import os
import sdcard
from machine import Pin, SoftSPI
from config import SPI_SCK, SPI_MOSI, SPI_MISO, SD_CS, DATA_FOLDER
import config

## Mount the SD card
print(f"Mounting SD card to {DATA_FOLDER}...")
# Initialize SPI
spi = SoftSPI(
	baudrate=4_000_000,
	sck=Pin(SPI_SCK),
	mosi=Pin(SPI_MOSI),
	miso=Pin(SPI_MISO),
)

sd = sdcard.SDCard(spi, Pin(SD_CS))
os.mount(sd, DATA_FOLDER)
print(f"SD card mounted successfully: check out its contents: {os.listdir(DATA_FOLDER)}")