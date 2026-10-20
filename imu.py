"""MPU6050 gyro/accelerometer driver (I2C, address 0x68)."""
import time
from smbus2 import SMBus

PWR_MGMT_1, SMPLRT_DIV, CONFIG = 0x6B, 0x19, 0x1A
GYRO_CONFIG, ACCEL_CONFIG, ACCEL_XOUT_H, WHO_AM_I = 0x1B, 0x1C, 0x3B, 0x75
GYRO_SCALE = 65.5     # LSB per deg/s at +/-500 deg/s
ACCEL_SCALE = 8192.0  # LSB per g at +/-4 g


def _s16(hi, lo):
    v = (hi << 8) | lo
    return v - 65536 if v > 32767 else v


class MPU6050:
    def __init__(self, bus=1, address=0x68):
        self.bus = SMBus(bus)
        self.addr = address
        who = self.bus.read_byte_data(address, WHO_AM_I)
        if who != 0x68:
            print(f"[IMU] WHO_AM_I = {hex(who)} (clone chip). Usually still works.")
        self.bus.write_byte_data(address, PWR_MGMT_1, 0x00)   # wake up
        time.sleep(0.1)
        self.bus.write_byte_data(address, PWR_MGMT_1, 0x01)   # gyro clock
        self.bus.write_byte_data(address, SMPLRT_DIV, 0x04)   # 200 Hz
        self.bus.write_byte_data(address, CONFIG, 0x03)       # 44 Hz filter (motor vibration)
        self.bus.write_byte_data(address, GYRO_CONFIG, 0x08)  # +/-500 deg/s
        self.bus.write_byte_data(address, ACCEL_CONFIG, 0x08) # +/-4 g
        time.sleep(0.05)
        self.gyro_bias = [0.0, 0.0, 0.0]

    def read_raw(self):
        d = self.bus.read_i2c_block_data(self.addr, ACCEL_XOUT_H, 14)
        accel = [_s16(d[i], d[i + 1]) / ACCEL_SCALE for i in (0, 2, 4)]
        gyro = [_s16(d[i], d[i + 1]) / GYRO_SCALE for i in (8, 10, 12)]
        return accel, gyro

    def calibrate(self, seconds=2.0):
        """Measures gyro drift. The car MUST be completely still."""
        n, sums, sq = 0, [0.0] * 3, [0.0] * 3
        end = time.time() + seconds
        while time.time() < end:
            _, g = self.read_raw()
            for i in range(3):
                sums[i] += g[i]
                sq[i] += g[i] * g[i]
            n += 1
            time.sleep(0.005)
        self.gyro_bias = [s / n for s in sums]
        noise = max((sq[i] / n - self.gyro_bias[i] ** 2) ** 0.5 for i in range(3))
        if noise > 1.0:
            print("[IMU] WARNING: car moved during calibration. Restart with it still.")
        return self.gyro_bias

    def read(self):
        accel, gyro = self.read_raw()
        return accel, [gyro[i] - self.gyro_bias[i] for i in range(3)]
