'''
Created on Jan 19, 2013

@author: joshandrews

Data interpreter: Returns values for current state passed from the arduino
Format of return from Arduino is defined by index in StaticVars
'''

import serial
import re
import sys
sys.path.append("..")
from control.datatype import datatypes
from serial.tools import list_ports
from control.logic import standardcalc
import time
import control.global_vars as gVars

SERIAL_PORT = '/dev/ttyACM0'
BAUD = 57600
PC = False

ARD_AUT = 0     # Auto Mode
ARD_LONG = 1    # GPS Longitude
ARD_LAT = 2     # GPS Latitude
ARD_COG = 3     # Course over Ground
ARD_HOG = 4     # Heading over Ground
ARD_AWA = 5     # Apparent Wind Angle
ARD_AWAV = 6    # Apparent Wind Angle Average
ARD_SHT = 7     # Sheet Percentage
ARD_SAT = 8     # Number of Satellites
ARD_ACC = 9     # GPS Accuracy
ARD_SOG = 10    # Speed over Ground
ARD_RUD = 11    # Rudder Angle

coms = list_ports.comports()
#print coms
usbserials = []
for com in coms:
    for port in com:
        if "USB" in port:
            usbserials.append(port)

if (len(usbserials) > 0):
    SERIAL_PORT = usbserials[0]

if (PC):
    SERIAL_PORT = 'COM3' 
    
class arduino:
    
    def __init__(self):
        self.ser = serial.Serial(SERIAL_PORT, BAUD)
        
    # Calls adjust_sheets on arduino with sheet percentage
    def adjust_sheets(self, sheet_percent):                                                
        # Format
        #    "ADJUST_SHEETS,<sheet_percent>"
        wr = "ADJUST_SHEETS,{sp}\r\n".format(sp=sheet_percent)
        print wr
        self.ser.write(wr)
        time.sleep(.1)
        
    # Calls steer on arduino with method and degree
    # COMPASS_METHOD = 0
    # COG_METHOD = 1
    # AWA_METHOD = 2 
    def steer(self, method, degree):
        # Format
        #    "STEER,<method>,<degree>"
        wr = "STEER,{m},{d}\n".format(m=method, d=degree)
        print wr
        self.ser.write(wr)
        time.sleep(.1)
    
    # Calls tack on arduino    
    def tack(self, weather, tack):
        # Format
        #     Tack: Port=0 Stbd=1
        #    "TACK,<Weather>, <WindwardSideOfBoat>"
        wr = "TACK,{w},{t}".format(w=weather, t=tack)
        print wr
        gVars.logger.info("------------TACK------------")
        self.ser.write(wr)
        
        if(weather == 0):
            time.sleep(6.5)
        elif(weather == 1):
            time.sleep(5.9)
        elif(weather == 2):
            time.sleep(5.6)
        elif(weather == 3):
            time.sleep(5.3)
     
    # Calls gybe on the arduino
    def gybe(self, tack):
        # Format
        #    Gybe: Port=0 Stbd=1
        #    "GYBE,<WindwardSideOfBoat>"
        wr = "GYBE,{t}".format(t=tack)
        self.ser.write(wr)
        gVars.logger.info("------------GYBE-------------")
        time.sleep(4)
    
    # Returns the latest array of all info from the arduino
    def getFromArduino(self):

        self.ser.flushInput()
        ardArr = []
        ardBuffer = ''
        for i in range(0,1):
            buff = self.ser.read(600)
            if (buff):
                ardBuffer = ardBuffer + buff
            if '\n' in ardBuffer:
                lines = ardBuffer.split('\n') # Guaranteed to have at least 2 entries
                ardArr = lines[-2]
                #If the Arduino sends lots of empty lines, you'll lose the
                #last filled line, so you could make the above statement conditional
                #like so: if lines[-2]: last_received = lines[-2]
                ardBuffer = lines[-1]                
        if (len(ardBuffer) > 0):
            ardArr = ardArr.replace(" ", "")
            ardArr = ardArr.replace("\x00", "")

        if (len(ardArr) > 0):
            ardArr = re.findall("[^,\s][^\,]*[^,\s]*", ardArr)
            i = 0
            while (i < len(ardArr)):
                ardArr[i] = float(ardArr[i])
                i+=1     
        if (len(ardArr) > 0):
            arduinoData = self.interpretArr(ardArr)
            return arduinoData
        else:
            return None
    
    # Takes an array from the arduino and maps it to the appropriate objects in the python array
    def interpretArr(self, ardArr):
        arduinoData = datatypes.ArduinoData()
        arduinoData.hog = standardcalc.boundTo180(ardArr[ARD_HOG])
        arduinoData.cog = standardcalc.boundTo180(ardArr[ARD_COG])
        arduinoData.sog = ardArr[ARD_SOG]
        arduinoData.awa = ardArr[ARD_AWAV]
        arduinoData.gps_coord = datatypes.GPSCoordinate(ardArr[ARD_LAT]/10000000, ardArr[ARD_LONG]/10000000)
        arduinoData.sheet_percent = ardArr[ARD_SHT]
        arduinoData.num_sat = ardArr[ARD_SAT]
        arduinoData.gps_accuracy = ardArr[ARD_ACC]
        arduinoData.auto = ardArr[ARD_AUT]
        arduinoData.rudder = ardArr[ARD_RUD]
        return arduinoData
