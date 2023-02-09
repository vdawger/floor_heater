# Complete project details at https://RandomNerdTutorials.com
 
import time
import machine

import esp
esp.osdebug(None)

import gc
gc.collect()

from src import WIFIconnector
from src import secrets
from src import PrefUpdater

#from: https://github.com/rdehuyss/micropython-ota-updater

ssid, password = WIFIconnector.connect_to_networks()

if ssid == "": # not connected to wifi, so create access point and prompt for wifi info updates:
  p = PrefUpdater()
  p.prompt_for_updates()
else:
  src.main.py