# Temperature Sensor Driver
# Reads the temperature of the sensor at that point.
# Largely based off the below reference
# http://www.reuk.co.uk/wordpress/raspberry-pi/ds18b20-temperature-sensor-with-raspberry-pi/
# Accessed on 20/11/2017

# Lab sensor address: 28-00000976a155
# Home sensor address: 28-000009773ac7

def read_int():
    tempfile = open("/sys/bus/w1/devices/28-00000976a155/w1_slave")
    thetext = tempfile.read()
    tempfile.close()
    tempdata = thetext.split("\n")[1].split(" ")[9]
    temperature = float(tempdata[2:])
    temperature = temperature/1000
    return temperature
def read_ext():
    tempfile = open("/sys/bus/w1/devices/28-000009773ac7/w1_slave")
    thetext = tempfile.read()
    tempfile.close()
    tempdata = thetext.split("\n")[1].split(" ")[9]
    temperature = float(tempdata[2:])
    temperature = temperature/1000
    return temperature

