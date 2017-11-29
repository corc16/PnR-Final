import pigo
import time  # import just in case students need
import datetime
import random

# setup logs
import logging
LOG_LEVEL = logging.INFO
LOG_FILE = "/home/pi/PnR-Final/log_robot.log"  # don't forget to make this file!
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
logging.basicConfig(filename=LOG_FILE, format=LOG_FORMAT, level=LOG_LEVEL)


class Piggy(pigo.Pigo):
    """Student project, inherits teacher Pigo class which wraps all RPi specific functions"""



    def __init__(self):
        """The robot's constructor: sets variables and runs menu loop"""
        print("I have been instantiated!")
        self.next_right = True
        # So our robot can find the right way to turn so it can keep moving forward
        self.start_time = datetime.datetime.utcnow()
        # Our servo turns the sensor. What angle of the servo( ) method sets it straight?
        self.MIDPOINT = 83
        # YOU DECIDE: How close can an object get (cm) before we have to stop?
        self.SAFE_STOP_DIST = 35
        self.HARD_STOP_DIST = 20
        # YOU DECIDE: What left motor power helps straighten your fwd()?
        self.LEFT_SPEED = 105
        # YOU DECIDE: What left motor power helps straighten your fwd()?
        self.RIGHT_SPEED = 115
        # This one isn't capitalized because it changes during runtime, the others don't
        self.turn_track = 0
        # Our scan list! The index will be the degree and it will store distance
        self.scan = [None] * 180
        self.set_speed(self.LEFT_SPEED, self.RIGHT_SPEED)
        # let's use an event-driven model, make a handler of sorts to listen for "events"
        while True:
            self.stop()
            self.menu()



    def menu(self):
        """Displays menu dictionary, takes key-input and calls method"""
        ## This is a DICTIONARY, it's a list with custom index values
        # You may change the menu if you'd like to add an experimental method
        menu = {"n": ("Navigate forward", self.nav),
                "d": ("Dance", self.dance),
                "o": ("Obstacle count", self.detect),
                "c": ("Calibrate", self.calibrate),
                "h": ("Restore Heading", self.test_restore_heading),
                "s": ("Check status", self.status),
                "q": ("Quit", quit_now)
                }
        # loop and print the menu...
        for key in sorted(menu.keys()):
            print(key + ":" + menu[key][0])
        # store the user's answer
        ans = raw_input("Your selection: ")
        # activate the item selected
        menu.get(ans, [None, error])[1]()

    #######################################################################################
    # DANCE ROUTINE
    def dance(self):
        """executes a series of methods that add up to a compound dance"""
        print("\n---- LET'S DANCE ----\n")
        ##### WRITE YOUR FIRST PROJECT HERE
        if self.safety_check():
            self.sprinkler()
            self.thriller()
            self.shooting_stars()

    def safety_check(self):
        """checks surrounding areas to make sure it has room to dance"""
        self.servo(self.MIDPOINT)  # Looks straight ahead
        for x in range(4):
            if not self.is_clear():
                return False
            print("Check Distance")
            self.encR(8)
        print("Safe to dance!")
        return True

    def sprinkler(self):
        """robot does the sprinkler dance"""
        self.set_speed(100, 100)
        for x in range(3):   # Loops the sprinkler dance three times
            for x in range(10):
                self.encR(1)
                self.servo(70)    # Moves head while doing the sprinkler
                self.servo(self.MIDPOINT)
            self.encL(18)

    def thriller(self):
        """robot does a version of the dance from Thriller"""
        self.set_speed(110, 105)
        self.encR(5)
        self.encF(20)
        for x in range(3):
            self.encR(31)
            self.encL(34)
        self.encR(20)
        self.encF(45)
        for x in range(3):
            self.encR(31)
            self.encL(34)
            self.stop()   # Allows robot to do shooting_stars while standing still

    def shooting_stars(self):
        """moves head back and forth quickly seven times"""
        for x in range(7):    # Brings head to 55 degrees then back to midpoint 7 times in a row
            self.servo(55)
            self.servo(self.MIDPOINT)

##########################################################################################################

    def restore_heading(self):
        """Uses self.turn_track to reorient to original heading"""
        print("Restoring heading!")
        if self.turn_track > 0:     # If the turn track is below zero it turns left
                self.encL(abs(self.turn_track))
        elif self.turn_track < 0:    # If the turn track is above zero it turns right
                self.encR(abs(self.turn_track))

    def nav(self):
        """auto pilots and attempts to maintain original heading"""
        logging.debug("Starting the nav method")
        print("-----------! NAVIGATION ACTIVATED !------------\n")
        print("-------- [ Press CTRL + C to stop me ] --------\n")
        print("-----------! NAVIGATION ACTIVATED !------------\n")
        right_now = datetime.datetime.utcnow()
        difference = (right_now - self.start_time).seconds
        print("It took you %d seconds to run this" % difference)
        while True:
            if self.is_clear():
                self.servo(self.MIDPOINT)
                self.cruise()  # Cruise forward until it gets to stopping distance
            else:
                self.encB(1)   # Piggy backs up to be able to turn better
                self.rl_turn()   # Turn to find the best bath

    def rl_turn(self):
        """Method that turns right and left until open path"""
        if self.next_right:  # Turn right first
            while self.dist() < self.SAFE_STOP_DIST:
                self.encR(5)
                time.sleep(.5)
            self.next_right = False
        else:  # If object is in the way to the right robots turns left
            while self.dist() < self.SAFE_STOP_DIST:
                self.encL(7)
                time.sleep(.5)
            self.next_right = True

    def smooth_turn(self):
        """Another rotation method"""
        self.right_rot()
        start = datetime.datetime.utcnow()
        self.servo(self.MIDPOINT)
        while True:
            if self.dist() > 100:
                self.stop()
            elif datetime.datetime.utcnow() - start > datetime.timedelta(seconds=10):  # Robot stops after 10 sec turn
                self.stop()
            time.sleep(.2)

    def cruise(self):
        """Drive straight while path is clear"""
        self.fwd()
        while self.dist() > self.SAFE_STOP_DIST:
            time.sleep(.5)
        self.stop()

    def test_restore_heading(self):
        """Test the restore_heading method"""
        self.encR(5)
        self.encL(15)
        self.encR(10)
        self.encL(10)
        self.encL(3)
        self.restore_heading()  # Moves robot in different directions and then back to original spot

    def detect(self):
        """scans surround area and counts the number of objects within sight"""
        self.wide_scan()  # Check surrounding areas for object using servo
        found_something = False
        counter = 0
        for dist in self.scan:
            if dist and dist < 95 and not found_something:
                found_something = True
                counter += 1  # Counts every object that is sees
                print("Object # %d found, I think" % counter)
            if dist and dist > 95 and found_something:
                found_something = False
        print("\n----I SEE %d OBJECTS----\n" % counter)



####################################################
############### STATIC FUNCTIONS

def error():
    """records general, less specific error"""
    logging.error("ERROR")
    print('ERROR')


def quit_now():
    """shuts down app"""
    raise SystemExit

##################################################################
######## The app starts right here when we instantiate our GoPiggy


try:
    g = Piggy()
except (KeyboardInterrupt, SystemExit):
    pigo.stop_now()
except Exception as ee:
    logging.error(ee.__str__())
