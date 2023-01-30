# Complete project details at https://RandomNerdTutorials.com
 
import time
import machine

import network

import esp
esp.osdebug(None)

import gc
gc.collect()

import secrets
# this is a secrets.py file that git ignores. 
# it is in same folder as boot.py. 
# See secrets_template.py


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
  print("checking for update from: ", secrets.url)
  o = OTAUpdater(secrets.url)
  if o.check_for_update_to_install_during_next_reboot() == True:
    #this creates a .version file to update if there's a newer version.
    print("found new update. resetting.")
    machine.reset()
  if o.install_update_if_available_after_boot(ssid, password) == True:
    #reboot if new version installed. otherwise, do not. 
    machine.reset()

def createAP():
  ap = network.WLAN(network.AP_IF) # create access-point interface
  ap.config(ssid=secrets.ap_ssid, key=secrets.ap_password, max_clients=4) # set the SSID of the access point, password, and set how many clients can connect to the network
  # from: https://docs.micropython.org/en/latest/library/network.WLAN.html
  ap.active(True) # activate the interface
  return ap

if station.isconnected() == True:
  print('Connection successful to: ' + str(ssid) )
  print(station.ifconfig())
  print("checking for updates:")
  download_and_install_update_if_available()
  print("update check complete")
  main.py
else: # NOT connected to either wifi:
  print("unable to connect to wifi. starting my own damn wifi.")
  ap = createAP()
  print("broadcasting on: ", ap.config('ssid'))
  main.py