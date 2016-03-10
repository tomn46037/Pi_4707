#NWRSAME_v2.py - Python library for controling the Silicon Labs Si4707 in I2C mode (Raspberry Pi)
#
#This file incorporates a conversion of the provided Arduino code for AIW Industries Si4707
#breakout module with the following license information
#------------------------------------------------------------------------
#Copyright 2013 by Ray H. Dees
#Copyright 2013 by AIW Industries, LLC
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program. If not, see <http:#www.gnu.org/licenses/>.
#------------------------------------------------------------------------
#
import RPi.GPIO as GPIO
from SI4707_I2C_v2 import SI4707
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import sys
import select
import operator
import time
import signal


#================================================================
#
# Si4707 Basic Demonstration Program.
#
#  16 JUN 2013
#
#  Note:
#
#  You must set your own startup frequency in setup().
#  You must enable the interrupts that you want in setup().
#
#===============================================================
#==============================================================
#       Setup
#=============================================================


#  Prints the Function Menu.


def showMenu():
        print "\nDisplay this menu =\t 'h' or '?'"
        print "Channel down =\t\t 'd'"
        print "Channel up =\t\t 'u'"
        print "Scan =\t\t\t 's'"
        print "Volume - =\t\t '-'"
        print "Volume + =\t\t '+'"
        print "Toggle Mute =\t\t 'm'"
        print "On / Off =\t\t 'o'"
	print "Check AGC =\t\t 'a'"
	print "Toggle AGC =\t\t 'A'"
        print "Signal Quality Check =\t 'r'"
	print "Toggle Relay 1 =\t '1'"
	print "Toggle Relay 2 =\t '2'"
	print "Send Test Email=\t 'z'"

def relayOn(relay):
	global relayActive1
	global relayActive2
	GPIO.output(relay, GPIO.HIGH)
	if (relay == 13):
                relayActive1 = 1
		print "Relay 1 On"
		return
	elif (relay == 19):
		relayActive2 = 1
		print "Relay 2 On"
		return		
	else:
		return

def relayOff(relay):
	global relayActive1
	global relayActive2
	GPIO.output(relay, GPIO.LOW)
	if (relay == 13):
		relayActive1 = 0
		print "Relay 1 Off"
		return
	elif (relay == 19):
		relayActive2 = 0
		print "Relay 2 Off"
		return		
	else:
		return



clnComplete = 0
eomCnt = 0
msg = ""
testMsg = "Pi2 4707 Test Message Activated"


#***Relay specific variables for Pi Board***#
relayTrigger1 = 0
relayActive1 = 0
relayTimerStart1 = 0
relayTrigger2 = 0
relayActive2 = 0
relayTimerStart2 = 0
relay1 = 13
relay2 = 19
#*******************************************#

radio = SI4707(0x22 >> 1)

GPIO.setmode(GPIO.BCM) # Use board pin numbering

GPIO.setup(17, GPIO.OUT) #  Setup the reset pin
GPIO.output(17, GPIO.LOW)    #  Reset the Si4707.  
time.sleep(radio.PUP_DELAY)
GPIO.output(17, GPIO.HIGH)

GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.add_event_detect(23, GPIO.FALLING)

#************This section is for the Pi specific board only******************#
# Each relay has a 3 pin jumper that allows you to establish whether you want
# the disabled state to be normally open (NO) or normally closed (NC). Place the 
# jumper accordingly. LOW=Disabled and HIGH=Active.
GPIO.setup(relay1, GPIO.OUT)  #setup GPIO pin for relay 1
GPIO.setup(relay2, GPIO.OUT)  #setup GPIO pin for relay 2
GPIO.output(relay1, GPIO.LOW) #boot to disabled state
GPIO.output(relay2, GPIO.LOW) #boot to disabled state
#****************************************************************************#

print "\n\nStarting up the Si4707.......\n"

time.sleep(1)
radio.patch();        #  Use this one to to include the 1050 Hz patch.
#radio.on();           #  Use this one if not using the patch.
time.sleep(2)
radio.getRevision(); #  Only captured on the logic analyzer - not displayed.
showMenu();


#  All useful interrupts are enabled here.


