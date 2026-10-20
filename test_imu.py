#!/usr/bin/env python3
"""Checks the gyro.  sudo python3 test_imu.py   (Ctrl+C to quit)
1) Keep the car still for 2 s while it calibrates.
2) Rotate the car LEFT (anticlockwise, seen from above).
   'yaw' must go POSITIVE. If it goes negative, set YAW_SIGN = -1 in config.py.
   If 'yaw' hardly moves but another axis does, your board is mounted on its
   side: set YAW_AXIS to that axis (0=x, 1=y, 2=z)."""
import time
import config as cfg
from imu import MPU6050

imu = MPU6050(cfg.I2C_BUS, cfg.IMU_ADDRESS)
print("Calibrating, keep still...")
print("bias:", [round(b, 2) for b in imu.calibrate(cfg.GYRO_CAL_SECONDS)])
heading, last = 0.0, time.perf_counter()
try:
    while True:
        a, g = imu.read()
        now = time.perf_counter()
        yaw = g[cfg.YAW_AXIS] * cfg.YAW_SIGN
        heading += yaw * (now - last)
        last = now
        print(f"\rgyro x={g[0]:+7.1f} y={g[1]:+7.1f} z={g[2]:+7.1f} deg/s | "
              f"yaw={yaw:+7.1f}  heading={heading:+7.1f} deg | accel z={a[2]:+.2f} g ",
              end="", flush=True)
        time.sleep(0.02)
except KeyboardInterrupt:
    print()
