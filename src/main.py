# Complete project details at https://RandomNerdTutorials.com
# TO RUN: 
# cd "C:\github_stored\floor_heater"
# ampy --port COM5 put main.py
# to Reset:
# cd "C:\Users\willYOGA\Desktop\ESP32RET_Updater"
# .\esptool.exe --chip esp32 --port COM5 --baud 460800 write_flash -z 0x1000 esp32-ota-20220618-v1.19.1.bin

from machine import Pin
import onewire, ds18x20
import time
import json
import network
import esp
import secrets
esp.osdebug(None)
import gc
gc.collect()

import tinyweb # https://github.com/belyalov/tinyweb

from micrologger import MicroLogger
from file_updater import FileUpdater

MAX_TEMPS_TO_KEEP = 25 #Max number of temperature records to keep
TIME_BETWEEN_TEMPS = 60 * 60 # 1 hour between temp reads.
READ_TEMPS = True # read temperatures every time between Temps
CIRCUIT_SWITCH_TIME = 90 #number of seconds to run each individual circuit
AUTO_SWITCH_CIRCUIT = True # switch each circuit automatically

valve_pins = {"Battery": 23 , "Bedroom": 22, "Bunks":21, "Bathroom":19, "Front":18} # OUT Is closed. 
heat_sources = {"electric_heater":3, "engine":9} #OUT is closed
valve_status = {} # Valve_Name : "Closed"
statuses = {"Open","Closed"}
pump_pin = Pin(13, Pin.OUT) #12v pump ON
pump_pin = Pin(13, Pin.IN) # OFF
temps = []
log = []

# Temperature sensors:
ds_pin = Pin(5)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

# Utility to fill in statuses with closed to start:
def init_valve_status():
    for v in valve_pins.keys():
        valve_status[v] = "Closed"
    for h in heat_sources.keys():
        valve_status[h] = "Closed"

#convert Celsius to Farenheit:
def CtoF(t):
    return int(round(t * (9/5) + 32.0, 0))

# update current temps:
async def read_ds_sensors():
    roms = ds_sensor.scan()
    log.insert(0, 'Found DS devices: ' + str(roms) )
    ds_sensor.convert_temp()
    await asyncio.sleep(.5)
    try:
        indoor = CtoF( ds_sensor.read_temp(bytearray(b'(\xcd\x0c@L \x01\x1f')) )
    except:
        indoor = ""
    try:
        outdoor = CtoF( ds_sensor.read_temp(bytearray(b'(HblL \x01\xcf')) )
    except:
        outdoor = ""
    temps.insert(0, ( (int( time.time() ), indoor, outdoor)) )
    temps = temps[:MAX_TEMPS_TO_KEEP]

def pin_to_status(pin_num, status):
    """ Open or Close a valve based on status"""
    if status == "Closed":
        Pin(pin_num, Pin.OUT)
    else:
        Pin(pin_num, Pin.IN)

def update_valve(valve_name,status):
    if valve_name not in statuses or status not in statuses:
        return {"message":"Wrong valve_name or status"}, 404
    valve_status[valve_name] = status
    if valve_name in valve_pins:
        pin_to_status(valve_pins[valve_name], status)
    else:
        pin_to_status(heat_sources[valve_name], status)

class TemperatureList():
    def get(self, data):
        """Return list of all temps"""
        return {"temps":temps}, 201
    def post(self,data):
        """Request a temperature refresh"""
        read_ds_sensors()
        return {"message","Got new Temps"}, 201

class Valve_Status_List():
    def get(self,data):
        return {"valve_status_list":valve_status}, 201

class Wifi_Settings_List():
    def get(self,data):
        return {"wifi_settings_list":secrets.network_data.append( (secrets.ap_ssid, secrets.ap_password) )}

class Valve():
    def not_exists(self):
        return {'message':'No such Valve'}, 404
    
    def get(self, data, valve_name, status):
        """Get status of requested valve"""
        if valve_name not in valve_status:
            return self.not_exists()
        if status in statuses:
            update_valve(valve_name, status)
            return {valve_name: valve_status[valve_name]}, 201
        # no status or incorrect status, so return the current status: 
        return {valve_name: valve_status[valve_name]}, 201

class Pump():  
    def get(self, data, on):
        """Get or set status of pump"""
        if on == "On":
            pump_pin = Pin(13, Pin.OUT)
            return {"pump": "On"}, 201
        elif on == "Off":
            pump_pin = Pin(13, Pin.IN)
            return {"pump":"Off"}, 201
        #no on variable, so return current status
        if pump_pin.value() == 0:
            return {"pump": "Off"}, 201
        return {"pump": "On"}, 201

# Change wifi settings:
class Wifi_Settings():
    self.prefs = secrets.network_data.append( (secrets.ap_ssid, secrets.ap_password) )
    self.prefs = [val for pair in self.prefs for val in pair]

    def get(self, data, old_val, new_val):
        """Change value of selected pref"""
        if old_val not in self.prefs:
            return {'message':'No such pref'}, 404
        f = FileUpdater(old_file='secrets.py',new_file='new_secrets.py')
        if f.replace_str_in_file(old_val, new_val):
            return {"message":old_val+" updated to "+new_val+". Machine reset to see changes"}, 201
        return {"message":"Failed to update pref"}, 404

# RESTAPI: System status
class Machine():
    def get(self, data, reset):
        if reset == "reset":
            machine.reset()
        mem = {'mem_alloc': gc.mem_alloc(),
                'mem_free': gc.mem_free(),
                'mem_total': gc.mem_alloc() + gc.mem_free()}
        sta_if = network.WLAN(network.STA_IF)
        ifconfig = sta_if.ifconfig()
        net = {'ip': ifconfig[0],
                'netmask': ifconfig[1],
                'gateway': ifconfig[2],
                'dns': ifconfig[3]
                }
        return {'memory': mem, 'network': net}, 201

# Get temperature every time interval:
async def timed_temp_logging():
    global READ_TEMPS
    while READ_TEMPS:
        await read_ds_sensors()
        await asyncio.sleep(TIME_BETWEEN_TEMPS)

# cycle through valve_pins to keep all zones warm:
async def auto_valve_cycle():
    global CIRCUIT_SWITCH_TIME
    cur = 0
    valve_names = list(valve_pins.keys())
    num_valves = len(valve_names)
    last = num_valves-1
    while AUTO_SWITCH_CIRCUIT:
        v_name = valve_names[cur]
        last_v_name = valve_names[last]
        cur = (cur + 1) % (num_valves -1 )
        last = (last + 1) % (num_valves -1 )
        update_valve(v_name,"Open")
        update_valve(last_v_name, "Closed")
        asyncio.sleep(CIRCUIT_SWITCH_TIME)

async def run_background_and_webserver():
    app = tinyweb.webserver(debug=True)
    app.add_resource(TemperatureList, '/temps')
    app.add_resource(Valve_Status_List, '/valve_statuses')
    app.add_resource(Valve, '/valve/<valve_name>/<status>')
    app.add_resource(Pump, "/pump/<on>")
    app.add_resource(Machine, '/machine/<reset>')
    station = network.WLAN(network.STA_IF)
    ap = network.WLAN(network.AP_IF)
    ip = "127.0.0.1"
    if station.isconnected() == True:
        ip = station.ifconfig()[0]
    elif ap.active():
        ip = ap.ifconfig()[0]
    async with asyncio.TaskGroup() as tg:
        tg.create_task(timed_temp_logging())
        tg.create_task(auto_valve_cycle())
        tg.create_task( app.run(host=ip, port=8081) )

asyncio.run(run_background_and_webserver())

