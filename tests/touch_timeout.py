from machine import Pin, TouchPad
import time
import touch_control
print(dir(touch_control))

LOOP_DELAY_MS = 100
NUM_LOOPS = 300
default = 0x3FFFFF

pads = [TouchPad(Pin(pin)) for pin in (7, 5, 6, 4)]
def print_loop():
    for i in range(NUM_LOOPS):
        print(f'{i}: {[pad.read() for pad in pads]}')
        time.sleep_ms(LOOP_DELAY_MS)



# touch_control.set_timeout(True, default)
# print(f"Touch timeout enabled: {default}")
# print_loop()


# touch_control.resume() #Resets possible timeout
# print('touch timeout cleared')
# print_loop()

touch_control.set_timeout(False, 0)
print('touch timeout disabled')
print_loop()


touch_control.set_timeout(True, default)
print(f"Touch timeout returned to {default}")


