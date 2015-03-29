#!/usr/bin/python

##################################################
# A python script to use a Raspberry Pi as a person 
# counter. 
#
# It uses an ultrasonic distance sensor to determine 
# when the invisible gate has been passed through.
#
# The script was called (by CRON) for each meal every
# day of the week for the duratrion of the meal and
# the results were uploaded to the server (in a 
# sperate thread using the uploadtoserver.py script) 
# during the meal so the catering staff could see how
# many people were left to eat and then analyse historic
# data.
#
# This was created as part of my A-Level computing 
# project.
##################################################



# import required library's
import RPi.GPIO as GPIO
import time
import sys
import subprocess
from array import *

# setup GPIO pins for this script
GPIO.cleanup()
GPIO.setmode(GPIO.BCM)

# read values from script call
global meal	
args = sys.argv
print str(args)
if len(args) == 3:
	runtime = int(args[1])
	meal = args[2].lower()
	print meal
else:
	sys.exit("Invalid parameters, should be: <runtime> <meal>")
if meal != "breakfast" and meal != "lunch" and meal != "supper":
	 sys.exit("Invalid parameters, meal must be 'breakfast', 'lunch' or 'supper'")

# define pins for the ultrasonic distance sensor
trig = 4
echo = 14
led = 24	# used for testing and debugging

# setup GPIO channels
GPIO.setup(trig, GPIO.OUT)
GPIO.output(trig, False)
GPIO.setup(echo, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(led, GPIO.OUT)


# define the getDistance function
def getDistance(triggerPin, echoPin):
	timeout = 2000 			# number of iteration before timeout

	# set the trigger to high for 0.0001s then low
	GPIO.output(triggerPin, True)
	time.sleep(0.0001)
	GPIO.output(triggerPin, False)

	# wait for the echo to go high (or timeout)
	countDown = timeout
	while(GPIO.input(echoPin) == 0 and countDown > 0):
		countDown = countDown - 1
	
	# if it did not timeout
	if countDown > 0:
		echoStart = time.time()
		countDown = 2000

		while(GPIO.input(echoPin) == 1 and countDown > 0):
			countDown = countDown - 1

		echoEnd = time.time()

		echoDuration = echoEnd - echoStart

	if countDown > 0:
		# get the distance in cm to 1dp
		distance = round((echoDuration*1000000)/58, 1)
		return distance;
	else:
		# if it did not work then return -1.0
		return -1.0;

print "Running..." + str(runtime)

global peopleEntered
global peopleLeft
global peopleInRoom
global startTime
global lastUploadTime
global lastUploadCount

# initialise variables
peopleEntered = 0
peopleLeft = 0
peopleInRoom = 0
startTime = time.time()
lastUploadTime = 0
lastUploadCount = 0

GPIO.output(led, False)

# define function to check if someone is currently passing through the gate
def isOn(trig, echo, count):
	distance = getDistanceAverage(trig, echo)
	if distance < 60 and distance > 2:
		#print "true"
		return True
	elif distance > 60: 
		#print "false"
		return False
	elif count < 5: 
		return isOn(trig, echo, count+1)

# function to get a disatance reading so we avoid misreadings 
def getDistanceAverage(trigPin, echoPin):
	distances = array('f', [0, 0, 0])
	for i in range(0,3):
		distances[i] = getDistance(trigPin, echoPin)
		distances[i] = getDistance(trigPin, echoPin) if distances[i] < 0 else distances[i]
		time.sleep(0.01)
	diffs = array('f', [0, 0, 0])
	diffs[0] = distances[0] - distances[1]
	diffs[1] = distances[1] - distances[2]
	diffs[2] = distances[0] - distances[2]

	smallestIndex = 0
	for f in range(0,3):
		diffs[f] = diffs[f] * -1 if diffs[f] < 0 else diffs[f]
		if diffs[f] < diffs[smallestIndex]:
			smallestIndex = f
	return distances[smallestIndex]

# function to pass current count to the upload script
# the upload script is called on a seperate thread
# so that it doesn't stop the counting whilst the upload takes place
def uploadToServer(count):
	global lastUploadCount
	global lastUploadTime
	call = "sudo python /home/pi/counter/uploadtoserver.py" + " " + str(count) + " " + meal
	print call
	subprocess.call(call, shell=True)
	lastUploadTime = time.time()
	lastUploadCount = count

# loop for the length of the meal
while time.time() - startTime < runtime:
	if isOn(trig, echo, 1):
		GPIO.output(led, True)
		time.sleep(0.1)
		while isOn(trig, echo, 1):
			time.sleep(0.1)
		peopleInRoom = peopleInRoom + 1
		print 'People in room: ' + str(peopleInRoom)
	GPIO.output(led, False)
	time.sleep(0.1)

	# upload from time to time
	if peopleInRoom - lastUploadCount >= 10 or time.time() - lastUploadTime > 60:
		uploadToServer(peopleInRoom)	

# once the meal is over, ensure the data has uploaded 
# by trying three times 10 seconds apart 
# then end the process by exiting
uploadToServer(peopleInRoom)
time.sleep(10)
uploadToServer(peopleInRoom+1)
time.sleep(10)
uploadToServer(peopleInRoom)
sys.exit('complete')