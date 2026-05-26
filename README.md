## To set the time on the board run this on PC (Windows)
1.  Navigate to project folder (cd ....)
2. .\.venv\Scripts\activate.ps #Activate virtual enviornment
3. mpremote rtc --set
4. Run test_RTC.py to run rtc.sync_time() 
  	mpremote
	import config; config.clock.sync_time()