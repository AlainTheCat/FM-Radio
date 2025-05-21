import serial
import time
import json

# On Linux, give permission with: sudo chmod a+rw /dev/ttyACM0

# open a serial connection
# s = serial.Serial("/dev/ttyACM0", 115200)
s = serial.Serial("COM4", 9600)

print(s)
# blink the led
while True:   
    bytearrayValue = s.readline()
    print(bytearrayValue)
    # b'{"date":"14/3/2023","time":"20:7:22","temperature":"21.1","humidity":"51.77","pressure":"995.43","gas":"57.47"}\r\n'
    jsonLine = bytearrayValue.decode('utf8')
    # print(jsonLine)
    # parse jsonLine:
    measure = json.loads(jsonLine)

    # the result is a Python dictionary:
    print(measure["date"])
    print(measure["time"])
    print(measure["temperature"])
    print(measure["humidity"])
    print(measure["pressure"])
    print(measure["gas"])
    print("--------------")

    time.sleep(10)
    