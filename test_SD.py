from config import SPI_SCK, SPI_MOSI, SPI_MISO, SD_CS

try:
	from machine import Pin, SoftSPI
	import sdcard
	import os
	
	print(f"✓ Modules imported (sdcard, os)")
	
	try:
		print(f"  Creating SPI instance (SCK={SPI_SCK}, MOSI={SPI_MOSI}, MISO={SPI_MISO})...")
		spi = SoftSPI(
			baudrate=100000,
			sck=Pin(SPI_SCK),
			mosi=Pin(SPI_MOSI),
			miso=Pin(SPI_MISO)
		)
		print(f"✓ SPI instance created")
		
		try:
			print(f"  Initializing SD card (CS={SD_CS})...")
			sd = sdcard.SDCard(spi, Pin(SD_CS))
			print(f"✓ SD card initialized!")
			
			try:
				os.mount(sd, "/data")
				print(f"✓ SD card mounted to /data")
				
				files = os.listdir("/data")
				print(f"✓ Files on SD card: {files}")
			except OSError as e:
				print(f"⚠ Mount failed: {e}")
				print(f"  (SD might already be mounted, or mount point issue)")
		except Exception as e:
			print(f"✗ SD card init failed: {e}")
			print(f"  → Check: SD card inserted? Wires connected to right pins?")
			print(f"  → Try: Reseat SD card, check if it's corrupted, try lower baudrate")
			
	except Exception as e:
		print(f"✗ SPI setup failed: {e}")
		print(f"  → Check: Pin numbers correct? SPI interface available?")
		
except ImportError as e:
	print(f"✗ Import failed: {e}")

print("\n" + "=" * 50)
print("DIAGNOSTICS COMPLETE")
print("=" * 50)
