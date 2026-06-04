class Status:
	# Normal states
	STARTUP = [[0, 0, 255], 0]
	PENDING = [[0, 255, 0], 1]
	RECORDING = [[0, 255, 0], 0]
	STOPPING_RECORDING = [[255, 255, 0], 1]
	WIFI_CONNECTED = [[255, 255, 0], 2]
	DATA_TRANSFER = [[255, 255, 0], 3]
	
	# Error states
	ERROR_SD = [[255, 0, 0], 0]
	ERROR_RTC = [[255, 0, 0], 3]
	ERROR_LED = [[255, 0, 0], 1]
	ERROR_TOUCH = [[255, 0, 0], 2]
	ERROR_BUTTON = [[255, 0, 0], 4]
	ERROR_GENERAL = [[255, 0, 0], 5]
	
current_status = Status.STARTUP