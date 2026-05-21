from config import I2C_SCL, I2C_SDA
try:
    import rtc
    print(f"✓ rtc module imported successfully")
    
    try:
        rtc_device = rtc.init_rtc(scl_pin=I2C_SCL, sda_pin=I2C_SDA)
        print(f"✓ RTC initialized on I2C (SCL={I2C_SCL}, SDA={I2C_SDA})")
        
        try:
            rtc_device.sync_time()
            timestamp = rtc_device.get_timestamp()
            print(f"✓ RTC time synced: {timestamp}")
        except Exception as e:
            print(f"✗ RTC sync failed: {e}")
    except Exception as e:
        print(f"✗ RTC init failed: {e}")
        print("  → Check: RTC powered? I2C wires connected? Pull-ups on SCL/SDA?")
        
except ImportError as e:
    print(f"✗ rtc module not found: {e}")
