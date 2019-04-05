import math,time
import I2C_LCD_driver, Sensor_Driver,Keypad_driver
import RPi.GPIO as GPIO
from time import gmtime,strftime, localtime
from array import array
import numpy as np

#GPIO Initialisation
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(11,GPIO.OUT)    #Heater pin

#Objects to components
sensor = Sensor_Driver
display = I2C_LCD_driver.lcd()
keypad = Keypad_driver
keypad.setup()

# Model parameters
DEF_K = 0.008121
DEF_A = 5.0343
t_lag = 0

# Initialise Arrays 
Numerics = ['0','1','2','3','4','5','6','7','8','9']

# Global settings varibles
# User heating cycle times
start_time = [0,0]
fin_time = [0,0]

#Controlled heating cycles times
con_st_time = [0,0]

error = [0,0,0,0,0,0,0,0,0,0,0,0]
A_con = [0,0,0,0,0,0,0,0,0,0,0,0]
# Used to convert times
weight = [10,1,0.1,0.01]

# Stores data during thermostat trigger
Test_data_time = [0,0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4,0]
Test_data_temp = [28.875,29,29.062,29.187,29.25,29.375,29.375,29.437,29.5,0,0,0,0,0,0,0,0]

#################
No_cycles = 1
# Reset the model
def model_reset():
    # Reset     
    A = DEF_A
    return A
    
# Function operates as a thermostat COMPLETE
def thermostat(T_aim):
    display.lcd_clear()
    trigger = False
    state = True
    n = 0
    Ref_time = current_time(1)
    print('Thermostat trigger at '+ str(Ref_time))
    # How to bound this into a limit????
    while(state == True):
        # Gathers current time
        crrnt_time = current_time(1)
        
        # Inside the heating period
        INT = sensor.read_int()
        #EXT = sensor.read_ext()
        display.lcd_display_string("INTERNAL: "+str(INT),2)
        #display.lcd_display_string("EXTERNAL: "+str(EXT),1)
        display.lcd_display_string("Time: "+current_time(3),3)
        
        # Check whether inside the desired time periods
        if(crrnt_time >= con_st_time[0] and crrnt_time < fin_time[0]):
            # heating period 1 triggered
            if(INT < T_aim):
                GPIO.output(11,1)
            elif(INT >= T_aim):
                GPIO.output(11,0)
                # Thermostat hit. Stop taking data
                trigger = True
        elif(crrnt_time >= con_st_time[1] and crrnt_time < fin_time[1]):
            # heating period 2 triggered
            if(INT < T_aim):
                GPIO.output(11,1)
            elif(INT >= T_aim):
                GPIO.output(11,0)
                # thermostat hit stop taking data
                trigger = True
        else:
            # Not currently in any heating period
            GPIO.output(11,0)
            state = False
        GPIO.cleanup
        
        # Measure the system repsonse to change model
        if(current_time(1) >= Ref_time + (n*0.05) and trigger == False):
            # triggered every 0.05hr(3mins)
            # grab the temperature and the time
            Test_data_temp[n] = INT
            Test_data_time[n] = current_time(1) - Ref_time   #Time in fractions of hours
            print('Temp '+str(n+1)+':'+str(Test_data_temp[n]))
            print('Time '+str(n+1)+':'+str(Test_data_time[n]))
            n = n+1
            
    return 0

# Get current time COMPLETE
def current_time(Op):
    hr = int(strftime('%H', localtime()))
    mn = float(strftime('%M', localtime()))
    if(Op == 1):
        # Decimal form
        time = hr + (mn/60)
    elif(Op == 2):
        # 24 Hour clock form
        time = hr + (weight[3]*mn)
    elif(Op == 3):
        # String form
        #Change to displayable format
        if(hr < 10):
            # Hour converted to 0Xhr
            hour = '0'+str(hr)
        elif(hr >= 10):
            hour = str(hr)
        if(mn < 10):
            # Minute converted to 0Xhr
            mint = '0'+str(mn)
        elif(mn >= 10):
            mint = str(mn)
        time = hour+':'+ mint
    return time

