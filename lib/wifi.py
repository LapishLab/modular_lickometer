import network
import time
import asyncio

def list_available_ssids():
	"""Scan and print all available Wi-Fi SSIDs."""
	sta = network.WLAN(network.STA_IF)
	if not sta.active():
		sta.active(True)

	print("Scanning for available networks...")
	networks = sta.scan()
	if not networks:
		print("No networks found.")
		return

	# scan() returns (ssid, bssid, channel, RSSI, authmode, hidden)
	print(f"SSID \t RSSI")
	for net in networks:
		print(f" {net[0].decode()} \t {net[3]}")
	return networks

def check_connection():
	sta = network.WLAN(network.STA_IF)
	if not sta.active():
		print("STA is not turned on")
		return
	if sta.isconnected():
		print(f"Connected to {sta.config('ssid')}")
		print(f"IP: {sta.ifconfig()[0]}")
	else:
		print(f"Not connected to WIFI")
	return

def disconnect_wifi():
	"""Disconnect and power down the station interface."""
	sta = network.WLAN(network.STA_IF)
	if sta.isconnected():
		sta.disconnect()
	sta.active(False)
	print("Wi-Fi disabled")

async def connect_to_wifi(SSID, PASSWORD, timeout_s=10):
	"""Connect to Wi-Fi without blocking other asyncio tasks."""
	sta = network.WLAN(network.STA_IF)
	if not sta.active():
		sta.active(True)

	if sta.isconnected():
		print(f"Already connected to {sta.config('ssid')}")
		print(f"Disconnecting from {sta.config('ssid')}")
		sta.disconnect()

	print(f"Connecting to {SSID}")
	sta.connect(SSID, PASSWORD)

	start = time.ticks_ms()
	while not sta.isconnected():
		if time.ticks_diff(time.ticks_ms(), start) > timeout_s * 1000:
			print("ERROR: connection timed out.")
			sta.disconnect()
			sta.active(False)
			print("STA turned off")
			return None
		await asyncio.sleep_ms(250)

	print(f"Connected to {SSID}")
	ip = sta.ifconfig()[0]
	print(f"IP: {ip}")
	return ip

