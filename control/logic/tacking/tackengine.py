from control.logic import standardcalc
from control import global_vars as gVars

class TackEngine:
  
    def __init__(self):
        LAY_ANGLE_DEFAULT = 75
        
    def readyToTack(self, AWA, HOG, bearing):        
        if self.hitLayLine(HOG, bearing, self.getLayAngle()) and  self.beatEstablished(AWA):
            gVars.logger.info("Hit  "+str(self.getLayAngle())+" degree lay line")
            return True
        else:
            return False
          
    def getLayAngle(self):
        return self.LAY_ANGLE_DEFAULT
         
    def hitLayLine(self, HOG, bearing, layAngle):
        angleDelta = abs(standardcalc.calculateAngleDelta(HOG,bearing))
        return angleDelta > layAngle

    def beatEstablished(self, AWA):
        beatingAWATarget = 30
        beatingAWAAcceptanceDelta = 10   
        absoluteAWADelta = abs(  abs(AWA) - beatingAWATarget  )
        return  absoluteAWADelta < beatingAWAAcceptanceDelta

    def onStarboardTack(self,AWA):
        return AWA>=0
            
    def onPortTack(self,AWA):
        return AWA<0
    
    # Sets 1, or 0 for Arduino Call to Tack
    def getTackDirection(self, AWA):
        if(AWA > 0):
            return 1
        else:
            return 0
