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

load_dotenv()

i2c = board.I2C()
i2c_0=busio.I2C(board.D1,board.D0,frequency=100000)


time.sleep(2)

try:
	sensor_bmp = adafruit_bmp280.Adafruit_BMP280_I2C(i2c)
except:
	print("Problem BMP")

try:
	sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c_0)
	sgp30.set_iaq_baseline(0x8973, 0x8AAE)
	sgp30.set_iaq_relative_humidity(celsius=22.1, relative_humidity=44)
except:
	print("Problem mit dem SGP30")

try:
	lcd = CharLCD('PCF8574',0x27)
except:
	print("no LCD available")

def write_lcd(pos,text,clear=False):
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
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		# connect() for UDP doesn't send packets
		s.connect(('10.0.0.0', 0))
		return s.getsockname()[0]
	except:
		return "no_ip"


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


def zeitregelung():
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


def connect_database():
	try:
		conn = mariadb.connect(
			user=DB_USER,
			password=DB_PASSWORD,
			host=DB_HOST,
			port=DB_PORT,
			database=DB_DATABASE,
			connect_timeout = 5)

		write_lcd((1,0),"DB:Yes",False)
		return conn
	except mariadb.Error as e:
		write_lcd((1,0),"DB:No ",False)

		print(f"Error connecting to MariaDB Platform: {e}")
		return False

def usb_available():
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


if __name__ == '__main__':


	zeitregelung()
	write_lcd((1,0),"test",True)
	conn = connect_database()
	usb_available_test = usb_available()


	while True:
		ts = time.time()
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

		dataset_no_writing = {
			"tvoc_sgp30": tvoc_sgp30()
		}

		time.sleep(5)
		write_lcd((1,0),"DB:Wri",False)
		write_lcd((1,7),"USB:Wri",False)

		if conn != False:
			"""
			columns = ', '.join("`" + str(x).replace('/', '_') + "`" for x in dataset.keys())
			values = ', '.join("'" + str(x).replace('/', '_') + "'" for x in dataset.values())
			sql = "INSERT INTO %s ( %s ) VALUES ( %s );" % ('sensor_geolabor', columns, values)
			cur.execute(sql)
			"""
			cur = conn.cursor()
			cur.execute(
		    		"INSERT INTO sensor_geolabor(eco2_sgp30,pres_qmp6988,timestamp,temp_bmp280,temp_sht30,hum_sht30,lux_tsl2561,pres_bmp280) VALUES (?,?,FROM_UNIXTIME(?),?,?,?,?,?)",
				(dataset["eco2_sgp30"],dataset["pres_qmp6988"],dataset["timestamp"],dataset["temp_bmp280"],dataset["temp_sht30"],dataset["hum_sht30"],dataset["lux_tsl2561"],dataset["pres_bmp280"])
		      	)

			conn.commit()


			print("sollte eingefügt sein")

			write_lcd((1,0),"DB:Yes",False)

		else:
			print("keine Datenbankverbindung ")
			write_lcd((1,0),"DB:No ",False)

		if usb_available_test == True:
			with open("/mnt/usb/protocoll.txt","a") as file:
				for data in dataset:
					file.write(str(dataset[data])+";")
				file.write("\n")

			write_lcd((1,7),"USB:Yes",False)
		else:
			print("kein USB-Stick eingesteckt")
			write_lcd((1,7),"USB:No ",False)

