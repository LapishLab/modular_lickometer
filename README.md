## Set the external RTC

From PowerShell in the project directory, set MicroPython's system clock from
the PC and then copy that time to the PCF85263A:

```powershell
mpremote connect COM24 rtc --set
mpremote connect COM24 run sync_rtc_to_board.py
```

Replace `COM24` if the board is assigned a different serial port.

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
- `DELETE /api/files/<filename>?size=<bytes>&crc32=<8-hex-digits>` - permanently
  delete a completed CSV file only when its size and CRC32 match
- `GET /api/power` - device hostname, battery voltage, and estimated charge
  percentage; for example,
  `{"hostname":"lickometer-01","voltage":3.87,"charge_percent":67.0}`

New recordings are named `YYYY_MM_DD_HHmmss.csv`. File listings can also
contain older recordings named `YYYY_MM_DD_HHmmss_cage_N.csv`; clients should
accept both forms.

For example:

```powershell
Invoke-RestMethod http://lickometer-01.local/api/files
Invoke-WebRequest http://lickometer-01.local/api/files/2026_09_22_143500.csv -OutFile recording.csv
Invoke-RestMethod -Method Delete "http://lickometer-01.local/api/files/2026_09_22_143500.csv?size=1234&crc32=89abcdef"
Invoke-RestMethod http://lickometer-01.local/api/power
```

The physical start button stops the HTTP server and powers down Wi-Fi before
recording. Wi-Fi remains off for the entire recording. The device reconnects and
restarts the file server after the physical stop button is pressed and the CSV
has been closed.
