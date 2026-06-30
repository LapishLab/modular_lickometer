## To set the time on the board run this on PC (Windows)
1.  Navigate to project folder (cd ....)
2. %%%% RAN IN POWERSHELL %%%%%%%
3. .\.venv\Scripts\activate.ps1 #Activate environment with mpremote
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

5. hardware.intialize()
6. t = machine.RTC().datetime()
7. hardware.clock.set_time(t[0], t[1], t[2], t[4], t[5], t[6]) #Use the correct internal ESP32 clock to set the external RTC