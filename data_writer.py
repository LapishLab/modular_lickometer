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
		
		# Initialize SPI
		self.spi = SoftSPI(
			baudrate=4_000_000,
			sck=Pin(spi_sck),
			mosi=Pin(spi_mosi),
			miso=Pin(spi_miso),
		)
		
		# Mount SD card if not already mounted
		self._mount_sd_card(sd_cs, data_folder=data_folder)
		
		# Construct full file path
		self.file_path = f"{data_folder}/{filename}"
		
		print(f"Creating data file: {self.file_path}")
		
		# Open file and write header
		with open(self.file_path, 'w') as f:
			f.write(f"{header}\n")
	
	def _mount_sd_card(self, sd_cs, data_folder=DATA_FOLDER):
		"""
		Mount SD card to data folder if not already mounted
		
		Args:
			sd_cs: Chip select pin for SD card
		"""
		# Check if data folder already exists (i.e., SD card already mounted)
		if data_folder.replace("/", "") not in os.listdir():
			print(f"Mounting SD card to {data_folder}...")
			try:
				sd = sdcard.SDCard(self.spi, Pin(sd_cs))
				os.mount(sd, data_folder)
				print(f"SD card mounted successfully")
			except Exception as e:
				print(f"Error mounting SD card: {e}")
				raise
		else:
			print(f"SD card already mounted at {data_folder}")
	
	def write(self, timestamp, value):
		self.pending_data.append(f'{timestamp},{value}')
		self.samples_since_flush += 1

		if self.samples_since_flush >= self.FLUSH_MAX:
			self.flush()
	
	def flush(self):		
		with open(self.file_path, 'a') as f:
			for d in self.pending_data:
				f.write(f"{d}\n")
		self.samples_since_flush = 0
	
	# def close(self):
	# 	"""Close the file and cleanup"""
	# 	if self.file:
	# 		self.file.flush()
	# 		self.file.close()
	# 		self.file = None
	# 		print(f"Data file closed: {self.file_path}")
	
	# def __enter__(self):
	# 	"""Context manager entry"""
	# 	return self
	
	# def __exit__(self, exc_type, exc_val, exc_tb):
	# 	"""Context manager exit - ensures file is closed"""
	# 	self.close()
	# 	return False
