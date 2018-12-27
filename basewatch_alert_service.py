#!/usr/bin/env python

import time
import math
import sys
from twilio.rest import TwilioRestClient
from ConfigParser import SafeConfigParser
import smtplib
from smtplib import SMTPException
from datetime import datetime, timedelta

import sensors
import triggers

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
						

def setup():		
	global SMS_from
	global SMS_to
	global Twillio_ACCOUNT_SID
	global Twillio_AUTH_TOKEN	
	global email_from
	global email_to
	global smtp_url
	
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

#todo:  This has never been tested
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
		

sensor_gas = sensors.sensor_PCF8591('Gas',19,0,10,0)
sensor_water = sensors.sensor_water('Water', 17,None,None,0)
sensor_flame = sensors.sensor_PCF8591('Flame', 16,2,10,0)
sensor_smoke = sensors.sensor_PCF8591('Smoke', 20,1,10,0)
sensor_co = sensors.sensor_PCF8591('CO', 18,3,15,0)
sensor_temp = sensors.sensor_temp('Temp', None,None,20,0)

drain_filler_trigger = triggers.trigger('Drain Filler',27)

def loop():
	water_count = 0
	
	drain_fill_time = datetime.now() + timedelta(minutes=1)
	while True:
		global count
		print "\n" + 'Cycle Started '

    	if datetime.now() > drain_fill_time:
    		print "\n" + 'Solenoid on'
    	 	drain_filler_trigger.on()
    	 	exit()
    	 	sleep(60)
    	 	drain_filler_trigger.off()
    	 	print "\n" + 'Solenoid off'
    		drain_fill_time = datetime.now() + timedelta(hours=1)
		
		
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
			
			if sensor_temp.check_analog_alert(): 
				print "\r" + sensor_temp.sensor_name + ' Alert!!!!' + "\r"			
				smsalert(sensor_temp.sensor_name + ' Alert!!!!', str(sensor_temp.get_analog_data()))
			print "Temp: " + str(sensor_temp.sensor_que)
			
			
			
		#once every hour	
		if count % (60 * 60) == 0 and count > 0 :
			print "One Hour" 	
			#sensor_gas.logger()
			#sensor_flame.logger()
			#sensor_co.logger()			
			#sensor_smoke.logger()
			#sensor_water.logger()
			#sensor_temp.logger()
			
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
			print "\r" + sensor_water.sensor_name + 'Binary  Alert!!!!' + "\r"			
			smsalert(sensor_water.sensor_name + ' Alert!!!!', 'True')	
			
		if sensor_temp.check_binary_alert():
			print "\r" + sensor_temp.sensor_name + 'Binary  Alert!!!!' + "\r"			
			smsalert(sensor_temp.sensor_name + ' Alert!!!!', 'True')		
		
		count += 1
				
		time.sleep(1)

if __name__ == '__main__':
	try:
		setup()
		loop()
	except KeyboardInterrupt: 
		pass	







