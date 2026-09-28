"""Battery voltage monitoring and charge indication."""

import asyncio
from machine import ADC, PWM, Pin
from config import BATTERY_VOLTAGE_PIN, LOW_BATTERY_LED_PIN

_instance_BatteryMonitor = None
def get_BatteryMonitor_instance() -> BatteryMonitor:
	global _instance_BatteryMonitor
	if _instance_BatteryMonitor is None:
		_instance_BatteryMonitor = BatteryMonitor()
	return _instance_BatteryMonitor

class BatteryMonitor:
	"""Periodically display the measured battery charge on a PWM LED.

	``divider_ratio`` is the ratio between the battery voltage and the voltage
	at the ADC pin. For example, two equal-value divider resistors use a ratio
	of 2.0. Voltage is mapped linearly from ``empty_voltage`` (LED off) to
	``full_voltage`` (LED at full brightness).
	"""

	PWM_MAX = 65535

	def __init__(
		self,
		analog_pin: int = BATTERY_VOLTAGE_PIN,
		led_pin: int = LOW_BATTERY_LED_PIN,
		*,
		empty_voltage: float = 3.3,
		full_voltage: float = 3.9,
		divider_ratio: float = 2.0,
		check_interval_ms: int = 10000,
	) -> None:
		if full_voltage <= empty_voltage:
			raise ValueError("full_voltage must be greater than empty_voltage")
		if divider_ratio <= 0:
			raise ValueError("divider_ratio must be greater than zero")
		if check_interval_ms <= 0:
			raise ValueError("check_interval_ms must be greater than zero")

		self.adc = ADC(Pin(analog_pin))
		self.led = PWM(Pin(led_pin))
		self.led.freq(1000)
		self.led.duty_u16(0)

		self.empty_voltage = empty_voltage
		self.range_voltage = full_voltage - empty_voltage
		self.divider_ratio = divider_ratio
		self.check_interval_ms = check_interval_ms

		self.voltage = None
		self.charge_fraction = 0.0
		self.task = asyncio.create_task(self.monitor_loop())

	def update(self) -> float:
		"""Measure the battery and immediately update the LED intensity."""
		self.voltage = self.divider_ratio * self.adc.read_uv() / 1e6
		v_span = (self.voltage - self.empty_voltage) / self.range_voltage
		self.charge_fraction = min(1.0, max(0.0, v_span))
		led_intensity = 1-self.charge_fraction
		self.led.duty_u16(int(led_intensity * self.PWM_MAX))
		return self.voltage

	async def monitor_loop(self) -> None:
		"""Continuously refresh the voltage and charge LED."""
		while True:
			self.update()
			await asyncio.sleep_ms(self.check_interval_ms)

	def deinit(self) -> None:
		"""Stop monitoring and release the PWM output."""
		self.task.cancel()
		self.led.duty_u16(0)
		self.led.deinit()

