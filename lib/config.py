# SD card pins
SPI_SCK  = 12
SPI_MOSI = 11
SPI_MISO = 13
SD_CS    = 10

# RTC pins
I2C_SCL = 9
I2C_SDA = 8

# LED pins
LED_REC_PIN = 15
LED_TRANSFER_PIN = 14
LED_ERROR_PIN = 16

# Input pins
TOUCH_PINS = [1, 4]  # List of touch pins
STOP_BUTTON_PIN = 21      # Press to stop recording and start Wi-Fi transfer

# Where do we save data
DATA_FOLDER = "/data"

# Sample period in milliseconds
SAMPLE_PERIOD_MS = 10

# Wi-Fi credentials are provisioned separately and are not tracked by Git.
from wifi_credentials import WIFI_SSID, WIFI_PASSWORD

# Network identity and HTTP file server
# DEVICE_HOSTNAME must be unique for every lickometer on the network.
DEVICE_HOSTNAME = "lickometer-01"
HTTP_SERVER_PORT = 80

TCP_SERVER_HOST = "10.247.178.229"
TCP_SERVER_PORT = 5000
