# Complete project details at https://RandomNerdTutorials.com
# TO RUN: 
# cd "G:\My Drive\Cars\bus Haus\floor_heater"
# ampy --port COM5 put test_run_alt_heater_pin.py
# to Reset:
# cd "C:\Users\willYOGA\Desktop\ESP32RET_Updater"
# .\esptool.exe --chip esp32 --port COM5 --baud 460800 write_flash -z 0x1000 esp32-ota-20220618-v1.19.1.bin

from machine import Pin
import onewire, ds18x20
import time
import json
try:
  import usocket as socket
except:
  import socket
import network
import esp
esp.osdebug(None)
import gc
gc.collect()
import secrets

"""
print("Connecting to wifi")
station = network.WLAN(network.STA_IF)
station.active(True)
startTime = time.time()
station.connect(secrets.bu_ssid, secrets.bu_password)
while startTime + 9 > time.time() and station.isconnected() == False:
  print( str( time.time() - startTime))
  time.sleep(1)
if station.isconnected() == True:
  print('Connection successful to: ' + str(secrets.bu_ssid) )
  print(station.ifconfig())
"""
valves = {"batt": 23 , "bedroom": 22, "bunks":21, "bathroom":19, "front:":18} # OUT Is closed. 
valve_names = list(valves.keys())
pump_pin = Pin(17, Pin.OUT) #pump ON
pump_pin = Pin(17, Pin.IN) #pump OFF
pump_pin = Pin(17, Pin.OUT) #pump ON
heater_valve = Pin(32, Pin.IN) # OPEN
ds_pin = Pin(5)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))
indoor = 0
outdoor = 0

def read_ds_sensors(lastTime):
    roms = ds_sensor.scan()
    ds_sensor.convert_temp()
    time.sleep(.75)
    try: 
        global indoor
        global outdoor
        indoor = int( round( ds_sensor.read_temp(roms[0]) * (9/5) + 32.0, 0 ) )
        outdoor = int( round( ds_sensor.read_temp(roms[1]) * (9/5) + 32.0, 0 ) )
        print("Indoor: " + str( indoor ) + "F  Outdoor: " + str( outdoor ) + "F Time: " + str( int( time.time() ) - lastTime ) )
        return time.time()
    except:
        print("failed to get temps. continuing.")
        return 0

lastTime = int( time.time() )
"""
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(2)
"""
pump_on = 1
valve_num = 0
current_valve_name = valve_names[valve_num]

while True:
    """
    try:
        if gc.mem_free() < 102000:
            gc.collect()
            print("collecting garbage")
        print("accepting")
        conn, addr = s.accept()
        print("waiting for 3 sec")
        conn.settimeout(0.5)
        print("done waiting")
        print( 'Got a connection from %s' % str(addr) )
        request = conn.recv(1024)
        conn.settimeout(None)
        request = str(request)
        pump_on = request.find('pump=on')
        pump_off = request.find('pump=off')
        pump_alt = request.find('pump=alt')
        heater_on = request.find('htr=on')
        heater_off = request.find('htr=off')
        conn.send('HTTP/1.1 200 OK\n')
        conn.send('Content-Type: application/javascript\n')
        conn.send('Connection: close\n\n')
        response = json.dumps({'indoor':indoor, 'outdoor': outdoor})
        conn.sendall(response)
        conn.close()
    except OSError as e:
        conn.close()
        print("issue with connection")
        print(e)
        pass
    """      
    newTime = read_ds_sensors( lastTime )
    if newTime > 0:
        lastTime = newTime
    if pump_on == 1: 
        pump_pin = Pin(17, Pin.OUT) #pump ON
        heater_valve = Pin(32, Pin.IN) # OPEN
        if valve_num < len(valve_names):
          valve_num += 1
        else: 
          valve_num = 0
        new_valve_name = valve_names[valve_num]
        #open new valve
        print("Opening: ", new_valve_name)
        Pin(valves[new_valve_name], Pin.IN )  #open
        #close old valve:
        print("closing: ", current_valve_name)
        Pin(valves[current_valve_name], Pin.OUT ) #closed
        #swap names:
        current_valve_name = new_valve_name
        print("Heater ON, Pump ON. Current:", current_valve_name, " new: ", new_valve_name)
        for i in range(0,30):
          print(30-i)
          time.sleep(1)
    else: 
        pump_pin = Pin(17, Pin.IN)
        print("Heater ON, Pump oFF")
        time.sleep(120)