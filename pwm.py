"""
Hardware PWM for the Raspberry Pi 5 using the Linux sysfs interface.
(pigpio and RPi.GPIO do NOT work on the Pi 5, so we talk to the kernel directly.)
Needs the 4-channel overlay installed by setup_pwm.sh (then reboot).
"""
import glob
import os
import shutil
import subprocess
import time

PWM_ROOT = "/sys/class/pwm"
RP1_PWM0_ADDRESS = "1f00098000"   # the Pi 5 PWM block that drives GPIO12/13/18/19

# Pi 5: which GPIO pin each channel comes out on, and the pin mode needed
CHANNEL_PINS = {0: (12, "a0"), 1: (13, "a0"), 2: (18, "a3"), 3: (19, "a3")}


def _write(path, value):
    fd = os.open(path, os.O_WRONLY)
    try:
        os.write(fd, f"{value}\n".encode())
    finally:
        os.close(fd)


def is_fan_chip(chip):
    return os.path.isdir(f"{chip}/device/consumer:platform:cooling_fan")


def list_chips():
    out = []
    for chip in sorted(glob.glob(f"{PWM_ROOT}/pwmchip*")):
        try:
            with open(f"{chip}/npwm") as f:
                npwm = int(f.read().strip())
        except OSError:
            npwm = -1
        out.append((chip, os.path.realpath(chip), npwm))
    return out


def find_chip(preferred=None):
    if preferred is not None:
        path = f"{PWM_ROOT}/pwmchip{preferred}"
        if not os.path.isdir(path):
            raise RuntimeError(f"{path} does not exist. Run check_pwm.py.")
        return path
    chips = list_chips()
    if not chips:
        raise RuntimeError(
            "No PWM chips found. Add the dtoverlay line to "
            "/boot/firmware/config.txt and reboot (README step 5).")
    for chip, real, _ in chips:
        if RP1_PWM0_ADDRESS in real:
            return chip
    usable = [c for c in chips if not is_fan_chip(c[0])]
    if len(usable) == 1:
        return usable[0][0]
    raise RuntimeError(
        "Several PWM chips found and none is clearly the right one. "
        "Run: sudo python3 check_pwm.py  and set PWM_CHIP in config.py")


class PWMChannel:
    """One RC output (ESC or servo). Pulse width is set in microseconds."""

    def __init__(self, chip_path, channel, freq_hz=50):
        self.channel = channel
        self.base = f"{chip_path}/pwm{channel}"
        if not os.path.isdir(self.base):
            _write(f"{chip_path}/export", channel)
        for _ in range(100):                      # wait for the kernel
            if os.path.exists(f"{self.base}/period"):
                break
            time.sleep(0.02)
        else:
            raise RuntimeError(f"Could not export PWM channel {channel}")
        time.sleep(0.05)
        self.period_ns = int(1_000_000_000 / freq_hz)
        try:
            _write(f"{self.base}/enable", 0)
        except OSError:
            pass
        _write(f"{self.base}/duty_cycle", 0)      # duty must never exceed period
        _write(f"{self.base}/period", self.period_ns)
        self.enabled = False
        self._route_pin()

    def _route_pin(self):
        """Safety net: make sure the GPIO pin is switched to PWM mode."""
        if channel_pin := CHANNEL_PINS.get(self.channel):
            if shutil.which("pinctrl"):
                pin, mode = channel_pin
                subprocess.run(["pinctrl", "set", str(pin), mode],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def set_pulse_us(self, us):
        ns = int(max(0.0, min(us * 1000.0, self.period_ns)))
        _write(f"{self.base}/duty_cycle", ns)
        if not self.enabled:
            _write(f"{self.base}/enable", 1)
            self.enabled = True

    def disable(self):
        try:
            _write(f"{self.base}/enable", 0)
        except OSError:
            pass
        self.enabled = False
