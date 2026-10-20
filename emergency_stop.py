#!/usr/bin/env python3
"""Forces motor STOP and steering CENTRE. Used by the autostart service if
main.py ever crashes. You can also run it by hand: sudo python3 emergency_stop.py"""
import config as cfg
from pwm import PWMChannel, find_chip

chip = find_chip(cfg.PWM_CHIP)
PWMChannel(chip, cfg.ESC_LEFT_CHANNEL, cfg.PWM_FREQUENCY_HZ).set_pulse_us(cfg.ESC_MIN_US)
if cfg.DUAL_REAR_MOTORS:
    PWMChannel(chip, cfg.ESC_RIGHT_CHANNEL, cfg.PWM_FREQUENCY_HZ).set_pulse_us(cfg.ESC_MIN_US)
PWMChannel(chip, cfg.SERVO_CHANNEL, cfg.PWM_FREQUENCY_HZ).set_pulse_us(
    cfg.SERVO_CENTER_US + cfg.STEER_TRIM_US)
print("Motor stopped, steering centred.")
