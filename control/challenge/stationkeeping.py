'''
Created on Jan 19, 2013

@author: joshandrews
'''
import math
import sys
import time
sys.path.append("..")
from datetime import datetime
from control.logic import standardcalc
from control import global_vars as gVars
from control import sailing_task
from control.parser import parsing
from os import path

class StationKeeping(sailing_task.SailingTask):
    
    CHALLENGE_TIME = 300
    DISTANCE_TO_EDGE = 15
    COMPASS_METHOD = 0
    AWA_METHOD = 2
    SAIL_BY_APPARENT_WIND_ANGLE_MAX = 110
    SAIL_BY_APPARENT_WIND_ANGLE_MIN = 34
    CRITICAL_HEIGHT_ABOVE_BOX_MIDPOINT = 10
    CRITICAL_HEIGHT_BELOW_BOX_MIDPOINT = 5
    CRITICAL_HEIGHT_ABOVE_BOTTOM_OF_BOX = 15
    SK_WEATHER_COLUMN =1 #don suspects this weather setting will do for SK
    TIME_BUFFER = 2
    
    def __init__(self):
        self.upwindWaypoint = 0
        self.sheetList = parsing.parse(path.join(path.dirname(__file__), 'apparentSheetSetting'))
        self.oldTackingAngle = 0
        self.oldSheet_percent = 0
        self.oldAwa = 0
        self.meanSpd = 0.75   #from old arduino code
        self.secLeft = self.CHALLENGE_TIME
        self.SKLogger = SKLogger()
        self.sheet_percent = 0
        self.STEER_METHOD = self.AWA_METHOD           
        self.exitSpeed = gVars.instructions.SK_exit_speed

    def setWayPtCoords(self, boxCoords): #sets the waypoints of the challenge
        wayPtCoords = []    #order = top face, right face, bottom face, left face
        wayPtCoords.append(standardcalc.returnMidPoint(boxCoords[0],boxCoords[1]))
        wayPtCoords.append(standardcalc.returnMidPoint(boxCoords[1],boxCoords[2]))
        wayPtCoords.append(standardcalc.returnMidPoint(boxCoords[2],boxCoords[3]))
        wayPtCoords.append(standardcalc.returnMidPoint(boxCoords[3],boxCoords[0]))    
        return wayPtCoords
    
    def getBoxDist(self, boxCoords, absoluteValue=True):
        boxDistList = []  #top, right, bottom, left
        
        TL2Boat = standardcalc.distBetweenTwoCoords(gVars.currentData.gps_coord, boxCoords[0]) #top left to boat
        TR2Boat = standardcalc.distBetweenTwoCoords(gVars.currentData.gps_coord, boxCoords[1]) #top right to boat
        BR2Boat = standardcalc.distBetweenTwoCoords(gVars.currentData.gps_coord, boxCoords[2]) #bottom right to boat
        BL2Boat = standardcalc.distBetweenTwoCoords(gVars.currentData.gps_coord, boxCoords[3]) #bottom left to boat
        
        TL2TR = standardcalc.distBetweenTwoCoords(boxCoords[0], boxCoords[1]) #top left to top right
        TR2BR = standardcalc.distBetweenTwoCoords(boxCoords[1], boxCoords[2]) #top right to bottom right
        BR2BL = standardcalc.distBetweenTwoCoords(boxCoords[2], boxCoords[3]) #bottom right to bottom left
        BL2TL = standardcalc.distBetweenTwoCoords(boxCoords[3], boxCoords[0]) #bottom left to top left
            
            
        topLeftAngle = standardcalc.findCosLawAngle(TL2TR, TL2Boat, TR2Boat)
        topRightAngle = standardcalc.findCosLawAngle(TR2BR, TR2Boat, BR2Boat)
        botRightAngle = standardcalc.findCosLawAngle(BR2BL, BR2Boat, BL2Boat)
        botLeftAngle = standardcalc.findCosLawAngle(BL2TL, BL2Boat, TL2Boat)
        
        topDist = TL2Boat * math.sin(topLeftAngle)
        rightDist = TR2Boat * math.sin(topRightAngle)
        bottomDist = BR2Boat * math.sin(botRightAngle)
        leftDist = BL2Boat * math.sin(botLeftAngle)
        
        if absoluteValue:
            boxDistList = [abs(topDist), abs(rightDist), abs(bottomDist), abs(leftDist)]
        else:
            boxDistList = [topDist, rightDist, bottomDist, leftDist]
            
        return boxDistList
    
    def getStartDirection(self, wayPtCoords):
        index = standardcalc.returnClosestWaypointIndex(wayPtCoords)
        index = (index+2)%4
        return index
                                                                                            
    def run(self, wayList):
        
        boxCoords = standardcalc.setBoxCoords(wayList[0].coordinate, wayList[1].coordinate, wayList[2].coordinate, wayList[3].coordinate)
        self.wayPtCoords = self.setWayPtCoords(boxCoords)  #top, right, bottom, left
        gVars.logger.info("North waypoint: " + str(self.wayPtCoords[0]) + " East waypoint: " + str(self.wayPtCoords[1]) +" South waypoint: " + str(self.wayPtCoords[2]) + " West waypoint: " + str(self.wayPtCoords[3]) )
        
        spdList = [self.meanSpd] * 100
        boxDistList = self.getBoxDist(boxCoords)  #top, right, bottom, left
        
        self.currentWaypoint = self.getStartDirection(self.wayPtCoords)
        self.printDistanceLogs(boxDistList)

        gVars.logger.info("------CURRENT WAYPOINT=" + str(self.currentWaypoint)+" ---------")
        gVars.logger.info("Station Keeping Initialization finished. Now running Station Keeping Challenge")
         
        if (gVars.currentData.awa > 0):
            self.upwindWaypoint = (self.currentWaypoint + 1) % 4
        else:
            self.upwindWaypoint = (self.currentWaypoint + 3) % 4
            
        gVars.logger.info("------UPWIND WAYPOINT=" + str(self.upwindWaypoint)+" ---------")
            
        self.stationKeep(boxCoords, spdList)
        
    def stationKeep(self, boxCoords, spdList):
        exiting = False
        inTurnZone = True
        turning = True
        
        while gVars.kill_flagSK == 0:
            time.sleep(.1)
            
            self.secLeft = self.CHALLENGE_TIME - (datetime.now() - gVars.taskStartTime).seconds

            boxDistList = self.getBoxDist(boxCoords)
            self.sailByApparentWind(boxDistList,exiting)
            self.printDistanceLogs(boxDistList)
            
            if (not exiting):
                
                spdList = self.updateMeanSpeed(turning, spdList)
                
                if self.boatIsTooCloseToEdgeAndMustTurn(boxDistList, inTurnZone):
                    self.updateCurrentWaypointAndGybe(boxDistList)
                        
                    inTurnZone = True
                    turning = True
                              
                elif ((boxDistList[(self.currentWaypoint+2)%4] > self.DISTANCE_TO_EDGE) and (inTurnZone == True)):
                    gVars.logger.info("Boat out of turn zone, checking for boundaries again. Distance to Edge: " + str(boxDistList[(self.currentWaypoint+2)%4]))
                    
                    inTurnZone = False
                    turning = False
                    
                if (boxDistList[self.currentWaypoint] >= self.exitSpeed*(self.secLeft+self.TIME_BUFFER+0)):
                    gVars.logger.info("distances: N: " + str(boxDistList[0]) + " E: " + str(boxDistList[1]) + " S: " + str(boxDistList[2]) + " W: " + str(boxDistList[3]))
                    gVars.logger.info("Seconds Left:" + str(self.secLeft))
                    exiting = True
                    gVars.logger.info("Station Keeping event is about to end. Exiting to current waypoint.")
                
                elif (boxDistList[(self.currentWaypoint + 2) % 4] >= self.exitSpeed*(self.secLeft+self.TIME_BUFFER+4) ): #4 seconds for gybe
                    gVars.logger.info("distances: N: " + str(boxDistList[0]) + " E: " + str(boxDistList[1]) + " S: " + str(boxDistList[2]) + " W: " + str(boxDistList[3]))
                    gVars.logger.info("Seconds Left:" + str(self.secLeft))
                    self.currentWaypoint = (self.currentWaypoint + 2) % 4
                    gVars.logger.info("Station Keeping event is about to end. Gybing and exiting to waypoint " + str(self.currentWaypoint))
                    if (gVars.currentData.awa > 0):
                        gVars.arduino.gybe(1)
                    else:
                        gVars.arduino.gybe(0)
                    exiting = True 
            else:
                if boxDistList[self.currentWaypoint] <1:
                    gVars.kill_flagSK = 1;
                    gVars.logger.info("Boat has exited box at " + str(self.secLeft) + " seconds.")
                    
        if gVars.kill_flagSK == 1:
            gVars.logger.info("Station Keeping Kill Flag initialized. Station Keeping Challenge has been stopped.")
    
    # StationKeeping's sail method.  This function steers and adjusts the sheets
    def sailByApparentWind(self, boxDistList,exiting):
        downwindWaypointIndex = (self.upwindWaypoint+2) % 4
        boxHeight = boxDistList[(self.currentWaypoint+1)%4]+boxDistList[(self.currentWaypoint+3)%4]
        downwindHeight = boxDistList[downwindWaypointIndex]
        downwindHeightIdeal = boxHeight/2

        if not exiting:
            self.STEER_METHOD = self.AWA_METHOD           
            target = self.calcTackingAngle(downwindHeight, downwindHeightIdeal)
            sheetPercentageMultiplier = self.calcDownwindPercent(downwindHeight, downwindHeightIdeal)*.01
            self.sheet_percent =round(sheetPercentageMultiplier*self.sheetList[abs(int(gVars.currentData.awa))][self.SK_WEATHER_COLUMN])
            windAngleMultiplier = self.calcWindAngleMultiplier()
            target = windAngleMultiplier*target
            
        else:
            target = self.calculateHeadingForExit()
            sheetMax = self.sheetList[abs(int(gVars.currentData.awa))][self.SK_WEATHER_COLUMN]
            self.sheet_percent = self.adjustSheetsForExit(boxDistList[self.currentWaypoint],sheetMax)

        if (self.isThereChangeInDownwindHeightOrTackingAngleOrAwa(target)):
            gVars.arduino.adjust_sheets(self.sheet_percent)
            gVars.arduino.steer(self.STEER_METHOD,target)
            self.printSailingLog(self.sheet_percent,target)
            self.printHeightLog(downwindHeight,downwindHeightIdeal)

            
    def adjustSheetsForExit(self, distance, sheetMax):
        MULTIPLIER = 5
        sheet_delta = distance - gVars.currentData.sog*(self.secLeft+self.TIME_BUFFER)
        sheets = self.sheet_percent + sheet_delta*MULTIPLIER
        if sheets<0:
            sheets=0
        elif sheets>sheetMax:
            sheets=sheetMax
        return sheets
      
    def calculateHeadingForExit(self):
        if standardcalc.isWPNoGoAWA(gVars.currentData.awa, gVars.currentData.hog, self.wayPtCoords[self.currentWaypoint],gVars.currentData.sog,self.wayPtCoords[(self.currentWaypoint+2)%4]):
            self.STEER_METHOD = self.AWA_METHOD
            if gVars.currentData.awa<0:
                tackAngleMultiplier = -1
            else:
                tackAngleMultiplier = 1
            return tackAngleMultiplier*34
        else:
            self.STEER_METHOD = self.COMPASS_METHOD                       
            return standardcalc.angleBetweenTwoCoords(self.wayPtCoords[(self.currentWaypoint+2)%4], self.wayPtCoords[self.currentWaypoint])
           
    def updateMeanSpeed(self, turning, spdList):
        if (not turning):
            spdList = standardcalc.changeSpdList(spdList)
            self.meanSpd = standardcalc.meanOfList(spdList)
        return spdList
    
    def isThereChangeInDownwindHeightOrTackingAngleOrAwa(self, tackingAngle):
        if gVars.currentData.awa != self.oldAwa or tackingAngle != self.oldTackingAngle or self.sheet_percent != self.oldSheet_percent:
            self.updateOldData(tackingAngle)
            return True
        else:
            return False
        
    def boatIsTooCloseToEdgeAndMustTurn(self, boxDistList, inTurnZone):
        if (boxDistList[self.currentWaypoint] < self.DISTANCE_TO_EDGE) and (inTurnZone == False):
            return True
        else:
            return False
    
    def updateCurrentWaypointAndGybe(self, boxDistList):
        gVars.logger.info("distances: N: " + str(boxDistList[0]) + " E: " + str(boxDistList[1]) + " S: " + str(boxDistList[2]) + " W: " + str(boxDistList[3]))
        gVars.logger.info("The boat is too close to an edge. Changing current waypoint.")
        
        self.currentWaypoint = (self.currentWaypoint + 2) % 4
        
        gVars.logger.info("------CURRENT WAYPOINT=" + str(self.currentWaypoint)+" ---------")
                            
        if (gVars.currentData.awa > 0):
            gVars.arduino.gybe(1)
        else:
            gVars.arduino.gybe(0)
    
    def updateOldData(self, tackingAngle):
        self.oldTackingAngle = tackingAngle
        self.oldAwa = gVars.currentData.awa
        self.oldSheet_percent = self.sheet_percent
        
    def calcWindAngleMultiplier(self):
        if self.upwindWaypoint == (self.currentWaypoint + 3) % 4:
            return -1
        else:
            return 1
        
    def calcTackingAngle(self, downwindHeight, downwindHeightIdeal):
        if downwindHeight-10 > downwindHeightIdeal:
            return self.SAIL_BY_APPARENT_WIND_ANGLE_MAX
        else:
            return self.SAIL_BY_APPARENT_WIND_ANGLE_MAX - (float(downwindHeightIdeal+10-downwindHeight)/float(downwindHeightIdeal))*(self.SAIL_BY_APPARENT_WIND_ANGLE_MAX-self.SAIL_BY_APPARENT_WIND_ANGLE_MIN)
    
    def calcDownwindPercent(self, downwindHeight, downwindHeightIdeal):
        if downwindHeight-self.CRITICAL_HEIGHT_ABOVE_BOX_MIDPOINT > downwindHeightIdeal:
            return 0
        elif downwindHeight-self.CRITICAL_HEIGHT_ABOVE_BOTTOM_OF_BOX > 0:
            return float(downwindHeightIdeal+self.CRITICAL_HEIGHT_ABOVE_BOX_MIDPOINT-downwindHeight)/float(downwindHeightIdeal-self.CRITICAL_HEIGHT_BELOW_BOX_MIDPOINT)*100
        else:
            return 100
    
    def printDistanceLogs(self, boxDistList):
        self.SKLogger.distanceLog=(str(int(boxDistList[self.upwindWaypoint]))+" wpt#"+str(self.upwindWaypoint)+ " - Top")+"<br>"
        self.SKLogger.distanceLog+=str(int(boxDistList[(self.upwindWaypoint+3)%4]))+" wpt#"+str((self.upwindWaypoint+3)%4)+" - Left,    "
        self.SKLogger.distanceLog+=str(int(boxDistList[(self.upwindWaypoint+1)%4]))+" wpt#"+str((self.upwindWaypoint+1)%4)+" - Right"+"<br>"
        self.SKLogger.distanceLog+=str(int(boxDistList[(self.upwindWaypoint+2)%4]))+" wpt#"+str((self.upwindWaypoint+2)%4)+" - Bot"
        self.SKLogger.printLog()
        
    def printHeightLog(self,downwindHeight,downwindHeightIdeal ):
        self.SKLogger.heightLog="HEIGHT:" + str(int(downwindHeight)) +"  Ideal:" + str(int(downwindHeightIdeal))
        self.SKLogger.printLog()
        
    def printSailingLog(self, sheet_percent, wind_bearing):
        self.SKLogger.sailLog="Sheet Percent:" + str(sheet_percent) +"  Course:" + str(wind_bearing)
        self.SKLogger.spdLog="meanSpd: "+str(self.meanSpd)+ " secLeft:"+ str(self.secLeft)
        self.SKLogger.printLog()

class SKLogger:
    LOG_UPDATE_INTERVAL=2
    def __init__(self):
        self.heightLog =''
        self.distanceLog=''
        self.sailLog=''
        self.spdLog=''
        self.logTimer =0
    def printLog(self):
        if (time.time() - self.logTimer>self.LOG_UPDATE_INTERVAL):
            self.logTimer = time.time()
            gVars.logger.sklog(self.heightLog)
            gVars.logger.sklog(self.distanceLog)        
            gVars.logger.sklog(self.sailLog)
            gVars.logger.sklog(self.spdLog)

