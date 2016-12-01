#!/usr/bin/env python

import PCF8591 as ADC
import RPi.GPIO as GPIO
import time
import math
import os
import glob
import time
import sys
import sqlite3
from twilio.rest import TwilioRestClient
from collections import deque
from ConfigParser import SafeConfigParser
import smtplib
from smtplib import SMTPException


ADC.setup(0x48)
GPIO.setmode(GPIO.BCM)

conn = None
count = 0
msg_time = {}

SMS_from = None
SMS_to = None
Twillio_ACCOUNT_SID = None
Twillio_AUTH_TOKEN = None

email_from = None
email_to = None
smtp_url = None


def read_temp_raw():	
	base_dir = '/sys/bus/w1/devices/'
	device_folder = glob.glob(base_dir + '28*')[0]
	device_file = device_folder + '/w1_slave'
	
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines

def read_temp():
	lines = read_temp_raw()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0	
		temp_f = temp_c * 9.0 / 5.0 + 32.0
		return {'c':temp_c, 'f':temp_f}


def temp_reader():
	def get_temp():
		return read_temp()['f']	
	return get_temp

def log_entry(sensor_name,analog_data,binary_data):	
		conn = sqlite3.connect('sensor_data.db')
		dbcur = conn.cursor()
		
		try:
			dbcur.execute('INSERT INTO sensor_logs(data_time, sensor_name, analog_data, gpio_data) VALUES(?,?,?,?)', (time.time(), sensor_name, analog_data, binary_data))
			conn.commit()
		except sqlite3.Error as er:
			print 'er:', er.message	
		conn.close()


#Class to handle sensors on the PCF8591 ADDA.  Or anything that just uses one GPIO
class Sensors:
	GPIO_Pin = 0
	AD_pin = 0	
	sensor_que = None
	que_size = 10
	sensor_name = None
	sensor_status = None
	sensor_change_threshold = None
	alert_count = None
	GPIO_alert = 0
	alt_function = None
	
	def __init__(self, sensor_name_in, GPIO_Pin_in, AD_pin_in, threshold_in, GPIO_Alert_in):
		self.sensor_name = sensor_name_in
		self.GPIO_Pin = GPIO_Pin_in
		self.AD_pin = AD_pin_in		
		self.sensor_change_threshold = threshold_in
		GPIO.setup(GPIO_Pin_in, GPIO.IN)
		self.sensor_que = deque()
		self.alert_count = 0;
		self.GPIO_alert = GPIO_Alert_in
					
	def logger(self):
		log_entry(self.sensor_name, self.get_analog_data(), self.check_binary_alert())
		
	def avg(self):
		total=0		
		if len(self.sensor_que) < self.que_size:
			return None		
		for i in self.sensor_que:
				total+=i	
									
		return total/self.que_size
				
	def add(self,input_data):
		self.sensor_que.append(input_data)
		if len(self.sensor_que) < self.que_size + 1: return
		self.sensor_que.popleft()
		
	def get_analog_data(self):
		return ADC.read(self.AD_pin)	
		
	"""
	Check to see if there is a sudden change in the analog data.
	Percent difference threshold is set when object is instantiated
	i.e, There is a 10% difference between the current reading and the last ten readings. 
	"""	
	def	check_analog_alert(self):
		before = self.avg()
		sensor_data = self.get_analog_data()		
		self.add(sensor_data)
		if before is None or sensor_data is None : return False			
		percent_diff = ((float(sensor_data)/float(before)) * 100) - 100
		percent_diff = abs(percent_diff)
		print 'Percent Diff ' + str(percent_diff)
		if percent_diff >= self.sensor_change_threshold: return True		
		return False
		
	def check_binary_alert(self):
		if(GPIO.input(self.GPIO_Pin) == self.GPIO_alert):
			return True
		return False
	
	def check_alt(self):
		return self.alt_function
									

def setup():		
	global SMS_from
	global SMS_to
	global Twillio_ACCOUNT_SID
	global Twillio_AUTH_TOKEN	
	global email_from
	global email_to
	global smtp_url
	
		
	os.system('modprobe w1-gpio')
	os.system('modprobe w1-therm')

	conn = sqlite3.connect('sensor_data.db')

	dbcur = conn.cursor()
	check_table = "SELECT name FROM sqlite_master WHERE type='table' AND name='sensor_logs'"
	create_table = "CREATE TABLE sensor_logs (data_time REAL, sensor_name VARCHAR(255), analog_data REAL, gpio_data BOOLEAN)"
	if not dbcur.execute(check_table).fetchone():
		print "Creating sensor_logs table"
		dbcur.execute(create_table)
		if not dbcur.execute(check_table).fetchone():
			print "Unable to create sensor_log table"
			exit()
	
	conn.close()
	
	config = SafeConfigParser()
	config.read('config.ini')
	
	SMS_from = config.get('sms', 'sms_from')
	SMS_to = config.get('sms', 'sms_to')
	Twillio_ACCOUNT_SID = config.get('sms', 'account_sid')
	Twillio_AUTH_TOKEN = config.get('sms', 'auth_token')	
	email_from = config.get('email', 'email_from')
	email_to = config.get('email', 'email_to')
	smtp_url = config.get('email', 'url')
	

def check_msg(msg, force):
	global count
	global msg_time	
	
	if count < 600 and not force :                                	#Don't do anything if for the first 10 minutes.  So we can get a good baseline.
		return True
	elif msg_time.has_key(msg) == False:						  	#If the key does not exist, then this is the first time we are sending the message.  Create the key with the time and send	
		msg_time.update({msg:time.time()})	
	elif (time.time() - msg_time[msg]) < 3600 and not force:		#Only allow messages to be sent once an hour.
		return True
	else:
		msg_time[msg] = time.time()
		
	return False		


