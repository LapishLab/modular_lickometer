To set the time on the board run this on PC (Windows)
Navigate to project folder (cd ....)
%%%% RAN IN POWERSHELL %%%%%%%
.\.venv\Scripts\activate.ps1 #Activate environment with mpremote
mpremote rtc --set # Set ESP built in time from PC
mpremote #Opened REPL
%%% RAN ON MPREMOTE
4. # Not sure why we need all these imports, but hardware.initialize failed otherwise
import config
import time
import _thread
import os
import states
from states import Status
from sd import mount_data_folder
import hardware
from utilities import print_error
hardware.initialize()
hardware.clock.sync_time() #Use the correct internal ESP32 clock to set the external RTC