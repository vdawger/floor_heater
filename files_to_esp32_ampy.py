import os
print("Resetting ESP32.")
print(".\esptool.exe --chip esp32 --port COM5 --baud 460800 erase_flash")
os.system(".\esptool.exe --chip esp32 --port COM5 --baud 460800 erase_flash")
print(".\esptool.exe --chip esp32 --port COM5 --baud 460800 write_flash -z 0x1000 esp32-ota-20220618-v1.19.1.bin")
os.system(".\esptool.exe --chip esp32 --port COM5 --baud 460800 write_flash -z 0x1000 esp32-ota-20220618-v1.19.1.bin")
print("This puts boot.py and then all files in the src folder onto the ESP32")
for f in os.listdir('src'):
    print("ampy --port COM5 put src/"+f )
    os.system("ampy --port COM5 put src/"+f ) # copies to root.
#boot last to not start things when files are missing:
print("ampy --port COM5 put boot.py")
os.system("ampy --port COM5 put boot.py")