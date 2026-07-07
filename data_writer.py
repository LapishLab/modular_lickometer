"""
Data Writer class for handling SD card file operations

Handles SD card initialization, file creation with headers, and data writing.
"""

import os
import sdcard
from machine import Pin, SoftSPI
from config import SPI_SCK, SPI_MOSI, SPI_MISO, SD_CS, DATA_FOLDER


class DataWriter:
	"""
	Handles SD card file creation and data writing
	
	Initializes SD card during construction, creates the file with headers,
	and provides methods for writing data.
	"""
	
	def __init__(self, filename, header="timestamp,touch_value", 
				 spi_sck=SPI_SCK, spi_mosi=SPI_MOSI, spi_miso=SPI_MISO, 
				 sd_cs=SD_CS, data_folder=DATA_FOLDER):
		"""
		Initialize DataWriter and prepare SD card and file
		
		Args:
			filename: Name of file to create (with or without path)
			header: CSV header line to write (default: "timestamp,touch_value")
			spi_sck: SPI clock pin (default from config)
			spi_mosi: SPI MOSI pin (default from config)
			spi_miso: SPI MISO pin (default from config)
			sd_cs: SD card chip select pin (default from config)
			data_folder: Mount point for SD card (default: "/data")
		"""
		self.FLUSH_MAX = 1000  # Number of samples between flushes
		self.samples_since_flush = 0
		self.pending_data = []
		
		# Construct full file path
		self.file_path = f"{data_folder}/{filename}"
		
		print(f"Creating data file: {self.file_path}")
		
		# Open file and write header
		self.file = open(self.file_path, 'w')
		self.file.write(f"{header}\n")
		
	
	def write(self, timestamp, value):
		"""Write a single data point to the file"""
		self.file.write(f"{timestamp},{value}\n")

	def close(self):
		if self.file:
			self.file.flush()
			self.file.close()