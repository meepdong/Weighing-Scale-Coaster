from machine import Pin
import time
from hx711 import HX711  # Ensure hx711.py is on your board

# === Pin assignments for XIAO ESP32-C6 ===
HX711_DT = 0   # Data pin from HX711 (DOUT)
HX711_SCK = 1  # Clock pin to HX711 (SCK)

# === Calibration factor ===
# Adjust this after calibration with a known weight
CALIBRATION_FACTOR = -38/24800

# === Initialize HX711 ===
hx = HX711(dout=HX711_DT, pd_sck=HX711_SCK)

print("HX711 raw + unfiltered weight test — press Ctrl+C to stop")
time.sleep(1)

# Optional: tare before starting
print("Taring...")
hx.tare()
time.sleep(0.5)
print("Tare complete.")

while True:
    raw_val = hx.get_value()
    if raw_val is not None:
        weight_grams = raw_val * CALIBRATION_FACTOR
        print("Raw: {:>10} | Weight: {:.2f} g".format(raw_val, weight_grams))
    else:
        print("No valid reading")
    time.sleep(0.2)  # ~5 readings per second