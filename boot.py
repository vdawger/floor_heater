# Complete project details at https://RandomNerdTutorials.com
import esp
esp.osdebug(None)

import gc
gc.collect()

from WIFIconnector import WifiConnector

# connects to the networks in the secrets.py folder in order. 
# If it cannot connect to a wifi hotspot, it creates its own wifi access point
w = WifiConnector()
w.connect_to_networks()
