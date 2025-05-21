"""
On Raspberry Pico only
"""

from machine import Pin, I2C  # importing relevant modules & classes
from time import sleep
import utime
from bme680 import *  # importing BME680 library
from ssd1306 import SSD1306_I2C  # importing SSD1306 library
from ds1307 import DS1307  # importing DS1307 library

i2c = I2C(0, sda=Pin(8), scl=Pin(9), freq=400000)  # initializing the I2C method
oled = SSD1306_I2C(128, 64, i2c)
oled.fill(0)

rtc = DS1307(i2c=i2c)
hour = 0
minute = 0
second = 0
date = 1
month = 1
year = 2000

# Uncomment only to set or update the time for first time in RTC then comment it back again.
"""
year = int(input("Year : "))
month = int(input("month (Jan --> 1 , Dec --> 12): "))
date = int(input("date : "))
day = int(input("day (1 --> monday , 2 --> Tuesday ... 0 --> Sunday): "))
hour = int(input("hour (24 Hour format): "))
minute = int(input("minute : "))
second = int(input("second : "))

now = (year,month,date,day,hour,minute,second,0)
rtc.datetime(now)
print(rtc.datetime())
"""


def loop():
    temperature = 25.00  # default values
    humidity = 75.00
    pressure = 1002.00
    gas = 12000.00

    while True:
        oled.fill(0)

        (year, month, date, day, hour, minute, second, p1) = rtc.datetime()

        # format date and time
        year = "{:04d}".format(year)
        month = "{:02d}".format(month)
        date = "{:02d}".format(date)
        day = "{:02d}".format(day)
        hour = "{:02d}".format(hour)
        minute = "{:02d}".format(minute)
        second = "{:02d}".format(second)

        time_ = str(hour) + ":" + str(minute) + ":" + str(second)
        date_ = str(date) + "/" + str(month) + "/" + str(year)

        temperature = round(bme.temperature, 2)
        humidity = round(bme.humidity, 2)
        pressure = round(bme.pressure, 2)
        gas = round(bme.gas / 1000, 2)

        # Format
        temperature = "{:.2f}".format(temperature)
        humidity = "{:.2f}".format(humidity)
        pressure = "{:.2f}".format(pressure)
        gas = "{:.2f}".format(gas)

        temp = "temp:" + str(temperature)
        hum_ = "hum :" + str(humidity)
        pres = "pres:" + str(pressure)
        gas_ = "gas :" + str(gas)

        date_json = '"date":"' + date_ + '",'
        time_json = '"time":"' + time_ + '",'
        temp_json = '"temperature":"' + str(temperature) + '",'
        hum_json = '"humidity":"' + str(humidity) + '",'
        pres_json = '"pressure":"' + str(pressure) + '",'
        gas_json = '"gas":"' + str(gas) + '"'
        # printing DS1307 and BME280 values with json format
        measure = '{' + date_json + time_json + temp_json + hum_json + pres_json + gas_json + '}'
        print(measure)

        file = open("measure.json", "w")
        file.write(measure)
        file.write('\n')
        file.close()

        oled.text(date_, 0, 0)
        oled.text(time_, 0, 10)
        oled.text(temp, 0, 20)
        oled.text(pres, 0, 30)
        oled.text(hum_, 0, 40)
        oled.text(gas_, 0, 50)
        oled.show()  # display

        sleep(60)  # delay of 60s


def error():
    msg__ = "Error"
    print(msg__)

    temperature = 25.00  # default values
    humidity = 75.00
    pressure = 1002.00
    gas = 12000.00

    while True:
        oled.fill(0)

        (year, month, date, day, hour, minute, second, p1) = rtc.datetime()
        # format date and time
        year = "{:04d}".format(year)
        month = "{:02d}".format(month)
        date = "{:02d}".format(date)
        day = "{:02d}".format(day)
        hour = "{:02d}".format(hour)
        minute = "{:02d}".format(minute)
        second = "{:02d}".format(second)

        time_ = str(hour) + ":" + str(minute) + ":" + str(second)
        date_ = str(date) + "/" + str(month) + "/" + str(year)

        temperature = round(bme.temperature, 2)
        humidity = round(bme.humidity, 2)
        pressure = round(bme.pressure, 2)
        gas = round(bme.gas / 1000, 2)

        # Format
        temperature = "{:.2f}".format(temperature)
        humidity = "{:.2f}".format(humidity)
        pressure = "{:.2f}".format(pressure)
        gas = "{:.2f}".format(gas)

        temp = "temp:" + str(temperature)
        hum_ = "hum :" + str(humidity)
        pres = "pres:" + str(pressure)
        gas_ = "gas :" + str(gas)

        date_json = '"date":"' + date_ + '",'
        time_json = '"time":"' + time_ + '",'
        temp_json = '"temperature":"' + str(temperature) + '",'
        hum_json = '"humidity":"' + str(humidity) + '",'
        pres_json = '"pressure":"' + str(pressure) + '",'
        gas_json = '"gas":"' + str(gas) + '"'

        # printing DS1307 and BME280 values with json format
        measure = '{' + date_json + time_json + temp_json + hum_json + pres_json + gas_json + '}'
        print(measure)

        file = open("measure.json", "w")
        file.write(measure)
        file.write('\n')
        file.close()

        oled.text(date_, 0, 0)
        oled.text(time_, 0, 10)
        oled.text(msg__, 0, 20)

        oled.show()  # display

        sleep(60)  # delay of 60s


try:
    bme = BME680_I2C(i2c=i2c)  # BME680 object created
    # loop()
except:
    error()
else:
    loop()

