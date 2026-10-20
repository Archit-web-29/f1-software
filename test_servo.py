#!/usr/bin/env python3
"""Finds steering centre and limits.  sudo python3 test_servo.py
Type a pulse in microseconds (e.g. 1500) and press Enter. Type q to quit.
Find: the pulse where wheels point straight (SERVO_CENTER_US), and how far you
can go each way before the wheels hit anything (SERVO_RANGE_US)."""
import config as cfg
from pwm import PWMChannel, find_chip

servo = PWMChannel(find_chip(cfg.PWM_CHIP), cfg.SERVO_CHANNEL, cfg.PWM_FREQUENCY_HZ)
servo.set_pulse_us(cfg.SERVO_CENTER_US)
print(f"Servo at {cfg.SERVO_CENTER_US} us. Change in small steps (10-20 us)!")
while True:
    txt = input("pulse us (900-2100, q=quit): ").strip().lower()
    if txt == "q":
        break
    try:
        us = int(txt)
    except ValueError:
        continue
    if 900 <= us <= 2100:
        servo.set_pulse_us(us)
    else:
        print("out of safe range")
servo.set_pulse_us(cfg.SERVO_CENTER_US)
