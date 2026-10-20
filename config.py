"""
=====================================================================
  F1 MODEL CAR - ALL SETTINGS LIVE HERE
=====================================================================
Change numbers in THIS file only. The other files read from it.
After changing anything, just run main.py again.
"""

# ------------------------------------------------------------------
# 1. BATTERY + MOTOR  (used by the RPM limiter)
# ------------------------------------------------------------------
MOTOR_KV       = 1000      # A2212 1000KV  -> 1000 rpm per volt (no load)
BATTERY_CELLS  = 3         # LiPo cells feeding the ESC. 2S = 7.4V, 3S = 11.1V
CELL_VOLTAGE   = 3.7       # nominal volts per LiPo cell
# 9000 rpm needs 3S. With 2S the motor can only reach about 7400 rpm.

RPM_LEVELS     = [3000, 6000, 9000]   # Circle = up a level, Square = down
START_LEVEL    = 0                    # 0 = start at 3000 rpm (safest)
RPM_CALIBRATION = 1.0   # If you measure real rpm with a tachometer and it is
                        # e.g. 10% low, set this to 1.10

# ------------------------------------------------------------------
# 2. PWM OUTPUT PINS  (hardware PWM on the Pi 5)
# ------------------------------------------------------------------
#   channel 0 = GPIO12 = physical pin 32
#   channel 1 = GPIO13 = physical pin 33
#   channel 2 = GPIO18 = physical pin 12
#   channel 3 = GPIO19 = physical pin 35
PWM_CHIP        = None  # None = find it automatically. If check_pwm.py says
                        # "set PWM_CHIP", put the number here (e.g. 0 or 2)
ESC_LEFT_CHANNEL  = 0   # LEFT rear motor ESC  -> GPIO12, pin 32
SERVO_CHANNEL     = 1   # steering servo       -> GPIO13, pin 33
ESC_RIGHT_CHANNEL = 2   # RIGHT rear motor ESC -> GPIO18, pin 12
PWM_FREQUENCY_HZ  = 50  # standard RC signal: one pulse every 20 ms

DUAL_REAR_MOTORS  = True   # 2 motors + 2 ESCs: outer wheel faster in turns
RIGHT_MOTOR_TRIM  = 1.00   # if the car pulls LEFT on a straight with the gyro
                           # assist OFF, the right motor is faster: try 0.97.
                           # Pulls RIGHT -> try 1.03

# ------------------------------------------------------------------
# 3. ESC (SimonK 30A)
# ------------------------------------------------------------------
ESC_MIN_US        = 1000   # pulse = motor stopped
ESC_MAX_US        = 2000   # pulse = full power
ESC_ARM_SECONDS   = 3.0    # send "stopped" this long at startup so the ESC arms
ESC_START_DEADBAND = 0.02  # commands below 2% are sent as fully stopped
ESC_HAS_BRAKE     = False  # Stock SimonK usually has NO brake. Set True only
                           # if your ESC is flashed with brake enabled.

# ------------------------------------------------------------------
# 4. STEERING SERVO (GOTECK 35kg)
# ------------------------------------------------------------------
SERVO_CENTER_US = 1500   # find the real centre with test_servo.py
SERVO_RANGE_US  = 400    # full lock = centre +/- this (1100..1900 us)
STEER_TRIM_US   = 0      # small fix if the car drifts with the stick centred
SERVO_REVERSED  = False  # True if stick-left makes the wheels go right

# ------------------------------------------------------------------
# 5. CONTROLLER (DualSense Edge over Bluetooth)
# ------------------------------------------------------------------
CONTROLLER_NAME_MATCH = "DualSense"
AXIS_STEER    = "ABS_X"     # left stick left/right
AXIS_BRAKE    = "ABS_Z"     # L2
AXIS_THROTTLE = "ABS_RZ"    # R2
BUTTON_SPEED_UP   = "BTN_EAST"   # Circle
BUTTON_SPEED_DOWN = "BTN_WEST"   # Square
STICK_DEADZONE   = 0.06   # stick movement smaller than 6% is ignored
TRIGGER_DEADZONE = 0.04
STEER_EXPO       = 0.0    # 0 = purely proportional. 0.3 = finer near centre

# ------------------------------------------------------------------
# 6. THROTTLE FEEL
# ------------------------------------------------------------------
ACCEL_RATE = 1.2    # how fast power can rise   (fraction per second)
COAST_RATE = 0.25   # how fast it falls when you let go of R2
                    # 0.25 => full speed to stop takes about 4 seconds

# ------------------------------------------------------------------
# 7. BRAKES + ABS
# ------------------------------------------------------------------
BRAKE_RATE        = 1.6    # speed removed per second at full L2
ABS_PERIOD_S      = 0.08   # one brake pulse cycle = 80 ms (12.5 per second)
ABS_MAX_DUTY      = 0.85   # even at full L2, brakes release 15% of each cycle
ABS_YAW_LIMIT_DPS = 60.0   # rear sliding out faster than this -> release brake
ABS_RELEASE_S     = 0.12   # how long to release when a skid is detected
ABS_RELEASE_MATCH = 0.9    # (brake ESC only) wheel-speed match while released
FAILSAFE_BRAKE    = 0.6    # brake strength used if the controller disconnects

# ------------------------------------------------------------------
# 8. GYRO STRAIGHT-LINE ASSIST
# ------------------------------------------------------------------
ASSIST_ENABLED   = True
ASSIST_KP        = 0.010   # steering added per degree off course
ASSIST_KD        = 0.002   # steering added per degree/second of rotation
ASSIST_MAX       = 0.15    # assist can never steer more than 15% (minor fixes)
ASSIST_MIN_SPEED = 0.05    # assist is off below 5% power

# Turning-wheel speed difference (only used if DUAL_REAR_MOTORS = True)
TV_GAIN = 0.35   # at full lock, outer wheel +35%, inner wheel -35%

# ------------------------------------------------------------------
# 9. GYRO (MPU6050)
# ------------------------------------------------------------------
I2C_BUS         = 1
IMU_ADDRESS     = 0x68
YAW_AXIS        = 2      # 0 = x, 1 = y, 2 = z. Board flat on the car -> 2
YAW_SIGN        = 1      # test_imu.py tells you if this must be -1
GYRO_CAL_SECONDS = 2.0   # car must be still while this runs at startup

# ------------------------------------------------------------------
# 10. PROGRAM
# ------------------------------------------------------------------
LOOP_HZ         = 100    # control loop runs 100 times per second
STATUS_PRINT_HZ = 4
