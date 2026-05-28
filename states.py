class Status:
	# Normal states
	STARTUP = [[0, 0, 255], 0]
	PENDING = [[0, 255, 0], 1]
	RECORDING = [[0, 255, 0], 0]
	DATA_TRANSFER = [[255, 255, 0], 2]
	
	# Error states
	ERROR_SD = [[255, 0, 0], 0]
	ERROR_RTC = [[255, 0, 0], 3]
	
