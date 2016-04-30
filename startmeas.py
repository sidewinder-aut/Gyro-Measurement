#!/usr/bin/env python


# Main program for Gyro measurement. Measurement data is either gather with "my_gyro.py" or "gyro_filter.py"
# gyro_filter.py contains a complementary filter where the output of the accelerometer is postprocesed by a 
# low pass filter and then combined with the high-pass filtered gyroscope signal. The time constant of the system
# has to be considered by the formula t= XXXXXXX.
# The latest version now has interrupts and a multithreading approach. The main thread is just waiting for the 
# variable "meas_on" - If it is 0, the measurement is not performed and nothing is done. If it is 1, the measurement
# is conducted. The variable f_check decides if the output is filtered or not. 
# If the button is pressed, the interrupt is triggered with the RPi.GPIO library and the actual  switching of the modes
# is carried out - The nthe main thread is resumed.
#-----------------------------------------------------------------------------------------------------------------
#                 Date                Programmer                Version
#                27.09.2015            Eder Lucas                1.0
#                28.03.2016            Eder Lucas                2.0 - Version with Interrupts and Multithreading
#                15.04.2016            Eder Lucas                3.0 - Revised interrupt version with revised decision tree in the main loop
#                28.04.2016            Eder Lucas                4.0 - Revised interrupt version with minor bugfixes and documetation
# test
#-----------------------------------------------------------------------------------------------------------------
#--- LIBRARY IMPORT ----------------------------------------------------------------------------------------------
import time,os
import my_sys
import gyro_normal
import gyro_filter
import RPi.GPIO as GPIO
from ssl import CHANNEL_BINDING_TYPES


#-----------------------------------------------------------------------------------------------------------------
#--- HARDWARE SETUP ----------------------------------------------------------------------------------------------
GPIO.setmode(GPIO.BCM)                                          # GPIO board setup - other mode would be GPIO.BOARD    
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)               # GPIO.setup(pin number, input) - this is the on switch
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)               # GPIO.setup(pin number, input) - this is the off switch
GPIO.setup(16,GPIO.OUT)                                         # GPIO.setup(pin number, output) - this is the LED prev_input = 1
                                                                # Check variable to see if the button is pressed

#-----------------------------------------------------------------------------------------------------------------
#--- INITIALISATION OF VARIABLES ---------------------------------------------------------------------------------
global meas_on
global f_check
global counter   
global dir_num
global basedir
global dirpath


meas_on = 0                                                     # Variable to determine if the measurement is running or not
dir_num = 1                                                     # directory number --> is changed by make_dir() in my_sys.py
counter = 0.0                                                   # Current timestep variable that is written to the gyro_out.txt file
basedir = os.getcwd()                                           # Directory the python files are stored in 
f_check = True                                                  # Gyroscope Filter can be set on or off - "on" produces more accurate values for the bank angle

#-----------------------------------------------------------------------------------------------------------------
#--- Blinking sequence for diode ---------------------------------------------------------------------------------
    
def blink():
    GPIO.output(16,False)                            #--- Blinking sequence end
    time.sleep(0.25)
    GPIO.output(16,True)
    time.sleep(0.25)
    GPIO.output(16,False)
    time.sleep(0.25)        
    GPIO.output(16,True)

#-----------------------------------------------------------------------------------------------------------------
#--- Interrupt for measurement start -----------------------------------------------------------------------------
def trig_switch_on(channel):                                               # Dummythread for testing
    global meas_on
    global f_check
    global counter   
    global dir_num
    global basedir
    global dirpath
        
    if meas_on == 0:                                                        # Check if measurement was off before
        print("*****************************************************")
        print("*** Measurement starting")
        dirpath = my_sys.make_dir(dir_num)                                  #--- Creation of measurement directory
        my_sys.start_log(dirpath)
        print("*** Directory created:"), dirpath
        dir_num = dir_num + 1
        if (f_check==True):
            print("*** Filter activated ")
            gyro_filter.writeheader(dirpath)            #--- Writing of Gyro Header File (filter or no-filter check)
        elif (f_check==False):
            print("*** No filter activated")
            gyro_normal.writeheader(dirpath)
        #print("*****************************************************")
        #print("Measurement starting")
        #dirpath = my_sys.make_dir(dir_num)                #--- Creation of measurement directory
        meas_on = 1
    else:
        pass
    
    
#-----------------------------------------------------------------------------------------------------------------
#--- Interrrupt for measurement stop -----------------------------------------------------------------------------
def trig_switch_off(channel):                                               # Dummythread for testing
    global meas_on
    global f_check
    global counter   
    global dir_num
    global basedir
    global dirpath
    if meas_on == 1:
            blink()
            print("******************************************************")        
            print("Measurement stopping")    
            my_sys.stop_log(dirpath)
            if (f_check==False):                                            #--- Check if filtered or normal output should be plotted (gnuplot needs different input files)
                tmp = "gnuplot plot_input_acc.plot"         
                os.chdir(dirpath)
                os.system(tmp)
                tmp = "gnuplot plot_input_rot.plot"
                os.system(tmp)
            elif(f_check==True):
                tmp= "gnuplot plot_input_fil.plot"
                os.chdir(dirpath)
                os.system(tmp)
            inet_ok = my_sys.inet_check(dirpath)
            inet_ok = False
            if(inet_ok == True):                                            #--- Check for internet connection
                if (f_check==False):
                    my_sys.send_mail(dirpath, 1)
                    my_sys.send_mail(dirpath, 2)
                elif(f_check==True):
                    my_sys.send_mail(dirpath, 3)
            os.chdir(basedir)       
            meas_on = 0
            
            blink()
            time.sleep(3)
            tmp= "sudo shutdown now"                        #--- Automatic shudwon - This was implemented to prevent a faulty Flash drive by just plugging out the power cable
            os.system(tmp)
    else:
        pass
    
    
    
#-----------------------------------------------------------------------------------------------------------------
#--- Interrrupt event add ----------------------------------------------------------------------------------------    
GPIO.add_event_detect(20, GPIO.FALLING, callback = trig_switch_on, bouncetime = 500)         
GPIO.add_event_detect(21, GPIO.FALLING, callback = trig_switch_off, bouncetime = 500)      




#-----------------------------------------------------------------------------------------------------------------
#--- Main thread -------------------------------------------------------------------------------------------------    
try:  
    while True:
        if (meas_on == 1):                                                  # If measurement is started
            GPIO.output(16,True)
            if (f_check==True):                                             # --- Filter activated
                #glob_time_start = time.time()  
                counter = counter + 1
                gyro_filter.writedata(dirpath, counter)
                #counter = counter + (time.time() - glob_time_start)
            elif (f_check==False):                                          # --- No filter activated
                glob_time_start = time.time()               
                gyro_normal.writedata(dirpath, counter)
                counter = counter + (time.time() - glob_time_start)
        elif (meas_on == 0):
            GPIO.output(16, False)
except KeyboardInterrupt:  
    GPIO.cleanup()       # clean up GPIO on CTRL+C exit  
GPIO.cleanup()           # clean up GPIO on normal exit  


