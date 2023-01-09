#!/bin/bash

sudo apt-get update
sudo apt-get upgrade

sudo apt-get install python-smbus i2c-tools

echo "Bitte fügen Sie 'echo ds1307 0x68 > /sys/class/i2c-adapter/i2c-1/new_device' in /etc/rc.local vor exit 0 ein"

python -m pip install mariadb board busio adafruie_tsl2561 adafruit_bmp280 RPLCD.i2c adafruit_sht31d adafruit_sht4x piqmp6988 adafruit_sgp30 python-dotenv


cd
mkdir sensorknoten
cd sensorknoten

wget https://raw.githubusercontent.com/Tobsti/Sensorknoten-HCU/main/sensorknoten.py

chmod +x sensorknoten.py


echo "@reboot ~/sensorknoten/sensorknoten.py >> ~/sensorknoten/protocoll.txt" >> sensoknoten_crontask

crontab sensoknoten_crontask
rm sensoknoten_crontask

