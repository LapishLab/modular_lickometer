from machine import Pin, SPI

import sdcard
import os

from machine import TouchPad
import time
import rtc

def record_touch():
	# ========= USER CONFIG =========
	TOUCH_PIN = 1
	STOP_BUTTON_PIN = 4      # Press to stop recording and start Wi-Fi transfer

	SPI_SCK  = 7
	SPI_MOSI = 9
	SPI_MISO = 8
	SD_CS    = 2

	# I2C config for RTC
	I2C_SCL = 6
	I2C_SDA = 5

	SAMPLE_PERIOD_MS = 50
	FLUSH_INTERVAL = 100
	# ===============================
	
	# Initialize RTC
	print("Initializing RTC...")
	try:
		rtc_device = rtc.init_rtc(scl_pin=I2C_SCL, sda_pin=I2C_SDA)
		# Auto-sync with system time on startup
		rtc_device.sync_time()
		print(f"RTC initialized: {rtc_device.get_timestamp()}")
		use_rtc = True
	except Exception as e:
		print(f"RTC initialization failed: {e}")
		use_rtc = False
	
	# ---- Capacitive touch setup ----
	touch = TouchPad(Pin(TOUCH_PIN))

	# ---- Stop button ----
	stop_button = Pin(STOP_BUTTON_PIN, Pin.IN, Pin.PULL_UP)

	# ---- SPI + SD card setup ----
	spi = SPI(
		2,
		baudrate=4_000_000,
		polarity=0,
		phase=0,
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
	if use_rtc:
		print("Using RTC timestamp for filename.")
		filename_timestamp = rtc_device.get_timestamp_filename()
	else:
		filename_timestamp = str(time.ticks_ms())
		print("not using RTC")
	
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

			if use_rtc:
				timestamp = rtc_device.get_timestamp()
			else:
				t_ms = time.ticks_ms()
				timestamp = t_ms
			
			val = touch.read()

			f.write("{},{}\n".format(timestamp, val))
			sample_count += 1

			if sample_count - last_flush >= FLUSH_INTERVAL:
				f.flush()
				last_flush = sample_count

			time.sleep_ms(SAMPLE_PERIOD_MS)
