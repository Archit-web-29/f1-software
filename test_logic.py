#!/usr/bin/env python3
"""Tests the car's brain WITHOUT any hardware (runs on a laptop too):
    python3 test_logic.py
"""
import types
import config
from control import CarController

DT = 0.01


def run(car, secs, steer=0, thr=0, brk=0, yaw=0.0, connected=True, t0=0.0, every=0.5):
    t, log = t0, []
    n = int(round(secs / DT))
    for i in range(n):
        out = car.update(steer, thr, brk, connected, yaw, True, DT, t)
        if i % int(every / DT) == 0 or i == n - 1:
            log.append((round(t, 2), out))
        t += DT
    return t, log


def show(title, log):
    print(f"\n--- {title} ---")
    for t, o in log:
        print(f"t={t:5.2f}s speed={o.speed_cmd*100:5.1f}% motorL={o.motor_left*100:5.1f}% "
              f"motorR={o.motor_right*100:5.1f}% steer={o.steer:+.3f} assist={o.assist:+.3f}"
              f"{' BRAKE' if o.braking else ''}{' ABS-RELEASE' if o.abs_release else ''}")


car = CarController(config)
print(f"Full-speed rpm at {config.BATTERY_CELLS}S: {car.full_rpm:.0f}")
for lvl in range(3):
    car.level = lvl
    print(f"  limit {car.rpm_limit()} rpm -> max motor {car.max_cmd()*100:.1f}%")
car.level = 1

t, log = run(car, 2.0, thr=1.0); show("Full R2 at 6000 rpm limit", log)
t, log = run(car, 3.0, thr=0.0, t0=t); show("R2 released -> slow coast-down", log)

car = CarController(config); car.level = 2
t, _ = run(car, 2.0, thr=1.0)
config.ESC_HAS_BRAKE = True   # pulsing is only visible with a brake-enabled ESC
t, log = run(car, 0.08, brk=0.5, t0=t, every=0.01); show("Half L2 (brake ESC): each wheel braked ~42% of the cycle, left/right offset", log)
config.ESC_HAS_BRAKE = False
t, log = run(car, 0.3, brk=1.0, yaw=120, t0=t, every=0.05); show("Rear sliding (yaw 120 deg/s) -> ABS releases", log)

car = CarController(config); car.level = 1
t, _ = run(car, 1.5, thr=0.8)
t, log = run(car, 1.0, thr=0.8, yaw=8.0, t0=t, every=0.25); show("Car drifting left 8 deg/s -> assist steers right (max 0.15)", log)

car = CarController(config); car.level = 1
t, _ = run(car, 1.0, thr=0.6)
t, log = run(car, 0.2, thr=0.6, steer=-0.7, t0=t); show("Turning LEFT -> right wheel faster", log)
t, log = run(car, 0.2, thr=0.6, steer=+0.7, t0=t); show("Turning RIGHT -> left wheel faster", log)
car = CarController(config); car.level = 1
t, _ = run(car, 1.5, thr=1.0)
t, log = run(car, 1.0, connected=False, t0=t, every=0.25); show("Controller lost -> failsafe brake", log)

# automatic checks
car = CarController(config); car.level = 0
_, log = run(car, 2, thr=1.0)
assert abs(log[-1][1].speed_cmd - car.max_cmd()) < 1e-9, "limiter failed"
_, log = run(car, 1.0, thr=0.0, t0=2)
assert log[-1][1].speed_cmd > 0.0, "coast-down too fast"
car = CarController(config); car.level = 1
_, log = run(car, 1.0, thr=0.6, steer=-0.7)
o = log[-1][1]
assert o.motor_right > o.motor_left, "left turn: right wheel must be faster"
_, log = run(car, 0.5, thr=0.6, steer=0.7, t0=1)
o = log[-1][1]
assert o.motor_left > o.motor_right, "right turn: left wheel must be faster"
_, log = run(car, 0.5, thr=1.0, steer=-1.0, t0=2)
o = log[-1][1]
assert o.motor_right <= car.max_cmd() + 1e-9, "outer wheel exceeded rpm limit"
print("\nALL CHECKS PASSED")
