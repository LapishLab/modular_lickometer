import machine
import neopixel
import time

# 1. Enable power to the onboard RGB LED
# The TinyS2 uses GPIO 2 to switch on power to the LED
rgb_pwr = machine.Pin(2, machine.Pin.OUT)
rgb_pwr.value(1) # Pull high to turn power on

# 2. Initialize the NeoPixel on GPIO 1
# Configuration: Pin 1, 1 single pixel
pixel = neopixel.NeoPixel(machine.Pin(1), 1)

# Helper function to clear the pixel before exiting
def clear_led():
    pixel[0] = (0, 0, 0)
    pixel.write()

print("Starting TinyS2 RGB LED Loop... Press Ctrl+C to stop.")

while True:
	# Set to Red (Red, Green, Blue) - values from 0 to 255
	pixel[0] = (50, 0, 0) # Kept at 50 brightness so it isn't blinding
	pixel.write()
	time.sleep(0.5)

	# Set to Green
	pixel[0] = (0, 50, 0)
	pixel.write()
	time.sleep(0.5)

	# Set to Blue
	pixel[0] = (0, 0, 50)
	pixel.write()
	time.sleep(0.5)
        
