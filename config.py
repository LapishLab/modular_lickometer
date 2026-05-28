# SD card pins
SPI_SCK  = 33
SPI_MOSI = 35
SPI_MISO = 36
SD_CS    = 14

# RTC pins
I2C_SCL = 9
I2C_SDA = 8

TOUCH_PIN = 1
STOP_BUTTON_PIN = 38      # Press to stop recording and start Wi-Fi transfer

# Where do we save data
DATA_FOLDER = "/data"

# Sample period in milliseconds
SAMPLE_PERIOD_MS = 10

# Global variables
import rtc
from machine import TouchPad, Pin

clock = rtc.init_rtc(scl_pin=I2C_SCL, sda_pin=I2C_SDA)
touch = TouchPad(Pin(TOUCH_PIN))
button = Pin(STOP_BUTTON_PIN, Pin.IN, Pin.PULL_UP)


# State managment
from states import Status
current_status = Status.STARTUP