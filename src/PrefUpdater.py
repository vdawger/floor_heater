""" Starts access point to update information in the secrets.py file"""
import os, gc
import secrets
import network
import time
import ubinascii as binascii
try: # https://github.com/micropython/micropython/blob/master/examples/network/http_server.py
    import usocket as socket
except:
    import socket
import ussl as ssl

class PrefUpdater():
    def __init__(self):
        # constants:
        self.directory = "src/"
        self.new_secrets_file = "new_secrets.py"

    # Helper Functions:
    def _copy_file(self, fromPath, toPath):
        with open(fromPath) as fromFile:
            with open(toPath, 'w') as toFile:
                CHUNK_SIZE = 512 # bytes
                data = fromFile.read(CHUNK_SIZE)
                while data:
                    toFile.write(data)
                    data = fromFile.read(CHUNK_SIZE)
            toFile.close()
        fromFile.close()
    def _delete_old_version(self):
        print('Deleting old version at {} ...'.format(self.modulepath(self.main_dir)))
        self._rmtree(self.modulepath(self.main_dir))
        print('Deleted old version at {} ...'.format(self.modulepath(self.main_dir)))
    def _exists_dir(self, path) -> bool:
        try:
            os.listdir(path)
            return True
        except:
            return False
    def _rm_file(self):
        os.remove(self.directory + "/"+ self.new_secrets_file)
    def _new_secrets_exists(self, directory) -> bool:
        return self.new_secrets_file in os.listdir(directory)

    def prompt_for_updates(self):
        #start AP
        print("unable to connect to wifi. starting my own damn wifi.")
        ap = network.WLAN(network.AP_IF)
        ap.active(True)
        ap.config(essid=secrets.ap_ssid, password=secrets.ap_password)
        startTime = time.time()
        while startTime+9 > time.time() and ap.active() == False:
            print( str(startTime - time.time()) + "Creating Access Point.")
            time.sleep(1)
        if startTime + 9 < time.time(): # took longer than 9 seconds:
            quit()
        print("Hosting AP at: "+ ap.config('essid'))
    
    def pref_server():
    #Read secrets.py
    # Serve secrets.py data
    # if saved, write new secrets.py data and overwrite current file