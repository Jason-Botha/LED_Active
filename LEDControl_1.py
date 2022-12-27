#First code test run March 2021
#Latest Edit: 6/10/2022
#Edited by: Jason

#Working??
#Zero check
#Zero check again

#Get all the libraries: 
import pandas as pd #Used to manipulate the lists
import time
from rpi_ws281x import * #This is to control the LED's
import argparse
import numpy
import requests
from gpiozero import LED, Button #Used for button pushing and interaction

# LED strip configuration (This comes from a example):
LED_COUNT      = 384     # Number of LED's = 64x6
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 50     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53

#Other inputs
colNames_1 = ["MappedLED", "Order", "AnimationID"]
colNames_2 = ["Color_1","Color_2","Color_3"]
colNames_3 = ["MappedLED", "ColourIndex", "ScenarioNum"]
colNames_4 = ["CurrentAnimations"]
colNames_5 = ["CurrentScenarios"]
colNames_6 = ["Value"]

button = Button(23, hold_time=2)
buttonPush = False #Button is false at start

AnimationList = []
colorArray = []
CountryColourList = []
ScenariosList = []
AnimationControl = []
ScenarioControl = []
CurrentCountryColourList = []
df_1 = []
df_3 = []
timeBetweenLED_ON = 300
timeBetweenLED_OFF = 300

#Links to google Sheets
pathto_AnimationList = r'https://docs.google.com/spreadsheets/d/1cvY7nFmQXcqeIgzIGluxPr4DZurvwUJ0DhEDwiHVGqs/export?format=csv&gid=2133138814'
pathto_ColourLookUp = r'https://docs.google.com/spreadsheets/d/1cvY7nFmQXcqeIgzIGluxPr4DZurvwUJ0DhEDwiHVGqs/export?format=csv&gid=1306523954'
pathto_CountryColour = r'https://docs.google.com/spreadsheets/d/1cvY7nFmQXcqeIgzIGluxPr4DZurvwUJ0DhEDwiHVGqs/export?format=csv&gid=740621852'
pathto_AnimationControl = r'https://docs.google.com/spreadsheets/d/1cvY7nFmQXcqeIgzIGluxPr4DZurvwUJ0DhEDwiHVGqs/export?format=csv&gid=1780015285'
pathto_ScenarioControl = r'https://docs.google.com/spreadsheets/d/1cvY7nFmQXcqeIgzIGluxPr4DZurvwUJ0DhEDwiHVGqs/export?format=csv&gid=686401352'
pathto_InputParameters = r'https://docs.google.com/spreadsheets/d/1cvY7nFmQXcqeIgzIGluxPr4DZurvwUJ0DhEDwiHVGqs/export?format=csv&gid=950944565'

def getGoogleData():
    """This is used once in the begining and everytime the button is pushed"""
    """The function just pulles the lits from the sheets"""
    #Need to define global here otherwise it doesent pass through the function
    global AnimationList    
    global colorArray
    global CountryColourList
    global ScenariosList
    global AnimationControl    
    global ScenarioControl
    global df_1
    global df_3
    global timeBetweenLED_ON
    global timeBetweenLED_OFF
    global LED_BRIGHTNESS
    
    #this is the LED animation sheet
    df_1 = pd.read_csv(pathto_AnimationList, encoding = 'utf8', usecols = colNames_1)
    #AnimationList = df_1.sort_values("Order").values.tolist()
    #This gets LED colour lists
    df_2 = pd.read_csv(pathto_ColourLookUp, encoding = 'utf8', usecols = colNames_2)
    colorArray = df_2.values
    #This get the Country Colour list
    df_3 = pd.read_csv(pathto_CountryColour, encoding = 'utf8', usecols = colNames_3)
    CountryColourList = df_3.values
    #Get unique scenarios list
    ScenariosList = df_3['ScenarioNum'].unique().tolist()
    #Get all the curent running Animations
    df_4 = pd.read_csv(pathto_AnimationControl, encoding = 'utf8', usecols = colNames_4)
    AnimationControl = df_4.values.tolist()
    #print("animationControl -->")
    #Get all the curent running Scenarios
    df_5 = pd.read_csv(pathto_ScenarioControl, encoding = 'utf8', usecols = colNames_5)
    ScenarioControl = df_5.values.tolist()
    #print("ScenarioControl -->")
    df_6 = pd.read_csv(pathto_InputParameters, encoding = 'utf8', usecols = colNames_6)
    timeBetweenLED_ON = df_6.iloc[0]
    timeBetweenLED_OFF = df_6.iloc[1]
    LED_BRIGHTNESS = = df_6.iloc[2]
    
