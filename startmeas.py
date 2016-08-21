#!/usr/bin/env python

#==========================================================================================================================================================
#==========================================================================================================================================================
#-----------------------------------------------------------------------------------------------------------------------------------------------------------
#                        SHORT DESCRIPTION: 
#                        ==================
# Main program for Gyro measurement. Measurement data is either gather with "my_gyro.py" or "gyro_filter.py"
# gyro_filter.py contains a complementary filter where the output of the accelerometer is postprocesed by a 
# low pass filter and then combined with the high-pass filtered gyroscope signal. The time constant of the system
# has to be considered by the formula t= XXXXXXX.
# The latest version now has interrupts and a multithreading approach. The main thread is just waiting for the 
# variable "meas_on" - If it is 0, the measurement is not performed and nothing is done. If it is 1, the measurement
# is conducted. The variable f_check decides if the output is filtered or not. 
# If the button is pressed, the interrupt is triggered with the RPi.GPIO library and the actual  switching of the modes
# is carried out - Then the main thread is resumed.
#-----------------------------------------------------------------------------------------------------------------------------------------------------------
#=                     RECORD OF REVISIONS:
#                      ====================
#        Date:          Programmer:       Description of changes:
#     ========         =============     =========================
#     2015/Sep/07         L.Eder            1.0
#     2016/Mar/28         L.Eder            2.0 - Version with Interrupts and Multithreading
#     2016/Apr/15         L.Eder            3.0 - Revised interrupt version with revised decision tree in the main loop
#     2016/Apr/29         L.Eder            4.0 - Revised interrupt version with minor bugfixes and documetation
#     2016/May/16         L.Eder            4.1 - Features support for the WS2812b LED strip with special pyhton library - code is currently very messy
#     2016/Aug/21         L.Eder            4.2 - WS2812b taken out again, some rearranging in the gyro_filter.py
#==========================================================================================================================================================
#==========================================================================================================================================================

#----------------------------------------------------------------------------------------------------------------------------------------------------------
#--- LIBRARY IMPORT ---------------------------------------------------------------------------------------------------------------------------------------
import time,os
import my_sys
import gyro_normal
import gyro_filter
import RPi.GPIO as GPIO


#----------------------------------------------------------------------------------------------------------------------------------------------------------
#--- HARDWARE SETUP ---------------------------------------------------------------------------------------------------------------------------------------
#--- GPIO Pin Setup 
GPIO.setmode(GPIO.BCM)                                          # GPIO board setup - other mode would be GPIO.BOARD    
GPIO.setup(20, GPIO.IN, pull_up_down=GPIO.PUD_UP)               # GPIO.setup(pin number, input) - this is the on switch
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)               # GPIO.setup(pin number, input) - this is the off switch
GPIO.setup(16,GPIO.OUT)                                         # GPIO.setup(pin number, output) - this is the LED prev_input = 1
                                                                # Check variable to see if the button is pressed
#----------------------------------------------------------------------------------------------------------------------------------------------------------
#--- INITIALISATION OF VARIABLES --------------------------------------------------------------------------------------------------------------------------
global meas_on                                                   # Variable to determine if the measurement is running or not
global f_check                                                   # Gyroscope Filter can be set on or off - "on" produces more accurate values for the bank angle
global counter                                                   # Current timestep variable that is written to the gyro_out.txt file
global dir_num                                                   # Directory number --> is changed by make_dir() in my_sys.py
global basedir                                                   # Directory the python files are stored in 
global dirpath                                                   # Path of the measurement directory

#----------------------------------------------------------------------------------------------------------------------------------------------------------
#--- DECLARATION OF VARIABLES  ----------------------------------------------------------------------------------------------------------------------------
meas_on = 0                                                                                        
dir_num = 1                                                                                         
counter = 0.0                                                                                      
basedir = os.getcwd()                                                                               
f_check = True    
                                                                                  

#----------------------------------------------------------------------------------------------------------------------------------------------------------
#--- SIGNAL PATTERNS FOR LEDS -----------------------------------------------------------------------------------------------------------------------------
#--- Signal pattern for normal LED     
#===============================================================================
# def blink():
#     GPIO.output(16,False)                                                   #--- Blinking sequence end, set output of the GPIO low and high 
#     time.sleep(0.25)
#     GPIO.output(16,True)
#     time.sleep(0.25)
#     GPIO.output(16,False)
#     time.sleep(0.25)        
#     GPIO.output(16,True)
#===============================================================================

