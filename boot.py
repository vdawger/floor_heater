# Complete project details at https://RandomNerdTutorials.com
import esp
esp.osdebug(None)

import gc
gc.collect()

from src import WIFIconnector

# connects to the networks in the secrets.py folder in order. 
# If it cannot connect to a wifi hotspot, it creates its own wifi access point
w = WIFIconnector.WifiConnector()
w.connect_to_networks()

src.main.py