from machine import Pin, SoftSPI

import sdcard
import os

from machine import TouchPad
import time
import rtc
from config import I2C_SCL, I2C_SDA, TOUCH_PIN, STOP_BUTTON_PIN, SPI_SCK, SPI_MOSI, SPI_MISO, SD_CS

def record_touch():
	SAMPLE_PERIOD_MS = 50
	FLUSH_INTERVAL = 100
	# ===============================
	
	# Initialize RTC
	rtc_device = rtc.init_rtc(scl_pin=I2C_SCL, sda_pin=I2C_SDA)
	rtc_device.sync_time(ntp=False)  # Sync with system time (no NTP)
	print(f"RTC initialized: {rtc_device.get_timestamp()}")
	
	# ---- Capacitive touch setup ----
	touch = TouchPad(Pin(TOUCH_PIN))

	# ---- Stop button ----
	stop_button = Pin(STOP_BUTTON_PIN, Pin.IN, Pin.PULL_UP)

	# ---- SPI + SD card setup ----
	spi = SoftSPI(
		baudrate=4_000_000,
		sck=Pin(SPI_SCK),
		mosi=Pin(SPI_MOSI),
		miso=Pin(SPI_MISO),
	)

	# Create csv file
	data_folder = "/data"

	# If you don't see the data folder, mount the SD card to the data folder location
	if data_folder.replace("/", "") not in os.listdir():
		sd = sdcard.SDCard(spi, Pin(SD_CS))
		os.mount(sd, data_folder)

	# Use RTC timestamp for filename if available, otherwise use milliseconds
	filename_timestamp = rtc_device.get_timestamp_filename()
	
	with open("/name.txt", 'r') as f:
		esp_name = f.read().strip()

	LOG_FILENAME = f'/{filename_timestamp}_{esp_name}.csv'

	log_path = data_folder + LOG_FILENAME
	print(f'Saving Data to: {log_path}')

	print("Recording started...")
	sample_count = 0
	last_flush = 0

	with open(log_path, "w") as f:
		f.write("timestamp,touch_value\n")
		while True:
			if stop_button.value() == 0:
				print("Stop button pressed. Ending recording.")
				f.flush()
				return

			timestamp = rtc_device.get_timestamp()
			
			val = touch.read()

			f.write("{},{}\n".format(timestamp, val))
			sample_count += 1

			if sample_count - last_flush >= FLUSH_INTERVAL:
				f.flush()
				last_flush = sample_count

			time.sleep_ms(SAMPLE_PERIOD_MS)