radio.setProperty(radio.GPO_IEN, (radio.CTSIEN | radio.ERRIEN | radio.RSQIEN | radio.SAMEIEN | radio.ASQIEN | radio.STCIEN))

#  RSQ Interrupt Sources.

radio.setProperty(radio.WB_RSQ_SNR_HIGH_THRESHOLD, 0x007F);   # 127 dBuV for testing.
radio.setProperty(radio.WB_RSQ_SNR_LOW_THRESHOLD, 0x0001);    # 1 dBuV for testing
radio.setProperty(radio.WB_RSQ_RSSI_HIGH_THRESHOLD, 0x004D);  # -30 dBm for testing
radio.setProperty(radio.WB_RSQ_RSSI_LOW_THRESHOLD, 0x0007);   # -100 dBm for testing

#Uncomment next line if you want the above interrupts to take place.
#Radio.setProperty(radio.WB_RSQ_INT_SOURCE, (radio.SNRHIEN | radio.SNRLIEN | radio.RSSIHIEN | radio.RSSILIEN)

#  SAME Interrupt Sources.

radio.setProperty(radio.WB_SAME_INTERRUPT_SOURCE, (radio.EOMDETIEN | radio.HDRRDYIEN))

#  ASQ Interrupt Sources.

radio.setProperty(radio.WB_ASQ_INT_SOURCE, radio.ALERTONIEN)

#  Tune to the desired frequency.
time.sleep(0.5)
radio.tuneDirect(162550)  #  Change to local frequency. 6 digits only.
radio.setAGCStatus(0x01) #Disables AGC
#if your unsure of local frequency or there are more than one, uncomment next line
#and it will select best frequncy to boot to. Besure to comment out radio.tuneDirect.

#radio.scan()

time.sleep(0.5)

#===================================================================
#Main Loop.
#===================================================================


def mainProgram():

        while True:
                
                global eomCnt
		global msg
                global relayTrigger1
                global relayTimerStart1
                global relayActive1
 
                if GPIO.event_detected(23):
                        getStatus();
                if (radio.intStatus & radio.INTAVL):
                        #print hex(radio.intStatus), hex(radio.INTAVL)
                        getStatus();

#*********************************
# User Input code taken from here:
#http://repolinux.wordpress.com/2012/10/09/non-blocking-read-from-stdin-in-python/
#*********************************
        # If there's input ready, do something, else do something
        # else. Note timeout is zero so select won't block at all.
                while sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                        proc = (sys.stdin.readline())
                        proc = proc
                        #print "User Input:", proc
                        if (proc):
                                getFunction(proc)

                        else:
                                return

		if (eomCnt > 2):
			eomCnt = 0
                        radio.getSameStatus(radio.INTACK)
			#sendAlert(msg)
                        
#***************Example of 15 sec relay timer setup once a relayTrigger is activated*****************#
                if (relayTrigger1 == 1 and relayActive1 == 0): #relay trigger active but not yet on
                        relayOn(relay1)
                        relayTimerStart1 = time.time() #establish a start time for timer
                        
                #Continually check current time against relay start time to deactivate as necessarry
                if (relayTrigger1 == 1 and relayActive1 == 1):
                        currentTime = time.time()
			print "Starting relay Timer\n"
                    
                        if (currentTime - relayTimerStart1 >= 15): #15 sec timer
                                relayOff(relay1)
                                relayTimerStart1 = 0
                                relayTrigger1 = 0
#*****************************************************************************************************#   

#  Status bits are processed here.

