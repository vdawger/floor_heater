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

def download_and_install_update_if_available(ssid, password):
  print("checking for update from: ", secrets.url)
  o = OTAUpdater(github_repo = secrets.url) #Check to ensure .url 
  if o.check_for_update_to_install_during_next_reboot() == True:
    #this creates a .version file to update if there's a newer version.
    print("found new update. resetting.")
    machine.reset()
  if o.install_update_if_available_after_boot(ssid, password) == True:
    # Double Check this url:
    # self.http_client.get('https://api.github.com/repos/{}/releases/latest'.format(self.github_repo))
    machine.reset()

station = network.WLAN(network.STA_IF)

# connect to primary then alternate wifi:
for ssid, password in [(secrets.ssid, secrets.password),(secrets.bu_ssid, secrets.bu_password)]:
  print("Trying to connect to ",ssid)
  station.active(True)
  startTime = time.time()
  station.connect(ssid, password)
  while startTime + 9 > time.time() and station.isconnected() == False:
    print( str(startTime - time.time( )   ))
    time.sleep(1)
  if station.isconnected() == True: #Connected to a wifi
    print('Connection successful to: ', ssid )
    print(station.ifconfig())
    print("checking for updates:")
    download_and_install_update_if_available(ssid, password)
    print("update check complete")
    main.py
  else:
    station.disconnect()

# NOT connected to either wifi:
print("unable to connect to wifi. starting my own damn wifi.")
ap = createAP()
print("broadcasting on: ", ap.config('ssid'))
main.py