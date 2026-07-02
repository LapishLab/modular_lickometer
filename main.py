from machine import TouchPad, Pin
import time

TOUCH_PINS = [4, 5]
pads = [TouchPad(Pin(p)) for p in TOUCH_PINS]
refresh_rate = 100 # in Hz
while(True):
	c = [p.read() for p in pads]
	print(f'{c[0]},{c[1]}')
	time.sleep(1 / refresh_rate)
