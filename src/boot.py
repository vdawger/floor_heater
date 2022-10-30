# Complete project details at https://RandomNerdTutorials.com
 
import time

import network

import esp
esp.osdebug(None)

import gc
gc.collect()

import secrets
# this is a secrets.py file that git ignores. 
# it is in same folder as boot.py. 
# it contains:
# ssid = "YOUR SSID HERE"
# password = "YOUR password here"

#from: https://github.com/rdehuyss/micropython-ota-updater
from ota_updater import OTAUpdater

station = network.WLAN(network.STA_IF)

# try to connect to phone wifi first for 5 seconds:
print("trying to connect to phone hotspot first.")
station.active(True)
startTime = time.time()
station.connect(secrets.ssid, secrets.password)
ssid = secrets.ssid
password = secrets.password
while startTime + 9 > time.time() and station.isconnected() == False:
  print( str( time.time() - startTime))
  time.sleep(1)

# if unable to connect to phone wifi, then connect to bus wifi:
if station.isconnected() == False:
  station.disconnect()
  print("connecting to backup wifi.")
  station.connect(secrets.bu_ssid, secrets.bu_password)
  ssid = secrets.bu_ssid
  password = secrets.bu_password
  startTime = time.time()
  while startTime + 10 > time.time() and station.isconnected() == False:
    print( time.time() - startTime )
    time.sleep(1)

def download_and_install_update_if_available():
    o = OTAUpdater(secrets.url)
    o.install_update_if_available_after_boot(ssid, password)

if station.isconnected() == True:
  print('Connection successful to: ' + str(ssid) )
  print(station.ifconfig())
  print("checking for updates:")
  download_and_install_update_if_available()
  print("update check complete")
  main.py
else:
  print("unable to connect. quitting.")
  quit()