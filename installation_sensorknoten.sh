#!/bin/bash

# Anlegen Der Ordnerstruktur
cd /home/pi
sudo mkdir /home/pi/sensorknoten
cd /home/pi/sensorknoten
sudo mkdir /mnt/usb

# Herunterladen des sensorknoten.py Scriptes und der environment-Datei mit dummy-Zugangsdaten
wget https://raw.githubusercontent.com/Tobsti/Sensorknoten-HCU/main/sensorknoten.py
wget https://raw.githubusercontent.com/Tobsti/Sensorknoten-HCU/main/.env

# sensorknoten.py Ausführbar mache
chmod +x sensorknoten.py

cd ~
# Updates Herunterladen, sofern noch nicht geschen
sudo apt-get update
sudo apt-get upgrade -y

# Installieren der apt-Pakete  und pigpio als Dienst hinzufügen
sudo apt-get install  i2c-tools python3-pip libmariadb3 libmariadb-dev pigpio -y
sudo systemctl enable pigpiod


# Installieren der benötigten pip Module für sensorknoten.py
sudo python -m pip install smbus  adafruit-extended-bus adafruit-circuitpython-tsl2561 adafruit-circuitpython-bmp280 RPLCD adafruit-circuitpython-sht31d adafruit-circuitpython-sht4x piqmp6988 adafruit-circuitpython-sgp30 python-dotenv
# Installieren eines älteren mariadb Moduls, da das paket libmariadb3 nicht mit dem aktuellen pip Paket umgehen kann.
sudo python -m pip install mariadb==1.0.11

# Aktivieren der zweiten i2c-Schnittstelle
echo "dtparam=i2c_vc=on" >> /boot/config.txt

# Hinzufügen des Crontask von sensorknoten.py und dem schreiben der Printnachriten in die protocoll.txt
echo "@reboot sleep 15 && sudo ~/sensorknoten/sensorknoten.py >> ~/sensorknoten/protocoll.txt" >> sensoknoten_crontask
sudo crontab sensoknoten_crontask
sudo rm sensoknoten_crontask

# Dies wird leider nur kurz angezeigt, ist aber in der Installationsanleitung gegeben
echo "Bitte fügen Sie 'echo ds1307 0x68 > /sys/class/i2c-adapter/i2c-1/new_device' in /etc/rc.local vor exit 0 ein"

# Herunterladen und installieren von raspi-blinka.py, einem Script, was den Raspberry Pi für die adafruitscripte vorbereitet.
sudo pip install adafruit-python-shell
wget https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/raspi-blinka.py
sudo python3 raspi-blinka.py
