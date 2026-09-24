import config
import math
from machine import TouchPad, Pin, PWM
import time

class SipperArray:
    def __init__(self) -> None:
        l = config.TOUCH_L_Pins
        r = config.TOUCH_R_Pins
        self.left = Sipper(cap_pin=l[0], ref_pin=l[1], led_pin=l[2])
        self.right = Sipper(cap_pin=r[0], ref_pin=r[1], led_pin=r[2])


BRIGHTNESS_MAX = 255
class Sipper:
    def __init__(self, cap_pin:int, ref_pin:int, led_pin:int) -> None:
        self.cap = TouchPad(Pin(cap_pin))
        self.ref = TouchPad(Pin(ref_pin))
        self.led = PWM(Pin(led_pin))
        self.led.freq(1000)
        self.led.duty_u16(0)
        (self.led_min_diff, self.led_diff_span) = self.calc_LED_mapping()

    def read(self, update_led: bool = True) -> int:
        cap_val: int = self.cap.read()
        ref_val: int = self.ref.read()
        diff = cap_val - ref_val
        if update_led:
            self.update_LED(diff)
        return diff

    def update_LED(self, diff: int) -> None:
        relative_diff: int = diff - self.led_min_diff
        if relative_diff <= 0:
            brightness: int = 0
        elif relative_diff >= self.led_diff_span:
            brightness = BRIGHTNESS_MAX
        else:
            brightness = relative_diff * BRIGHTNESS_MAX // self.led_diff_span

        squared_brightness = brightness * brightness
        self.led.duty_u16(squared_brightness)


    def calc_LED_mapping(self, avg: float = 0.2, std: float = 0.1) -> tuple[int, int]:
        """Return the minimum difference and span for gamma-2 brightness.

        ``avg`` is the perceived brightness assigned to the measured average
        difference. ``std`` is the perceived-brightness increase assigned to
        one measured standard deviation above the average.
        """
        if not 0.0 <= avg <= 1.0:
            raise ValueError("avg must be between zero and one")
        if std <= 0.0:
            raise ValueError("std must be positive")

        diff_avg, diff_std = self.calc_diff_distribution()
        led_min_diff: int = round(diff_avg - (avg / std) * diff_std)
        led_max_diff: int = round(diff_avg + ((1.0 - avg) / std) * diff_std)
        led_diff_span: int = led_max_diff - led_min_diff
        if led_diff_span <= 0:
            led_diff_span = 1
        return (led_min_diff, led_diff_span)


    def calc_diff_distribution(self, n: int = 500, pause_ms: int = 1) -> tuple[float, float]:
        if n <= 0:
            raise ValueError("n must be greater than zero")
        avg: float = 0.0
        squared_diff_sum: float = 0.0
        for sample_number in range(1, n + 1):
            diff: int = self.read(update_led=False)
            delta: float = diff - avg
            avg += delta / sample_number
            squared_diff_sum += delta * (diff - avg)
            time.sleep_ms(pause_ms)
        std: float = math.sqrt(squared_diff_sum / n)
        return (avg, std)
        


