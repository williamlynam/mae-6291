"""
==== William Lynam
======== Plant Pal Monitoring System
======== Made for MAE 6291 Midterm Project
"""

# IMPORT MODULES ====================================================

import RPi.GPIO as GPIO
import time
import yagmail
   
yag_mail = yagmail.SMTP(user='willlynam@gmail.com', password="dlmx dfmk vlip nean", host='smtp.gmail.com')

# =====================================================================
# INTIALIZE GPIO-PINS =================================================
# Declare the channels for each device

WSENSOR = 22 #Water Sensor
RedLED = 26 #Red LED
GreenLED = 13 #Green LED
DHTPIN = 17 #Humiture Sensor

GPIO.setwarnings(False)
# =====================================================================

        
# User Changable Variables=============================================
watering_time = 20
cooldown_time = 5
max_humidity = 70
min_humidity = 5
max_temp = 35
min_temp = 0
To = ""
Temp_Subject = "HELP ME!!"
Temp_Body = """
            My temperature and humidity are wrong! Please come and fix it as soon as possible!
            """
Water_Subject = "I need water!"
Water_Body = """
             It's been a while since you've watered me... Please give me some water so I don't die :(
             """

MAX_UNCHANGE_COUNT = 100

# DEFINE FUNCTIONS ====================================================
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Set up GPIO mode and define input and output pins

def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(WSENSOR, GPIO.IN)
    GPIO.setup(RedLED, GPIO.OUT)
    GPIO.setup(GreenLED, GPIO.OUT)

#    global buzz
#    buzz = GPIO.PWM(SPEAK, 400) #S ets the speaker's channel to 440hz
#    buzz.start(100) # Sends a constant high voltage (duty cycle of 100%)

#Humiture Sensor Function
STATE_INIT_PULL_DOWN = 1
STATE_INIT_PULL_UP = 2
STATE_DATA_FIRST_PULL_DOWN = 3
STATE_DATA_PULL_UP = 4
STATE_DATA_PULL_DOWN = 5
def read_dht11_dat():
    GPIO.setup(DHTPIN, GPIO.OUT)
    GPIO.output(DHTPIN, GPIO.HIGH)
    time.sleep(0.05)
    GPIO.output(DHTPIN, GPIO.LOW)
    time.sleep(0.02)
    GPIO.setup(DHTPIN, GPIO.IN, GPIO.PUD_UP)

    unchanged_count = 0
    last = -1
    data = []
    while True:
        current = GPIO.input(DHTPIN)
        data.append(current)
        if last != current:
            unchanged_count = 0
            last = current
        else:
            unchanged_count += 1
            if unchanged_count > MAX_UNCHANGE_COUNT:
                break

    state = STATE_INIT_PULL_DOWN

    lengths = []
    current_length = 0

    for current in data:
        current_length += 1

        if state == STATE_INIT_PULL_DOWN:
            if current == GPIO.LOW:
                state = STATE_INIT_PULL_UP
            else:
                continue
        if state == STATE_INIT_PULL_UP:
            if current == GPIO.HIGH:
                state = STATE_DATA_FIRST_PULL_DOWN
            else:
                continue
        if state == STATE_DATA_FIRST_PULL_DOWN:
            if current == GPIO.LOW:
                state = STATE_DATA_PULL_UP
            else:
                continue
        if state == STATE_DATA_PULL_UP:
            if current == GPIO.HIGH:
                current_length = 0
                state = STATE_DATA_PULL_DOWN
            else:
                continue
        if state == STATE_DATA_PULL_DOWN:
            if current == GPIO.LOW:
                lengths.append(current_length)
                state = STATE_DATA_PULL_UP
            else:
                continue
    if len(lengths) != 40:
        #print ("Data not good, skip")
        return False

    shortest_pull_up = min(lengths)
    longest_pull_up = max(lengths)
    halfway = (longest_pull_up + shortest_pull_up) / 2
    bits = []
    the_bytes = []
    byte = 0

    for length in lengths:
        bit = 0
        if length > halfway:
            bit = 1
        bits.append(bit)
    #print ("bits: %s, length: %d" % (bits, len(bits)))
    for i in range(0, len(bits)):
        byte = byte << 1
        if (bits[i]):
            byte = byte | 1
        else:
            byte = byte | 0
        if ((i + 1) % 8 == 0):
            the_bytes.append(byte)
            byte = 0
    #print (the_bytes)
    checksum = (the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3]) & 0xFF
    if the_bytes[4] != checksum:
        #print ("Data not good, skip")
        return False

    return the_bytes[0], the_bytes[2]


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~                
# Main Control Loop for the system

def loop():
    remaining_time = watering_time
    remaining_cooldown = cooldown_time
    water_email_flag = 0
    temp_email_flag = 0
    temp_error = 0
    while True:
        result = read_dht11_dat()
        if remaining_cooldown > 0:
            wstate = 0
            remaining_cooldown -= 1
        else:
            remaining_cooldown = cooldown_time
            wstate = GPIO.input(WSENSOR)
        
        if wstate:
            print("Thank you for watering me!")
            remaining_time = watering_time
        
        if result:
            humidity, temperature = result
            print ("humidity: %s %%,  Temperature: %s C" % (humidity, temperature))
            if humidity > max_humidity or humidity < min_humidity or temperature > max_temp or temperature < min_temp:
                temp_error = 1
            else:
                temp_error = 0
                
        if remaining_time > 0:
            print(f"Time remaining: {remaining_time}", end="\r")
            remaining_time -= 1
          
        if temp_error:
            GPIO.output(GreenLED, GPIO.LOW)
            GPIO.output(RedLED, GPIO.HIGH)
            if temp_email_flag == 0:
                print ("\nTemperature Email Sent")
                yag_mail.send(to=To, subject=Temp_Subject, contents=Temp_Body)
                temp_email_flag = 1
                
        elif remaining_time == 0:
            GPIO.output(GreenLED, GPIO.LOW)
            GPIO.output(RedLED, GPIO.HIGH)
            if water_email_flag == 0:
                print ("\nWater Email Sent")
                yag_mail.send(to=To, subject=Water_Subject, contents=Water_Body)
                water_email_flag = 1
        else:
            GPIO.output(GreenLED, GPIO.HIGH)
            GPIO.output(RedLED, GPIO.LOW)
            temp_email_flag = 0
            water_email_flag = 0
            
                
            
        
            
        time.sleep(1)
            
            
        

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~        
# CLEAR GPIO CHANNELS, STOP Buzzer and close CSV FILEs

def destroy():
    GPIO.cleanup()

# ====================================================================
# MAIN FUNCTION to RUN PROGRAM  ======================================

if __name__ == '__main__':
    setup()
    try:
        loop()
    except KeyboardInterrupt: #Quits out on ctrl+c
        destroy()
# ====================================================================
