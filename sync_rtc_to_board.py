from config import I2C_SCL, I2C_SDA
from rtc import PCF85263A


try:
	rtc_device = PCF85263A(scl_pin=I2C_SCL, sda_pin=I2C_SDA)
	print(f"RTC initialized on I2C (SCL={I2C_SCL}, SDA={I2C_SDA})")
	rtc_device.sync_time()
	print(f"RTC time synced: {rtc_device.get_timestamp()}")
except Exception as error:
	print(f"RTC synchronization failed: {error}")
