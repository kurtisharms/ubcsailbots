'''
Created on Apr 14, 2013

@author: joshandrews
'''

from os import path
from control.parser import parsing
from control.logic import standardcalc
from control import StaticVars as sVars
from control import GlobalVars as gVars
from control import sailingtask

class PointToPoint(sailingtask.SailingTask):
    
    def __init__(self):
        self.COMPASS_METHOD = 0
        self.COG_METHOD = 1
        self.AWA_METHOD = 2
    
        self.TACKING_ANGLE = 34
        
        self.ANGLE_CHANGE_THRESHOLD = 5
        
    # --- Point to Point ---
    # Input: Destination GPS Coordinate, initialTack: 0 for port, 1 for starboard, nothing calculates on own, TWA = 0 for sailing using only AWA and 1 for attempting to find TWA.
    # Output: Nothing
    def run(self, Dest, initialTack = None, ACCEPTANCE_DISTANCE = sVars.ACCEPTANCE_DISTANCE_DEFAULT):
        sheetList = parsing.parse(path.join(path.dirname(__file__), 'apparentSheetSetting'))
        tackSailing = 0
        newTackSailing = 0
        gVars.kill_flagPTP = 0
        self.end_flag = 0
        arduino = gVars.arduino
        appWindAng = 0
        oldColumn = 0
        oldAngleBetweenCoords = 0
        tackDirection = 0
        gVars.logger.info("Started point to pointAWA")
        
        while(self.end_flag == 0 and gVars.kill_flagPTP == 0):
            gVars.logger.info("End flag and kill flag OK")
            GPSCoord = gVars.currentData.gps_coord
            newappWindAng = gVars.currentData.awa
            cog = gVars.currentData.cog
            hog = gVars.currentData.hog
            sog = gVars.currentData.sog * 100
            angleBetweenCoords = standardcalc.angleBetweenTwoCoords(GPSCoord,Dest)        
            
            if(standardcalc.distBetweenTwoCoords(GPSCoord, Dest) > ACCEPTANCE_DISTANCE):
                gVars.logger.info("Boat not at point, continuing code")
                #This if statement determines the sailing method we are going to use based on apparent wind angle
                standardcalc.getWeatherSetting(newappWindAng,sog)
                    #print ("Hit else statement")
                    #print ("TWA is: " + str(gVars.TrueWindAngle))
                                    
                if(standardcalc.isWPNoGoAWA(newappWindAng,hog,Dest,sog,GPSCoord)):
                    gVars.logger.info("Point cannot be reached directly")
                    #Trying to determine whether 45 degrees clockwise or counter clockwise of TWA wrt North is closer to current heading
                    #This means we are trying to determine whether hog-TWA-45 or hog-TWA+45 (both using TWA wrt North) is closer to our current heading.
                    #Since those values give us TWA wrt to north, we need to subtract hog from them to get TWA wrt to our heading and figure out which one has a smaller value.
                    #To get it wrt to current heading, we use hog-TWA-45-hog and hog-TWA+45-hog.  Both terms have hogs cancelling out.
                    #We are left with -TWA-45 and -TWA+45, which makes sense since the original TWA was always with respect to the boat.
                    #Since we are trying to figure out which one is closest to turn to, we use absolute values.
                    if(self.starboardTackWanted(newappWindAng,initialTack)):
                        newTackSailing = 1
                        initialTack = None
                        gVars.tacked_flag = 0
                        while(self.doWeStillWantToTack(hog,GPSCoord,Dest)):
                            gVars.logger.info("On starboard tack")
                            
                            gVars.tacked_flag = 0
                            GPSCoord = gVars.currentData.gps_coord
                            newappWindAng = gVars.currentData.awa
                            cog = gVars.currentData.cog
                            hog = gVars.currentData.hog
                            sog = gVars.currentData.sog * 100  #Using speed in cm/s
                                                   
                            standardcalc.getWeatherSetting(newappWindAng, sog)                            
                            
                            if(self.isThereChangeToAWAorWeatherOrMode(appWindAng,newappWindAng,oldColumn,tackSailing,newTackSailing) ):
                                gVars.logger.info("Changing sheets and rudder")
                                arduino.adjust_sheets(sheetList[abs(int(newappWindAng))][gVars.currentColumn])
                                arduino.steer(self.AWA_METHOD,hog-newappWindAng-self.TACKING_ANGLE)
                                appWindAng = newappWindAng
                                oldColumn = gVars.currentColumn
                                tackSailing = newTackSailing
                                
                            if(newappWindAng > 0):
                                tackDirection = 1
                            else:
                                tackDirection = 0
                            
                            if( len(gVars.boundaries) > 0 ):
                                for boundary in gVars.boundaries:
                                    if(standardcalc.distBetweenTwoCoords(boundary, GPSCoord) <= boundary.radius):
                                        gVars.logger.info("Tacked from boundary")
                                        arduino.tack(gVars.currentColumn,tackDirection)
                                        gVars.tacked_flag = 1
                                        break
                            if(gVars.tacked_flag):
                                break
                            
                        if(gVars.tacked_flag == 0):                                                                
                            arduino.tack(gVars.currentColumn,tackDirection)
                        gVars.logger.info("Tacked from 80 degrees")
                        
                    elif(self.portTackWanted(newappWindAng,initialTack)):
                        newTackSailing = 2
                        initialTack = None
                        gVars.tacked_flag = 0
                        while(self.doWeStillWantToTack(hog,GPSCoord,Dest)):
                            gVars.logger.info("On port tack")
                            gVars.tacked_flag = 0
                            GPSCoord = gVars.currentData.gps_coord
                            newappWindAng = gVars.currentData.awa
                            cog = gVars.currentData.cog
                            hog = gVars.currentData.hog
                            sog = gVars.currentData.sog *100
                            
                            standardcalc.getWeatherSetting(newappWindAng,sog)
                            #TWA = abs(int(TWA))
                            #print ("TWA is: " + str(newTWA))
                            
                            if(self.isThereChangeToAWAorWeatherOrMode(appWindAng,newappWindAng,oldColumn,tackSailing,newTackSailing)):
                                gVars.logger.info("Changing sheets and rudder")
                                arduino.adjust_sheets(sheetList[abs(int(newappWindAng))][gVars.currentColumn])
                                arduino.steer(self.AWA_METHOD,hog-newappWindAng+self.TACKING_ANGLE)
                                appWindAng = newappWindAng
                                oldColumn = gVars.currentColumn
                                tackSailing = newTackSailing
                                
                            if(newappWindAng > 0):
                                tackDirection = 1
                            else:
                                tackDirection = 0
                                
                            if( len(gVars.boundaries) > 0 ):
                                for boundary in gVars.boundaries:
                                    if(standardcalc.distBetweenTwoCoords(boundary, GPSCoord) <= boundary.radius):
                                        gVars.logger.info("Tacked from boundary")
                                        arduino.tack(gVars.currentColumn,tackDirection)
                                        gVars.tacked_flag = 1
                                        break
                            
                            if(gVars.tacked_flag):
                                break
                            
                        if(gVars.tacked_flag == 0):                                                                
                            arduino.tack(gVars.currentColumn,tackDirection)
                        gVars.logger.info("Tacked from 80 degrees")
                        
                else:
                    gVars.logger.info("Sailing straight to point")
                    newTackSailing = 3
                    if(self.isThereChangeToAWAorWeatherOrModeOrAngle(appWindAng,newappWindAng,oldColumn,tackSailing,newTackSailing,oldAngleBetweenCoords, angleBetweenCoords)):
                        gVars.logger.info("Changing sheets and rudder")
                        arduino.adjust_sheets(sheetList[abs(int(newappWindAng))][gVars.currentColumn])
                        arduino.steer(self.COMPASS_METHOD,standardcalc.angleBetweenTwoCoords(GPSCoord,Dest))
                        gVars.logger.info(str(standardcalc.angleBetweenTwoCoords(GPSCoord, Dest)))
                        appWindAng = newappWindAng
                        oldColumn = gVars.currentColumn
                        tackSailing = newTackSailing
                        oldAngleBetweenCoords = angleBetweenCoords
                
            else:
                self.end_flag = 1
                gVars.logger.info("Finished Point to Point")
        
        return 0
    
    def killPointToPoint(self):
        gVars.kill_flagPTP = 1
        
    def starboardTackWanted(self, AWA,initialTack):
        if( (abs(-AWA-self.TACKING_ANGLE)<abs(-AWA+self.TACKING_ANGLE) and initialTack is None) or initialTack == 1 ):
            return 1
        else:
            return 0
            
    def portTackWanted(self, AWA,initialTack):
        if( (abs(-AWA-self.TACKING_ANGLE)>=abs(-AWA+self.TACKING_ANGLE) and initialTack is None) or initialTack == 0 ):
            return 1
        else:
            return 0
    
    def doWeStillWantToTack(self, hog,GPSCoord,Dest):
        if(abs(hog-standardcalc.angleBetweenTwoCoords(GPSCoord, Dest))<80 and gVars.kill_flagPTP ==0):
            return 1
        else:
            return 0
        
    def isThereChangeToAWAorWeatherOrModeOrAngle(self, AWA,newAWA,oldColumn,tackSailing,newTackSailing,oldAngle,newAngle):
        if(AWA != newAWA or oldColumn != gVars.currentColumn or tackSailing != newTackSailing or abs(oldAngle-newAngle)>self.ANGLE_CHANGE_THRESHOLD):
            return 1
        else:
            return 0
        
    def isThereChangeToAWAorWeatherOrMode(self, AWA,newAWA,oldColumn,tackSailing,newTackSailing):
        if(AWA != newAWA or oldColumn != gVars.currentColumn or tackSailing != newTackSailing):
            return 1
        else:
            return 0