#!/usr/bin/env python3
"""Step 1 check: is hardware PWM switched on?   sudo python3 check_pwm.py"""
import subprocess
import config as cfg
from pwm import RP1_PWM0_ADDRESS, find_chip, is_fan_chip, list_chips

chips = list_chips()
if not chips:
    print("NO PWM chips found -> run setup_pwm.sh and reboot (README step 5).")
    raise SystemExit(1)
for chip, real, npwm in chips:
    tag = ("  <-- GPIO12/13/18/19 PWM (this is the one)" if RP1_PWM0_ADDRESS in real
           else "  (cooling fan - not used)" if is_fan_chip(chip) else "")
    print(f"{chip}  channels={npwm}  {real}{tag}")
try:
    chip = find_chip(cfg.PWM_CHIP)
    with open(f"{chip}/npwm") as f:
        n = int(f.read())
    need = max(cfg.ESC_LEFT_CHANNEL, cfg.SERVO_CHANNEL,
               cfg.ESC_RIGHT_CHANNEL if cfg.DUAL_REAR_MOTORS else 0) + 1
    if n < need:
        print(f"\nPROBLEM: {chip} has {n} channels but {need} are needed.")
    else:
        print(f"\nmain.py will use: {chip} ({n} channels) -> PWM OK")
except RuntimeError as e:
    print(f"\nPROBLEM: {e}")
print("\nPin modes (after main.py or a test has run, 12/13 should be a0 and 18 a3):")
subprocess.run(["pinctrl", "get", "12-13,18"])
