"""Minimal HTTP server for listing and downloading recorded CSV files."""

import asyncio
import json
import network
import os

import config
from battery import BatteryMonitor
from file_checksum import calculate_file_crc32
from wifi import connect_to_wifi, disconnect_wifi


_REASONS = {
	200: "OK",
	400: "Bad Request",
	404: "Not Found",
	405: "Method Not Allowed",
	409: "Conflict",
	500: "Internal Server Error",
}


class HTTPServer:
	def __init__(
		self,
		battery: BatteryMonitor,
		port: int | None = None,
	) -> None:
		self.battery = battery
		self.port = config.HTTP_SERVER_PORT if port is None else port
		self._server = None

	async def start(self) -> bool:
		network.hostname(config.DEVICE_HOSTNAME)
		ip = await connect_to_wifi(config.WIFI_SSID, config.WIFI_PASSWORD)
		if ip is None:
			return False

		self._server = await asyncio.start_server(
			self._handle_client, "0.0.0.0", self.port
		)
		print("Ready at http://{}.local:{}/api/files".format(
			config.DEVICE_HOSTNAME, self.port
		))
		return True

	async def stop(self) -> None:
		if self._server is not None:
			self._server.close()
			await self._server.wait_closed()
			self._server = None
			print("HTTP server stopped")
		disconnect_wifi()

	async def _handle_client(
		self,
		reader: asyncio.StreamReader,
		writer: asyncio.StreamWriter,
	) -> None:
		try:
			request_line = await reader.readline()
			if not request_line:
				return

			parts = request_line.decode().strip().split()
			if len(parts) != 3:
				await self._send_json(writer, 400, {"error": "invalid request"})
				return

			method, target, _ = parts
			# Headers are not currently used, but must be consumed before replying.
			for _ in range(32):
				line = await reader.readline()
				if not line or line == b"\r\n" or line == b"\n":
					break
			else:
				await self._send_json(writer, 400, {"error": "too many headers"})
				return

			target_parts = target.split("?", 1)
			path = target_parts[0]
			query = target_parts[1] if len(target_parts) == 2 else ""
			if method == "GET" and path == "/api/files":
				await self._send_json(writer, 200, {
					"hostname": config.DEVICE_HOSTNAME,
					"files": self._list_files(),
				})
			elif method == "GET" and path == "/api/power":
				await self._send_json(writer, 200, self._get_power())
			elif method == "GET" and path.startswith("/api/files/"):
				filename = path[len("/api/files/"):]
				await self._send_file(writer, filename)
			elif method == "DELETE" and path.startswith("/api/files/"):
				filename = path[len("/api/files/"):]
				await self._delete_file(writer, filename, query)
			elif (
				path == "/api/files"
				or path.startswith("/api/files/")
				or path == "/api/power"
			):
				await self._send_json(writer, 405, {"error": "method not allowed"})
			else:
				await self._send_json(writer, 404, {"error": "not found"})
		except Exception as exc:
			print("HTTP request failed: {}".format(exc))
		finally:
			writer.close()
			try:
				await writer.wait_closed()
			except Exception:
				pass

	def _list_files(self) -> list:
		files = []
		for name in os.listdir(config.DATA_FOLDER):
			if not name.endswith(".csv"):
				continue
			try:
				size = os.stat(config.DATA_FOLDER + "/" + name)[6]
			except OSError:
				continue
			files.append({"name": name, "size": size})
		files.sort(key=lambda item: item["name"])
		return files

	def _get_power(self) -> dict:
		"""Take a fresh battery reading and return its charge estimate."""
		voltage = self.battery.update()
		return {
			"hostname": config.DEVICE_HOSTNAME,
			"voltage": round(voltage, 3),
			"charge_percent": round(self.battery.charge_fraction * 100, 1),
		}

	async def _delete_file(
		self,
		writer: asyncio.StreamWriter,
		filename: str,
		query: str,
	) -> None:
		"""Delete a recording only when size and CRC32 match the requester."""
		if not filename.endswith(".csv") or "/" in filename or "\\" in filename:
			await self._send_json(writer, 404, {"error": "file not found"})
			return
		verification = self._parse_delete_verification(query)
		if verification is None:
			await self._send_json(writer, 400, {
				"error": "size and eight-digit crc32 are required",
			})
			return
		expected_size, expected_crc32 = verification

		path = config.DATA_FOLDER + "/" + filename
		try:
			device_size = os.stat(path)[6]
		except OSError:
			await self._send_json(writer, 404, {"error": "file not found"})
			return
		if device_size != expected_size:
			await self._send_json(writer, 409, {"error": "file size mismatch"})
			return

		try:
			device_crc32 = calculate_file_crc32(path)
		except OSError:
			await self._send_json(writer, 500, {"error": "could not read file"})
			return
		if device_crc32 != expected_crc32:
			await self._send_json(writer, 409, {"error": "file crc32 mismatch"})
			return

		try:
			os.remove(path)
		except OSError:
			await self._send_json(writer, 500, {"error": "could not delete file"})
			return

		await self._send_json(writer, 200, {
			"deleted": filename,
			"size": device_size,
			"crc32": "{:08x}".format(device_crc32),
		})

	def _parse_delete_verification(self, query: str) -> tuple | None:
		"""Parse the expected size and CRC32 from a DELETE query string."""
		values = {}
		for field in query.split("&"):
			key, separator, value = field.partition("=")
			if separator and key not in values:
				values[key] = value

		crc32_text = values.get("crc32", "")
		try:
			size = int(values.get("size", ""))
			crc32 = int(crc32_text, 16)
		except ValueError:
			return None
		if size < 0 or len(crc32_text) != 8 or crc32 < 0 or crc32 > 0xFFFFFFFF:
			return None
		return size, crc32

	async def _send_file(
		self,
		writer: asyncio.StreamWriter,
		filename: str,
	) -> None:
		# Recorded filenames contain no path separators. Keep the check strict so
		# the API can never expose files outside DATA_FOLDER.
		if not filename.endswith(".csv") or "/" in filename or "\\" in filename:
			await self._send_json(writer, 404, {"error": "file not found"})
			return

		path = config.DATA_FOLDER + "/" + filename
		try:
			size = os.stat(path)[6]
			file = open(path, "rb")
		except OSError:
			await self._send_json(writer, 404, {"error": "file not found"})
			return

		header = (
			"HTTP/1.1 200 OK\r\n"
			"Content-Type: text/csv\r\n"
			"Content-Length: {}\r\n"
			"Content-Disposition: attachment; filename=\"{}\"\r\n"
			"Connection: close\r\n\r\n"
		).format(size, filename)
		writer.write(header.encode())
		await writer.drain()

		buffer = bytearray(4096)
		try:
			while True:
				count = file.readinto(buffer)
				if not count:
					break
				writer.write(memoryview(buffer)[:count])
				await writer.drain()
		finally:
			file.close()

	async def _send_json(
		self,
		writer: asyncio.StreamWriter,
		status: int,
		payload: dict,
	) -> None:
		body = json.dumps(payload).encode()
		reason = _REASONS.get(status, "")
		header = (
			"HTTP/1.1 {} {}\r\n"
			"Content-Type: application/json\r\n"
			"Content-Length: {}\r\n"
			"Connection: close\r\n\r\n"
		).format(status, reason, len(body))
		writer.write(header.encode())
		writer.write(body)
		await writer.drain()
