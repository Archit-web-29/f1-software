#!/usr/bin/env python3
"""Shows live controller values.  sudo python3 test_controller.py   (Ctrl+C to quit)
Check: stick left = negative, R2/L2 go 0.00 -> 1.00, Circle/Square print +1/-1."""
import time
import config as cfg
from controller import DualSense

pad = DualSense(cfg)
print("Waiting for controller... press the PS button")
try:
    while True:
        s, t, b, ok, presses = pad.read()
        for p in presses:
            print(f"\nButton: {'Circle (+1)' if p > 0 else 'Square (-1)'}")
        print(f"\r{'CONNECTED' if ok else 'waiting  '}  steer={s:+.2f}  "
              f"R2={t:.2f}  L2={b:.2f}   ", end="", flush=True)
        time.sleep(0.05)
except KeyboardInterrupt:
    print()
