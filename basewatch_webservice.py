import web
import sensors
import sqlite3
import copy
from tornado.test import concurrent_test


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


urls = (    
    '/sensor/', 'getsensor'
)

app = web.application(urls, globals())

print len(sensors.sensor.instances)



print len(sensors.sensor.instances)

class getsensor:        
    def GET(self):        
        getInput = web.input(timing="current",sensorname="gas",datatype="binary")
        
        timing = getInput.timing
        sensor_name = getInput.sensorname
        data_type = getInput.datatype
        
        """
        Instantiate the right class based on sensor name.
        Possible sensors" gas, water, flame, smoke, co, and temp
        """
        if sensor_name == 'gas':
            sensor = sensors.sensor_PCF8591('Gas',19,0,10,0)
        elif sensor_name == 'water':
            sensor = sensors.sensor_water('Water', 17,None,None,0)
        elif sensor_name == 'flame':
            sensor = sensors.sensor_PCF8591('Flame', 16,2,10,0)
        elif sensor_name == 'smoke':
            sensor = sensors.sensor_PCF8591('Smoke', 20,1,10,0)
        elif sensor_name == 'co':
            sensor = sensors.sensor_PCF8591('CO', 18,3,15,0)
        elif sensor_name == 'temp':
            sensor = sensors.sensor_temp('Temp', None,None,20,0)
        else:
            print "Error: Invalid sensor name."
            return "Error: Invalid sensor name."    
        
        """
        Get by type.
        Possible types: binary, analog.
        Binary is an alert that is either on of off.  (true or false)
        Analog is a number returned from the sensor.  All the numbers are arbitrary,
        except for the temp sensor, which is returning fahrenheit.          
        
        """           
        dt = ''           
        if data_type == 'binary':
            dt = 'binary'
        elif data_type == 'analog':
            dt = 'analog'
        else:
            print "Error: Invalid data type."
            return "Error: Invalid data type."
        
        time_in_seconds = 
        if timing.isdigit():
            time_in_seconds = int(timing)
        else:    
            timings = {'current': 0 ,
                       'day': 86400,
                       '2days': (86400 * 2),                   
                       '3days': (86400 * 3),                   
                       '4days': (86400 * 4),                   
                       '5days': (86400 * 5),                   
                       '6days': (86400 * 6),                   
                       'week': (86400 * 7),   
                       '1week': (86400 * 7 * 1),
                       '2weeks': (86400 * 7 * 2),
                       '3weeks': (86400 * 7 * 3),
                       '4weeks': (86400 * 7 * 4),
                       '2months': (86400 * 30 * 2),
                       '3months': (86400 * 30 * 3),
                       '4months': (86400 * 30 * 4),
                       '5months': (86400 * 30 * 5),
                       '6months': (86400 * 30 * 6),
                       }
        
        time_in_seconds = timings[timing]
        
        if time_in_seconds == None:
            print "Error: Invalid timing."
            return "Error: Invalid Timing."
        
        
        
        
        
        
          
        
        
           

class sensor_current_binary:
    def GET(self, sensor_name):        
        if not sensor_name:
            print "No Name" 
            exit()
        elif sensor_name == 'gas':
            print "gas binary"    
            
if __name__ == "__main__":
    app.run()