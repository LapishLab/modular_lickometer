# Global variables
from machine import Pin
from config import SYNC_PIN

# Initialize hardware with error handling
sync_out = None

async def initialize():
	global touch, touch2, button, sync_out
	sync_out = Pin(SYNC_PIN, Pin.OUT, value=0)
	