def RunAnimation_Scenario(strip):
    """For each animation run through all the differnt scenarions and repeat"""
    global CurrentCountryColourList
    
    getGoogleData()
    
    for animationNum in AnimationControl:
        for scenario in ScenarioControl:
            #Data will be ["MappedLED", "Order", "AnimationID", "ColourIndex", "ScenarioNum"]
            df_merge = pd.merge(df_1, df_3, on = 'MappedLED', how = 'left')
            CurrentCountryColourList = df_merge.loc[(df_merge['AnimationID'] == animationNum) & (df_merge['ScenarioNum'] == scenario)].sort_values("Order").values.tolist()
            
            #Once we have the current list just go and switch them on
            LightLEDsInOrder(strip,CurrentCountryColourList)
            #Wipe the map
            LightLEDsInOrder_Off(strip,CurrentCountryColourList)

 
      
def whichColour(colourIndex):
    """This just builds the Color needed for the LED"""
    #colorArray looks like (255,0,0)
    x = colorArray[colourIndex][0]
    y = colorArray[colourIndex][1]
    z = colorArray[colourIndex][2]
    return Color(x,y,z)


def colorWipe(strip, color, wait_ms=20):
    """Wipe color across all LEDs at one time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)


def LightLEDsInOrder(strip, LEDList, wait_ms = 300):
    """This sets the LEDs to their colours as per their order"""
    #Clear map first
    colorWipe(strip, Color(0,0,0), 1)
    
    for i in range(len(LEDList)):
        strip.setPixelColor(LEDList[i][0],int(whichColour(LEDList[i][3])))
        strip.show()
        time.sleep(wait_ms/1000.0)
        #print(LEDList[i][0])


def LightLEDsInOrder_Off(strip, LEDList, wait_ms = 300):
    """This sets the LEDs to their colours as per their order"""
   
    for i in range(len(LEDList)):
        #Set to black
        strip.setPixelColor(LEDList[i][0],int(Color(0,0,0)))
        strip.show()
        time.sleep(wait_ms/1000.0)




def colorTest(strip, wait_ms=100):
    """Array index test"""
    global buttonPush
    if buttonPush == False:
        #Clear the map first
        colorWipe(strip, Color(0,0,0), 10)

        for i in range(len(LEDList)):
            if buttonPush == True: break
            strip.setPixelColor(LEDList[i][0],int(whichColour(LEDList[i][1])))
            strip.show()
            time.sleep(wait_ms/1000.0)

    if buttonPush == True:
        #Get new Google data
        getGoogleData()
        print("Just updated data")

        for i in range(len(LEDList)):
            if buttonPush == False: break
            strip.setPixelColor(LEDList[i][0],int(whichColour(LEDList[i][1])))
            strip.show()

        time.sleep(.1)

def setButtonPush():
    global buttonPush
    buttonPush = not buttonPush
    print(buttonPush)

# Main program logic follows:
if __name__ == '__main__':
    # Process arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--clear', action='store_true', help='clear the display on exit')
    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration.
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    # Intialize the library (must be called once before other functions).
    strip.begin()
    
    #Set the call back up to watch button
    button.when_held = setButtonPush
    #Get the first set of Google data
    #getGoogleData()

    print ('Press Ctrl-C to quit.')
    if not args.clear:
        print('Use "-c" argument to clear LEDs on exit')

    try:
        while True:
            print('Starting LED animation script')
            #LightLEDsInOrder(strip,100)
            #LightLEDsInOrder_Off(strip,100)
            #getGoogleData()
            RunAnimation_Scenario(strip)
            time.sleep(10)

    except KeyboardInterrupt:
        if args.clear:
            colorWipe(strip, Color(0,0,0), 10)


