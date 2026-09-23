# Repository instructions

## Purpose and related repository

This repository contains the MicroPython firmware for the ESP32-S3 modular
lickometer. The sibling `../modular_lick_PC` repository contains the Python
application that discovers and communicates with these devices.

Changes may span both repositories. Treat the HTTP interface between them as a
shared contract, and inspect both implementations before changing that contract.

## Repository layout

- `main.py` is the device entry point.
- `experiment.py` defines experiment behavior.
- `lib/` contains hardware drivers, state handling, networking, persistence, and
  the HTTP server.
- `lib/config.py` contains hardware pins and device-level configuration.
- `tests/` contains scripts intended for diagnostics on actual hardware; these
  are not a host-side pytest suite.
- `requirements-stubs.txt` contains editor/type-checking stubs, not packages to
  install on the ESP32.

## Firmware constraints

- Target MicroPython on ESP32-S3, not desktop CPython. Use APIs and language
  features supported the MicroPython version listed in requirements-stubs.txt.
- Keep memory use bounded. Avoid reading complete recordings or large request
  bodies into memory when streaming is practical.
- Do not add desktop-only dependencies to firmware code.
- Preserve the existing asynchronous design for networking and device state.
- Hardware pin assignments and recording timing are behavioral requirements;
  do not change them incidentally.
- Never commit Wi-Fi credentials. `lib/wifi_credentials.py` is provisioned
  locally from `lib/wifi_credentials.example.py` and must remain untracked.

## PC/firmware coordination

- The HTTP API is implemented in `lib/http_server.py` and summarized in
  `README.md`.
- If an endpoint, status code, JSON field, filename rule, port, hostname rule,
  or availability behavior changes, update the PC client and relevant
  documentation in the same task.
- The HTTP server is intentionally unavailable while the device is recording;
  PC-side code must treat that as an expected device state rather than immediate
  evidence of failure.
- Keep protocol parsing and transport details explicit enough to test on the PC
  without attached hardware.

## Validation

- For firmware-only logic, run the most focused checks that can execute without
  hardware and report any MicroPython-only behavior that could not be exercised.
- Treat scripts under `tests/` as manual hardware diagnostics. Do not claim they
  passed unless they were run successfully on the target board.
- Ask before flashing firmware, resetting a board, changing provisioned device
  configuration, or running a diagnostic that can affect connected hardware or
  stored recordings.
- When a change crosses the HTTP boundary, validate both the firmware response
  shape and the PC client's handling of success, unavailable devices, timeouts,
  malformed responses, and interrupted downloads as applicable.
- Utilize type hinting for all function arguments and outputs and check against these types.

## Definition of done

- The requested behavior is implemented in every affected repository.
- Shared HTTP behavior and documentation agree.
- Relevant checks have been run, with hardware-dependent gaps stated clearly.
- Secrets, generated recordings, virtual environments, and device-specific
  credentials are not committed.
