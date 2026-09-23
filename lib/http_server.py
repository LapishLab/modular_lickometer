"""Minimal HTTP server for listing and downloading recorded CSV files."""

import asyncio
import json
import network
import os

import config
from wifi import connect_to_wifi, disconnect_wifi


_REASONS = {
	200: "OK",
	400: "Bad Request",
	404: "Not Found",
	405: "Method Not Allowed",
}


class HTTPServer:
	def __init__(self, port: int | None = None) -> None:
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

			path = target.split("?", 1)[0]
			if method == "GET" and path == "/api/files":
				await self._send_json(writer, 200, {"files": self._list_files()})
			elif method == "GET" and path.startswith("/api/files/"):
				filename = path[len("/api/files/"):]
				await self._send_file(writer, filename)
			elif path == "/api/files":
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
