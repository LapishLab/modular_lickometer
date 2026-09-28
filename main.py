
if __name__ == "__main__":
	import time
	print('Giving time for REPL interrupt')
	time.sleep(5)
	import asyncio
	import main_control
	asyncio.run(main_control.main())
