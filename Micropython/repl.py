import serial
import time
import json

def printText(text, maxChar):
    """Print text on  maximum chars"""
    space = " "
    lenToAdd = maxChar - len(text)
    if lenToAdd > 0:
        for i in range(lenToAdd):
            text = text + space
        return text
    else:
        return text


# On Linux, give permission with: sudo chmod a+rw /dev/ttyACM0

# open a serial connection
# LINUX
# s = serial.Serial("/dev/ttyACM0", 115200)

# WINDOWS
s = serial.Serial("COM4", 115200)

# print(s)
# blink the led

lenOfMeasure = 11
dateTitle = printText("Date", 11)
timeTitle = printText("Time", 11)
temperatureTitle = printText("Temperature", 11)
humidityTitle = printText( "Humidity", 11)
pressureTitle = printText( "Pressure", 11)
gasTitle = printText("Gas", 11)

print("WEATHER MEASURES")
print("|1234567891234|1234567891234|1234567891234|1234567891234|1234567891234|1234567891234|")
print("-------------------------------------------------------------------------------------")
print("|", dateTitle, "|", timeTitle, "|", temperatureTitle, "|", humidityTitle, "|",pressureTitle, "|", gasTitle, "|" )
print("-------------------------------------------------------------------------------------")

while True:
    bytearrayValue = b'{"date":"14/3/2023","time":"20:7:22","temperature":"21.1","humidity":"51.77","pressure":"995.43","gas":"57.47"}\r\n'
    try:
        bytearrayValue = s.readline()
    except:
        print("Error")
        time.sleep(60)

    jsonLine = bytearrayValue.decode('utf8')
    # print(jsonLine)
    # parse jsonLine:
    measure = json.loads(jsonLine)
    
    date = printText(measure["date"], 11)
    times = printText(measure["time"], 11)
    temperature = printText(measure["temperature"], 11)
    humidity = printText(measure["humidity"], 11)
    pressure = printText(measure["pressure"], 11)
    gas = printText(measure["gas"], 11)
    
    

    # the result is a Python dictionary:
    print("|", date, "|", times, "|", temperature, "|", humidity, "|", pressure, "|", gas, "| ")
    # print("-----------------------------------------------------------------------------------")


    

