import web
import sensors
import sqlite3
import copy


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
        getInput = web.input(time="current",sensor="gas",type="binary")
        
        if getInput.sensor == 'gas':
            sensor_gas = sensors.sensor_PCF8591('Gas',19,0,10,0)
        elif getInput.sensor == 'gas':
            sensor_water = sensors.sensor_water('Water', 17,None,None,0)
        elif getInput.sensor == 'gas':
            sensor_flame = sensors.sensor_PCF8591('Flame', 16,2,10,0)
        elif getInput.sensor == 'gas':
            sensor_smoke = sensors.sensor_PCF8591(
        elif getInput.sensor == 'gas':'Smoke', 20,1,10,0)
            sensor_co = sensors.sensor_PCF8591('CO', 18,3,15,0)
        elif getInput.sensor == 'gas':
            sensor_temp = sensors.sensor_temp('Temp', None,None,20,0)
        elif getInput.sensor == 'gas':
        
        
        
        #print "sensor_obj = copy.deepcopy(sensor_" +  getInput.sensor + ")"
        
        #exec("sensor_obj = copy.deepcopy(sensor_" +  getInput.sensor + ")")
        
        #exec("return_data = sensor_obj.get_" +  getInput.type + "_data()")        
        
        
        
        print getInput.time
        print getInput.sensor
        print getInput.type
        
        print len(sensors.sensor.instances)
        
        return_data = ''
        for instance in sensors.sensor.instances:
            return_data += instance.sensor_name + '.'
                
        return '<br>' + return_data
        
        
           

class sensor_current_binary:
    def GET(self, sensor_name):        
        if not sensor_name:
            print "No Name" 
            exit()
        elif sensor_name == 'gas':
            print "gas binary"    
            
if __name__ == "__main__":
    app.run()