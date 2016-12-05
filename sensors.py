'''
Created on Dec 5, 2016

@author: sskirch
'''
import sqlite3
import PCF8591 as ADC
import RPi.GPIO as GPIO
import os
import glob
import time
from collections import deque
from abc import ABCMeta, abstractmethod
import weakref


#Class to handle sensor on the PCF8591 ADDA.  Or anything that just uses one GPIO
class sensor:
    GPIO_Pin = 0
    AD_pin = 0    
    sensor_que = None
    que_size = 10
    sensor_name = None
    sensor_status = None
    sensor_change_threshold = None
    alert_count = None
    GPIO_alert = 0
    
    instances = []
    
    
    def __init__(self, sensor_name_in, GPIO_Pin_in, AD_pin_in, threshold_in, GPIO_Alert_in):
        self.sensor_name = sensor_name_in
        self.GPIO_Pin = GPIO_Pin_in
        self.AD_pin = AD_pin_in        
        self.sensor_change_threshold = threshold_in
        if GPIO_Pin_in != None: GPIO.setup(GPIO_Pin_in, GPIO.IN)
        self.sensor_que = deque()
        self.alert_count = 0;
        self.GPIO_alert = GPIO_Alert_in        
        self.__class__.instances.append(self)
    
                    
    def logger(self,sensor_name,analog_data,binary_data):
        conn = sqlite3.connect('sensor_data.db')
        dbcur = conn.cursor()        
        try:
            dbcur.execute('INSERT INTO sensor_logs(data_time, sensor_name, analog_data, gpio_data) VALUES(?,?,?,?)', (time.time(), self.sensor_name, self.get_analog_data(), self.check_binary_alert()))
            conn.commit()
        except sqlite3.Error as er:
            print 'er:', er.message                
        conn.close()
        
    def __avg(self):
        total=0        
        if len(self.sensor_que) < self.que_size:
            return None        
        for i in self.sensor_que:
                total+=i    
                                    
        return total/self.que_size
                
    def __add(self,input_data):
        self.sensor_que.append(input_data)
        if len(self.sensor_que) < self.que_size + 1: return
        self.sensor_que.popleft()        
        
    """
    Check to see if there is a sudden change in the analog data.
    Percent difference threshold is set when object is instantiated
    i.e, There is a 10% difference between the current reading and the last ten readings. 
    """ 
    @abstractmethod    
    def check_analog_alert(self): pass
        
    @abstractmethod    
    def check_binary_alert(self): pass
    
    @abstractmethod
    def get_analog_data(self): pass
   
    
    
class sensor_PCF8591(sensor):                      
    def get_analog_data(self):
        return ADC.read(self.AD_pin)    
   
    def check_analog_alert(self):
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
        

"""
The water sensor for this project is a simple transitor with a pull up
resistor on a GPIO pin.  So, no analog alert.
"""
class sensor_water(sensor):
    water_count = 0
    def get_analog_data(self):
        return None    
        
    def check_analog_alert(self):
        return False
        
    def check_binary_alert(self):  
        #Check five times to make sure the signal is constant and correct
        self.water_count+=1
        if not GPIO.input(self.GPIO_Pin) == self.GPIO_alert:
            self.water_count = 0
            return False
        else:    
            if self.water_count > 5:
                self.water_count = 0
                return True
                
        
            

"""
The temp sensor is a DS18B20 digital thermometer.  It uses a 1 wire protocol on GPIO 4.
Analog data only.  Binary alert is triggered by a tempeture range in fahrenheit.
"""   

class sensor_temp(sensor):
    temp_high = 100
    temp_low = 45
    
    def __read_temp_raw(self):    
        base_dir = '/sys/bus/w1/devices/'
        device_folder = glob.glob(base_dir + '28*')[0]
        device_file = device_folder + '/w1_slave'
    
        f = open(device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def __read_temp(self):
        lines = self.__read_temp_raw()
        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            lines = self.__read_temp_raw()
        equals_pos = lines[1].find('t=')
        
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0    
            temp_f = temp_c * 9.0 / 5.0 + 32.0
            return {'c':temp_c, 'f':temp_f}

    def get_temp(self):
        return self.__read_temp()['f']    
        
    def get_analog_data(self):
        return self.get_temp()    
        
    def check_binary_alert(self): #the Temp sensor is unique and use the 1 wire protocol on GPIO 4
        tempature = self.get_temp()
        print tempature
        if tempature > self.temp_high or tempature < self.temp_low:
            return True
        return False       
               
    
"""    
# Setup Sensors    
"""

#For Annalog PCF8591     
ADC.setup(0x48)
#For Binary PCF8591
GPIO.setmode(GPIO.BCM)

#for 1 Wire DS18B20 digital thermometer
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')


"""
    Set up SQLite DB for logging
"""
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

print len(sensors.sensor.instances)

