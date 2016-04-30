#=================================================================================================================
#-----------------------------------------------------------------------------------------------------------------
# Subroutine reads the data of the gyroscope. The bank angle in x- and y-direction can be deterimined by the gyroscope sensor or by using
# the output of the accelerometer. The filter is a complementary type that takes a low pass filtered signal of the accelerometer and a high
# pass filtered signal of the gyroscope (integrated angular velocity) and combines them with a certain weight that is depeniding on time constant
# of the overall system
#
#                       RECORD OF REVISIONS:
#                      =====================
#        Date:      Programmer:       Description of changes:
#     ========    =============     =========================
#     2015/Dec/13    L.Eder            v 1.0
#     2016/Jan/07    L.Eder            v 2.0 - Minor bugfixes and some more documentation
#     2016/Apr/28    L.Eder            v 4.0  - Rework of the time checking loop to ensure equal time steps
#=================================================================================================================
#--- writing of the header data for the text output file
def writeheader(dirpath):    
    gyrodata = open(dirpath + "/gyro_out.txt", "w")
    gyrodata.write(str("Time"))
    gyrodata.write(str('\t'))
    gyrodata.write(str("last x-Angle"))
    gyrodata.write(str('\t'))
    gyrodata.write(str("last y-Angle"))
    gyrodata.write(str('\t'))
    gyrodata.write(str("Total x-Angle"))
    gyrodata.write(str('\t'))
    gyrodata.write(str("Total y-Angle"))
    gyrodata.write(str('\n'))
    gyrodata.close()



#=================================================================================================================
#--- Getting the raw data from the gyro, calculating the needed output data and writing of the data to the output file.
#--- Reading the output from the gyro file is taken from: http://blog.bitify.co.uk/2013/11/using-complementary-filter-to-combine.html
def writedata(dirpath, counter):
    import smbus
    import math
    import time
    

    power_mgmt_1 = 0x6b                                                                             # Power management registers
    gyrodata = open(dirpath + "/gyro_out.txt", "a")
    
    #---- SCALING SETTINGS --> THIS NEEDS CALIBRATION
    gyro_scale = 131.0
    accel_scale = 16384.0
    
    #---- DEFNINING OF READ-IN SUBFUNCTIONS
    def read_all():
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
    
    
    #---- START MPU 6050
    bus = smbus.SMBus(1)                                                        # or bus = smbus.SMBus(1) for Revision 2 boards
    address = 0x68                                                              # This is the address value read via the i2cdetect command
    bus.write_byte_data(address, power_mgmt_1, 0                                # --- Now wake the 6050 up as it starts in sleep mode
    now = time.time()
    
    #---- DEFINING FILTER CONSTANTS --> THIS NEEDS CALIBRATION
    K = 0.98
    K1 = 1 - K
    
    time_diff = 0.02
    
    
    #---- READ SENSOR OUTPUT
    (gyro_scaled_x, gyro_scaled_y, gyro_scaled_z, accel_scaled_x, accel_scaled_y, accel_scaled_z) = read_all()
    
    last_x = get_x_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
    last_y = get_y_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
    
    #---- ADJUSTING GYRO DATA WITH AN OFFSET --> THIS NEEDS CALIBRATION
    gyro_offset_x = gyro_scaled_x 
    gyro_offset_y = gyro_scaled_y
    
    gyro_total_x = (last_x) - gyro_offset_x
    gyro_total_y = (last_y) - gyro_offset_y
    
    #print "{0:.4f} {1:.2f} {2:.2f} {3:.2f} {4:.2f} {5:.2f} {6:.2f}".format( time.time() - now, (last_x), gyro_total_x, (last_x), (last_y), gyro_total_y, (last_y))
    
    
    #---- COMPLEMENTRAY FILTER 
    #---- THE LOOP NEEDS TO BE > 100 HZ to work accurately !!
    for i in range(0, int(3.0 / time_diff)): 
        
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
        
        
    gyrodata.write(str("%s" %counter))
    gyrodata.write(str('\t'))
  
    gyrodata.write(str(last_x))
    gyrodata.write(str('\t'))
    gyrodata.write(str(last_y)) 
    gyrodata.write(str('\t'))
    gyrodata.write(str(gyro_total_x))
    gyrodata.write(str('\t'))
    gyrodata.write(str(gyro_total_y))
    gyrodata.write('\n')
    
    gyrodata.close()   