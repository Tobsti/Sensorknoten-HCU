#!/usr/bin/python3
# Module Imports
import time
import mariadb
import sys
import board
import busio
import os
import adafruit_tsl2561
import adafruit_bmp280
import time
import datetime
from RPLCD.i2c import CharLCD
import subprocess
import socket
import adafruit_sht31d
import adafruit_sht4x
import piqmp6988 as QMP6988
import adafruit_sgp30
from dotenv import load_dotenv

# Läd die Datenbankparameter aus der .env Datei.
load_dotenv()

# öffnet die I2C Schnittstellen. Der Raspberry Pi besitzt zwei, wobei der i2c_0 über den D0 und D1 (27 u 28) Port läuft. (siehe BCM-Pinout https://pinout.xyz/ )
i2c = board.I2C()
i2c_0=busio.I2C(board.D1,board.D0,frequency=100000)

# Sleep, da es nach direkt nach der I2C Initialisierung zu Fehlern kommen könnte 
time.sleep(2)

# Initialisierung der Bosch BMP280 (Temperatur und Luftdruck)
try:
	sensor_bmp = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
except:
	print("Problem BMP")

# Initialisierung des sgp30 Sensors läuft über die zweite i2c Schnittstelle, da dieser sonst mit dem BMP280, oder dem LCD-Display nicht funktioniert. 
# Code nicht aktuell angepasst siehe README.md "https://github.com/Tobsti/Sensorknoten-HCU"
try:
	sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c_0)
	sgp30.set_iaq_baseline(0x8973, 0x8AAE)
	sgp30.set_iaq_relative_humidity(celsius=22.1, relative_humidity=44)
except:
	print("Problem mit dem SGP30")

# Ein LCD Display für die IP-Adresse und einer kleinen Statusbenachrichtigung. Sollte nur zu Debugging zwecken genutzt werden. Sonst sollte vorher ein Levelschifter für 3,3V auf 5V genutzt werden.
try:
	lcd = CharLCD('PCF8574',0x27)
except:
	print("no LCD available")


def write_lcd(pos,text,clear=False):
	""" Diese Funktion schreibt immer die IP-Adresse in die erste Zeile und kann dafür genutzt werden etwas in die zweite Zeile zu schreiben."""
	ip = own_ip()
	try:
		if clear == True:
			lcd.clear()
		lcd.cursor_pos = (0,0)
		lcd.write_string(ip)

		lcd.cursor_pos = pos
		lcd.write_string(text)
	except:
		print("no LCD available")


def own_ip():
	"""Diese Funktion gibt die IP-Adresse des Raspberry Pis im eigenen Netzwerk wieder. Dies ist für Wartungszwecke über SSH sehr nützlich. """
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		# connect() for UDP doesn't send packets
		s.connect(('10.0.0.0', 0))
		return s.getsockname()[0]
	except:
		return "no_ip"

def zeitregelung():
	"""Mit dieser Funktion kann das Raspberry Pi ohne Internetverbindung Daten mit einem Zeitstempel versehen.
	Es wird nach einem Zeitserver gesucht, wenn dieser vorhanden ist wird seine Zeit auf die RTC sychronisiert (um zu langen Zeitdrift zu vermeiden)
	Wenn der Zeitserver nicht erreichbar ist wird die Zeit der RTC auf den Raspberry Synchronisiert. 
	Die Implementierung der RTC erfolgt in dem Betriebssystem, nicht in diesem Script. Siehe README.md  https://github.com/Tobsti/Sensorknoten-HCU """
	timeserver = "2.de.pool.ntp.org"
	response = os.system("ping -c 1 " + timeserver)
	if response == 0:
		try:
			os.system("sudo hwclock -w")
		except:
			print("Keine RTC vorhanden")
	else:
		try:
			os.system("sudo hwclock -s")
		except:
			print("Keine RTC vorhanden")



