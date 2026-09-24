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
import asyncio
import os
import states
from states import Status
from sd import mount_data_folder
import hardware
from utilities import print_error
asyncio.run(hardware.initialize())
hardware.clock.sync_time() #Use the correct internal ESP32 clock to set the external RTC

## HTTP API

Before copying the project to a device, copy `lib/wifi_credentials.example.py`
to `lib/wifi_credentials.py` and enter the private network credentials. The
credentials file is ignored by Git and must be provisioned separately.

While the device is idle it connects to Wi-Fi and serves HTTP using the unique
`DEVICE_HOSTNAME` and `HTTP_SERVER_PORT` configured in `lib/config.py`.

Endpoints:

- `GET /api/files` - device hostname plus completed CSV files and their sizes;
  for example, `{"hostname":"lickometer-01","files":[{"name":"2026_09_22_143500.csv","size":1234}]}`
- `GET /api/files/<filename>` - download a completed CSV file
- `DELETE /api/files/<filename>` - permanently delete a completed CSV file
- `GET /api/power` - device hostname, battery voltage, and estimated charge
  percentage; for example,
  `{"hostname":"lickometer-01","voltage":3.87,"charge_percent":67.0}`

For example:

```powershell
Invoke-RestMethod http://lickometer-01.local/api/files
Invoke-WebRequest http://lickometer-01.local/api/files/2026_09_22_143500.csv -OutFile recording.csv
Invoke-RestMethod -Method Delete http://lickometer-01.local/api/files/2026_09_22_143500.csv
Invoke-RestMethod http://lickometer-01.local/api/power
```

The physical start button stops the HTTP server and powers down Wi-Fi before
recording. Wi-Fi remains off for the entire recording. The device reconnects and
restarts the file server after the physical stop button is pressed and the CSV
has been closed.
