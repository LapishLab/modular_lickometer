from config import DATA_FOLDER

class DataWriter:
	"""Write sample rows to a file."""

	def __init__(self, filename: str) -> None:
		file_path = f"{DATA_FOLDER}/{filename}.csv"
		print(f"Creating data file: {file_path}")
		self.file = open(file_path, "w")

	def write(self, timestamp: int, values: list[int]) -> None:
		"""Write a timestamp and one or more values to the file."""
		row = [timestamp]
		row.extend(values)
		self.file.write(",".join(str(value) for value in row) + "\n")

	def close(self) -> None:
		"""Flush and close the file."""
		self.file.close()
