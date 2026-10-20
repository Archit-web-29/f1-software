#!/usr/bin/env python3
"""
F1 MODEL CAR - MAIN PROGRAM
Run with:   sudo python3 main.py
Options:    sudo python3 main.py --no-imu    (drive without the gyro)
Stop with:  Ctrl + C   (motor stops, steering centres)
"""
import signal
import sys
import time

import config as cfg
from control import CarController
from controller import DualSense
from pwm import PWMChannel, find_chip

LEVEL_COLOURS = [(0, 255, 0), (255, 140, 0), (255, 0, 0)]  # green, orange, red


def motor_to_us(m):
    if m < cfg.ESC_START_DEADBAND:
        return cfg.ESC_MIN_US
    return cfg.ESC_MIN_US + min(m, 1.0) * (cfg.ESC_MAX_US - cfg.ESC_MIN_US)


def steer_to_us(s):
    sign = -1.0 if cfg.SERVO_REVERSED else 1.0
    return cfg.SERVO_CENTER_US + cfg.STEER_TRIM_US + sign * s * cfg.SERVO_RANGE_US


def _sigterm(*_):
    raise SystemExit(0)


def main():
    use_imu = "--no-imu" not in sys.argv
    signal.signal(signal.SIGTERM, _sigterm)

    print("=== F1 car starting ===")
    chip = find_chip(cfg.PWM_CHIP)
    print(f"[PWM] using {chip}")
    esc = PWMChannel(chip, cfg.ESC_LEFT_CHANNEL, cfg.PWM_FREQUENCY_HZ)
    esc_r = (PWMChannel(chip, cfg.ESC_RIGHT_CHANNEL, cfg.PWM_FREQUENCY_HZ)
             if cfg.DUAL_REAR_MOTORS else None)
    servo = PWMChannel(chip, cfg.SERVO_CHANNEL, cfg.PWM_FREQUENCY_HZ)

    try:
        # ---- arm ESC + centre steering ----
        esc.set_pulse_us(cfg.ESC_MIN_US)
        if esc_r:
            esc_r.set_pulse_us(cfg.ESC_MIN_US)
        servo.set_pulse_us(steer_to_us(0.0))
        print(f"[ESC] arming for {cfg.ESC_ARM_SECONDS}s (listen for the beeps)...")
        arm_end = time.time() + cfg.ESC_ARM_SECONDS

        # ---- gyro ----
        imu = None
        if use_imu:
            try:
                from imu import MPU6050
                imu = MPU6050(cfg.I2C_BUS, cfg.IMU_ADDRESS)
                print("[IMU] calibrating - DO NOT touch the car...")
                imu.calibrate(cfg.GYRO_CAL_SECONDS)
                print("[IMU] ready")
            except Exception as e:
                print(f"[IMU] not available ({e}). Driving without assist/ABS skid check.")
                imu = None
        while time.time() < arm_end:
            time.sleep(0.05)

        pad = DualSense(cfg)
        car = CarController(cfg)
        print("[PAD] waiting for controller (press the PS button)...")
        print("R2 = go, L2 = brake, left stick = steer, Circle/Square = rpm limit")

        period = 1.0 / cfg.LOOP_HZ
        last = next_t = time.perf_counter()
        last_print = 0.0
        last_level = -1
        imu_errors = 0

        while True:
            now = time.perf_counter()
            dt = min(now - last, 0.05)
            last = now

            steer, throttle, brake, connected, presses = pad.read()
            for p in presses:
                car.change_level(p)
            if car.level != last_level and connected:
                last_level = car.level
                pad.set_lightbar(*LEVEL_COLOURS[car.level % len(LEVEL_COLOURS)])
                print(f"[LIMIT] {car.rpm_limit()} rpm")

            yaw, imu_ok = 0.0, False
            if imu is not None:
                try:
                    _, gyro = imu.read()
                    yaw = gyro[cfg.YAW_AXIS] * cfg.YAW_SIGN
                    imu_ok = True
                    imu_errors = 0
                except OSError:
                    imu_errors += 1
                    if imu_errors == 10:
                        print("[IMU] read errors - check the 4 gyro wires")

            out = car.update(steer, throttle, brake, connected, yaw, imu_ok, dt, now)

            servo.set_pulse_us(steer_to_us(out.steer))
            if esc_r:
                esc.set_pulse_us(motor_to_us(out.motor_left))
                esc_r.set_pulse_us(motor_to_us(out.motor_right * cfg.RIGHT_MOTOR_TRIM))
            else:
                esc.set_pulse_us(motor_to_us(out.motor_left))

            if now - last_print > 1.0 / cfg.STATUS_PRINT_HZ:
                last_print = now
                state = ("ABS-RELEASE" if out.abs_release else
                         "BRAKE" if out.braking else "DRIVE")
                print(f"{'PAD' if connected else 'NO-PAD'} {state:11s} "
                      f"limit={car.rpm_limit()} speed={out.speed_cmd*100:5.1f}% "
                      f"L={out.motor_left*100:5.1f}% R={out.motor_right*100:5.1f}% "
                      f"steer={out.steer:+.2f} assist={out.assist:+.3f} yaw={yaw:+6.1f}")

            next_t += period
            sleep = next_t - time.perf_counter()
            if sleep > 0:
                time.sleep(sleep)
            else:
                next_t = time.perf_counter()

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        esc.set_pulse_us(cfg.ESC_MIN_US)
        if esc_r:
            esc_r.set_pulse_us(cfg.ESC_MIN_US)
        servo.set_pulse_us(steer_to_us(0.0))
        time.sleep(0.3)
        print("Motor stopped, steering centred. Bye!")


if __name__ == "__main__":
    main()
