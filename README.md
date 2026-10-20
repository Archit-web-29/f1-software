# F1 Model Car: Raspberry Pi 5 Software Guide

Follow these steps **in order**. Do not skip the tests in Step 9. Each test checks one part, so if something is wrong you know exactly which part.

---

## 0. Read this first: what your hardware can and cannot do

| Feature | Status with your parts |
|---|---|
| Proportional steering, throttle, brake | ✅ Works fully |
| Slow coast-down when R2 is released | ✅ Works fully (about 4 s from full speed to stop, adjustable) |
| RPM limiter 3k / 6k / 9k | ✅ Works, but it is an **estimate**. The Pi has no way to measure rpm, so it calculates `max power = target rpm ÷ (1000 KV × battery volts)`. **9000 rpm needs a 3S battery.** On 2S the motor tops out near 7400 rpm. |
| Gyro straight-line assist | ✅ Works fully (small corrections, max 15% steering) |
| ABS | ⚠️ Partly. ABS needs brakes. Stock SimonK ESCs usually have **no brake**: releasing throttle just coasts. The code pulses each rear wheel's brake proportional to L2 (left and right pulse half a cycle apart, so one wheel is usually rolling). It releases both if the gyro detects the rear sliding out. It only has a real effect if your ESCs have brake enabled (`ESC_HAS_BRAKE = True`). Real ABS also uses wheel-speed sensors, which this car does not have. |
| Right wheel faster when turning left | ✅ Works fully with your 2 motors + 2 ESCs. The outer wheel speeds up and the inner wheel slows down, proportional to steering. |

---

## 1. Extra parts you need

- **Battery:** 3S LiPo (11.1 V), 2200 mAh, **25C or higher** (two motors draw more current), with an XT60 plug and a LiPo charger.
- **XT60 parallel splitter (Y-cable)** so the battery feeds both ESCs.
- **5 V 5 A buck converter (UBEC) with USB-C output** to power the Pi from the battery. The Pi 5 needs a steady 5 V. *Never* power it straight from the battery.
- **Servo power:** a UBEC set to 6–7.4 V rated **5 A or more**. A 35 kg servo can pull 3 A or more. It will reset the Pi if it shares the Pi's power.
- MicroSD card, 32 GB, class A1/A2.
- Female-to-female jumper wires; 3.5 mm bullet connectors for the motor.

---

## 2. Wiring

**Pi 5 GPIO pin numbers** (pin 1 is the corner pin nearest the SD card side, marked with a square pad):

| From | To Pi pin | Notes |
|---|---|---|
| **LEFT** ESC signal (white/yellow) | **Pin 32** (GPIO12) | |
| LEFT ESC ground (black/brown) | **Pin 34** (GND) | |
| **RIGHT** ESC signal (white/yellow) | **Pin 12** (GPIO18) | Careful: *physical pin 12*, not GPIO12 |
| RIGHT ESC ground (black/brown) | **Pin 14** (GND) | |
| Both ESC red (5 V BEC) wires | **NOT connected** | Tape them off. They fight the Pi's own power. |
| Servo signal (orange/yellow) | **Pin 33** (GPIO13) | |
| Servo + and − | Servo UBEC output | Not the Pi |
| Servo UBEC ground | **Pin 39** (GND) | **All grounds must be joined**, or the signals will not work |
| MPU6050 VCC | **Pin 1** (3.3 V) | |
| MPU6050 GND | **Pin 6** (GND) | |
| MPU6050 SDA | **Pin 3** | |
| MPU6050 SCL | **Pin 5** | |
| 5 V buck USB-C | Pi USB-C port | |
| Each ESC's 3 thick wires | Its own motor's 3 wires | Wrong direction? Swap **any two** |

```
 3S LiPo ──┬── LEFT ESC  (30A) ──3 wires── LEFT A2212 motor
           ├── RIGHT ESC (30A) ──3 wires── RIGHT A2212 motor
           ├── 5V 5A buck ──USB-C── Raspberry Pi 5
           └── 6-7.4V UBEC ──────── Servo (+/-)
 Pi pin 32 ─── LEFT ESC signal    Pi pin 12 ─── RIGHT ESC signal
 Pi pin 33 ─── Servo signal
 Pi GND ── both ESC GNDs ── UBEC GND   (all grounds joined)
 Pi pins 1,3,5,6 ─── MPU6050 (VCC, SDA, SCL, GND)
```
"LEFT" and "RIGHT" mean as seen from **behind the car, looking forward**.

**Mounting the MPU6050:** flat, near the middle of the car, on double-sided foam tape (absorbs vibration), as far from the motor as possible.

---

## 3. Put the operating system on the SD card (on your laptop)

