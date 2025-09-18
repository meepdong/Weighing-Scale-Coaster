# Weighing Scale Coaster
A precision coffee scale built around the HX711 load cell amplifier, optimized for responsiveness and stability. Designed for baristas, tinkerers, and embedded engineers who care about both performance and personality.
![Weighing Scale Coaster](renderv1.jpg)
## Features
• 	HX711-based load cell interface with high-resolution weight readings
• 	Reference-inspired filtering pipeline adapted from Analog Devices' weigh scale design
• 	OLED display with expressive dome-shaped eyes and smile animation
• 	Timer with short press toggle and long press reset
• 	Flicker-free weight display using hysteresis and trimmed averaging
• 	Designed for both Raspberry Pi Pico W and Seeed Studio XIAO ESP32-C6

## Hardware Overview
### Components
• 	HX711 Load Cell Amplifier
• 	5 kg Load Cell
• 	SSD1306 OLED Display (128×32)
• 	Two momentary push buttons (Tare + Timer)
• 	Microcontroller: Raspberry Pi Pico W or Seeed Studio XIAO ESP32-C6

## Wiring Table

| Signal        | Pin on HX711 | Pin on Pico W | Pin on XIAO ESP32-C6 |
|---------------|--------------|----------------|----------------------|
| VCC           | VCC          | 3.3V           | 3.3V                 |
| GND           | GND          | GND            | GND                  |    
| Data (DT)     | DT           | GPIO 16        | GPIO 10              |
| Clock (SCK)   | SCK          | GPIO 17        | GPIO 11              |
| OLED SDA      | SDA          | GPIO 4         | GPIO 4               |    
| OLED SCL      | SCL          | GPIO 5         | GPIO 5               |
| Tare Button   | -            | GPIO 18        | GPIO 6               |
| Timer Button  | -            | GPIO 19        | GPIO 7               |

## Load Cell Algorithm
This project adapts the signal processing architecture from Analog Devices' weigh scale reference design to the HX711.
Filtering Pipeline
• 	Trimmed Moving Average: Removes min/max outliers from a rolling window to suppress noise while preserving step response.
• 	Step Detection: Detects real weight changes using dual-threshold logic and pre-fills the filter buffer to skip lag.
• 	Display Hysteresis: Prevents flicker by suppressing small changes below a threshold.
Why It Works
• 	HX711 is a 24-bit sigma-delta ADC with built-in gain and ratiometric measurement.
• 	Filtering compensates for its limited noise-free resolution and slow sample rate.
• 	The result: smooth, stable, and responsive weight readings even with low-cost hardware.

## User Interaction

OLED shows timer and weight. Startup animation includes blinking eyes and a smile. A Hall effect sensor to be integrated for a lid-activated deep sleep and wake mode.

Future Improvements
• 	Calibration helper script for computing 
• 	BLE or Wi-Fi integration for remote brew tracking
• 	Capacitive touch or rotary encoder input

Credits
Built by Maurice D'Moss, mechanical product design engineer with a passion for coffee and embedded systems.
Filtering architecture inspired by Analog Devices' weigh scale reference design.
