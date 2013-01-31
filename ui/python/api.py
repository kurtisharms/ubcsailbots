import json
import unittest
from simulator import *


""" Handles all data that is passed from the API 
*EDITING NOTE: Please make sure you understand how python handles classes before making any edits to this file. Mutable data types in 
        python have to be declared as instance variables and NOT as public variables in global scope. Global scope variables are shared
        between instances and will cause messy results that do not report any errors. 
"""
class ApiControl:
    interface = Simulator()
    def __init__(self):
        # Declare all public instance variables
        self.hardwareData = ""
        # We need to update the interface with all current data. The interface class is static, but it may need to renew data
        self.interface.update()
        
    def update(self):
        self.interface.update()
        
    def getOverviewData(self):
        overviewData = self.interface.getOverviewData()
        return overviewData
    
    def getOverviewDataAsJson(self):
        return json.dumps(self.getOverviewData())
    
    def getInstructionsData(self):
        instructionData = {"challenge": {"currentlyRunning": "Point-to-Point"},
                           "waypoints": {"indicator": "123"},
                           "boundaries": {"indicator":[2,3,4]},
                           }
        return instructionData
    
    def getInstructionsDataAsJson(self):
        return json.dumps(self.getInstructionsData())
        
    
    # forces data to be updated from the Control Unit
    def forceDataUpdate(self):
        pass
    
    
    def setChallenge(self,name,arg):
        # Arguments passed as jquery 
        if name == "navigationChallenge":
            navigationChallenge(arg)
        elif name == "stationKeepingChallenge":
            stationKeepingChallenge(arg)
        elif name == "longDistanceChallenge":
            longDistanceChallenge(arg)
            
