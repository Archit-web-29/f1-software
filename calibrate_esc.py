#!/usr/bin/env python3
"""
SimonK ESC throttle calibration (do this ONCE).
!!! LIFT THE CAR SO THE REAR WHEELS ARE IN THE AIR !!!
1) Battery for the ESC must be UNPLUGGED.
2) Run:  sudo python3 calibrate_esc.py
"""
import time
import config as cfg
from pwm import PWMChannel, find_chip

chip = find_chip(cfg.PWM_CHIP)
chans = [cfg.ESC_LEFT_CHANNEL] + ([cfg.ESC_RIGHT_CHANNEL] if cfg.DUAL_REAR_MOTORS else [])
escs = [PWMChannel(chip, c, cfg.PWM_FREQUENCY_HZ) for c in chans]
try:
    input("Wheels in the air and ESC battery UNPLUGGED? Press Enter...")
    for e in escs:
        e.set_pulse_us(cfg.ESC_MAX_US)
    input("Sending FULL throttle signal. Now PLUG IN the battery.\n"
          "Wait for the beeps from BOTH ESCs (power-up + 'max set' beeps), then press Enter...")
    for e in escs:
        e.set_pulse_us(cfg.ESC_MIN_US)
    print("Sending MINIMUM. You should hear confirmation beeps...")
    time.sleep(4)
    print("Done. Calibration saved inside the ESC. Unplug the battery.")
except KeyboardInterrupt:
    pass
finally:
    for e in escs:
        e.set_pulse_us(cfg.ESC_MIN_US)