def getStatus():

        radio.getIntStatus()

        if (radio.intStatus & radio.STCINT):
                radio.getTuneStatus(radio.INTACK)  # Using INTACK clears STCINT, CHECK preserves it.
                print "FREQ:", radio.frequency, " RSSI:", int(radio.rssi-107), "dBm", " SNR:", int(radio.snr), "dBuV\n"
                radio.sameFlush()    # This should be done after any tune function.
                #radio.intStatus = ior(radio.intStatus,radio.RSQINT)  # We can force it to get rsqStatus on any tune.


        if (radio.intStatus & radio.RSQINT):
                radio.getRsqStatus(radio.INTACK)
                print "RSSI:", int(radio.rssi-107), "dBm", " SNR:", int(radio.snr), "dBuV", " FREQOFF:", radio.freqoff

        if (radio.intStatus & radio.SAMEINT):
                radio.getSameStatus(radio.INTACK)

                if (radio.sameStatus & radio.EOMDET):
                        global eomCnt
                        radio.sameFlush()
                        print "EOM detected.\n"
                        eomCnt = eomCnt + 1
                        #print int(eomCnt)			
                        ##More application specific code could go here. (Mute audio, turn something on/off, etc.)
                        return
                if (radio.msgStatus & radio.MSGAVL and (not(radio.msgStatus & radio.MSGUSD)) and radio.sameHeaderCount >=3): # If a message is available and not already used,
                        radio.sameParse()
			
                	if (radio.msgStatus & radio.MSGPAR):			
                        	global msg
                        	global relayTrigger1 # used to activate relay

                        	#Example of looking for a specific event code..i.e. TOR for Tornado
                        	if (radio.sameEventName[0] == 'T' and radio.sameEventName[1] == 'O' and radio.sameEventName[2] == 'R'):
                                	#print "Event Match True!"
                                	relayTrigger1 = 1 #trigger relay1 based on Tornado event
                               
                        	msg = "ZCZC"
                        	radio.msgStatus = operator.iand(radio.msgStatus,~radio.MSGPAR) # Clear the parse status, so that we don't print it again.
                        	#print ''.join(radio.finalMsg), "\n"
                        	msg = msg + str(''.join(radio.finalMsg))
                        	msg = msg + "\n\n"
                        	print "Originator: ", ''.join(radio.sameOriginatorName)
                        	msg = msg + "Originator: "
                        	msg = msg + str(''.join(radio.sameOriginatorName))
                        	msg = msg + "\n"
                        	print "Event: ", ''.join(radio.sameEventName)
                        	msg = msg + "Event: "
                        	msg = msg + str(''.join(radio.sameEventName))
                        	msg = msg + "\n"
                       	 	print "Locations: ", int(radio.sameLocations)
                        	msg = msg + "Locations: "
                        	msg = msg + str(int(radio.sameLocations))
                        	msg = msg + "\n"
                        	print "Location Codes:"
                        	msg = msg + "Location Codes: "                        
                        	print ', '.join(radio.sameLocationCodes)
                        	msg = msg + str(','.join(radio.sameLocationCodes))			
                        	print "\nDuration: ", ''.join(radio.sameDuration)
                        	msg = msg + "\nDuration: "
                        	msg = msg + str(''.join(radio.sameDuration))
                        	msg = msg + "\n"
                        	print "Day: ", ''.join(radio.sameDay)
                        	msg = msg + "Day: "
                        	msg = msg + str(''.join(radio.sameDay))
                        	msg = msg + "\n"
                        	print "Time: ", ''.join(radio.sameTime)
                        	msg = msg + "Time: "
                        	msg = msg + str(''.join(radio.sameTime))
                        	msg = msg + "\n"
                        	print "Callsign: ", ''.join(radio.sameCallSign), "\n"
                        	msg = msg + "Callsign: "
                        	msg = msg + str(''.join(radio.sameCallSign))
                        	msg = msg + "\n"		

                if (radio.msgStatus & radio.MSGPUR):  #  Signals that the third header has been received.
                        radio.sameFlush()

                
        if ((radio.intStatus & radio.ASQINT) or (radio.sameWat == 0x01)):
                radio.getAsqStatus(radio.INTACK)
                #print "sameWat:" , hex(radio.sameWat), "ASQ Stat:", hex(radio.asqStatus)

                if (radio.sameWat == radio.asqStatus):
                        return

                if (radio.asqStatus == 0x01):
                        radio.sameFlush()
                        print "\n1050Hz Alert Tone: ON\n"
			radio.sameWat = radio.asqStatus
		if (radio.asqStatus == 0x02):
                        print "1050Hz Alert Tone: OFF\n"
			radio.sameWat = radio.asqStatus

        if (radio.intStatus & radio.ERRINT):
                radio.intStatus = operator.iand(radio.intStatus,~radio.ERRINT)
                print "An error occured!\n"

        return

