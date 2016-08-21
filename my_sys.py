
#==========================================================================================================================================================
#==========================================================================================================================================================
#-----------------------------------------------------------------------------------------------------------------------------------------------------------
#                        SHORT DESCRIPTION: 
#                        ==================
# Subscripts used by gyro_measurement_v2.py. 
#
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


#=================================================================================================================
#--- make_dir : Makes the directory with the measurement results and checks if there is already a folder with the 
#--- name measurement_i. If it already exists, a new folder with the naming measurement_i+1 is created.

def make_dir(dir_num):
    import os
    check = 0
    dirname = os.getcwd() + "/measurement_" + str(dir_num) 
    while(check == 0):
        if (os.path.exists(dirname) == True):  
            dir_num = dir_num + 1
            dirname = os.getcwd() + "/measurement_" + str(dir_num)
        else:
            os.mkdir(dirname)
            tmp = "cp " + os.getcwd() + "/plot_input_rot.plot " + dirname
            os.system(tmp)
            tmp = "cp " + os.getcwd() + "/plot_input_acc.plot " + dirname
            os.system(tmp)
            tmp = "cp " + os.getcwd() + "/plot_input_fil.plot " + dirname
            os.system(tmp)
            check = 1
    return dirname            

#=================================================================================================================
#--- start_log: Creates the logfile and writes the measurement start time in it
def start_log(dirpath, f_check):

    import time
    logdata = open(dirpath + "/measurement_log.txt", "w")
    logdata.write("Measurement successfully started at: ")
    logdata.write(str(time.ctime()))
    if f_check == True:
        logdata.write('\n')
        logdata.write('Filter activated')
    else:
        logdata.write('\n')
        logdata.write('No filter activated')   
    logdata.write('\n')
    logdata.write("Measurement folder created: ")
    logdata.write(str(dirpath))
    logdata.write('\n')
    logdata.close()

#=================================================================================================================
#--- stop_log: Opens the log file and writes the measurement stop time in it
def stop_log(dirpath):
    import time
    logdata = open(dirpath + "/measurement_log.txt", "a")
    logdata.write("Measurement successfully stopped at: ")
    logdata.write(str(time.ctime()))
    logdata.write('\n')
    logdata.close()    

#=================================================================================================================
#--- inet_check: The routine tries to connect to google.com  
def inet_check(dirpath): 
    import time
    import urllib
    
    try:
        urllib.urlopen('http://google.com')
        inet_ok = True
    except:
        inet_ok = False
        
    logdata = open(dirpath + "/measurement_log.txt", "a")
    
    if(inet_ok == True):
        logdata.write("Internet connection available at: ")
        logdata.write(str(time.ctime()))
        logdata.write('\n')
        logdata.write("Mail with appended measurement data sent")
        logdata.write('\n')
    else:
        logdata.write("No internet connection available at: ")
        logdata.write(str(time.ctime()))
        logdata.write('\n')
        logdata.write("No mail sent")
        logdata.write('\n')
    logdata.close()    
    return inet_ok   

#=================================================================================================================
#--- sends the mail with the already postprocessed data. It needs to know if you want to have the filtered data or
#--- the raw data  
def send_mail(dirpath, plot_type):
    #!/usr/bin/python
 
    # Import smtplib for the actual sending function
    import smtplib    
    # For guessing MIME type
    import mimetypes
     
    # Import the email modules we'll need
    import email
    import email.mime.application
     
    #Import sys to deal with command line arguments
    import sys
     
    # Create a text/plain message
    msg = email.mime.Multipart.MIMEMultipart()
    msg['Subject'] = 'Measurement data from gyroscope'
    msg['From'] = 'schnupfen1l@gmail.com'
    msg['To'] = 'schnupfen1@gmail.com'
     
    # The main body is just another attachment
    body = email.mime.Text.MIMEText("""Attached data contains gyro plot""")
    msg.attach(body)
     
    # PDF attachment block code
    if (plot_type==1): 
        directory= dirpath + "/gyro_plot_rot.png"
    elif (plot_type==2):
        directory= dirpath + "/gyro_plot_acc.png"
    elif (plot_type==3):
        directory= dirpath + "/gyro_plot_fil.png"
      
    # Split de directory into fields separated by / to substract filename
     
    spl_dir=directory.split('/')
     
    # We attach the name of the file to filename by taking the last
    # position of the fragmented string, which is, indeed, the name
    # of the file we've selected
     
    filename=spl_dir[len(spl_dir)-1]
     
    # We'll do the same but this time to extract the file format (pdf, epub, docx...)
     
    spl_type=directory.split('.')
     
    type=spl_type[len(spl_type)-1]
     
    fp=open(directory,'rb')
    att = email.mime.application.MIMEApplication(fp.read(),_subtype=type)
    fp.close()
    att.add_header('Content-Disposition','attachment',filename=filename)
    msg.attach(att)
     
    # send via Gmail server
    # NOTE: my ISP, Centurylink, seems to be automatically rewriting
    # port 25 packets to be port 587 and it is trashing port 587 packets.
    # So, I use the default port 25, but I authenticate.
    s = smtplib.SMTP('smtp.gmail.com:587')
    s.starttls()
    s.login('schnupfen1@gmail.com','2009sg2013TZ!')
    s.sendmail('schnupfen1@gmail.com',['schnupfen1@gmail.com'], msg.as_string())
    s.quit()

