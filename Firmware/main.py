from machine import Pin, I2C
import ssd1306
import time
from hx711 import HX711

# =======================
# Pin Config (XIAO ESP32-C6)
# =======================
HX711_DT = 0
HX711_SCK = 1
OLED_SCL = 23
OLED_SDA = 22
BTN_TARE = 2
BTN_TIMER = 21

# =======================
# Calibration & Timing
# =======================
CALIBRATION_FACTOR = 38 / 24800
REFRESH_MS = 10
LONG_PRESS_MS = 1500

# =======================
# Reference-style Filtering
# =======================
TMA_WINDOW = 16
STEP_THRESHOLD_G = 0.8
PREFILL_CYCLES = 6
DISPLAY_HYST_G = 0.2

class TrimmedMovingAverage:
    def __init__(self, size=16):
        self.size = size
        self.buf = []
        self.prefill_cycles_remaining = 0

    def reset(self):
        self.buf = []
        self.prefill_cycles_remaining = 0

    def prefill(self, sample, cycles=6):
        self.buf = [sample] * min(self.size, max(1, len(self.buf) or self.size))
        self.prefill_cycles_remaining = max(0, cycles)

    def push(self, sample):
        if self.prefill_cycles_remaining > 0:
            self.buf = [sample] * len(self.buf)
            self.prefill_cycles_remaining -= 1
            return sample
        self.buf.append(sample)
        if len(self.buf) > self.size:
            self.buf.pop(0)
        return self.value()

    def value(self):
        n = len(self.buf)
        if n < 4:
            return sum(self.buf) / max(1, n)
        srt = sorted(self.buf)
        core = srt[1:-1]
        return sum(core) / len(core)

class StepDetector:
    def __init__(self, threshold):
        self.threshold = threshold
        self.prev_delta_exceeded = False

    def check(self, new_sample, current_avg):
        if current_avg is None:
            self.prev_delta_exceeded = False
            return False
        delta = abs(new_sample - current_avg)
        exceeded = delta > self.threshold
        is_step = exceeded and self.prev_delta_exceeded
        self.prev_delta_exceeded = exceeded
        return is_step

class DisplayHysteresis:
    def __init__(self, threshold_display_units):
        self.threshold = threshold_display_units
        self.last_display = None

    def decide(self, proposed_value):
        if self.last_display is None:
            self.last_display = proposed_value
            return proposed_value
        if abs(proposed_value - self.last_display) < self.threshold:
            return self.last_display
        self.last_display = proposed_value
        return proposed_value

# =======================
# Hardware Init
# =======================
i2c = I2C(0, scl=Pin(OLED_SCL), sda=Pin(OLED_SDA), freq=400000)
display = ssd1306.SSD1306_I2C(128, 32, i2c, addr=0x3C)
display.rotate()

hx = HX711(dout=HX711_DT, pd_sck=HX711_SCK)
btn_tare = Pin(BTN_TARE, Pin.IN, Pin.PULL_UP)
btn_timer = Pin(BTN_TIMER, Pin.IN, Pin.PULL_UP)

tma = TrimmedMovingAverage(size=TMA_WINDOW)
step = StepDetector(threshold=STEP_THRESHOLD_G)
disp = DisplayHysteresis(threshold_display_units=DISPLAY_HYST_G)

# =======================
# Eye Drawing
# =======================
def draw_dome_eye(cx, cy, rx, ry, pupil_offset):
    for dx in range(-rx, rx + 1):
        for dy in range(-ry, 1):
            if (dx*dx)/(rx*rx) + (dy*dy)/(ry*ry) <= 1:
                display.pixel(cx + dx, cy + dy, 1)
    for dx in range(-rx, rx + 1):
        display.pixel(cx + dx, cy, 1)
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            display.pixel(cx + pupil_offset + dx, cy - 1 + dy, 0)

def draw_eyes(pupil_offset):
    display.fill(0)
    draw_dome_eye(40, 8, 5, 4, pupil_offset)
    draw_dome_eye(88, 8, 5, 4, pupil_offset)
    display.show()

def draw_smile():
    display.fill(0)
    draw_dome_eye(40, 14, 5, 4, 0)
    draw_dome_eye(88, 14, 5, 4, 0)
    for x in range(54, 74):
        y = int(32 - 0.04 * (x - 64) ** 2)
        display.pixel(x, y, 1)
    display.show()

def write_text():
    display.fill(0)
    display.text("Happy brewing!", 5, 15)
    display.show()

# =======================
# Startup Animation
# =======================
print("Intitialising......")
draw_eyes(-2)
time.sleep(0.5)
draw_eyes(2)
time.sleep(0.5)
draw_smile()
time.sleep(1.0)
write_text()
time.sleep(1.0)

hx.tare()
tma.reset()
disp.last_display = None
time.sleep(0.5)
print("Taring complete. Display is live.")

# =======================
# Timer State
# =======================
timer_running = False
elapsed_ms = 0
last_tick = time.ticks_ms()
timer_btn_pressed_time = None
long_press_handled = False

# =======================
# Main Loop
# =======================
while True:
    now = time.ticks_ms()
    dt = time.ticks_diff(now, last_tick)
    last_tick = now

    if timer_running:
        elapsed_ms += dt

    if btn_tare.value() == 0:
        hx.tare()
        tma.reset()
        disp.last_display = None
        time.sleep(0.3)
        print("Tare pressed")

    if btn_timer.value() == 0:
        if timer_btn_pressed_time is None:
            timer_btn_pressed_time = now
            long_press_handled = False
        elif not long_press_handled and time.ticks_diff(now, timer_btn_pressed_time) > LONG_PRESS_MS:
            elapsed_ms = 0
            timer_running = False
            long_press_handled = True
            print("Timer reset & stopped")
            time.sleep(0.3)
    else:
        if timer_btn_pressed_time is not None:
            if not long_press_handled and time.ticks_diff(now, timer_btn_pressed_time) <= LONG_PRESS_MS:
                timer_running = not timer_running
                print("Timer", "started" if timer_running else "stopped")
            timer_btn_pressed_time = None
            long_press_handled = False

    raw_val = hx.get_value()
    if raw_val is not None:
        weight_grams = -raw_val * CALIBRATION_FACTOR
        current_avg = tma.value()

        if step.check(weight_grams, current_avg):
            tma.prefill(weight_grams, cycles=PREFILL_CYCLES)

        filtered_weight = tma.push(weight_grams)
        displayed_weight = disp.decide(filtered_weight)

        if displayed_weight < -0.2:
            weight_text = "-{:.1f}g".format(abs(displayed_weight))
        elif displayed_weight < 0.2:
            weight_text = "0.0g"
        else:
            weight_text = "{:.1f}g".format(abs(displayed_weight))

        secs = elapsed_ms // 1000
        minutes = secs // 60
        seconds = secs % 60
        time_text = "{}:{:02d}".format(minutes, seconds)

        display.fill(0)
        display.text(time_text, 0, 0)
        display.text(weight_text, 0, 16)
        display.show()

        print("Raw: {:>10} | Weight: {:.2f} g | Display Weight: {} | Timer: {}".format(raw_val, displayed_weight, weight_text, time_text), end='\r')
    else:
        print("No valid reading", end='\r')

    time.sleep_ms(REFRESH_MS)