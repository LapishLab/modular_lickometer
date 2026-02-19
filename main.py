from machine import Pin, SPI

import sdcard
import os
from network_stuff import connect_to_hotspot, send_data_via_websocket

import socket
from machine import TouchPad
import time

# ========= USER CONFIG =========
TOUCH_PIN = 1
STOP_BUTTON_PIN = 4      # Press to stop recording and start Wi-Fi transfer

SPI_SCK  = 7
SPI_MOSI = 9
SPI_MISO = 8
SD_CS    = 2

LOG_FILENAME = "touch_log.csv"
SAMPLE_PERIOD_MS = 50
FLUSH_INTERVAL = 100

# AP_SSID = "ESP32S3_Logger"
# AP_PASSWORD = "12345678"
HOTSPOT_SSID = "TP-Link_E48C"
HOTSPOT_PASSWORD = "10859209"
WIFI_CONNECT_TIMEOUT_S = 30

# WebSocket server config
WEBSOCKET_SERVER_HOST = "192.168.0.61"  # Change to your server IP
WEBSOCKET_SERVER_PORT = 8765

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

try:
    os.mount(sd, "/sd")
except OSError:
    pass

log_path = "/sd/" + LOG_FILENAME

if LOG_FILENAME not in os.listdir("/sd"):
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


# ---------------------------------------------------------
#  MAIN
# ---------------------------------------------------------
def main():
    record_touch()
    ip = connect_to_hotspot(HOTSPOT_SSID, HOTSPOT_PASSWORD, WIFI_CONNECT_TIMEOUT_S)
    
    if ip is None:
        print("ERROR: Could not connect to WiFi")
        return
    
    print(f"Connected with IP: {ip}")
    print("Sending data to websocket server...")
    
    # Send recorded data via websocket
    success = send_data_via_websocket(
        WEBSOCKET_SERVER_HOST, 
        WEBSOCKET_SERVER_PORT, 
        log_path
    )
    
    if success:
        print("Data transmission complete!")
    else:
        print("Data transmission failed.")
    

main()