def connect_database():
	"""Diese Funktion verbindet sich über die Daten aus der .env Datei mit der Datenbank.
	Das Ergebnis wird auf dem lcd Display dargestellt. 
	Wenn eine connection funktioniert wird diese mit conn übergeben. 
	Die Fehlermeldung wird per print() in die Konsole geschrieben"""
	try:
		conn = mariadb.connect(
			user=os.environ.get('DB_USER'),
			password=os.environ.get('DB_PASSWORD'),
			host=os.environ.get('DB_HOST'),
			port=os.environ.get('DB_PORT'),
			database=os.environ.get('DB_DATABASE'),
			connect_timeout = 5)

		write_lcd((1,0),"DB:Yes",False)
		return conn
	except mariadb.Error as e:
		write_lcd((1,0),"DB:No ",False)

		print(f"Error connecting to MariaDB Platform: {e}")
		return False

def usb_available():
	"""Diese Funktion dient zum Mounten eines usb-Sticks. Unter Linux werden eingesteckte USB Sticks in /dev/sd{a-z} aufgelistet. 
	Dieser Codeabschnitt kann nur mit sda und sdb umgehen. Dies ist nur ein Problem, wenn ein USB Stick im laufenden Betrieb mehrfahch entfernt wird. 
	Am Besten ein USB Stick einstecken und dann einschalten. """
	proc = subprocess.Popen('lsblk',stdout=subprocess.PIPE)
	lsblk = proc.stdout.read()
	if str.encode("sda") in lsblk:
		print("sda")
		os.system("sudo mount -t vfat -o utf8,uid=pi,gid=pi,noatime /dev/sda /mnt/usb")
		return True
	elif str.encode("sdb") in lsblk:
		print("sdb")
		os.system("sudo mount -t vfat -o utf8,uid=pi,gid=pi,noatime /dev/sdb /mnt/usb")
		return True
	else:
		return False


# Ab hier hat jeder Sensorwert seine einene Fuktion. So kann an jeden Wert eine Korrektur angebracht werden, ohne den Restlichen Code zu verändern. 
# Die Funktionsnahmen sind wie folgt aufgebaut: messwert_sensor() Damit im nachhinnein klar ist, um welchen Wert/Sensor es sich handelt. Durch das "try:","except:" funktioniert der Sonsorknoten auch dann weiter, wenn ein Sensor fehlerhaft ist.  
def co2_sgp30():
	try:
		eco2 = sgp30.eCO2
		return eco2
	except:
		return "error"

def tvoc_sgp30():
	try:
		tvoc = sgp30.TVOC
		return tvoc
	except:
		return "error"



def press_qmp6988():
	try:
		config = {
		    'temperature' : QMP6988.Oversampling.X4.value,
		    'pressure' :    QMP6988.Oversampling.X32.value,
		    'filter' :      QMP6988.Filter.COEFFECT_32.value,
		    'mode' :        QMP6988.Powermode.NORMAL.value
		}
		obj = QMP6988.PiQmp6988(config)
		value = obj.read()
		press = value['pressure']
		return press

	except:
		return "error"


def temp_sht40():
	try:
		sht = adafruit_sht4x.SHT4x(board.I2C())
		temp = sht.temperature
		return temp
	except:
		return "error"

def hum_sht40():
	try:
		sht = adafruit_sht4x.SHT4x(board.I2C())
		hum = sht.relative_humidity
		return hum
	except:
		return "error"


def temp_sht30():
	try:
		sensor = adafruit_sht31d.SHT31D(i2c)
		temp = sensor.temperature
		return temp
	except:
		return "error"

def hum_sht30():
	try:
		sensor = adafruit_sht31d.SHT31D(i2c)
		hum = sensor.relative_humidity
		return hum
	except:
		return "error"


def temp_BMP():
	try:
		temp = sensor_bmp.temperature
		return temp
	except:
		return "error"

def press_BMP():
	try:
		press = sensor_bmp.pressure
		return press
	except:
		return "error"

def lux_TSL():
	try:
		i2c = busio.I2C(board.SCL, board.SDA)
		licht = adafruit_tsl2561.TSL2561(i2c).lux
		return licht
	except:
		return "error"




