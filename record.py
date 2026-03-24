from machine import Pin, SPI

import sdcard
import os

from machine import TouchPad
import time

# ========= USER CONFIG =========
TOUCH_PIN = 1
STOP_BUTTON_PIN = 4      # Press to stop recording and start Wi-Fi transfer

SPI_SCK  = 7
SPI_MOSI = 9
SPI_MISO = 8
SD_CS    = 2

LOG_FILENAME = "/touch_log.csv"
SAMPLE_PERIOD_MS = 50
FLUSH_INTERVAL = 100
# ===============================
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

sd = sdcard.SDCard(spi, Pin(SD_CS))
data_folder = "/data"

os.mount(sd, data_folder)

log_path = data_folder + LOG_FILENAME
print(f'Log path {log_path}')

if LOG_FILENAME not in os.listdir(data_folder):
    with open(log_path, "w") as f:
        f.write("timestamp_ms,touch_value\n")


# ---------------------------------------------------------
#  RECORDING LOOP
# ---------------------------------------------------------
def record_touch():
    print("Recording started...")
    sample_count = 0
    last_flush = 0

    with open(log_path, "a") as f:
        while True:
            if stop_button.value() == 0:
                print("Stop button pressed. Ending recording.")
                f.flush()
                return

            t_ms = time.ticks_ms()
            val = touch.read()

            f.write("{},{}\n".format(t_ms, val))
            sample_count += 1

            if sample_count - last_flush >= FLUSH_INTERVAL:
                f.flush()
                last_flush = sample_count

            time.sleep_ms(SAMPLE_PERIOD_MS)
