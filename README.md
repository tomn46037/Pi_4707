# Pi_4707
If you have not already used your Pi with Adafruit Python and I2C libraries Please follow the initial setup instructions located at http://www.aiwindustries.com/raspberry-pi-operation.html prior to using the code

This code is specially for the 4707 NOAA Weather Receiver board with built in Pi B+/2 40 pin header and relays. It will work with the original breadboard receiver module, but the you will need to comment out the relay operations as they won't do anything other than activate the GPIO pins that are attached in the code. 

relay1 is on GPIO 13
relay2 is on GPIO 19

Activation/Deactivation is very easy to implement in the code as you see fit. relayOn(relay1) and relayOff(relay2)...change relay numbers as needed withing the function argument. I also implemented a menu function to toggle both relays for testing purposes.

Both relays utilize 2222A transistors to activate the relays in order to put less stress on the GPIO pin itself.

This is included in the code notes, but if you decide to use the email or email to text feature to send alert notifications...GMAIL may need to provide your device an app password to be able to log in and send the alerts. Go to this address to add an app password and enter the password in your code so it can access you email server. I have placed a menu function to send a sample message using your email setup for testing purposes.

https://security.google.com/settings/security/apppasswords


The new Pi reveiver board has a built in low noise amplifier circuit that provides roughly +20dB of gain on the front end. This greatly improves reception performance even in areas you may not normally receive the signal. The 4707 by defualt will come up with AGC enabled which I have found actually attenuates the signal strength even when it is not close to the 0dBm max input. I have left it as is, but have included functions to disable AGC if you would like to in order to see a true representation of RSSI (signal strength) being seen with the use of the LNA circuit. To disable in the code just uncomment the setAGCStatus(0x01) after the initial tune function. If you want to test first I also established a menu function to toggle AGC. You should see a difference when you toggle AGC and then use "r" to check the signal quality. You can check the current status of the AGC by entering "a". 0: AGC enabled, 1: AGC disabled

3/10/16 Update:
I have fixed the way the messages are displayed when received, as well as indicating when the 1050Hz tone is present. The messages, if you are monitoring/controlling via a terminal will lok like this:

-WXR-RWT-029095-029091+0030-1511229-KEAX/NWS 
12222222333333333333333333333333333333333333 

Originator:  WXR 
Event:  RWT 
Locations:  2
Location Codes:
029095 , 029091 

Duration:  0030 
Day:  151 
Time:  1229 
Callsign:  KEAX/NWS  


 
-WXR-RWT-029095-029091+0030-1511229-KEAX/NWS 
33332222333333333333333333333333333333333333 


 
-WXR-RWT-029095-029091+0030-1511229-KEAX/NWS 
33333333333333333333333333333333333333333333 


1050Hz Alert Tone: ON

1050Hz Alert Tone: OFF

EOM detected.

EOM detected.

EOM detected.

The numbers under the the message are quality indicators for each message character above it on a scale from 0 to 3. You can see that even when the quality indicators are low (1 for example) the 4707 is still able to reliably decode the message. I have seen where some terminal programs space out these numbers instead of having them grouped together. I may see if there is a better way to print them out then how I'm doing it now.