#----------------------------------------------------------------------------------------------------------------------------------------------------------
#--- INTERRUPT FUNCTION FOR MEASUREMENT START -------------------------------------------------------------------------------------------------------------
def trig_switch_on(channel):                                               
    # Input variables:
    # --- channel        ... definition which callback shall be used
    global meas_on                                                         # --- Variable definition see top of this code 
    global f_check
    global counter   
    global dir_num
    global basedir
    global dirpath
        
    if meas_on == 0:                                                        # --- Check if measurement was off before
        print("*****************************************************")
        print("*** Measurement starting")
        dirpath = my_sys.make_dir(dir_num)                                  # --- Creation of measurement directory
        my_sys.start_log(dirpath, f_check)                                  # --- Creation of log file
        print("*** Directory created:"), dirpath
        dir_num = dir_num + 1                                               # --- To adress the current directory, the directory number has to be increased
        if (f_check==True):                                                 # --- Check for filter and write the header for filter activated 
            print("*** Filter activated ")
            gyro_filter.writeheader(dirpath)                                
        elif (f_check==False):                                              # --- Check for filter and write the header for filter deactivated 
            print("*** No filter activated")                        
            gyro_normal.writeheader(dirpath)
        meas_on = 1                                                         # --- set meas_on variable back to activated measurement
        gyro_check = gyro_filter.gyro_wakeup()
        if gyro_check:
            print("*** Gyroscope successfully started")
            
    else:                                                                   # --- If the measurement was on before, pass through (usually this should not happen)
        pass
      
#----------------------------------------------------------------------------------------------------------------------------------------------------------
#--- INTERRUPT FUNCTION FOR MEASUREMENT STOP --------------------------------------------------------------------------------------------------------------
def trig_switch_off(channel):   
    # Input variables:
    # --- channel        ... definition which callback shall be used                                            
    global meas_on                                                          # --- Variable definition see top of this code
    global f_check
    global counter   
    global dir_num
    global basedir
    global dirpath
    if meas_on == 1:                                                        # --- Check if measurement was on before
            #blink()       
            print("*** Measurement stopping")  
            print("******************************************************")  
            my_sys.stop_log(dirpath)                                        # --- Write some stuff to the log file                      
            if (f_check==False):                                            # --- Create a plot of the unfiltered variable
                tmp = "gnuplot plot_input_acc.plot"         
                os.chdir(dirpath)
                os.system(tmp)
                tmp = "gnuplot plot_input_rot.plot"
                os.system(tmp)
            elif(f_check==True):                                            # --- Create a plot of the filtered variable
                tmp= "gnuplot plot_input_fil.plot"
                os.chdir(dirpath)
                os.system(tmp)
            inet_ok = my_sys.inet_check(dirpath)                            # --- Check for internet connection
            inet_ok = False                                                 # --- Used to switch off the e-mail sending in a hardcoded way
            if(inet_ok == True):                                            # --- If the internet connection available, send an e-mail
                if (f_check==False):                                        # --- Send unfiltered plot
                    my_sys.send_mail(dirpath, 1)
                    my_sys.send_mail(dirpath, 2)
                elif(f_check==True):                                        # --- Send filtered plot
                    my_sys.send_mail(dirpath, 3)
            os.chdir(basedir)                                               # --- Change back to base directory
            meas_on = 0                                                     # --- Reset the measurement check to "off"
#            tmp = "sudo cp -r " + dirpath + " /media/pi/HUGOII/."
#            os.system(tmp)
#            blink()
#            time.sleep(1)    
#            tmp= "sudo shutdown now"                                       #--- Automatic shudwon - This was implemented to prevent a faulty Flash drive by just plugging out the power cable
#            os.system(tmp)
    else:
        pass
    

#----------------------------------------------------------------------------------------------------------------------------------------------------------
#--- INTERRUPT EVENT ADDS AND SET OF MEASUREMENT START TIME -----------------------------------------------------------------------------------------------
GPIO.add_event_detect(20, GPIO.FALLING, callback = trig_switch_on, bouncetime = 500) 		       # Add measurement start interrupt event on pin 20 when a falling voltage is detected, the time in between nothing happens when the button is pressed is 500 ms
GPIO.add_event_detect(21, GPIO.FALLING, callback = trig_switch_off, bouncetime = 500)              # Add measurement stop interrupt event on pin 21

now = time.time()                                                                                  # Start time for the measurement log

#----------------------------------------------------------------------------------------------------------------------------------------------------------
#--- MAIN THREAD ------------------------------------------------------------------------------------------------------------------------------------------   
try:                                                                        # General try block
    while True:                                                             # Loop goes on until an error happens or the user does a keyboard interrupt
        if (meas_on == 1):                                                  # --- If measurement is started
#            GPIO.output(16,True)
            if (f_check==True):                                             # ------ Filter activated               
                gyro_filter.writedata(dirpath, now)
            elif (f_check==False):                                          # ------ No filter activated
                glob_time_start = time.time()               
                gyro_normal.writedata(dirpath, counter)
                counter = counter + (time.time() - glob_time_start)
        elif (meas_on == 0):
            pass
#            GPIO.output(16, False)
     
except KeyboardInterrupt:  
    GPIO.cleanup()                                                          # clean up GPIO on CTRL+C exit  


