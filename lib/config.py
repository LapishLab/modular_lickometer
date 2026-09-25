# SD card pins (native 4-bit SDMMC/SDIO, D0 through D3)
SD_DATA_PINS = (40, 41, 36, 37)
SD_CLK = 39
SD_CMD = 38
SD_DETECT = 42  # Active low: 0 means a card is inserted

# RTC pins
I2C_SCL = 48
I2C_SDA = 47

# LED pins
LED_REC_PIN = 14
LED_TRANSFER_PIN = 13
LED_ERROR_PIN = 12
LOW_BATTERY_LED_PIN = 10

# Battery voltage monitoring pin
BATTERY_VOLTAGE_PIN = 8
USING_BATTERY_PIN = 21

# Input pins
TOUCH_L_Pins = (7, 5, 11)  # Pins for left sipper (capacitance, reference, LED)
TOUCH_R_Pins = (6, 4, 9) # Pins for right sipper (capacitance, reference, LED)

START_BUTTON_PIN = 17     # Press to start recording
STOP_BUTTON_PIN = 18      # Press to stop recording

# Where do we save data
DATA_FOLDER = "/data"

# Sample period in milliseconds
SAMPLE_PERIOD_MS: int = 10

# Wi-Fi credentials are provisioned separately and are not tracked by Git.
from wifi_credentials import WIFI_SSID, WIFI_PASSWORD

# Network identity and HTTP file server
# DEVICE_HOSTNAME must be unique for every lickometer on the network.
DEVICE_HOSTNAME = "lickometer-01"
HTTP_SERVER_PORT = 80