def smsalert(msg, data, force=False):		
	global count
	global msg_time	
	global SMS_from
	global SMS_to
	global Twillio_ACCOUNT_SID
	global Twillio_AUTH_TOKEN	
	
	if check_msg(msg,force): return
	
	client = TwilioRestClient(Twillio_ACCOUNT_SID, Twillio_AUTH_TOKEN)
	client.messages.create(
        	to=SMS_to,
	        from_=SMS_from,
        	body=msg + ' ' + data,
		)
	print ''
	print 'SMS sent ' + msg
	print ''

def emailalert(msg, data, force=False):		
	global count
	global msg_time
	global email_from
	global email_to	
	
	if check_msg(msg,force): return
			
	message = """From: From Person <""" +  email_from + """>
	To: To Person <""" +  email_to + """>
	Subject: """ +  msg + """

	This is a test e-mail message.
	"""

	try:
		smtpObj = smtplib.SMTP('localhost')
		smtpObj.sendmail(email_from, email_to, message)         
		print "Successfully sent email: " + msg
	except SMTPException:
		print "Error: unable to send email"
		print ''
		

sensor_gas = Sensors('Gas',19,0,10,0)
sensor_water = Sensors('Water', 17,None,1,0)
sensor_flame = Sensors('Flame', 16,2,10,0)
sensor_smoke = Sensors('Smoke', 20,1,10,0)
sensor_co = Sensors('CO', 18,3,15,0)


def loop():
	water_count = 0
	while True:
		global count
		
		print "\n" + 'count: ' + str(count)
							
		if (count == 0 or (count % 86400 == 0)) : smsalert('Basewatcher Heartbeat', '', True)  # Send heartbeat on startup and once a day
		
		#once every 10 minutes
		if count % (60 * 10) == 0 and count > 0 : 
			print "Ten Minutes"
			if sensor_flame.check_analog_alert(): 
				print "\r" + sensor_flame.sensor_name + ' Alert!!!!' + "\r"
				smsalert(sensor_flame.sensor_name + ' Alert!!!!', str(sensor_flame.get_analog_data()))	
			print "flame: " + str(sensor_flame.sensor_que)
							
			if sensor_gas.check_analog_alert(): 
				print "\r" + sensor_gas.sensor_name + ' Alert!!!!' + "\r"			
				smsalert(sensor_gas.sensor_name + ' Alert!!!!', str(sensor_gas.get_analog_data()))
			print "gas: " + str(sensor_gas.sensor_que)
			
			if sensor_co.check_analog_alert(): 
				print "\r" + sensor_co.sensor_name + ' Alert!!!!' + "\r"			
				smsalert(sensor_co.sensor_name + ' Alert!!!!', str(sensor_co.get_analog_data()))
			print "CO: " + str(sensor_co.sensor_que)	
			
			if sensor_smoke.check_analog_alert(): 
				print "\r" + sensor_smoke.sensor_name + ' Alert!!!!' + "\r"			
				smsalert(sensor_smoke.sensor_name + ' Alert!!!!', str(sensor_smoke.get_analog_data()))
			print "Smoke: " + str(sensor_smoke.sensor_que)
			
			#the Temp sensor is unique and use the 1 wire protocol on GPIO 4
			temp_high = 100
			temp_low = 45
			tempature = read_temp()['f']
			if tempature > temp_high or tempature < temp_low:		
				print "Temp!: " + str(tempature)
				smsalert("Temp!: " , str(tempature))
						
			log_entry("Temp",tempature,None)
			
		#once every hour	
		if count % (60 * 60) == 0 and count > 0 :
			print "One Hour" 	
			sensor_gas.logger()
			sensor_flame.logger()
			sensor_co.logger()			
			sensor_smoke.logger()
			
		#once every Minute	
		#if (count % 60 == 0 and count > 0) :
		#	print "One Minute"
						
						
		#Once Every Second: 				
		if sensor_flame.check_binary_alert() : 
			print "\r" + sensor_flame.sensor_name + 'Binary Alert!!!!' + "\r"
			smsalert(sensor_flame.sensor_name + ' Alert!!!!', 'True')	
						
		if sensor_gas.check_binary_alert(): 
			print "\r" + sensor_gas.sensor_name + 'Binary Alert!!!!' + "\r"			
			smsalert(sensor_gas.sensor_name + ' Alert!!!!', 'True')
		
		if sensor_co.check_binary_alert(): 
			print "\r" + sensor_co.sensor_name + 'Binary  Alert!!!!' + "\r"			
			smsalert(sensor_co.sensor_name + ' Alert!!!!', 'True')
		
		if sensor_smoke.check_binary_alert(): 
			print "\r" + sensor_smoke.sensor_name + 'Binary  Alert!!!!' + "\r"			
			smsalert(sensor_smoke.sensor_name + ' Alert!!!!', 'True')		
									
		if sensor_water.check_binary_alert():
			print "Maybe Water"
			
			water_count += 1      
			#Check ten times to make sure the signal is constant and correct 
			if not sensor_water.check_binary_alert():
				water_count = 0
				
			if water_count > 9:		
				smsalert("Water!",'')
				print sensor_water.sensor_name + ': ' + str(sensor_water.check_binary_alert())
				water_count = 0
		
		
		count += 1
				
		time.sleep(1)

if __name__ == '__main__':
	try:
		setup()
		loop()
	except KeyboardInterrupt: 
		pass	