1. Download **Raspberry Pi Imager** from raspberrypi.com/software and install it.
2. Choose Device: **Raspberry Pi 5**. Choose OS: **Raspberry Pi OS (other) → Raspberry Pi OS Lite (64-bit)**. Choose storage: your SD card.
3. Click **Next → Edit Settings**:
   - Hostname: `f1car`
   - Username: `pi`, and pick a password (write it down)
   - Wi-Fi: your network name and password; Wi-Fi country: IN
   - **Services tab → Enable SSH → Use password authentication**
4. Save → Yes → wait for it to finish. Put the card in the Pi and power it on. Wait 2 minutes.

## 4. Connect to the Pi from your laptop

Open **PowerShell** (Windows) or **Terminal** (Mac/Linux), with the laptop on the same Wi-Fi:
```
ssh pi@f1car.local
```
Type `yes`, then your password (it stays invisible while typing; that's normal). You are now typing commands **on the Pi**.

> If `f1car.local` is not found, find the Pi's IP address in your router's device list and use `ssh pi@192.168.x.x`.

## 5. Turn on I2C (gyro) and hardware PWM (2 motors + servo)

The Pi 5's built-in setting only switches on 2 PWM outputs, and you need 3. The project includes a small file (`pwm-pi5-overlay.dts`) that switches on all 4, plus a script that installs it. **Do step 7 (copy the code) first**, then come back here:
```
sudo apt update && sudo apt full-upgrade -y
sudo raspi-config nonint do_i2c 0
cd ~/f1car
bash setup_pwm.sh
sudo reboot
```
Wait 1 minute and run `ssh pi@f1car.local` again.

To check it worked, open the settings file with `sudo nano /boot/firmware/config.txt` and look at the last lines. You should see `dtoverlay=pwm-pi5` below the `[all]` line. Exit with Ctrl+X.

> **Order:** do steps 6 and 7 before step 5.

## 6. Install the software the code needs

```
sudo apt install -y python3-evdev python3-smbus2 i2c-tools unzip
```

## 7. Copy the code to the Pi

On your **laptop** (a new terminal window, not the SSH one), in the folder where you downloaded `f1car.zip`:
```
scp f1car.zip pi@f1car.local:~/
```
Then on the **Pi**:
```
unzip f1car.zip
cd ~/f1car
ls
```
You should see `main.py`, `config.py` and the other files.

## 8. Pair the DualSense Edge

1. On the Pi, type `bluetoothctl`
2. Type these one at a time:
```
power on
agent on
default-agent
scan on
```
3. On the controller, **hold Create (small button left of the touchpad) + PS button** for about 5 s until the light bar **flashes rapidly**.
4. Wait for a line like `DualSense Edge Wireless Controller` with an address like `AA:BB:CC:11:22:33`. Then type (using your address):
```
pair AA:BB:CC:11:22:33
trust AA:BB:CC:11:22:33
connect AA:BB:CC:11:22:33
scan off
exit
```
From now on, pressing the **PS button** reconnects it automatically.

> If the controller is also paired to a PS5 or PC nearby, switch that device off, or it will grab the controller first.

## 9. Test each part (in this order)

Always `cd ~/f1car` first.

| # | Command | What should happen |
|---|---|---|
| 1 | `i2cdetect -y 1` | A grid with **68** in it. No 68 means check the gyro wires. |
| 2 | `sudo python3 check_pwm.py` | Shows `(4 channels) -> PWM OK` |
| 3 | `sudo python3 test_controller.py` | Stick left shows a **negative** number; R2 and L2 go 0.00→1.00; Circle and Square print. |
| 4 | `sudo python3 test_imu.py` | Keep still for 2 s. Turn the car **left** by hand: `yaw` goes **positive**. If it goes negative, set `YAW_SIGN = -1` in config.py. |
| 5 | `sudo python3 test_servo.py` | Type 1500, then 1480, 1520… Find straight-ahead and the lock limits. Put them in `SERVO_CENTER_US` and `SERVO_RANGE_US`. |
| 6 | `sudo python3 calibrate_esc.py` | **Wheels off the ground!** Calibrates **both** ESCs at once. Do this once. Calibration makes both motors respond the same to the same signal. |
| 7 | `sudo python3 test_motor.py` | **Wheels off the ground!** The LEFT wheel spins, then the RIGHT one. Both must turn in the "forward" direction. One motor faces the other way, so you will probably need to swap two wires on one of them. If RIGHT spins first, swap the two signal wires (pins 32 and 12). |
| 8 | `python3 test_logic.py` | Simulates all the driving features with no hardware. Ends with `ALL CHECKS PASSED`. |

To edit settings: `nano config.py`, then Ctrl+O, Enter, Ctrl+X.

## 10. Drive!

```
cd ~/f1car
sudo python3 main.py
```
Keep the car **still** for the first 3 seconds while the gyro calibrates and the ESC arms (it beeps). Then press PS on the controller.

| Control | Action |
|---|---|
| Left stick | Steer (proportional) |
| R2 | Accelerate (proportional; slow coast when released) |
| L2 | Brake + ABS (proportional) |
| ○ Circle | RPM limit up (light bar: green 3k → orange 6k → red 9k) |
| □ Square | RPM limit down |

**Ctrl+C** stops the program: motor stops and steering centres. If the controller disconnects, the car brakes automatically.

## 11. Start automatically when the car powers on (optional, do it last)

```
sudo cp ~/f1car/f1car.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now f1car
```
- See live messages: `journalctl -u f1car -f`
- Stop it: `sudo systemctl stop f1car`
- Turn autostart off: `sudo systemctl disable f1car`

If the program ever crashes, `emergency_stop.py` runs automatically and stops the motor.

---

## 12. Tuning (all in config.py)

| Problem | Change |
|---|---|
| Car pulls to one side with the stick centred | First `STEER_TRIM_US` (try ±10). If it still pulls, set `ASSIST_ENABLED = False`, drive straight, and adjust `RIGHT_MOTOR_TRIM` (pulls left → 0.97, pulls right → 1.03). Then turn assist back on. |
| Turns feel too pushy / not enough | `TV_GAIN` (0 = wheels equal, 0.35 default, 0.5 strong) |
| Coasting stops too fast / too slow | `COAST_RATE` (smaller = longer coast) |
| Car takes off too violently | lower `ACCEL_RATE` |
| Assist wobbles left-right | lower `ASSIST_KP`, raise `ASSIST_KD` slightly |
| Assist too weak to hold straight | raise `ASSIST_KP` |
| Steering too twitchy near centre | `STEER_EXPO = 0.3` |
| Real rpm doesn't match the limit | measure with a tachometer, adjust `RPM_CALIBRATION` |

## 13. Troubleshooting

| Symptom | Fix |
|---|---|
| `Permission denied` | You forgot `sudo` |
| `No PWM chips found` | Step 5 overlay line is missing, or you didn't reboot |
| Servo works but a motor only beeps | Run `calibrate_esc.py`; check that ESC's ground wire (pin 34 left, pin 14 right) |
| Right motor does nothing, left works | Signal must be on **physical pin 12** (GPIO18). Run `check_pwm.py`: pin 18 should show `a3` |
| `setup_pwm.sh` worked but `check_pwm.py` shows only 2 channels or none | Open `/boot/firmware/config.txt` and check that `dtoverlay=pwm-pi5` is under `[all]` and `pwm-2chan` is gone, then reboot |
| Pi reboots when steering | Servo is drawing power from the Pi. Use its own UBEC. |
| Lightning-bolt / undervoltage warning | Buck converter too weak; it must be 5 V **5 A** |
| `[IMU] read errors` | Loose SDA/SCL wire; keep gyro wires short |
| Controller never connects | Re-do step 8; turn off the PS5 or PC it was paired to |

## 14. How the code works (file by file)

- **config.py**: every number you can tune.
- **main.py**: runs 100 times per second: read controller → read gyro → `control.py` decides → send pulses to the ESC and servo.
- **control.py**: the brain (pure maths, testable on any laptop):
  - *Throttle:* R2 × limiter cap is the target. Power rises at `ACCEL_RATE` and falls at `COAST_RATE`, which gives the slow stop.
  - *Limiter:* `cap = rpm ÷ (KV × volts)`. For example, 6000 ÷ 11100 = 54% power.
  - *ABS:* every 80 ms each rear wheel's brake is ON for `L2 × 85%` of the time and OFF for the rest, so the wheels never stay locked. The right wheel pulses half a cycle after the left. If the gyro sees the car spinning (rear sliding out), both brakes are fully released for 0.12 s.
  - *Gyro assist:* while the stick is centred, the gyro adds up how many degrees the car has turned. It steers back proportionally, capped at 15%.
  - *Turn speed difference:* left wheel ×(1 + 0.35 × steer), right wheel ×(1 − 0.35 × steer). Steer is negative for left, so in a left turn the right (outer) wheel speeds up. The outer wheel can never go above the RPM limit.
- **controller.py**: reads the DualSense in the background and reconnects automatically.
- **imu.py**: talks to the MPU6050 over I2C and removes gyro drift (calibration).
- **setup_pwm.sh + pwm-pi5-overlay.dts**: switch on all 4 PWM outputs of the Pi 5.
- **pwm.py**: Pi 5 hardware PWM. Older libraries like `RPi.GPIO` and `pigpio` do not work on the Pi 5.

## Safety rules
1. Wheels **off the ground** whenever you test the motor on the bench.
2. Unplug the battery before changing any wiring.
3. Never leave a LiPo charging unattended. Charge it in a LiPo-safe bag.
4. Start driving at the 3000 rpm limit until everything feels right.
