"""Bounded-memory checksums for files stored on the device."""

import binascii


def calculate_file_crc32(path: str) -> int:
	"""Calculate and return a file's unsigned CRC32."""
	checksum = 0
	buffer = bytearray(4096)
	file = open(path, "rb")
	try:
		while True:
			count = file.readinto(buffer)
			if not count:
				break
			checksum = binascii.crc32(memoryview(buffer)[:count], checksum)
	finally:
		file.close()
	return checksum & 0xFFFFFFFF
