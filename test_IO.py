from machine import Pin
import time


# loop through all pins and turn on
for i in range(1, 40):
	try:
		pin = Pin(i, Pin.OUT)
		pin.value(0)
		print("Pin {}: OFF".format(i))
		time.sleep(2)
		pin.value(1)
		print("Pin {}: ON".format(i))
		time.sleep(2)
		pin.value(0)
		print("Pin {}: OFF".format(i))
	except Exception as e:
		print("Pin {}: Error - {}".format(i, e))