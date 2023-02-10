import secrets
import network
from ota_updater import OTAUpdater
from micrologger import MicroLogger
# this is a secrets.py file that git ignores. 
# it is in same folder as boot.py. 
# See secrets_template.py

class WifiConnector():
    def __init__(self):
        self.m = MicroLogger()

    def download_and_install_update_if_available(self, ssid, password):
        print("checking for update from: ", secrets.url)
        self.m.log("checking for update from: ", secrets.url)
        o = OTAUpdater(github_repo = secrets.url, secrets_file="secrets.py", main_dir='/', github_src_dir="src")  
        if o.install_update_if_available_after_boot() == True:
            print("Update installed. Advise reboot")
            self.m.log("Update installed. Advise reboot")
        elif o.check_for_update_to_install_during_next_reboot() == True:
            #this creates a .version file to update if there's a newer version.
            print("found new update. advise reboot.")
            self.m.log("found new update. advise reboot.")

    def connect_to_networks(self) -> bool:
        """ will attempt to connect to the networks in the secrets file for 10 seconds each.
        If it fails, it will create an access point to broadcast from.
        """
        try:
            station = network.WLAN(network.STA_IF)
            # connect to primary then alternate wifi:
            for ssid, password in secrets.network_data:
                print("Trying to connect to ", ssid)
                self.m.log("Trying to connect to ", ssid)
                station.active(True)
                startTime = time.time()
                station.connect(ssid, password)
                while startTime + 9 > time.time() and station.isconnected() == False:
                    print( str(startTime - time.time( )   ))
                    self.m.log( str(startTime - time.time( )   ))
                    time.sleep(1)
                if station.isconnected() == True: #Connected to a wifi
                    print('Connection successful to: ', ssid )
                    self.m.log('Connection successful to: ', ssid )
                    print(station.ifconfig())
                    self.m.log(station.ifconfig())
                    self.download_and_install_update_if_available(ssid, password)
                    return True
                else:
                    station.disconnect()
            # START Access Point. 
            # (It returns before this if successfully connected.)
            print("unable to connect to wifi. starting my own damn wifi.")
            self.m.log("unable to connect to wifi. starting my own damn wifi.")
            ap = network.WLAN(network.AP_IF)
            ap.active(True)
            ap.config(essid=secrets.ap_ssid, password=secrets.ap_password)
            startTime = time.time()
            while startTime+9 > time.time() and ap.active() == False:
                print( str(startTime - time.time()) + "Creating Access Point.")
                self.m.log( str(startTime - time.time()) + "Creating Access Point.")
                time.sleep(1)
            if startTime + 9 < time.time(): # took longer than 9 seconds:
                quit() # Cannot connect to wifi or access point, so revert to REPL
            print("Hosting AP at: "+ ap.config('essid'))
            self.m.log("Hosting AP at: "+ ap.config('essid'))
            return (ssid, password)
        except:
            print("did not connect to any wifi or create my own.")
            self.m.log("did not connect to any wifi or create my own.")
            return False