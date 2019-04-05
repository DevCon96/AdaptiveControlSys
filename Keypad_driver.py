import RPi.GPIO as GPIO
import time

# Initalise GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
# Define buttons
Key_digits = [ ['CLR','0','ENT','.'],
               ['1','2','3','BLANK'],
               ['4','5','6', 'DOWN'],
               ['7','8','9', 'UP']]
# Pinout configuration
Row = [32,36,38,40]
Col = [31,33,35,37]

# Assigning GPIO pins to keypad
def setup():
    for j in range(4):
        GPIO.setup(Col[j],GPIO.OUT)
        GPIO.output(Col[j],1)
        for i in range(4):
            GPIO.setup(Row[i],GPIO.IN,pull_up_down = GPIO.PUD_UP)

def check_press():
    count = 0
    for j in range(4):
        GPIO.output(Col[j],0)
        for i in range(4):
            if GPIO.input(Row[i]) == 0:
                # Button press has been found!
                digit = Key_digits[i][j]
                time.sleep(0.2)
            elif GPIO.input(Row[1]) == 1:
                # No Button press on this row
                count = count + 1
        GPIO.output(Col[j],1)
    if count < 16:
        # Return button
        return digit
    elif count == 16:
        # No button press found
        return 64
