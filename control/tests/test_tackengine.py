#Unit tests of standardcalc.py module
import sys
sys.path.append('..')
import unittest
from control import global_vars as gVars
from control import sailbot_logger
import control.datatype.datatypes as datatypes
from control.logic.tacking import tackengine
from control.logic.tacking import roundingtackengine
from control.logic.tacking import chaseracetackengine
from control.logic import standardcalc


class TestTackEngine(unittest.TestCase):
    def setUp(self):
        self.tackengine = tackengine.TackEngine()
        gVars.logger = sailbot_logger.Logger()

    def testWhichTackWantedStarboardWanted(self):
    
        AWA = 30
        self.assertTrue(self.tackengine.onStarboardTack(AWA))
        self.assertFalse(self.tackengine.onPortTack(AWA))
    
        AWA = 150
        self.assertTrue(self.tackengine.onStarboardTack(AWA))
        self.assertFalse(self.tackengine.onPortTack(AWA))
    
        AWA = 0
        self.assertTrue(self.tackengine.onStarboardTack(AWA))
        self.assertFalse(self.tackengine.onPortTack(AWA))
    def testWhichTackWantedPortWanted(self):
        AWA = -30
        self.assertFalse(self.tackengine.onStarboardTack(AWA))
        self.assertTrue(self.tackengine.onPortTack(AWA))
        
        AWA = -150
        self.assertFalse(self.tackengine.onStarboardTack(AWA))
        self.assertTrue(self.tackengine.onPortTack(AWA))

        
    def testReadyToTackFalse(self):
        AWA =30      
        GPSCoord = datatypes.GPSCoordinate(49,-123)
        Dest = datatypes.GPSCoordinate(49.1,-123) # 0 degrees, N
        bearingToMark = standardcalc.angleBetweenTwoCoords(GPSCoord, Dest)            
        hog = 0 # N
        self.assertFalse(self.tackengine.readyToTack(AWA, hog, bearingToMark))
        
        hog = 45 # NE
        self.assertFalse(self.tackengine.readyToTack(AWA, hog, bearingToMark))
        
        hog = -45 # NW
        self.assertFalse(self.tackengine.readyToTack(AWA, hog, bearingToMark))
        
        
    def testReadyToTackTrue(self):
        AWA =30      
        GPSCoord = datatypes.GPSCoordinate(49,-123)
        Dest = datatypes.GPSCoordinate(49.1,-123) # 0 degrees, N
        bearingToMark = standardcalc.angleBetweenTwoCoords(GPSCoord, Dest)            
        hog = 90 # E
        self.assertTrue(self.tackengine.readyToTack(AWA, hog, bearingToMark))
        
        hog = -90 # NW
        self.assertTrue(self.tackengine.readyToTack(AWA, hog, bearingToMark))
    
        
    def testSetTackDirectionToPort(self):
        AWA = 130
        port=1
        self.assertEqual(self.tackengine.getTackDirection(AWA), port)
    
    def testSetTackDirectionToStarboard(self):
        AWA = -20
        starboard=0
        self.assertEqual(self.tackengine.getTackDirection(AWA), starboard)

class TestRoundingTackEngine(unittest.TestCase):
    def setUp(self):
        self.tackengine = roundingtackengine.RoundingTackEngine("starboard")
        gVars.logger = sailbot_logger.Logger()
    
    def testWhichTackWantedStarboardWanted(self):
    
        AWA = 90
        self.tackengine.initialTack = "starboard"
        self.assertTrue(self.tackengine.onStarboardTack(AWA))
        self.assertFalse(self.tackengine.onPortTack(AWA))

    def testWhichTackWantedPortWanted(self):
        AWA = 90
        self.tackengine.initialTack = "port"
        self.assertFalse(self.tackengine.onStarboardTack(AWA))
        self.assertTrue(self.tackengine.onPortTack(AWA))
    
    def testWhichTackWantedAfterInitialStarboardWanted(self):
        AWA = 30
        self.tackengine.initialTack = None
        self.assertTrue(self.tackengine.onStarboardTack(AWA))
        self.assertFalse(self.tackengine.onPortTack(AWA))

    def testWhichTackWantedAfterInitialPortWanted(self):
        AWA = -30
        self.tackengine.initialTack = None
        self.assertFalse(self.tackengine.onStarboardTack(AWA))
        self.assertTrue(self.tackengine.onPortTack(AWA))
    
    def testLayAngle90(self):
        self.tackengine.rounding ="starboard"
        self.tackengine.currentTack = "starboard"
        self.assertEqual(self.tackengine.layAngle, 90)
        
        self.tackengine.rounding ="port"
        self.tackengine.currentTack = "port"
        self.assertEqual(self.tackengine.layAngle, 90)

    def testLayAngle45(self):
        self.tackengine.rounding ="starboard"
        self.tackengine.currentTack = "port"
        self.assertEqual(self.tackengine.layAngle, 45)
        
        self.tackengine.rounding ="port"
        self.tackengine.currentTack = "starboard"
        self.assertEqual(self.tackengine.layAngle, 45)

class TestChaseRaceTackEngine(unittest.TestCase):
    def setUp(self):
        edgeBearing = 0
        rounding = "starboard"
        self.tackengine = chaseracetackengine.ChaseRaceTackEngine(rounding,edgeBearing)
        
    def testHitEdge(self):
        AWA =30
        bearingToMark = 0
        hog = 0 # N
        self.tackengine.rounding = "starboard"
        self.tackengine.currentTack = "port"
        self.assertTrue(self.tackengine.readyToTack(AWA, hog, bearingToMark))
        
        self.tackengine.rounding = "port"
        self.tackengine.currentTack = "starboard"
        self.assertTrue(self.tackengine.readyToTack(AWA, hog, bearingToMark))
        
    def testHitEdgeOnTheOKTack(self):
        AWA =30
        bearingToMark = 0            
        hog = 0 # N
        self.tackengine.rounding = "port"
        self.tackengine.currentTack = "port"
        self.assertFalse(self.tackengine.readyToTack(AWA, hog, bearingToMark))
        
        self.tackengine.rounding = "starboard"
        self.tackengine.currentTack = "starboard"
        self.assertFalse(self.tackengine.readyToTack(AWA, hog, bearingToMark))
        
    def testDidntHitEdge(self):
        AWA =30
        bearingToMark = 30
        hog = 0 # N
        self.tackengine.rounding = "port"
        self.tackengine.currentTack = "port"
        self.assertFalse(self.tackengine.readyToTack(AWA, hog, bearingToMark))
        
             
