# Complete project details at https://RandomNerdTutorials.com
# TO RUN: 
# cd "G:\My Drive\Cars\bus Haus\floor_heater"
# ampy --port COM5 put main.py
# to Reset:
# cd "C:\Users\willYOGA\Desktop\ESP32RET_Updater"
# .\esptool.exe --chip esp32 --port COM5 --baud 460800 write_flash -z 0x1000 esp32-ota-20220618-v1.19.1.bin

from machine import Pin
import onewire, ds18x20
import json
try:
  import usocket as socket
except:
  import socket

pump_pin = Pin(13, Pin.OUT)
pump_pin.value(1) # OFF. 1 is OFF.
heater_pin = Pin(16, Pin.OUT)
heater_pin.value(1)
ds_pin = Pin(15)
ds_sensor = ds18x20.DS18X20(onewire.OneWire(ds_pin))

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)
indoor_temps = []
outdoor_temps = []
times = []
log = []

def read_ds_sensors():
  roms = ds_sensor.scan()
  log.insert(0, 'Found DS devices: ' + str(roms) )
  ds_sensor.convert_temp()
  time.sleep(2)
  temps = []
  for rom in roms:
    temp = ds_sensor.read_temp(rom)
    if isinstance(temp, float):
      msg = int(round(temp * (9/5) + 32.0, 0)) #F, not C
      temps.append(msg)
  return temps

log.insert(0, "reading first sensors")
temps = read_ds_sensors()
if len(temps) > 1:
  indoor_temps.append(temps[0])
  outdoor_temps.append(temps[1])
  times.append( int( time.time() ) ) # full time in sec
next_time = int( time.time() )

while True:
  curTime = int( time.time() )
  if curTime > next_time: 
    temps = read_ds_sensors()
    log.insert(0, str(temps) )
    log = log[0:20]
    if len(temps) > 1:
      indoor_temps.insert(0, temps[0])
      indoor_temps = indoor_temps[0:25]
      outdoor_temps.insert(0, temps[1])
      outdoor_temps = outdoor_temps[0:25]
      times.insert(0, curTime - times[0] ) #time delta in sec
      next_time = curTime + 60 * 30 #30 minutes
  try:
    if gc.mem_free() < 102000:
      gc.collect()
    conn, addr = s.accept()
    conn.settimeout(3.0)
    log.insert(0, 'Got a connection from %s' % str(addr) )
    request = conn.recv(1024)
    conn.settimeout(None)
    request = str(request)
    #log.insert(0, 'Content = %s' % request)
    log = log[0:20]
    response = json.dumps({'times':times,'indoor':indoor_temps, 'outdoor': outdoor_temps, 'log': log})
    conn.send('HTTP/1.1 200 OK\n')
    conn.send('Content-Type: application/javascript\n')
    conn.send('Connection: close\n\n')
    conn.sendall(response)
    conn.close()
    next_time = curTime # get new temp on web refresh
  except OSError as e:
    conn.close()
    print('Connection closed')