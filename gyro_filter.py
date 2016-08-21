#==========================================================================================================================================================
#==========================================================================================================================================================
#-----------------------------------------------------------------------------------------------------------------------------------------------------------
#                        SHORT DESCRIPTION: 
#                        ==================
# Subroutine reads the data of the gyroscope. The bank angle in x- and y-direction can be deterimined by the gyroscope sensor or by using
# the output of the accelerometer. The filter is a complementary type that takes a low pass filtered signal of the accelerometer and a high
# pass filtered signal of the gyroscope (integrated angular velocity) and combines them with a certain weight that is depeniding on time constant
# of the overall system. 
# The py file is divided into two subfunctions: 1) writheader(dirpath):
#                                               2) writedata(dirpath,now)
#-----------------------------------------------------------------------------------------------------------------------------------------------------------
#=                     RECORD OF REVISIONS:
#                      ====================
#        Date:          Programmer:       Description of changes:
#     ========         =============     =========================
#     2015/Sep/07         L.Eder            1.0
#     2016/Mar/28         L.Eder            2.0 - Version with Interrupts and Multithreading
#     2016/Apr/15         L.Eder            3.0 - Revised interrupt version with revised decision tree in the main loop
#     2016/Apr/29         L.Eder            4.0 - Revised interrupt version with minor bugfixes and documetation
#     2016/May/16         L.Eder            4.1 - Features support for the WS2812b Diode with special pyhton library - code is currently very messy
#==========================================================================================================================================================
#==========================================================================================================================================================


#==========================================================================================================================================================
#--- WRITING GYRO-OUT HEADER DATA -------------------------------------------------------------------------------------------------------------------------
def writeheader(dirpath):    
    gyrodata = open(dirpath + "/gyro_out.txt", "w")
    gyrodata.write(str("Time" " \t" "last x-Angle" "\t" "last y-Angle" "\t" "Total x-Angle" "\t" "Total y-Angle" "\t" \
                       "Gyro x-Angle raw" "\t" "Gyro y-Angle raw" "\t" "Acc x-Angle raw" "\t" "Acc y-Angle raw" \
                       "Acc x-raw" "\t" "Acc y-raw" \
                       "\n"))
    
    gyrodata.write(str("[s]" "\t" "[deg]" "\t" "[deg]" "\t" "[deg]" "\t" "[deg]" "\t" \
                       "[deg]" "\t" "[deg]" "\t" "[deg]" "\t" "[deg]" \
                       "[m/s2]" "\t" "[m/s2]" \
                       "\n"))
    #===========================================================================
    # gyrodata.write(str("Time"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("last x-Angle"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("last y-Angle"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("Total x-Angle"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("Total y-Angle"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("Gyro x-Angle raw"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("Gyro y-Angle raw"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("Acc x-Angle raw"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("Acc y-Angle raw"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("Acc x-raw"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("Acc y-raw"))
    # gyrodata.write(str('\n'))
    #===========================================================================
    #===========================================================================
    # gyrodata.write(str("[s]"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("[deg]"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("[deg]"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("[deg]"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("[deg]"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("[deg]"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("[deg]"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("[deg]"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("[deg]"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("[m/s2]"))
    # gyrodata.write(str('\t'))
    # gyrodata.write(str("[m/s2]"))
    # gyrodata.write(str('\n'))
    #===========================================================================
    gyrodata.close()



#==========================================================================================================================================================
#--- WRITING GYRO-OUT DATA WITH FILTER --------------------------------------------------------------------------------------------------------------------
#--- Getting the raw data from the gyro, calculating the needed output data and writing of the data to the output file.
def gyro_wakeup():
    import smbus                                                                # smbus library needed for the gyroscope read 

    
    power_mgmt_1 = 0x6b                                                         # Power management registers
    #power_mgmt_2 = 0x6c
    bus = smbus.SMBus(1)                                                        #--- or bus = smbus.SMBus(1) for Revision 2 boards
    address = 0x69                                                              #--- This is the address value read via the i2cdetect command
    if (bus.write_byte_data(address, power_mgmt_1, 0)):                               #--- Now wake the 6050 up as it starts in sleep mode
        return True
    else:
        return False
    
