#!/bin/bash
# Installs the 4-channel PWM overlay for the Pi 5.   Run:  bash setup_pwm.sh
set -e
cd "$(dirname "$0")"
CFG=/boot/firmware/config.txt
echo "1/4 Installing the device tree compiler..."
sudo apt install -y device-tree-compiler
echo "2/4 Compiling the overlay..."
dtc -q -I dts -O dtb -o pwm-pi5.dtbo pwm-pi5-overlay.dts
sudo cp pwm-pi5.dtbo /boot/firmware/overlays/
echo "3/4 Updating $CFG (backup saved as config.txt.backup)..."
sudo cp "$CFG" "$CFG.backup"
sudo sed -i '/^dtoverlay=pwm-2chan/d' "$CFG"
grep -q '^dtoverlay=pwm-pi5' "$CFG" || echo 'dtoverlay=pwm-pi5' | sudo tee -a "$CFG" > /dev/null
grep -q '^dtparam=i2c_arm_baudrate' "$CFG" || echo 'dtparam=i2c_arm_baudrate=400000' | sudo tee -a "$CFG" > /dev/null
echo "4/4 Done. Now run:  sudo reboot"
