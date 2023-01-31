# Complete project details at https://RandomNerdTutorials.com
# TO RUN: 
# cd "G:\My Drive\Cars\bus Haus\floor_heater"
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
esp.osdebug(None)
import gc
gc.collect()

import tinyweb # https://github.com/belyalov/tinyweb

MAX_TEMPS_TO_KEEP = 25 #Max number of temperature records to keep
TIME_BETWEEN_TEMPS = 60 * 60 # 1 hour between temp reads.
CIRCUIT_SWITCH_TIME = 90 #number of seconds to run each individual circuit
AUTO_SWITCH_CIRCUIT = True # switch each circuit automatically

valves = {"Battery": 23 , "Bedroom": 22, "Bunks":21, "Bathroom":19, "Front":18} # OUT Is closed. 
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
  for v in valves.keys():
    valve_status[v] = "Closed"
  for h in heat_sources.keys():
    valve_status[h] = "Closed"

#convert Celsius to Farenheit:
def CtoF(t):
  return int(round(t * (9/5) + 32.0, 0))

# update current temps:
def read_ds_sensors():
  roms = ds_sensor.scan()
  log.insert(0, 'Found DS devices: ' + str(roms) )
  ds_sensor.convert_temp()
  time.sleep(.5)
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
  if valve_name in valves:
    pin_to_status(valves[valve_name], status)
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
    return {"valves":valve_status}, 201

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

class ValveHandler():
  def __init__(self):
    """Runs Valves and eventually CAN in background
    """
    self.loop = asyncio.get_event_loop()
    self.read_temps = True
  async def _timed_temp_logging():
    while self.read_temps:
      read_ds_sensors()
      time.sleep(TIME_BETWEEN_TEMPS)
  async def _auto_valve_cycle():
    i = 0
    while AUTO_SWITCH_CIRCUIT:
      for v in valves.keys():
        #TODO: repeat through valve names and open next one, then close last one every CIRCUIT_SWITCH_TIME
        pass
  def run(self):
    self._timed_temps = self._timed_temp_logging()
    self.loop.create_task(self._timed_temps)
    self.loop.run_forever()


def run():
  app = tinyweb.webserver(debug=True)
  app.add_resource(TemperatureList, '/temps')
  app.add_resource(Valve_Status_List, '/valves')
  app.add_resource(Valve, '/valve/<valve_name>/<status>')
  app.add_resource(Pump, "/pump/<on>")
  app.add_resource(Machine, '/machine/<reset>')
  station = network.WLAN(network.STA_IF)
  ip = "127.0.0.1"
  if station.isconnected() == True:
    ip = station.ifconfig()[0]
  app.run(host=ip, port=8081)

run()