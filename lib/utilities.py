def print_error(error_title: str, exception: Exception | None = None) -> None:
	"""Print detailed error information"""
	print(f"\n{'='*60}")
	print(f"ERROR: {error_title}")
	print(f"{'='*60}")
	if exception:
		print(f"Exception Type: {type(exception).__name__}")
		print(f"Exception: {exception}")
	print(f"{'='*60}\n")
