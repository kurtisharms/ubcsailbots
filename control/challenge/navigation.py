'''
Created on Jan 19, 2013

@author: joshandrews
'''
import time
import math
import thread
import sys
sys.path.append("..")
from control.logic import standardcalc
from control.datatype import datatypes
from control import global_vars as gVars
from control.logic import roundbuoy
from control.logic import pointtopoint
from control import sailing_task

# ---    Navigation Challenge    ---
#Input: Buoy GPS Coordinates (Latitude and Longitude of the Buoy), Left Inner Point (The coordinates of the left innermost gate), Right Inner Point (The coordinates of the right innermost gate)
#Output: None
class Navigation(sailing_task.SailingTask):
    LOG_UPDATE_INTERVAL=1
    def __init__(self):
        self.roundbuoy = roundbuoy.RoundBuoy()
        self.pointtopoint = pointtopoint.PointToPoint()
        
    def run(self, waypoint1,waypoint2,waypoint3,waypoint4=None):
        self.nav_log_timer=0
        
        buoyCoords = None
        portStartInnerPoint = None
        starboardStartInnerPoint = None
        navMidpoint = None
        
        gVars.kill_flagNav = 0
        
        wayList = list()
        
        wayList.append(waypoint1)
        wayList.append(waypoint2)
        wayList.append(waypoint3)
        
        if waypoint4:
            wayList.append(waypoint4)
        
        for waypoint in wayList:
            if(waypoint.wtype == "nav_first"):
                buoyCoords = waypoint.coordinate
            elif(waypoint.wtype == "nav_start_port"):
                portStartInnerPoint = waypoint.coordinate
            elif(waypoint.wtype == "nav_start_stbd"):
                starboardStartInnerPoint = waypoint.coordinate
            elif(waypoint.wtype == "nav_midpoint"):
                navMidpoint = waypoint.coordinate
        
        if not (buoyCoords and portStartInnerPoint and starboardStartInnerPoint):
            gVars.logger.error("Arguments Incorrect!")
        
        self.interpolatedPoint = standardcalc.returnMidPoint(portStartInnerPoint,starboardStartInnerPoint)

        if not navMidpoint:
            halfwayBackPoint = datatypes.GPSCoordinate((self.interpolatedPoint.lat+buoyCoords.lat)/2,(self.interpolatedPoint.long+buoyCoords.long)/2)
            gVars.logger.info("Using dynamically created midpoint.")
        else:
            halfwayBackPoint = navMidpoint
            gVars.logger.info("Using user given midpoint")
            
        gVars.logger.info("Rounding Buoy")      
        if(gVars.kill_flagNav == 0):
            self.roundbuoy.run(buoyCoords)
        gVars.logger.info("Heading for Midpoint ")
        
        if(gVars.kill_flagNav == 0):
            self.pointtopoint.run(halfwayBackPoint)
        gVars.logger.info("Heading for Finish")               
        
        if(gVars.kill_flagNav == 0):
            acceptDistance = 1
            thread.start_new_thread(self.printNavigationLog, ())
            self.pointtopoint.run(self.interpolatedPoint,acceptDistance)
        
        return 0
    
    def printNavigationLog(self):
        while (gVars.kill_flagNav == 0):
            if (time.time() - self.nav_log_timer>self.LOG_UPDATE_INTERVAL):
                self.nav_log_timer = time.time()
                gVars.logger.info("Distance: "+ str(standardcalc.distBetweenTwoCoords(gVars.currentData.gps_coord, self.interpolatedPoint)))
                