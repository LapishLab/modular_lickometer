import machine
import neopixel
import time
import _thread
import config
from states import Status

class LED:
	def __init__(self, rgb_pwr_pin, rgb_data_pin, get_state):
		"""
		Initialize LED with neopixel control
		
		Args:
			rgb_pwr_pin: GPIO pin to enable power to the RGB LED
			rgb_data_pin: GPIO pin for the RGB LED data line
			get_state: Callable function that returns [color, num_flashes]
		"""
		# Enable power to the onboard RGB LED
		self.rgb_pwr = machine.Pin(rgb_pwr_pin, machine.Pin.OUT)
		self.rgb_pwr.value(1)  # Pull high to turn power on
		
		# Initialize the NeoPixel
		self.pixel = neopixel.NeoPixel(machine.Pin(rgb_data_pin), 1)
		
		# Timing constants (in milliseconds)
		self.FLASH_ON = 100
		self.FLASH_OFF = 100
		self.PAUSE_OFF = 1000
		
		self.get_state = get_state
		
		# Start watching state in a separate thread
		_thread.start_new_thread(self.watch_state, ())
	
	def watch_state(self):
		"""
		Continuously monitor state and take LED actions
		"""
		while True:
			try:
				color, num_flashes = self.get_state()
				r, g, b = color
				self.flash(times=num_flashes, r=r, g=g, b=b)
			except Exception as e:
				print(f"Error in watch_state: {e}")
				time.sleep(1)  # Try again in 1 second if there's an error
	
	def set_color(self, r, g, b):
		"""Set LED color (RGB values 0-255)"""
		self.pixel[0] = (r, g, b)
		self.pixel.write()
	
	def flash(self, times=1, r=255, g=255, b=255):
		"""
		Flash LED a specified number of times
		
		Args:
			times: Number of flashes (0 = stay on continuously)
			r, g, b: Color values
		"""
		if times == 0:
			self.set_color(r, g, b)
			time.sleep(1)  # Stay on for 1 second before checking state again
			return
		
		for _ in range(times):
			self.set_color(r, g, b)
			time.sleep(self.FLASH_ON / 1000)
			self.set_color(0, 0, 0)
			time.sleep(self.FLASH_OFF / 1000)
		time.sleep(self.PAUSE_OFF / 1000)
 