if __name__ == '__main__':

	# Ausführen der Initialsfunktionen. Dementsprechend wird nur am Anfang überprüft, ob ein USB-Stick, oder eine Datenbankverbindung vorhanden ist, oder nicht.
	zeitregelung()
	write_lcd((1,0),"test",True)
	conn = connect_database()
	usb_available_test = usb_available()

	# Die Messschleife, die durchgehend nach der Initialisierung ausgeführt wird. durch viele Try Except Statements ist diese Schleife sehr wiederstandsfähig gegen Fehler der Sensoren, oder der Infrastruktur
	
	while True:
		# Die aktuelle Zeit wird geholt
		ts = time.time()
		# In diesem Dictionary werden Alle Daten gesammelt und die Funktionen ausgeführt. Dieser Aufbau wurde gewählt, um eine möglichst geringe Latenz zu erreichen. 
		# In der Kalibrierung war trotzdem eine Latenz zwischen den Sensoren messbar, weshalb gerade dieser Abschnitt zu einer Refaktorisierung einläd.
		dataset = {
			"timestamp" : time.time(),
			"timestamp_hr" : datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S'),
			"temp_bmp280" : temp_BMP(),
			"temp_sht30" : temp_sht30(),
			"temp_sht40": temp_sht40(),
			"hum_sht30": hum_sht30(),
			"hum_sht40": hum_sht40(),
			"pres_qmp6988":press_qmp6988(),
			"pres_bmp280" : press_BMP(),
			"lux_tsl2561" : lux_TSL(),
			"eco2_sgp30": co2_sgp30(),

			}
		# Um flexiebel zu sein sollen nicht genutzte Datensätze erstmal dem dataset_no_writng Dictionary gespeichert werden. Sollte der Sensorknoten 
		# nicht mit einem der Sensoren Ausgestattet sein kann dieses Dictionary aus dem Code entfernt werden, um Zeit und rechneleistung zu sparen.
		dataset_no_writing = {
			"tvoc_sgp30": tvoc_sgp30()
		}

		# Seleep Timer, um die Daten zu erhalten und um ein ungefähres Delta_t einzustellen. Im Laufenden betrieb kann der Sleep auf minimum 2 Sekunden eingestellt werden. 
		
		time.sleep(5)

		# LCD-Indiz, dass das schreiben der Daten beginnt
		write_lcd((1,0),"DB:Wri",False)
		write_lcd((1,7),"USB:Wri",False)

		if conn != False:
			"""Dieser Part wird nur ausgeführt, sofern eine Datenbankverbindung vorhanden ist. Dieser Part ist auch für eine refaktorisierung prädestieniert.
			Aktuell wird in cur.execute und SQL anfrage gestellt. 
			Neue Messwerte benötigen:
			- Den Namen der datenbankspalte von "sensor_geolabor"
			- Ein Fragezeichen bei den VALUES
			- Den Wert aus dataset mit dem Schlüssel

			Die ganzen Parameter müssen jeweils an der gleichen Stelle stehen. Also am Besten immer am Ende einfügen
			"""
			cur = conn.cursor()
			cur.execute(
		    		"INSERT INTO sensor_geolabor(eco2_sgp30,pres_qmp6988,timestamp,temp_bmp280,temp_sht30,hum_sht30,lux_tsl2561,pres_bmp280) VALUES (?,?,FROM_UNIXTIME(?),?,?,?,?,?)",
				(dataset["eco2_sgp30"],dataset["pres_qmp6988"],dataset["timestamp"],dataset["temp_bmp280"],dataset["temp_sht30"],dataset["hum_sht30"],dataset["lux_tsl2561"],dataset["pres_bmp280"])
		      	)

			conn.commit()

			# Bestätigung, dass der Datensatz zur Datenbank hinzugefügt wurde.
			write_lcd((1,0),"DB:Yes",False)

		else:
			# Loggt, dass keine Datenbankverbindung besteht und Zeigt den Umstand auch auf dem LCD Display
			print("keine Datenbankverbindung ")
			write_lcd((1,0),"DB:No ",False)

		if usb_available_test == True:
			"""Dieser Part wird nur ausgeführt, wenn ein USB-Stick vorhanden ist. Das gesamte dataset wird auf den USB-Stick geschrieben, sofern vorhanden."""
			with open("/mnt/usb/protocoll.txt","a") as file:
				for data in dataset:
					file.write(str(dataset[data])+";")
				file.write("\n")

			write_lcd((1,7),"USB:Yes",False)
		else:
			# Loggt, dass kein USB-Stick eingesteckt ist und zweigt dies auch auf dem LCD Display
			print("kein USB-Stick eingesteckt")
			write_lcd((1,7),"USB:No ",False)

