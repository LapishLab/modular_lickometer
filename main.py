
if __name__ == "__main__":
	import time
	print('Giving time for REPL interrupt')
	time.sleep(2)
	import asyncio
	import machine
	from update_manager import get_UpdateManager_instance

	update_manager = get_UpdateManager_instance()
	update_manager.recover()
	update_manager.start_trial()
	try:
		import main_control
		asyncio.run(main_control.main())
	except Exception:
		if update_manager.rollback_trial():
			machine.reset()
		raise
