import secrets
import network
from ota_updater import OTAUpdater
# this is a secrets.py file that git ignores. 
# it is in same folder as boot.py. 
# See secrets_template.py


def download_and_install_update_if_available(ssid, password):
  print("checking for update from: ", secrets.url)
  o = OTAUpdater(github_repo = secrets.url, secrets_file="src/secrets.py", main_dir='/', github_src_dir="src")  
  if o.install_update_if_available_after_boot(ssid, password) == True:
    machine.reset()
  elif o.check_for_update_to_install_during_next_reboot() == True:
    #this creates a .version file to update if there's a newer version.
    print("found new update. resetting.")
    machine.reset()

def connect_to_networks() -> (str, str):
    """ will attempt to connect to the networks in the secrets file for 10 seconds each.
    """
    try:
        station = network.WLAN(network.STA_IF)
        # connect to primary then alternate wifi:
        for ssid, password in secrets.network_data:
            print("Trying to connect to ", ssid)
            station.active(True)
            startTime = time.time()
            station.connect(ssid, password)
            while startTime + 9 > time.time() and station.isconnected() == False:
                print( str(startTime - time.time( )   ))
                time.sleep(1)
            if station.isconnected() == True: #Connected to a wifi
                print('Connection successful to: ', ssid )
                print(station.ifconfig())\
                download_and_install_update_if_available(ssid, password)
                return (ssid, password)
            else:
                station.disconnect()
    except:
        print("did not connect to any wifi or create my own.")
        return ("","")

