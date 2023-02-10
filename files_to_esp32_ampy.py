import os
print("This puts boot.py and then all files in the src folder onto the ESP32")
print("ampy --port COM5 put boot.py")
os.system("ampy --port COM5 put boot.py")
for f in os.listdir('src'):
    print("ampy --port COM5 put src/"+f)
    os.system("ampy --port COM5 put src/"+f)