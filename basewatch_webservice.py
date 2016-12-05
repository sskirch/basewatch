import web
import sensors
import sqlite3


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
    '/sensor/', 'sensor_current_analog',
    '/sensorcurrentbinary/(.*)', 'sensor_current_binary'
)

"""
urls = (
    '/users', 'list_users',
    '/users/(.*)', 'get_user'
)
"""
app = web.application(urls, globals())

sensor_gas = sensors.sensor_PCF8591('Gas',19,0,10,0)
sensor_water = sensors.sensor_water('Water', 17,None,None,0)
sensor_flame = sensors.sensor_PCF8591('Flame', 16,2,10,0)
sensor_smoke = sensors.sensor_PCF8591('Smoke', 20,1,10,0)
sensor_co = sensors.sensor_PCF8591('CO', 18,3,15,0)
sensor_temp = sensors.sensor_temp('Temp', None,None,20,0)


class sensor:        
    def GET(self, sensor_name):        
        getInput = web.input(time="current",sensor="gas",type="binary")
        print getInput.time   

class sensor_current_binary:
    def GET(self, sensor_name):        
        if not sensor_name:
            print "No Name" 
            exit()
        elif sensor_name == 'gas':
            print "gas binary"    
            
if __name__ == "__main__":
    app.run()