def writedata(dirpath, now):
    import smbus                                                                # smbus library needed for the gyroscope read 
    import math                                                                 # math library needed for the angular functions
    import time
    
    power_mgmt_1 = 0x6b                                                         # Power management registers
    power_mgmt_2 = 0x6c
    gyrodata = open(dirpath + "/gyro_out.txt", "a")                             # Opening pre-written gyro_out.txt file
    
    
    gyro_scale = 131.0                                                          #--- Scaling for gyroscope - this value probably needs scaling from actual measurement data
    accel_scale = 16384.0                                                       #--- Scaling for accelerometer - this value probably needs scaling from actual measurement data
                                                                                #--- Look into the technichal sheet of the MPU6050 for further information

    def read_all():                                                             #---- DEFNINING OF READ-IN SUBFUNCTIONS
        raw_gyro_data = bus.read_i2c_block_data(address, 0x43, 6)
        raw_accel_data = bus.read_i2c_block_data(address, 0x3b, 6)
    
        gyro_scaled_x = twos_compliment((raw_gyro_data[0] << 8) + raw_gyro_data[1]) / gyro_scale
        gyro_scaled_y = twos_compliment((raw_gyro_data[2] << 8) + raw_gyro_data[3]) / gyro_scale
        gyro_scaled_z = twos_compliment((raw_gyro_data[4] << 8) + raw_gyro_data[5]) / gyro_scale
    
        accel_scaled_x = twos_compliment((raw_accel_data[0] << 8) + raw_accel_data[1]) / accel_scale
        accel_scaled_y = twos_compliment((raw_accel_data[2] << 8) + raw_accel_data[3]) / accel_scale
        accel_scaled_z = twos_compliment((raw_accel_data[4] << 8) + raw_accel_data[5]) / accel_scale
    
        return (gyro_scaled_x, gyro_scaled_y, gyro_scaled_z, accel_scaled_x, accel_scaled_y, accel_scaled_z)
        
    def twos_compliment(val):
        if (val >= 0x8000):
            return -((65535 - val) + 1)
        else:
            return val
    
    def dist(a, b):
        return math.sqrt((a * a) + (b * b))
    
    
    def get_y_rotation(x,y,z):
        radians = math.atan2(x, dist(y,z))
        return -math.degrees(radians)
    
    def get_x_rotation(x,y,z):
        radians = math.atan2(y, dist(x,z))
        return math.degrees(radians)
    
    
                                                                                #--- START MPU 6050
    bus = smbus.SMBus(1)                                                        #--- or bus = smbus.SMBus(1) for Revision 2 boards
    address = 0x69                                                              #--- This is the address value read via the i2cdetect command
    #bus.write_byte_data(address, power_mgmt_1, 0)                              #--- Now wake the 6050 up as it starts in sleep mode
    
                                                                   
                                                                                #---- DEFINING FILTER CONSTANTS --> THIS NEEDS CALIBRATION       
    K = 0.98                                                                    #--- The closer the K is to one, the more the code trusts the gyro. The closer to zero, the more it trusts the accelerometer
    K1 = 1 - K 
    time_diff = 0.02
    
    
    #---- READ SENSOR OUTPUT
    (gyro_scaled_x, gyro_scaled_y, gyro_scaled_z, accel_scaled_x, accel_scaled_y, accel_scaled_z) = read_all()
    
    last_x = get_x_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
    last_y = get_y_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
    
                                                                                #---- ADJUSTING GYRO DATA WITH AN OFFSET --> THIS NEEDS CALIBRATION
    gyro_offset_x = gyro_scaled_x                                               #--- 
    gyro_offset_y = gyro_scaled_y
    
    gyro_total_x = (last_x) - gyro_offset_x
    gyro_total_y = (last_y) - gyro_offset_y
    
    #print "{0:.4f} {1:.2f} {2:.2f} {3:.2f} {4:.2f} {5:.2f} {6:.2f}".format( time.time() - now, (last_x), gyro_total_x, (last_x), (last_y), gyro_total_y, (last_y))
    
    
    
    
    for i in range(0, int(3.0 / time_diff)):                                                                            #--- Complementary filter loop
        loopstart = time.time()                                                                                          #--- The loop needs to run at 100Hz or higher to work accurately
        (gyro_scaled_x, gyro_scaled_y, gyro_scaled_z, accel_scaled_x, accel_scaled_y, accel_scaled_z) = read_all()
         
        gyro_scaled_x -= gyro_offset_x
        gyro_scaled_y -= gyro_offset_y
         
        gyro_x_delta = (gyro_scaled_x * time_diff)
        gyro_y_delta = (gyro_scaled_y * time_diff)
     
        gyro_total_x += gyro_x_delta
        gyro_total_y += gyro_y_delta
     
        rotation_x = get_x_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
        rotation_y = get_y_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
     
        last_x = K * (last_x + gyro_x_delta) + (K1 * rotation_x)
        last_y = K * (last_y + gyro_y_delta) + (K1 * rotation_y)
         
        #print "{0:.4f} {1:.2f} {2:.2f} {3:.2f} {4:.2f} {5:.2f} {6:.2f}".format( time.time() - now, (rotation_x), (gyro_total_x), (last_x), (rotation_y), (gyro_total_y), (last_y))
        counter = time.time() - now
        (gyro_scaled_x, gyro_scaled_y, gyro_scaled_z, accel_scaled_x, accel_scaled_y, accel_scaled_z) = read_all()    
        rotation_x = get_x_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
        rotation_y = get_y_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
         
             
        gyrodata.write(str("%s" %counter))
        gyrodata.write(str('\t'))
        gyrodata.write(str(last_x))
        gyrodata.write(str('\t'))
        gyrodata.write(str(last_y)) 
        gyrodata.write(str('\t'))
        gyrodata.write(str(gyro_total_x))
        gyrodata.write(str('\t'))
        gyrodata.write(str(gyro_total_y))
        gyrodata.write(str('\t'))
        gyrodata.write(str(gyro_scaled_x))
        gyrodata.write(str('\t'))
        gyrodata.write(str(gyro_scaled_y)) 
        gyrodata.write(str('\t'))
        gyrodata.write(str(rotation_x))
        gyrodata.write(str('\t'))
        gyrodata.write(str(rotation_y))
        gyrodata.write(str('\t'))
        gyrodata.write(str(accel_scaled_x))
        gyrodata.write(str('\t'))
        gyrodata.write(str(accel_scaled_y))
        gyrodata.write('\n')


        loopend = time.time()
        looptime = loopend - loopstart
        if looptime < time_diff:                                                                        #--- Check to keep a constant time-step between the loops - this makes the filter more accurate. 
            time.sleep((time_diff-looptime))                                                            #--- CAUTION: I assume that the timestep of the loop will never be larger than X ms - there is currently no possiblity to care for any larger tmestep
    gyrodata.close()  
    return 