# Generates an optimum turn on time COMPLETE
def on_time(T_aim,A):
    k = DEF_K
    time = 0
    T_start = sensor.read_int()
    # Find 2% settling point
    Max_T = 0.98*(T_start+A)
    if (T_aim > Max_T):
        # Unable to reach the aiming temperature
        # Find the time to reach the max temperature
        d_T = Max_T - T_start
        C = math.log(1 - (d_T/A))
        time = - C/k                #Time in minutes
    elif (T_aim <= Max_T):
        # Generate optimum turn-on time
        print 'Able to reach aiming temperature'
        d_T = T_aim - T_start
        C = math.log(1 - (d_T/A))
        time = -C/k                 #Time in minutes
    # Change all the start times using the current model
    for n in range(No_cycles):
        con_st_time[n] = start_time[n] - (time/60) - t_lag
        print(con_st_time[n])
    return time/60

# Measure lag from test data COMPLETE
def meas_lag():
    count = 0
    t_lag = 0
    # How many data points are Non-zero
    i = np.count_nonzero(Test_data_time)
    for n in range(i):
        # Is the (n+1)th > nth? 
        if(Test_data_temp[n] < Test_data_temp[n+1]):
          # First increase in temperature found
          if(Test_data_temp[n+1] < Test_data_temp[n+2]):
              #First 3 increases found  
              t_lag = Test_data_time[n]
              break
    return t_lag

    
# System lag test COMPLETE
def system_lag_test():
    # Turn heater ON
    GPIO.output(11, True)
    n = 0
    count = 0
    test_start = current_time(1)
    while(n<=3):
        temp1 = sensor.read_int()
        print temp1
        time.sleep(60)
        temp2 = sensor.read_int()
        print temp2
        # Increase in temperature detected
        if(temp1 < temp2 and n == 0):
            # First increase found
            test_fin = current_time(1)
            n = n+1
        elif(temp1 < temp2 and n != 0):
            # Increase found, not the first
            n = n+1
        # decrease in temperature detected
        # Reset n
        elif(temp2 < temp1):
            n = 0
    t_lag = test_fin - test_start        
    # Turn heater OFF
    GPIO.output(11, False)
    return t_lag

# Change the thermostat temperature COMPLETE
def thermo_temp():
    display.lcd_clear()
    display.lcd_display_string('Aiming Temperature:',1)
    display.lcd_display_string('Press ENT when done',4)
    button = False
    temp = 0
    count = 0
    while(count != 10):
        button = keypad.check_press()
        if (button == 64):
            # No button press found
            pass
        elif ((button in Numerics) and count<=1):
            # Numerical button press
            temp = temp + int(button)
            display.lcd_display_string(str(temp)+' DegC',3)
            temp = temp*weight[count]
            count = count+1
        elif (button == 'CLR'):
            # Begin loop again and clear temp and n 
            temp = 0
            count = 0
            display.lcd_clear()
            display.lcd_display_string('Aiming Temperature:',1)
            display.lcd_display_string('Press ENT when done',4)
        elif (button == 'ENT'):
            #Temperature set. break loop
            count = 10
            display.lcd_clear()
            display.lcd_display_string('Thermostat set: ',1)
            display.lcd_display_string('      '+str(temp)+' DegC',3) 
    time.sleep(2)
    display.lcd_clear()
    # Returns the thermostat temperature
    return int(temp)

