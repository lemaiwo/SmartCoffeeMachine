#-----------------------------
#    IMPORT LIBRARIES
#-----------------------------

import RPi.GPIO as GPIO
import time, sys, sched, threading, datetime, math, shlex, subprocess, os, requests

#-----------------------------
#    CONNECTION SETUP
#-----------------------------

hostiot4 ='flexso.eu10.cp.iot.sap/iot/gateway/rest'


path = '/measures/1743'
capabilityAltID='1741'
sensorAlternateId='1744'


url = "https://"+hostiot4+path


#-----------------------------
#    SETUP GPIO FLOW SENSOR
#-----------------------------

FLOW_SENSOR = 26
GPIO.setmode(GPIO.BCM)
GPIO.setup(FLOW_SENSOR, GPIO.IN, pull_up_down = GPIO.PUD_UP)


#-----------------------------
#    CREATE VARIABLES
#-----------------------------

maxDebietInUur = []
maxDebietInUurTimestamp = []
allPulses = []
localPulses = []
maxLiter = []
coffeeTaken = ""
onderhoud = False
coffee = False
isTimeSet = False


#-----------------------------
#    SETUP FUNCTIONS
#-----------------------------

# Create funciton for flow measuring
global count
count = 0

def countPulse(channel):
   global count
   if start_counter == 1:
      count = count+1


# Start the flow listener
GPIO.add_event_detect(FLOW_SENSOR, GPIO.FALLING, callback=countPulse)



def MeasureCountFlow():
   global start_counter
   global flow
   global count
   global onderhoud
   global coffee
   global startDoorloopTijd
   global stopDoorloopTijd
   global isTimeSet
   global allPulses
   global localPulses
   global maxLiter
   global coffeeTaken
   global maxDebietInUur
   global maxDebietInUurTimestamp
   
   start_counter = 1
   time.sleep(1)
   start_counter = 0
   flow = (count * 60 * 2.25 / 1000)
   
   if flow > 0:
      if flow > 120:
         onderhoud = True
         print("Onderhoud bezig...")
         
      else:
         print("count: ", str(count))
         print("The flow is: %.3f Liter/min" % (flow))
         if onderhoud != True:
            coffeeTaken = datetime.datetime.now()
            
            if isTimeSet != True:
               startDoorloopTijd = time.time()
               isTimeSet = True
            
            maxDebietInUur.append(flow)
            i = datetime.datetime.now()
            maxDebietInUurTimestamp.append(i.isoformat())
            
            localPulses.append(count)
            
            allPulses.append(count)
            print(maxDebietInUur)
            
            coffee = True

   if flow == 0:
         
      if coffee != False:
            print("Ready to break en het was coffee!")
            
            #STOP DE TIMER VAN DE DOORLOOPTIJD
            stopDoorloopTijd = time.time()

            
            coffee = False
            localPulses = []
            isTimeSet = False
            aantalLiter = ((sum(allPulses) * 2.25) /1000)
        
            #post data to SAP
            payload ="{ \"capabilityAlternateId\": \""+str(capabilityAltID)+"\",\"sensorAlternateId\": \""+str(sensorAlternateId)+"\", \"measures\":" + "{\"CoffeeTakenTimeStamp\":" + "\"" + str(coffeeTaken)+ "\"" +", \"MaxFlow\":" + "\"" + str(max(maxDebietInUur))+ "\"" +",\"MaxFlowTimeStamp\":" + "\"" + str(max(maxDebietInUurTimestamp))+ "\"" +",\"WaterFlowDuration\":" + "\"" + str(round((stopDoorloopTijd - startDoorloopTijd)%60))+ "\"" +", \"TotalLiter\":" + "\"" + str(aantalLiter) +"\"" +" }"+"}"
            headers = {'content-type': "application/json", 'cache-control': "no-cache" }
            print("Payload to post: ", payload )
            response = requests.request("POST", url, data=payload, headers=headers,cert=('./credentials.crt', './credentials.key'))
            print(response.status_code, response.text)
            
            #reset values
            coffeeTaken = ""
            maxDebietInUur = []
            maxDebietInUurTimestamp = []
            aantalLiter = ""
            allPulses= []
         
   count = 0

while True:
    try:
        MeasureCountFlow()
        
    except KeyboardInterrupt:
        print('\ncaught keyboard interrupt!, bye')
        os.system("sudo pkill python3")
        os.system("sudo pkill python")
        GPIO.cleanup()
        sys.exit()
