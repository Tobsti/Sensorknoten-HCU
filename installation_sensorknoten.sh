#!/bin/bash

cd /home/pi
sudo mkdir /home/pi/sensorknoten
cd /home/pi/sensorknoten
sudo mkdir /mnt/usb

wget https://raw.githubusercontent.com/Tobsti/Sensorknoten-HCU/main/sensorknoten.py
wget https://raw.githubusercontent.com/Tobsti/Sensorknoten-HCU/main/.env

chmod +x sensorknoten.py

cd ~

sudo apt-get update
sudo apt-get upgrade -y

sudo apt-get install  i2c-tools python3-pip libmariadb3 libmariadb-dev pigpio -y
sudo systemctl enable pigpiod



sudo python -m pip install smbus  adafruit-extended-bus adafruit-circuitpython-tsl2561 adafruit-circuitpython-bmp280 RPLCD adafruit-circuitpython-sht31d adafruit-circuitpython-sht4x piqmp6988 adafruit-circuitpython-sgp30 python-dotenv
sudo python -m pip install mariadb==1.0.11

echo "dtparam=i2c_vc=on" >> /boot/config.txt
echo "@reboot sleep 15 && sudo ~/sensorknoten/sensorknoten.py >> ~/sensorknoten/protocoll.txt" >> sensoknoten_crontask

sudo crontab sensoknoten_crontask
sudo rm sensoknoten_crontask

echo "Bitte fügen Sie 'echo ds1307 0x68 > /sys/class/i2c-adapter/i2c-1/new_device' in /etc/rc.local vor exit 0 ein"

sudo pip install adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo python3 raspi-blinka.py
