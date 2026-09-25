# Native `touch_control` module

`touch_control` exposes ESP-IDF 5.5.2 touch-sensor functions that are not
available through MicroPython's `machine.TouchPad` API. It is compiled into the
custom firmware; copying Python files to a stock MicroPython installation will
not provide it.

Construct at least one `machine.TouchPad` before using `touch_control`. The
first `TouchPad` initializes the shared ESP-IDF touch driver.

## API

The wrappers follow ESP-IDF's legacy `touch_pad_*` functions, with Python
return values replacing C output pointers. See the
[ESP32-S3 legacy touch API reference (ESP-IDF 5.4.4)](https://docs.espressif.com/projects/esp-idf/en/v5.4.4/esp32s3/api-reference/peripherals/touch_pad.html)
for usage and parameter details.

For the exact declarations used by the build, see
[`touch_sensor_legacy.h`](https://github.com/espressif/esp-idf/blob/v5.5.2/components/driver/touch_sensor/esp32s3/include/driver/touch_sensor_legacy.h)
and
[`touch_sensor_common.h`](https://github.com/espressif/esp-idf/blob/v5.5.2/components/driver/touch_sensor/include/driver/touch_sensor_common.h).

| MicroPython | ESP-IDF |
| --- | --- |
| `set_timeout()` | `touch_pad_timeout_set()` |
| `resume()` | `touch_pad_timeout_resume()` |
| `set_charge_discharge_times()`, `get_charge_discharge_times()` | `touch_pad_set_charge_discharge_times()`, `touch_pad_get_charge_discharge_times()` |
| `set_measurement_interval()`, `get_measurement_interval()` | `touch_pad_set_measurement_interval()`, `touch_pad_get_measurement_interval()` |
| `set_count_mode()`, `get_count_mode()` | `touch_pad_set_cnt_mode()`, `touch_pad_get_cnt_mode()` |
| `set_voltage()`, `get_voltage()` | `touch_pad_set_voltage()`, `touch_pad_get_voltage()` |
| `set_idle_connection()`, `get_idle_connection()` | `touch_pad_set_idle_channel_connect()`, `touch_pad_get_idle_channel_connect()` |
| `current_channel()` | `touch_pad_get_current_meas_channel()` |
| `measurement_in_progress()` | `touch_pad_meas_is_done()` |
| `interrupt_status()`, `clear_interrupts()` | `touch_pad_read_intr_status_mask()`, `touch_pad_intr_clear()` |
| `configure_filter()`, `get_filter_config()` | `touch_pad_filter_set_config()`, `touch_pad_filter_get_config()` |
| `enable_filter()`, `disable_filter()` | `touch_pad_filter_enable()`, `touch_pad_filter_disable()` |
| `read_smooth()` | `touch_pad_filter_read_smooth()` |

Use the named constants exposed by `touch_control` for ESP-IDF enum and
interrupt values. Full Python signatures and constants are in
[`typings/touch_control/__init__.pyi`](../typings/touch_control/__init__.pyi).

`machine.TouchPad.read()` returns raw data. `touch_control.read_smooth()`
returns hardware-filtered data after the filter has been configured and
enabled. The timeout default is available as
`touch_control.TIMEOUT_THRESHOLD_DEFAULT`.

Run [`tests/touch_control_api.py`](../tests/touch_control_api.py) on the board,
outside an experiment, to check every wrapper. It validates the API and return
types, not the electrical effect of each setting.

## Building the firmware

The following steps were verified on Ubuntu running under WSL 2. I tried building on Windows 11, but hit an issue with cmd.exe’s 8,191-character command-line limit.

Pinned build configuration:

- MicroPython `v1.29.0`
- ESP-IDF `v5.5.2`
- project board configuration based on `ESP32_GENERIC_S3`
- FreeRTOS tick rate `1000 Hz`

The generic board build auto-detects Quad-SPI PSRAM (e.g ESP32-S3-WROOM-1-N8R2) and adds it to the MicroPython heap. Modules with Octal-SPI PSRAM instead require `BOARD_VARIANT=SPIRAM_OCT`.

### 1. Install build prerequisites

On Ubuntu or another Debian-derived distribution:

```sh
sudo apt update
sudo apt install -y \
    build-essential git wget flex bison gperf \
    python3 python3-venv python3-pip \
    cmake ninja-build ccache \
    libffi-dev libssl-dev dfu-util libusb-1.0-0
```

### 2. Install ESP-IDF 5.5.2 and its ESP32-S3 toolchain

```sh
mkdir -p ~/esp
cd ~/esp
git clone --branch v5.5.2 --recursive \
    https://github.com/espressif/esp-idf.git esp-idf-v5.5.2
cd ~/esp/esp-idf-v5.5.2
./install.sh esp32s3
```

`install.sh` downloads the compiler and Python environment, normally under
`~/.espressif`. Run it only once. Activate ESP-IDF in every new build shell:

```sh
source ~/esp/esp-idf-v5.5.2/export.sh
```

### 3. Clone MicroPython and this repository

We will download git repositories to `~/src`, but any directory can be used. These repositories can be deleted after building, but keeping them makes later updates and rebuilds faster.

```sh
mkdir -p ~/src
cd ~/src
git clone --branch v1.29.0 --recursive \
    https://github.com/micropython/micropython.git
git clone https://github.com/LapishLab/modular_lickometer.git
```

### 4. Build MicroPython with `touch_control`
- The LICKOMETER_BOARD path tells MicroPython where to read our custom ESP-IDF configuration (e.g. CONFIG_FREERTOS_HZ=1000).
- The LICKOMETER_CMAKE path tells MicroPython where to find and compile the touch_control native module.

```sh
source ~/esp/esp-idf-v5.5.2/export.sh

cd ~/src/micropython
make -C mpy-cross

cd ~/src/micropython/ports/esp32
make submodules

LICKOMETER_BOARD="$(realpath \ ~/src/modular_lickometer/native/boards/MODULAR_LICKOMETER)"
LICKOMETER_CMAKE="$(realpath \ ~/src/modular_lickometer/native/micropython.cmake)"
make BOARD_DIR="$LICKOMETER_BOARD" USER_C_MODULES="$LICKOMETER_CMAKE"
```

The combined image to flash is:

```text
~/src/micropython/ports/esp32/build-MODULAR_LICKOMETER/firmware.bin
```

Confirm that it exists and optionally calculate a checksum:

```sh
ls -lh ~/src/micropython/ports/esp32/build-MODULAR_LICKOMETER/firmware.bin
sha256sum ~/src/micropython/ports/esp32/build-MODULAR_LICKOMETER/firmware.bin
```

Flash this combined `firmware.bin` at address `0x0`. Building and flashing the
firmware does not copy this repository's Python application files to the ESP32
filesystem.

### Subsequent builds

Update the Linux repository, activate ESP-IDF, and repeat the final `make`:

```sh
git -C ~/src/modular_lickometer pull --ff-only
source ~/esp/esp-idf-v5.5.2/export.sh
cd ~/src/micropython/ports/esp32
LICKOMETER_CMAKE="$(realpath \
    ~/src/modular_lickometer/native/micropython.cmake)"
LICKOMETER_BOARD="$(realpath \
    ~/src/modular_lickometer/native/boards/MODULAR_LICKOMETER)"
make BOARD_DIR="$LICKOMETER_BOARD" USER_C_MODULES="$LICKOMETER_CMAKE"
```

If the CMake module structure changes or a stale configuration causes problems,
clean and rebuild:

```sh
cd ~/src/micropython/ports/esp32
LICKOMETER_BOARD="$(realpath \
    ~/src/modular_lickometer/native/boards/MODULAR_LICKOMETER)"
make BOARD_DIR="$LICKOMETER_BOARD" clean
LICKOMETER_CMAKE="$(realpath \
    ~/src/modular_lickometer/native/micropython.cmake)"
make BOARD_DIR="$LICKOMETER_BOARD" USER_C_MODULES="$LICKOMETER_CMAKE"
```
