"""
The car's brain. Pure maths, no hardware - so it can be tested on any computer
(see test_logic.py).

Conventions:
  steer:  -1 = full left, 0 = straight, +1 = full right
  motor:   0 = stopped, 1 = full power
  yaw rate (deg/s): positive = car rotating LEFT (anticlockwise seen from above)
"""
from dataclasses import dataclass


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


def deadzone(x, dz):
    if abs(x) <= dz:
        return 0.0
    s = 1.0 if x > 0 else -1.0
    return s * (abs(x) - dz) / (1.0 - dz)      # rescale so it stays proportional


def expo(x, e):
    return (1.0 - e) * x + e * x * x * x


@dataclass
class Outputs:
    steer: float = 0.0
    motor_left: float = 0.0
    motor_right: float = 0.0
    assist: float = 0.0
    braking: bool = False
    abs_release: bool = False
    speed_cmd: float = 0.0


class CarController:
    def __init__(self, cfg):
        self.c = cfg
        self.level = clamp(cfg.START_LEVEL, 0, len(cfg.RPM_LEVELS) - 1)
        self.cmd = 0.0             # current motor command (our estimate of wheel speed)
        self.heading = 0.0         # degrees turned since stick was centred
        self.release_until = 0.0
        self.full_rpm = cfg.MOTOR_KV * cfg.BATTERY_CELLS * cfg.CELL_VOLTAGE

    # ---------------- RPM limiter ----------------
    def rpm_limit(self):
        return self.c.RPM_LEVELS[self.level]

    def max_cmd(self):
        return clamp(self.rpm_limit() * self.c.RPM_CALIBRATION / self.full_rpm, 0.0, 1.0)

    def change_level(self, step):
        self.level = clamp(self.level + step, 0, len(self.c.RPM_LEVELS) - 1)

    def _vector(self, base, factor):
        """Scale one wheel. The faster wheel may reach the rpm cap, never above."""
        if base <= 0.0:
            return 0.0
        return min(base * factor, max(base, self.max_cmd()), 1.0)

    # ---------------- main update ----------------
    def update(self, steer_raw, throttle_raw, brake_raw, connected,
               yaw_rate, imu_ok, dt, now):
        c = self.c
        if connected:
            steer_in = expo(deadzone(steer_raw, c.STICK_DEADZONE), c.STEER_EXPO)
            throttle = max(0.0, deadzone(throttle_raw, c.TRIGGER_DEADZONE))
            brake = max(0.0, deadzone(brake_raw, c.TRIGGER_DEADZONE))
        else:                                   # FAILSAFE
            steer_in, throttle, brake = 0.0, 0.0, c.FAILSAFE_BRAKE

        out = Outputs()

        # ---------- BRAKING with ABS (brake wins over throttle) ----------
        if brake > 0.0:
            out.braking = True
            self.cmd = max(0.0, self.cmd - c.BRAKE_RATE * brake * dt)

            # Skid detection: rear wheels locking makes the car spin.
            # Allowed yaw grows with steering, because turning is meant to rotate the car.
            limit = c.ABS_YAW_LIMIT_DPS * (1.0 + 2.0 * abs(steer_in))
            if imu_ok and abs(yaw_rate) > limit:
                self.release_until = now + c.ABS_RELEASE_S

            def pulse(offset):
                # brake ON-time inside each cycle is proportional to L2
                phase = (now / c.ABS_PERIOD_S + offset) % 1.0
                return phase < brake * c.ABS_MAX_DUTY

            if now < self.release_until:
                apply_l = apply_r = False
                out.abs_release = True
            else:
                # With 2 motors the right wheel pulses half a cycle later, so
                # at least one rear wheel is usually rolling = more stability.
                apply_l = pulse(0.0)
                apply_r = pulse(0.5 if c.DUAL_REAR_MOTORS else 0.0)

            roll = self.cmd * c.ABS_RELEASE_MATCH if c.ESC_HAS_BRAKE else 0.0
            motor_l = 0.0 if apply_l else roll      # 0 = ESC brake (or coast)
            motor_r = 0.0 if apply_r else roll

        # ---------- ACCELERATE / SLOW COAST-DOWN ----------
        else:
            target = throttle * self.max_cmd()           # proportional + limiter
            if target > self.cmd:
                self.cmd = min(target, self.cmd + c.ACCEL_RATE * dt)
            else:
                self.cmd = max(target, self.cmd - c.COAST_RATE * dt)
            motor_l = motor_r = self.cmd

        # ---------- GYRO STRAIGHT-LINE ASSIST ----------
        if (c.ASSIST_ENABLED and imu_ok and steer_in == 0.0
                and self.cmd > c.ASSIST_MIN_SPEED):
            self.heading += yaw_rate * dt
            # turned left (positive) -> steer right (positive), and vice versa
            out.assist = clamp(c.ASSIST_KP * self.heading + c.ASSIST_KD * yaw_rate,
                               -c.ASSIST_MAX, c.ASSIST_MAX)
        else:
            self.heading = 0.0       # driver is steering: new heading is the target
        out.steer = clamp(steer_in + out.assist, -1.0, 1.0)

        # ---------- OUTER WHEEL FASTER IN TURNS (needs 2 motors) ----------
        if c.DUAL_REAR_MOTORS:
            # steer < 0 (left):  left wheel slower, right wheel faster
            # steer > 0 (right): left wheel faster, right wheel slower
            motor_l = self._vector(motor_l, 1.0 + c.TV_GAIN * out.steer)
            motor_r = self._vector(motor_r, 1.0 - c.TV_GAIN * out.steer)
        else:
            motor_l = motor_r = max(motor_l, motor_r)
        out.motor_left, out.motor_right = motor_l, motor_r

        out.speed_cmd = self.cmd
        return out
