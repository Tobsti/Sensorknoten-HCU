#!/bin/bash

cd
mkdir sensorknoten
cd sensorknoten

wget https://raw.githubusercontent.com/Tobsti/Sensorknoten-HCU/main/sensorknoten.py

chmod +x sensorknoten.py

cd

sudo apt-get update
sudo apt-get upgrade

sudo apt-get install  i2c-tools python3-pip libmariadb3 libmariadb-dev -y



sudo python -m pip install smbus mariadb adafruit-extended-bus adafruit-circuitpython-tsl2561 adafruit-circuitpython-bmp280 RPLCD adafruit-circuitpython-sht31d adafruit-circuitpython-sht4x piqmp6988 adafruit-circuitpython-sgp30 python-dotenv



echo "@reboot sleep 15 && sudo ~/sensorknoten/sensorknoten.py >> ~/sensorknoten/protocoll.txt" >> sensoknoten_crontask

sudo crontab sensoknoten_crontask
sudo rm sensoknoten_crontask

echo "Bitte fügen Sie 'echo ds1307 0x68 > /sys/class/i2c-adapter/i2c-1/new_device' in /etc/rc.local vor exit 0 ein"

sudo pip install adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo python3 raspi-blinka.py