# Set the heating periods COMPLETE
def heating_cycles():
    # Input how many heating cycles per day
    display.lcd_clear()
    display.lcd_display_string('Number of Cycles',1)
    display.lcd_display_string('Max of 2 cycles',3)
    display.lcd_display_string('Press ENT when done',4)
    n = 0
    while(n == 0):
        button = keypad.check_press()
        if(button in Numerics):
            # Button press has be found
            No_cycles = int(button)
            display.lcd_display_string('     '+str(button)+' Cycles',2)
        elif(button == 'CLR'):
            pass
        elif(button == 'ENT' and No_cycles > 2):
            # Begin loop again is No_cycles > 2
            display.lcd_display_string('Error, exceeded max', 2)
            time.sleep(2)
            display.lcd_display_string('                    ',2)
        elif(button == 'ENT' and No_cycles == 1):
            # Set the second period to 0,0
            start_time[1] = 0
            fin_time[1] = 0
            n = 1
        elif(button == 'ENT' and No_cycles == 2):
            n = 1
    # Set time periods
    display.lcd_clear()
    display.lcd_display_string('   24 Hour format   ',2)
    time.sleep(2)
    display.lcd_clear()
    for n in range(No_cycles):
        i = 0
        #Reset the stored times
        for x in range(No_cycles):
            start_time[x] = 0
            fin_time[x] = 0
        #Start times
        display.lcd_clear()
        display.lcd_display_string('Start Cycle '+str(n+1),1)
        display.lcd_display_string('00:00',3)
        while(i < 4):
            button = keypad.check_press()
            if(button not in Numerics):
                # No numerical buttons pressed
                pass
            elif(button in Numerics):
                # Numerical button press found
                if(button == '0' and i == 0):
                    hel = '0'
                elif(button != '0' and i == 0):
                    hel = ''
                start_time[n] = start_time[n] +(int(button)*weight[i])
                display.lcd_display_string(hel+str(start_time[n]),3)
                i = i+1
        i = 0
        time.sleep(1)
        #Finish times
        display.lcd_display_string('Finish Cycle '+str(n+1),1)
        display.lcd_display_string('00:00',3)        
        while(i < 4):
            button = keypad.check_press()
            if(button not in Numerics):
                pass
            elif(button in Numerics):
                if(button == '0' and i ==0):
                    hel = button
                elif(button != '0' and i == 0):
                    hel = ''
                fin_time[n] = fin_time[n] +(int(button)*weight[i])
                display.lcd_display_string(hel+str(fin_time[n]),3)
                i = i+1

        # Convert to decimal form
        st_hour = int(start_time[n])
        st_mins = start_time[n] - int(start_time[n])
        st_frac = (st_mins/60)*100
        fn_hour = int(fin_time[n])
        fn_mins = fin_time[n] - int(fin_time[n])
        fn_frac = (fn_mins/60)*100
        New_start = st_hour+st_frac
        New_fin = fn_hour+fn_frac
        start_time[n] = New_start
        fin_time[n] = New_fin

    display.lcd_clear()
    return No_cycles

# ADAPITVITY COMPLETE
# pass this function the old A value and usingthe test data it will generate a new one
def Adapt_model(A):
    Temp_mod = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    # Generate model expectation
    k = DEF_K
    r = np.count_nonzero(Test_data_temp)-1
    #Final data point
    t = Test_data_time[r]
    int_temp = Test_data_temp[0]
    # 10 itterations of the algorithm
    print Test_data_temp[0]
    for n in range(10):
        #Generate expected Temp at final data point
        Temp_mod = A*(1-math.exp(-0.008121*(t*60)))+ int_temp
        error = Test_data_temp[r] -Temp_mod # Change for actual test data
        A = A + error
        print error
    print('New A = '+str(A))
    return A



##############################################
#########          Main Code        ##########
##############################################

#Initalisation
display.lcd_display_string('      Welcome!',2)
time.sleep(2)
display.lcd_clear()
No_cycles = heating_cycles()
temp = thermo_temp()
temp = 21.3
A = DEF_A

# User interface menu
while(True):
    time.sleep(1)
    on_time(temp,A)
    print(current_time(1))
    if(con_st_time[0] <= current_time(1) and fin_time[0] > current_time(1)):
        # Heating period 1 triggered
        print('Heating period 1 triggered')
        thermostat(temp)
        # Thermostat turned off, Adpat the model
        t_lag = meas_lag()
        A = Adapt_model(A)
    elif(con_st_time[1] <= current_time(1) and fin_time[1] > current_time(1)):
        # Heating period 2 triggered
        print('Heating period 2 triggered')
        thermostat(temp)
        # Thermostat turned off, Adpat the model
        t_lag = meas_lag()
        A = Adapt_model(A)
    else:
        # Display menu system
        display.lcd_display_string("1:Change temperature",1)
        display.lcd_display_string("2:Heating periods",2)
        display.lcd_display_string("3:System Lag test",3)
        button = keypad.check_press()
        if button == '1':
            # Change thermostat temperature setting triggered
            thermo_temp()
        elif button == '2':
            # Change heating period setting
            heating_cycles()
        elif button == '3':
            # Run the system lag test
            sys_lag_test()


##############################################
#########       End of main code   ###########
##############################################
