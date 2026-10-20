#!/usr/bin/env python3
"""Spins each motor gently, one at a time.  !!! REAR WHEELS IN THE AIR !!!
sudo python3 test_motor.py   (Ctrl+C stops instantly)
Check: (1) the LEFT wheel spins first, then the RIGHT one.
       (2) BOTH spin in the direction that would push the car FORWARD.
           Wrong direction? Swap ANY two of that motor's three wires."""
import time
import config as cfg
from pwm import PWMChannel, find_chip

chip = find_chip(cfg.PWM_CHIP)
escs = [("LEFT", PWMChannel(chip, cfg.ESC_LEFT_CHANNEL, cfg.PWM_FREQUENCY_HZ))]
if cfg.DUAL_REAR_MOTORS:
    escs.append(("RIGHT", PWMChannel(chip, cfg.ESC_RIGHT_CHANNEL, cfg.PWM_FREQUENCY_HZ)))
span = cfg.ESC_MAX_US - cfg.ESC_MIN_US
try:
    for _, e in escs:
        e.set_pulse_us(cfg.ESC_MIN_US)
    print("Arming 3 s...")
    time.sleep(3)
    for name, e in escs:
        print(f"--- {name} motor ---")
        for pct in range(0, 11):                 # ramp to 10 %
            e.set_pulse_us(cfg.ESC_MIN_US + span * pct / 100)
            time.sleep(0.3)
        time.sleep(2)
        e.set_pulse_us(cfg.ESC_MIN_US)
        time.sleep(1.5)
    print("Done.")
except KeyboardInterrupt:
    pass
finally:
    for _, e in escs:
        e.set_pulse_us(cfg.ESC_MIN_US)
    print("Stopped.")
