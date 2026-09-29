"""Minimal HTTP server for listing and downloading recorded CSV files."""

import asyncio
import json
import network
import os
import config
from battery import BatteryMonitor, get_BatteryMonitor_instance
from file_checksum import calculate_file_crc32
from rtc import get_PCF85263A_instance
from wifi import connect_to_wifi, disconnect_wifi
from led import Blinking_LED, get_Status_LEDS_instance
from states import Wireless as state
from states import Error
from update_manager import UpdateError, get_UpdateManager_instance

_instance_HTTPServer = None
def get_HTTPServer_instance() -> HTTPServer:
	global _instance_HTTPServer
	if _instance_HTTPServer is None:
		leds = get_Status_LEDS_instance()
		battery = get_BatteryMonitor_instance()
		_instance_HTTPServer = HTTPServer(battery=battery, led=leds.wireless, error=leds.error)
	return _instance_HTTPServer

_REASONS = {
	200: "OK",
	202: "Accepted",
	400: "Bad Request",
	413: "Payload Too Large",
	404: "Not Found",
	405: "Method Not Allowed",
	409: "Conflict",
	500: "Internal Server Error",
}


class HTTPServer:
	def __init__(
		self,
		battery: BatteryMonitor,
		led: Blinking_LED,
		error: Blinking_LED,
		port: int | None = None,
	) -> None:
		self.battery = battery
		self.port = config.HTTP_SERVER_PORT if port is None else port
		self._server = None
		self._start_task = None
		self.led = led
		self.error = error
		self.start_trigger = asyncio.ThreadSafeFlag()
		self.update_trigger = asyncio.ThreadSafeFlag()
		self.update_manager = get_UpdateManager_instance()
		self._stopping = False

	async def start(self) -> None:
		self._start_task = asyncio.create_task(self.start_worker())

	async def start_worker(self) -> bool:
		await self.led.set_blinks(state.WIFI_CONNECTING)
		network.hostname(config.DEVICE_HOSTNAME)
		ip = await connect_to_wifi(config.WIFI_SSID, config.WIFI_PASSWORD)
		if ip is None:
			await self.led.set_blinks(state.WIFI_OFF)
			await self.error.set_blinks(Error.WIFI)
			await asyncio.sleep(10)
			await self.error.set_blinks(Error.CLEAR)
			return False

		
		await self.stop_server() #Just double check a server instance isn't already running
		self._stopping = False
		self.update_manager.reset_commit()
		await self.led.set_blinks(state.HTTP_STARTING)
		self._server = await asyncio.start_server(self._handle_client, "0.0.0.0", self.port)
		await self.led.set_blinks(state.HTTP_ACTIVE)
		print(f"Ready at http://{config.DEVICE_HOSTNAME}.local:{self.port}/api/files")
		return True

	async def stop_server(self) -> None:
		if self._server is not None:
			self._server.close()
			await self._server.wait_closed()
			self._server = None
			print("HTTP server stopped")
		
	async def stop(self) -> None:
		self._stopping = True
		await self.stop_server()
		await self.update_manager.wait_for_upload()
		disconnect_wifi()
		await self.led.set_blinks(state.WIFI_OFF)	

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
			# Parse only the request metadata this server needs.
			content_length = None
			for _ in range(32):
				line = await reader.readline()
				if not line or line == b"\r\n" or line == b"\n":
					break
				header = line.decode().strip()
				key, separator, value = header.partition(":")
				if separator and key.lower() == "content-length":
					if content_length is not None:
						await self._send_json(writer, 400, {"error": "duplicate content length"})
						return
					try:
						content_length = int(value.strip())
					except ValueError:
						await self._send_json(writer, 400, {"error": "invalid content length"})
						return
					if content_length < 0:
						await self._send_json(writer, 400, {"error": "invalid content length"})
						return
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
			elif method == "POST" and path == "/api/rtc":
				await self._set_rtc(writer, reader, content_length)
			elif method == "POST" and path == "/api/experiment/start":
				await self._start_experiment(writer)
			elif method == "POST" and path == "/api/update/begin":
				await self._begin_update(writer, reader, content_length)
			elif method == "POST" and path.startswith("/api/update/files/"):
				await self._upload_update_file(
					writer,
					reader,
					path[len("/api/update/files/"):],
					content_length,
				)
			elif method == "POST" and path == "/api/update/commit":
				await self._commit_update(writer)
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
				or path == "/api/rtc"
				or path == "/api/experiment/start"
				or path == "/api/update/begin"
				or path.startswith("/api/update/files/")
				or path == "/api/update/commit"
			):
				await self._send_json(writer, 405, {"error": "method not allowed"})
			else:
				await self._send_json(writer, 404, {"error": "not found"})
		except Exception as exc:
			print(f"HTTP request failed: {exc}")
		finally:
			writer.close()
			try:
				await writer.wait_closed()
			except Exception:
				pass

	async def _begin_update(
		self,
		writer: asyncio.StreamWriter,
		reader: asyncio.StreamReader,
		content_length: int | None,
	) -> None:
		if self.update_manager.operation_active:
			await self._send_json(writer, 409, {"error": "an update operation is active"})
			return
		if content_length is None or content_length == 0:
			await self._send_json(writer, 400, {"error": "update manifest is required"})
			return
		if content_length > 8192:
			await self._send_json(writer, 413, {"error": "update manifest is too large"})
			return
		body = bytearray()
		try:
			while len(body) < content_length:
				chunk = await asyncio.wait_for(
					reader.read(content_length - len(body)), 10
				)
				if not chunk:
					await self._send_json(writer, 400, {"error": "incomplete update manifest"})
					return
				body.extend(chunk)
		except asyncio.TimeoutError:
			await self._send_json(writer, 400, {"error": "update manifest timed out"})
			return
		try:
			payload = json.loads(body.decode())
			count = self.update_manager.begin(payload)
		except (UnicodeError, ValueError, UpdateError) as exc:
			await self._send_json(writer, 400, {"error": str(exc)})
			return
		await self._send_json(writer, 200, {"accepted": True, "files": count})

	async def _upload_update_file(
		self,
		writer: asyncio.StreamWriter,
		reader: asyncio.StreamReader,
		path: str,
		content_length: int | None,
	) -> None:
		if self._stopping or self.update_manager.operation_active:
			await self._send_json(writer, 409, {"error": "device is stopping or busy"})
			return
		try:
			expected_size = self.update_manager.expected_size(path)
		except UpdateError as exc:
			await self._send_json(writer, 404, {"error": str(exc)})
			return
		if content_length is None or content_length != expected_size:
			await self._send_json(writer, 400, {"error": "content length does not match manifest"})
			return

		if not self.update_manager.start_upload():
			await self._send_json(writer, 409, {"error": "device is busy"})
			return
		temporary = None
		try:
			temporary = self.update_manager.stage_path(path)
			with open(temporary, "wb") as output:
				remaining = expected_size
				while remaining:
					if self._stopping:
						raise UpdateError("upload interrupted by device mode change")
					chunk = await asyncio.wait_for(reader.read(min(1024, remaining)), 10)
					if not chunk:
						raise UpdateError("incomplete file upload")
					output.write(chunk)
					remaining -= len(chunk)
			self.update_manager.finish_file(path)
			await self._send_json(writer, 200, {"accepted": True, "path": path})
		except (OSError, asyncio.TimeoutError, UpdateError) as exc:
			if temporary is not None:
				try:
					os.remove(temporary)
				except OSError:
					pass
			status = 409 if self._stopping else 400
			await self._send_json(writer, status, {"error": str(exc)})
		finally:
			self.update_manager.finish_upload()

	async def _commit_update(
		self,
		writer: asyncio.StreamWriter,
	) -> None:
		if self.update_manager.operation_active:
			await self._send_json(writer, 409, {"error": "an update commit is already pending"})
			return
		try:
			self.update_manager.verify_ready()
		except UpdateError as exc:
			await self._send_json(writer, 409, {"error": str(exc)})
			return
		if not self.update_manager.start_commit():
			await self._send_json(writer, 409, {"error": "an update operation is active"})
			return
		try:
			await self._send_json(writer, 202, {"accepted": True})
		except Exception:
			self.update_manager.cancel_commit()
			raise
		asyncio.create_task(self._activate_update())

	async def _activate_update(self) -> None:
		await asyncio.sleep_ms(100)
		if not self._stopping:
			self.update_trigger.set()

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

	async def _start_experiment(self, writer: asyncio.StreamWriter) -> None:
		"""Acknowledge a recording request and signal its configured start trigger."""
		await self._send_json(writer, 202, {"accepted": True})
		asyncio.create_task(self._activate_requested_experiment())

	async def _activate_requested_experiment(self) -> None:
		"""Let the HTTP response leave before stopping Wi-Fi for recording."""
		await asyncio.sleep_ms(100)
		self.start_trigger.set()

	async def _set_rtc(
		self,
		writer: asyncio.StreamWriter,
		reader: asyncio.StreamReader,
		content_length: int | None,
	) -> None:
		"""Set the external RTC from a bounded JSON calendar-time request."""
		if content_length is None or content_length == 0:
			await self._send_json(writer, 400, {"error": "JSON request body is required"})
			return
		if content_length > 1024:
			await self._send_json(writer, 413, {"error": "request body exceeds 1024-byte limit"})
			return

		body = b""
		while len(body) < content_length:
			chunk = await reader.read(content_length - len(body))
			if not chunk:
				await self._send_json(writer, 400, {"error": "incomplete request body"})
				return
			body += chunk

		try:
			payload = json.loads(body.decode())
		except (UnicodeError, ValueError):
			await self._send_json(writer, 400, {"error": "invalid JSON body"})
			return

		fields = ("year", "month", "day", "hour", "minute", "second", "weekday")
		required = fields[:-1]
		if (
			not isinstance(payload, dict)
			or any(key not in payload for key in required)
			or any(key not in fields for key in payload)
			or any(type(value) is not int for value in payload.values())
		):
			await self._send_json(writer, 400, {"error": "invalid RTC fields"})
			return
		year = payload["year"]
		month = payload["month"]
		day = payload["day"]
		if 1 <= month <= 12:
			days_in_month = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
			if month == 2 and (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)):
				max_day = 29
			else:
				max_day = days_in_month[month - 1]
			if not 1 <= day <= max_day:
				await self._send_json(writer, 400, {"error": "day is invalid for the selected month"})
				return

		try:
			rtc = get_PCF85263A_instance()
			rtc.set_time(
				payload["year"],
				payload["month"],
				payload["day"],
				payload["hour"],
				payload["minute"],
				payload["second"],
				payload.get("weekday", 0),
			)
			timestamp = rtc.get_timestamp()
		except ValueError as exc:
			await self._send_json(writer, 400, {"error": str(exc)})
			return
		except Exception as exc:
			print(f"RTC update failed: {exc}")
			await self._send_json(writer, 500, {"error": "could not set RTC time"})
			return

		await self._send_json(writer, 200, {"timestamp": timestamp})

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
			"crc32": f"{device_crc32:08x}",
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
			f"Content-Length: {size}\r\n"
			f"Content-Disposition: attachment; filename=\"{filename}\"\r\n"
			"Connection: close\r\n\r\n"
		)
		writer.write(header.encode())
		await writer.drain()

		
		buffer = bytearray(4096)
		try:
			await self.led.set_blinks(state.DATA_TRANSFER)
			while True:
				count = file.readinto(buffer)
				if not count:
					break
				writer.write(memoryview(buffer)[:count])
				await writer.drain()
		finally:
			file.close()
			await self.led.set_blinks(state.HTTP_ACTIVE)

	async def _send_json(
		self,
		writer: asyncio.StreamWriter,
		status: int,
		payload: dict,
	) -> None:
		body = json.dumps(payload).encode()
		reason = _REASONS.get(status, "")
		header = (
			f"HTTP/1.1 {status} {reason}\r\n"
			"Content-Type: application/json\r\n"
			f"Content-Length: {len(body)}\r\n"
			"Connection: close\r\n\r\n"
		)
		writer.write(header.encode())
		writer.write(body)
		await writer.drain()
