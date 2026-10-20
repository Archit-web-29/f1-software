"""
DualSense Edge reader. Runs in a background thread, reconnects automatically.
Uses the Linux 'evdev' input system (the controller appears as /dev/input/eventX).
"""
import glob
import threading
import time
from evdev import InputDevice, ecodes, list_devices


class DualSense:
    def __init__(self, cfg):
        self.cfg = cfg
        self.code_steer = ecodes.ecodes[cfg.AXIS_STEER]
        self.code_brake = ecodes.ecodes[cfg.AXIS_BRAKE]
        self.code_throttle = ecodes.ecodes[cfg.AXIS_THROTTLE]
        self.code_up = ecodes.ecodes[cfg.BUTTON_SPEED_UP]
        self.code_down = ecodes.ecodes[cfg.BUTTON_SPEED_DOWN]
        self._lock = threading.Lock()
        self._presses = []
        self.connected = False
        self.name = ""
        self.steer = self.throttle = self.brake = 0.0
        self._ranges = {}
        threading.Thread(target=self._run, daemon=True).start()

    # ---------- device search ----------
    def _find(self):
        for path in list_devices():
            try:
                dev = InputDevice(path)
            except OSError:
                continue
            n = dev.name.lower()
            if (self.cfg.CONTROLLER_NAME_MATCH.lower() in n
                    and "motion" not in n and "touchpad" not in n):
                abs_codes = [c for c, _ in dev.capabilities().get(ecodes.EV_ABS, [])]
                if self.code_steer in abs_codes:
                    return dev
            dev.close()
        return None

    # ---------- value scaling ----------
    def _norm(self, code, value):
        lo, hi = self._ranges[code]
        if code == self.code_steer:                  # stick: -1 .. +1
            mid, half = (lo + hi) / 2.0, (hi - lo) / 2.0
            return max(-1.0, min(1.0, (value - mid) / half))
        return max(0.0, min(1.0, (value - lo) / float(hi - lo)))  # trigger: 0..1

    def _apply(self, code, value):
        v = self._norm(code, value)
        with self._lock:
            if code == self.code_steer:
                self.steer = v
            elif code == self.code_throttle:
                self.throttle = v
            elif code == self.code_brake:
                self.brake = v

    # ---------- background thread ----------
    def _run(self):
        while True:
            dev = self._find()
            if dev is None:
                time.sleep(1.0)
                continue
            try:
                for code in (self.code_steer, self.code_brake, self.code_throttle):
                    info = dev.absinfo(code)
                    self._ranges[code] = (info.min, info.max)
                    self._apply(code, info.value)
                self.name = dev.name
                self.connected = True
                print(f"[PAD] Connected: {dev.name}")
                for ev in dev.read_loop():
                    if ev.type == ecodes.EV_ABS and ev.code in self._ranges:
                        self._apply(ev.code, ev.value)
                    elif ev.type == ecodes.EV_KEY and ev.value == 1:   # pressed
                        with self._lock:
                            if ev.code == self.code_up:
                                self._presses.append(+1)
                            elif ev.code == self.code_down:
                                self._presses.append(-1)
            except OSError:
                pass
            finally:
                self.connected = False
                with self._lock:
                    self.steer = self.throttle = self.brake = 0.0
                try:
                    dev.close()
                except Exception:
                    pass
                print("[PAD] Controller disconnected - failsafe braking")
            time.sleep(0.5)

    # ---------- used by main.py ----------
    def read(self):
        with self._lock:
            presses, self._presses = self._presses, []
            return self.steer, self.throttle, self.brake, self.connected, presses

    def set_lightbar(self, r, g, b):
        """Best effort: colour the light bar. Silently ignored if not possible."""
        for led in glob.glob("/sys/class/leds/*:rgb:indicator"):
            try:
                with open(f"{led}/multi_intensity", "w") as f:
                    f.write(f"{r} {g} {b}")
                with open(f"{led}/brightness", "w") as f:
                    f.write("255")
            except OSError:
                pass
