"""Stage, verify, and transactionally install application Python files."""

import json
import os
import asyncio
from file_checksum import calculate_file_crc32


UPDATE_FOLDER = "/.application_update"
MAX_FILES = 32
MAX_FILE_SIZE = 256 * 1024
MAX_UPDATE_SIZE = 1024 * 1024

_instance = None
def get_UpdateManager_instance() -> UpdateManager:
	global _instance
	if _instance is None:
		_instance = UpdateManager()
	return _instance


class UpdateError(Exception):
	"""An application update is invalid or cannot be safely installed."""


class UpdateManager:
	def __init__(self, root: str = "/") -> None:
		self.root = root.rstrip("/")
		self._upload_active = False
		self._upload_done = asyncio.Event()
		self._upload_done.set()
		self._commit_pending = False

	@property
	def upload_active(self) -> bool:
		return self._upload_active

	@property
	def commit_pending(self) -> bool:
		return self._commit_pending

	@property
	def operation_active(self) -> bool:
		return self._upload_active or self._commit_pending

	def start_upload(self) -> bool:
		"""Reserve the update transaction for one incoming file."""
		if self.operation_active:
			return False
		self._upload_active = True
		self._upload_done.clear()
		return True

	def finish_upload(self) -> None:
		"""Release the upload reservation and unblock mode shutdown."""
		self._upload_active = False
		self._upload_done.set()

	async def wait_for_upload(self) -> None:
		"""Wait until any active update file has been closed."""
		await self._upload_done.wait()

	def start_commit(self) -> bool:
		"""Reserve the update transaction for its verified commit."""
		if self.operation_active:
			return False
		self._commit_pending = True
		return True

	def cancel_commit(self) -> None:
		"""Release a commit reservation when its acknowledgement fails."""
		self._commit_pending = False

	def reset_commit(self) -> None:
		"""Clear transient commit state when the HTTP server starts again."""
		self._commit_pending = False

	def begin(self, payload: object) -> int:
		"""Validate and persist a manifest, clearing any previous staging."""
		if self._exists(self._update_path("journal.json")):
			raise UpdateError("an installed update is awaiting boot confirmation")
		if not isinstance(payload, dict):
			raise UpdateError("manifest must be an object")
		files = payload.get("files")
		if not isinstance(files, list) or not files or len(files) > MAX_FILES:
			raise UpdateError("manifest must contain between 1 and 32 files")

		validated = []
		seen = []
		total_size = 0
		for entry in files:
			if not isinstance(entry, dict):
				raise UpdateError("manifest file entries must be objects")
			path = entry.get("path")
			size = entry.get("size")
			checksum = entry.get("crc32")
			if not self._is_allowed_path(path):
				raise UpdateError("manifest contains a protected or unsafe path")
			if path in seen:
				raise UpdateError("manifest contains a duplicate path")
			if type(size) is not int or size < 0 or size > MAX_FILE_SIZE:
				raise UpdateError("manifest contains an invalid file size")
			if not self._is_crc32(checksum):
				raise UpdateError("manifest contains an invalid CRC32 checksum")
			seen.append(path)
			total_size += size
			if total_size > MAX_UPDATE_SIZE:
				raise UpdateError("update exceeds the 1 MiB limit")
			validated.append({"path": path, "size": size, "crc32": checksum})

		self._remove_tree(self._update_path("staging"))
		self._remove_tree(self._update_path("backup"))
		self._remove_if_exists(self._update_path("manifest.json"))
		self._remove_if_exists(self._update_path("manifest.json.tmp"))
		self._remove_if_exists(self._update_path("journal.json.tmp"))
		self._make_dirs(self._update_path("staging"))
		self._make_dirs(self._update_path("backup"))
		self._write_json(self._update_path("manifest.json"), {"files": validated})
		return len(validated)

	def expected_size(self, path: str) -> int:
		"""Return the expected size for a path in the active manifest."""
		return self._manifest_entry(path)["size"]

	def stage_path(self, path: str) -> str:
		"""Return a temporary path for receiving one manifest file."""
		self._manifest_entry(path)
		temporary = self._update_path("staging/" + path + ".part")
		self._make_dirs(temporary.rsplit("/", 1)[0])
		self._remove_if_exists(temporary)
		return temporary

	def finish_file(self, path: str) -> None:
		"""Verify a completed temporary file and publish it into staging."""
		entry = self._manifest_entry(path)
		temporary = self._update_path("staging/" + path + ".part")
		if not self._exists(temporary):
			raise UpdateError("uploaded file is missing")
		if os.stat(temporary)[6] != entry["size"]:
			os.remove(temporary)
			raise UpdateError("uploaded file size does not match the manifest")
		if "{:08x}".format(calculate_file_crc32(temporary)) != entry["crc32"]:
			os.remove(temporary)
			raise UpdateError("uploaded file CRC32 does not match the manifest")
		staged = self._update_path("staging/" + path)
		self._remove_if_exists(staged)
		os.rename(temporary, staged)

	def verify_ready(self) -> None:
		"""Recheck every staged file before allowing the commit request."""
		for entry in self._read_manifest()["files"]:
			path = self._update_path("staging/" + entry["path"])
			if not self._exists(path) or os.stat(path)[6] != entry["size"]:
				raise UpdateError("update is incomplete")
			if "{:08x}".format(calculate_file_crc32(path)) != entry["crc32"]:
				raise UpdateError("staged file failed CRC32 verification")

	def install(self) -> None:
		"""Install a verified update, retaining backups until boot confirmation."""
		self.verify_ready()
		entries = []
		for entry in self._read_manifest()["files"]:
			entries.append({
				"path": entry["path"],
				"had_original": self._exists(self._app_path(entry["path"])),
			})
		journal = {"files": entries}
		self._write_json(self._update_path("journal.json"), journal)

		try:
			for entry in entries:
				relative_path = entry["path"]
				destination = self._app_path(relative_path)
				backup = self._update_path("backup/" + relative_path)
				staged = self._update_path("staging/" + relative_path)
				self._make_dirs(backup.rsplit("/", 1)[0])
				if entry["had_original"]:
					os.rename(destination, backup)
				os.rename(staged, destination)
			self._write_text(self._update_path("trial"), "pending")
		except Exception:
			self._rollback(journal)
			self._clear_transaction()
			raise

	def recover(self) -> None:
		"""Roll back an interrupted install or discard an interrupted upload."""
		journal_path = self._update_path("journal.json")
		if self._exists(journal_path):
			journal = self._read_json(journal_path)
			if not self._exists(self._update_path("trial")):
				self._rollback(journal)
				self._clear_transaction()
			return
		self._remove_tree(self._update_path("staging"))
		self._remove_tree(self._update_path("backup"))
		self._remove_if_exists(self._update_path("manifest.json"))
		self._remove_if_exists(self._update_path("manifest.json.tmp"))

	def start_trial(self) -> None:
		"""Allow one boot attempt before automatically restoring the backup."""
		trial = self._update_path("trial")
		if not self._exists(trial):
			return
		attempt = self._update_path("attempt")
		if self._exists(attempt):
			self._rollback(self._read_json(self._update_path("journal.json")))
			self._clear_transaction()
			return
		self._write_text(attempt, "started")

	def confirm_trial(self) -> bool:
		"""Discard rollback files after the new application starts successfully."""
		if not self._exists(self._update_path("trial")):
			return False
		self._clear_transaction()
		return True

	def rollback_trial(self) -> bool:
		"""Restore the previous application after a failed trial boot."""
		journal_path = self._update_path("journal.json")
		if not self._exists(journal_path):
			return False
		self._rollback(self._read_json(journal_path))
		self._clear_transaction()
		return True

	def _manifest_entry(self, path: str) -> dict:
		if not self._is_allowed_path(path):
			raise UpdateError("path is protected or unsafe")
		for entry in self._read_manifest()["files"]:
			if entry["path"] == path:
				return entry
		raise UpdateError("file is not listed in the update manifest")

	def _read_manifest(self) -> dict:
		return self._read_json(self._update_path("manifest.json"))

	def _rollback(self, journal: dict) -> None:
		for entry in journal["files"]:
			destination = self._app_path(entry["path"])
			backup = self._update_path("backup/" + entry["path"])
			if entry["had_original"]:
				if self._exists(backup):
					self._remove_if_exists(destination)
					os.rename(backup, destination)
			elif self._exists(destination):
				os.remove(destination)

	def _clear_transaction(self) -> None:
		self._remove_tree(self._update_path("staging"))
		self._remove_tree(self._update_path("backup"))
		for filename in ("manifest.json", "manifest.json.tmp", "journal.json", "trial", "attempt"):
			self._remove_if_exists(self._update_path(filename))

	def _app_path(self, relative_path: str) -> str:
		return (self.root or "") + "/" + relative_path

	def _update_path(self, relative_path: str) -> str:
		return (self.root or "") + UPDATE_FOLDER + "/" + relative_path

	def _is_allowed_path(self, path: object) -> bool:
		if not isinstance(path, str) or not path.endswith(".py") or "\\" in path:
			return False
		parts = path.split("/")
		if len(parts) == 2 and parts[0] == "lib":
			filename = parts[1]
		elif len(parts) == 1:
			filename = parts[0]
		else:
			return False
		if not filename or filename in (".", ".."):
			return False
		if any(character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-" for character in filename):
			return False
		return filename not in (
			"main.py",
			"boot.py",
			"update_manager.py",
			"wifi_credentials.py",
			"wifi_credentials.example.py",
			"update_credentials.py",
		)

	def _read_json(self, path: str) -> dict:
		try:
			with open(path, "r") as file:
				payload = json.loads(file.read())
		except (OSError, ValueError):
			raise UpdateError("could not read update metadata")
		if not isinstance(payload, dict):
			raise UpdateError("update metadata is invalid")
		return payload

	def _write_json(self, path: str, payload: dict) -> None:
		temporary = path + ".tmp"
		with open(temporary, "w") as file:
			file.write(json.dumps(payload))
		self._remove_if_exists(path)
		os.rename(temporary, path)

	def _write_text(self, path: str, text: str) -> None:
		with open(path, "w") as file:
			file.write(text)

	def _is_crc32(self, value: object) -> bool:
		if not isinstance(value, str) or len(value) != 8:
			return False
		for character in value:
			if character not in "0123456789abcdef":
				return False
		return True

	def _exists(self, path: str) -> bool:
		try:
			os.stat(path)
			return True
		except OSError:
			return False

	def _make_dirs(self, path: str) -> None:
		if self._exists(path):
			return
		parent = path.rsplit("/", 1)[0]
		if parent and parent != path and not self._exists(parent):
			self._make_dirs(parent)
		os.mkdir(path)

	def _remove_if_exists(self, path: str) -> None:
		if self._exists(path):
			os.remove(path)

	def _remove_tree(self, path: str) -> None:
		if not self._exists(path):
			return
		try:
			children = os.listdir(path)
		except OSError:
			os.remove(path)
			return
		for child in children:
			self._remove_tree(path + "/" + child)
		os.rmdir(path)


