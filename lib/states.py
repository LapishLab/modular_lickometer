
## Value indicates #LED blinks, with -1=ON and 0=OFF
class Experiment:
	""" Recording (Green LED) related states"""
	STARTUP = 10
	PENDING = 1
	RECORDING = -1
	NONE = 0

class Wireless:
	""" Wireless (Yellow LED) related states """
	WIFI_CONNECTING = 1
	HTTP_STARTING = 2
	HTTP_ACTIVE = -1
	DATA_TRANSFER = 10
	WIFI_OFF = 0

class Error:
	""" Error (Red LED) related states """
	GENERAL = 1
	WIFI = 2
	SD = 3
	RTC = 4
	SERVER = 5
	CLEAR = 0