def sendAlert(alert):
	# Credentials (if needed)
	# For GMAIL you may need to provide your device an app password to be able to log in.
	# Go to this address to add an app password and enter the password below:
	# https://security.google.com/settings/security/apppasswords
        username = "emailaddress to be accessed"
        password = "password"
        
        #Referenced from:http://stackoverflow.com/questions/8856117/how-to-send-email-to-multiple-recipients-using-python-smtplib
	
	fromaddr = username
        toaddrs  = "onereceipient@email.com"
        #toaddrs = "email1@email.com,textnumber@txt.att.net"
	emsg = MIMEMultipart()
	emsg["From"] = fromaddr
	emsg["To"] = toaddrs
	#emsg['Cc'] = ...
	emsg["Subject"] = "Pi SAME Alert" 
	body = MIMEText(alert)
	emsg.attach(body)
	server = smtplib.SMTP("mailhost.example.com", 25) #gmail is smtp.gmail.com, 587
       	server.starttls()
       	server.login(username,password)
	server.sendmail(emsg["From"],emsg["To"].split(","),emsg.as_string())
       	server.quit()
	print "Message Sent"
	return

def getFunction(function):

        #print "getFunction:", function
        if (function == 'h') or (function == 'h\n') or (function == '?') or (function == '?\n'):
                showMenu();

        elif (function == 'd') or (function == 'd\n'):
                if radio.currentFreq == 0:
                        return
                radio.currentFreq -= 1
                radio.tune(radio.freqLowByte[radio.currentFreq])
                return

        elif (function == 'u') or (function == 'u\n'):
                if radio.currentFreq == 6:
                        return
                radio.currentFreq += 1
                radio.tune(radio.freqLowByte[radio.currentFreq])
                return

        elif (function == 's') or (function == 's\n'):
                print "Scanning.....\n"
                radio.scan()
                return
       
        elif (function == 'a') or (function == 'a\n'):
                radio.getAGCStatus()
                return

	elif (function == 'A') or (function == 'A\n'):
                if (radio.agcStatus == 0x00):
                        radio.setAGCStatus(0x01)
			return
                else:
                        radio.setAGCStatus(0x00)
                        return

        elif (function == '-') or (function == '-\n'):
                if (radio.volume <= 0x0000): return
                radio.volume -= 1
                radio.setVolume(radio.volume)
                print "Volume:", int(radio.volume)
                return

        elif (function == '+') or (function == '+\n'):
                if (radio.volume >= 0x003F): return
                radio.volume += 1

	elif (function == 'm') or (function == 'm\n'):
                if (radio.mute):
                        radio.setMute(radio.OFF)
                        print "Mute: Off"
                        return
                else:
                        radio.setMute(radio.ON)
                        print "Mute: On"
                        return		
		
        elif (function == 'o') or (function == 'o\n'):
                if (radio.power):
                        radio.off()
                        print "Radio powered off."
                        return
                else:
                        radio.on()
                        print "Radio powered on."
                        radio.tune(radio.freqLowByte[radio.currentFreq])
                        return

	elif (function == 'r') or (function == 'r\n'):
		radio.getRsqStatus(radio.CHECK)
		return

	elif (function == 'z') or (function == 'z\n'):
                sendAlert(testMsg)
                return
		
        elif (function == '1') or (function == '1\n'):
                if (relayActive1 == 0):
                        relayOn(relay1)
                        return
                else:
                        relayOff(relay1)
                        return
					
        elif (function == '2') or (function == '2\n'):
                if (relayActive2 == 0):
                        relayOn(relay2)
                        return
                else:
                        relayOff(relay2)
                        return
				
        else:
                print "Menu Command Not Recognized"
                return


def handler(signum, frame):
	global clnComplete
	print "Ctrl+Z pressed, but ignored"
	GPIO.cleanup();
	clnComplete = 1
	return 

signal.signal(signal.SIGTSTP, handler)


if __name__ == '__main__':
		
	try:
		while 1:
			mainProgram();
	
	except KeyboardInterrupt:
		print "CTRL+C pressed!"
		
	except:
		print "Other error or exception occurred!"
	
	finally:
		print "Program Exiting Now"
		if (clnComplete == 0):
			GPIO.cleanup();
			print "GPIO cleared for next usage"
