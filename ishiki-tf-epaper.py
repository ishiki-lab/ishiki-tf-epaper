#!/usr/bin/env python
# -*- coding: utf-8 -*-

HOST = "127.0.0.1"
PORT = 4223
WIDTH = 296 # pixel width
HEIGHT = 128 # pixel height
INTERVAL = 60 # update interval in seconds

debug = True
verbose = True
#send_to_influx = True
#columns_number = 1
reading_interval = 10.0
logo = "./img/Architectural_Association_School_of_Architecture_logo.png"
logo_scaling = 0.4
spacing = 5 # spacing in pixels

from tinkerforge.ip_connection import IPConnection
from tinkerforge.bricklet_ambient_light_v2 import BrickletAmbientLightV2
from tinkerforge.bricklet_temperature import BrickletTemperature
from tinkerforge.bricklet_humidity import BrickletHumidity
from tinkerforge.bricklet_sound_intensity import BrickletSoundIntensity
from tinkerforge.bricklet_e_paper_296x128 import BrickletEPaper296x128
from tinkerforge.bricklet_sound_pressure_level import BrickletSoundPressureLevel
from tinkerforge.bricklet_motion_detector_v2 import BrickletMotionDetectorV2
from tinkerforge.bricklet_humidity_v2 import BrickletHumidityV2

from time import sleep
from os.path import join, splitext
from os import listdir
import math, time, datetime
from PIL import Image, ImageFont, ImageDraw

import netifaces
import schedule
import socket
from socket import gethostname

font_large = ImageFont.truetype('font/DejaVuSans.ttf', 16)
font_small = ImageFont.truetype('font/DejaVuSans.ttf', 12)

# convert PIL image to matching color bool list
def bool_list_from_pil_image(image, width=296, height=128, color=(0, 0, 0)):
    image_data = image.load()
    pixels = []

    for row in range(height):
        for column in range(width):
            pixel = image_data[column, row]
            value = (pixel[0] == color[0]) and (pixel[1] == color[1]) and (pixel[2] == color[2])
            pixels.append(value)

    return pixels

tfIDs = [
]

def get_ipaddresses(adapters):
    addresses = []
    for adapter in adapters:
        if adapter in ('eth0','wlan0'):
            mac_addr = netifaces.ifaddresses(adapter)[netifaces.AF_LINK][0]['addr']
            try:
                ip_addr = netifaces.ifaddresses(adapter)[netifaces.AF_INET][0]['addr']
            except:
                ip_addr = 'disconnected'
            #print(mac_addr, ip_addr)
            addresses.append((adapter,mac_addr,ip_addr))
    return(addresses)

def print_ipaddresses():
    adapters = netifaces.interfaces()
    addresses = get_ipaddresses(adapters)
    print(addresses)

tfConnect = True

if tfConnect:
    tfIDs = []

imgPath = 'img'

deviceIdentifiersDict = {
    216: {
        "name": "Temperature",
        "type": "Temperature Bricklet",
        "device_type": "sensor",
        "class": BrickletTemperature,
        "unit": " ºC",
        "brick_tag": "Temperature_Sensor",
        "value_func": "get_temperature",
        "correction": "0.01*%s",
        "callback_func": "CALLBACK_TEMPERATURE",
        "variance": 1,
    },
    238: {
        "name": "Sound Intensity",
        "type": "Sound Intensity Bricklet",
        "device_type": "sensor",
        "class": BrickletSoundIntensity,
        "quantity": "sound_level",
        "unit": "dB",
        "brick_tag": "Noise_Sensor",
        "value_func": "get_intensity",
        "callback_func": "CALLBACK_INTENSITY",
        "correction": "20*math.log10(%s/1)",
        "publish_limit": 30,
        "variance": 400,
    },
    259: {
        "name": "Ambient Light",
        "type": "Ambient Light Bricklet 2.0",
        "device_type": "sensor", 
        "class": BrickletAmbientLightV2,
        "quantity": "illuminance",
        "unit": "lux",
        "brick_tag": "LightingSystem_Illuminance_Sensor",
        "value_func": "get_illuminance",
        "correction": "0.01*%s",
        "callback_func": "CALLBACK_ILLUMINANCE",
    },
    283: {
        "name": "Humidity",
        "type": "Humidity Bricklet 2.0",
        "device_type": "sensor",
        "class": BrickletHumidityV2,
        "quantity": "humidity",
        "unit": "RH (%)",
        "brick_tag": "Humidity",
        "value_func": "get_humidity",
        "correction": "%s/100",
        "callback_func": "CALLBACK_HUMIDITY",
    },
    290: {
        "name": "Sound Pressure",
        "type": "Sound Pressure Level Bricklet",
        "device_type": "sensor",
        "class": BrickletSoundPressureLevel,
        "quantity": "decibel",
        "unit": "dB (A)",
        "brick_tag": "",
        "value_func": "get_decibel",
        "correction": "0.1*%s",
        "callback_func": "CALLBACK_DECIBEL",
    },
    292: {
        "name": "Motion Detection",
        "type": "Motion Detector Bricklet 2.0",
        "device_type": "sensor",
        "class": BrickletMotionDetectorV2,
        "quantity": "motion",
        "unit": "",
        "brick_tag": "",
        "value_func": "get_motion_detected",
        "correction": "%s",
        "callback_func": "CALLBACK_MOTION_DETECTED",
    },
    2146: {
        "name": "E-Paper 296x128",
        "type": "E-Paper 296x128 Bricklet",
        "device_type": "display",
        "class": BrickletEPaper296x128,
        "quantity": "",
        "unit": "",
        "brick_tag": "",
        "value_func": "get_draw_status",
        "correction": "%s",
        "callback_func": "CALLBACK_DRAW_STATUS",
    },
}

deviceIdentifiersList = [
[11, "DC Brick",""],
[13, "Master Brick",""],
[14, "Servo Brick",""],
[15, "Stepper Brick",""],
[16, "IMU Brick","sensor",["get_all_data"],[""]],
[17, "RED Brick",""],
[18, "IMU Brick 2.0","sensor",["get_all_data"],[""]],
[19, "Silent Stepper Brick",""],
[21, "Ambient Light Bricklet","sensor",["get_illuminance"],["lux"]],
[23, "Current12 Bricklet","sensor"],
[24, "Current25 Bricklet","sensor"],
[25, "Distance IR Bricklet","sensor"],
[26, "Dual Relay Bricklet","actuator"],
[27, "Humidity Bricklet","sensor",["get_humidity"],["%RH"]],
[28, "IO-16 Bricklet","sensor"],
[29, "IO-4 Bricklet","sensor"],
[210, "Joystick Bricklet","sensor"],
[211, "LCD 16x2 Bricklet","actuator"],
[212, "LCD 20x4 Bricklet","actuator"],
[213, "Linear Poti Bricklet","sensor"],
[214, "Piezo Buzzer Bricklet","actuator"],
[215, "Rotary Poti Bricklet","sensor"],
[216, "Temperature Bricklet","sensor",["get_temperature"],["ºC"]],
[217, "Temperature IR Bricklet","sensor"],
[218, "Voltage Bricklet","sensor"],
[219, "Analog In Bricklet","sensor"],
[220, "Analog Out Bricklet","actuator"],
[221, "Barometer Bricklet","sensor"],
[222, "GPS Bricklet","sensor"],
[223, "Industrial Digital In 4 Bricklet","sensor"],
[224, "Industrial Digital Out 4 Bricklet","actuator"],
[225, "Industrial Quad Relay Bricklet","actuator"],
[226, "PTC Bricklet","sensor"],
[227, "Voltage/Current Bricklet","sensor"],
[228, "Industrial Dual 0-20mA Bricklet",""],
[229, "Distance US Bricklet","sensor"],
[230, "Dual Button Bricklet","sensor"],
[231, "LED Strip Bricklet","actuator"],
[232, "Moisture Bricklet","sensor"],
[233, "Motion Detector Bricklet","sensor"],
[234, "Multi Touch Bricklet","sensor"],
[235, "Remote Switch Bricklet","sensor"],
[236, "Rotary Encoder Bricklet","sensor"],
[237, "Segment Display 4x7 Bricklet","actuator"],
[238, "Sound Intensity Bricklet","sensor", ["get_intensity"],["dB"]],
[239, "Tilt Bricklet","sensor"],
[240, "Hall Effect Bricklet","sensor"],
[241, "Line Bricklet","sensor"],
[242, "Piezo Speaker Bricklet","actuator"],
[243, "Color Bricklet","sensor"],
[244, "Solid State Relay Bricklet","actuator"],
[245, "Heart Rate Bricklet","sensor"],
[246, "NFC/RFID Bricklet","sensor"],
[249, "Industrial Dual Analog In Bricklet","sensor"],
[250, "Accelerometer Bricklet","sensor"],
[251, "Analog In Bricklet 2.0","sensor"],
[252, "Gas Detector Bricklet","sensor"],
[253, "Load Cell Bricklet","sensor"],
[254, "RS232 Bricklet",""],
[255, "Laser Range Finder Bricklet","sensor"],
[256, "Analog Out Bricklet 2.0","actuator"],
[257, "AC Current Bricklet",""],
[258, "Industrial Analog Out Bricklet",""],
[259, "Ambient Light Bricklet 2.0","",["get_illuminance"],["lux"]],
[260, "Dust Detector Bricklet","sensor"],
[261, "Ozone Bricklet","sensor"],
[262, "CO2 Bricklet","sensor"],
[263, "OLED 128x64 Bricklet","actuator"],
[264, "OLED 64x48 Bricklet","actuator"],
[265, "UV Light Bricklet","sensor"],
[266, "Thermocouple Bricklet","sensor"],
[267, "Motorized Linear Poti Bricklet","sensor"],
[268, "Real-Time Clock Bricklet",""],
[269, "Pressure Bricklet","sensor"],
[270, "CAN Bricklet",""],
[271, "RGB LED Bricklet","actuator"],
[272, "RGB LED Matrix Bricklet","actuator"],
[276, "GPS Bricklet 2.0","sensor"],
[277, "RS485 Bricklet",""],
[278, "Thermal Imaging Bricklet",""],
[282, "RGB LED Button Bricklet","sensor"],
[283, "Humidity Bricklet 2.0","sensor"],
[284, "Dual Relay Bricklet 2.0","actuator"],
[285, "DMX Bricklet","actuator"],
[286, "NFC Bricklet","sensor"],
[287, "Moisture Bricklet 2.0","sensor"],
[288, "Outdoor Weather Bricklet","sensor"],
[289, "Remote Switch Bricklet 2.0","actuator"],
[290, "Sound Pressure Level Bricklet","sensor"],
[291, "Temperature IR Bricklet 2.0","sensor"],
[292, "Motion Detector Bricklet 2.0","sensor"],
[294, "Rotary Encoder Bricklet 2.0","sensor"],
[295, "Analog In Bricklet 3.0","sensor"],
[296, "Solid State Relay Bricklet 2.0","actuator"],
[2146, " E-Paper 296x128 Bricklet", "display"],
[21111, "Stream Test Bricklet",""],
]

deviceIDs = [i[0] for i in deviceIdentifiersList]
deviceIDs = [item for item in deviceIdentifiersDict]
if debug:
    print(deviceIDs)
    for dID in deviceIDs:
        print(deviceIdentifiersDict[dID])

def getImages(path):
    files = listdir(path)
    imgs = []
    for f in files:
        #print(f, splitext(f)[1])
        # print(splitext(f)[1].lower())
        if splitext(f)[1].lower() in ['.jpg', '.png']:
            # print(f)
            imgs.append(f)
    return(imgs)

def getIdentifier(ID):
    deviceType = ""
    # for t in deviceIdentifiers:
        # if ID[1]==t[0]:
        #     #print(ID,t[0])
        #     deviceType = t[1]
    for t in deviceIDs:
        if ID[1]==t:
            #print(ID,t[0])
            deviceType = deviceIdentifiersDict[t]["type"]
    return(deviceType)

# Tinkerforge sensors enumeration
def cb_enumerate(uid, connected_uid, position, hardware_version, firmware_version,
                 device_identifier, enumeration_type):
    tfIDs.append([uid, device_identifier])

class tf_App():

    # def cb_illuminance(illuminance):
    #     print("Illuminance: " + str(illuminance/100.0) + " Lux")

    def cb_sensors(self):
        # print("Illuminance: "+str(al.get_illuminance()/100))
        i = 0
        sensor_text = ""
        for sensor in self.sensors:
            if debug:
                print("Sensor type: "+str(sensor.DEVICE_IDENTIFIER))
                quantity = getattr(sensor, deviceIdentifiersDict[sensor.DEVICE_IDENTIFIER]["value_func"])()+1
                v = eval(deviceIdentifiersDict[sensor.DEVICE_IDENTIFIER]["correction"] % quantity)
                unit = deviceIdentifiersDict[sensor.DEVICE_IDENTIFIER]["unit"]
                sensor_text += "%s: %.1f %s\n" % (deviceIdentifiersDict[sensor.DEVICE_IDENTIFIER]["name"], v, unit)
                if debug:
                    print(quantity, deviceIdentifiersDict[sensor.DEVICE_IDENTIFIER]["correction"] % quantity)

        # Get timestamp
        ts = time.time()
        #print(time.time(), prev_time)
        datestr = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
        print(datestr)

        hostname = gethostname()

        for display in self.displays:
            if display.DEVICE_IDENTIFIER == 2146:
                image = Image.open(logo)

                # Resize image to WIDTH x HEIGHT
                hpercent = (HEIGHT/float(image.size[1]))
                wsize = int((float(image.size[0])*float(hpercent))*logo_scaling)
                img = image.resize((wsize,int(HEIGHT*logo_scaling)))

                # Paste scaled image to new image with WIDTH x HEIGHT canvas size
                image = Image.new(img.mode, (WIDTH, HEIGHT), (0x00, 0x00, 0x00))
                image.paste(img, (0, 0))

                draw = ImageDraw.Draw(image)

                row = 1
                # Write date and time
                draw.multiline_text((int(HEIGHT*logo_scaling+spacing), spacing/2), "%s - %s" % (hostname, datestr), fill=(0x99, 0x99, 0x99), font=font_small)

                # Write IP addresses
                adapters = netifaces.interfaces()
                addresses = get_ipaddresses(adapters)
                if debug:
                    print(addresses)
                for i in range(len(addresses)):
                    if debug:
                        print(addresses[i])
                    address = '%s - %s' % (addresses[i][0], addresses[i][2])
                    draw.multiline_text((int(HEIGHT*logo_scaling+spacing), spacing/2+row*(spacing+12)), address, fill=(0x00, 0x99, 0x99), font=font_small)
                    row += 1

                # Write sensors values
                draw.multiline_text((spacing, int(HEIGHT*logo_scaling)), sensor_text, fill=(255, 255, 255), font=font_large)

                # Get black/white pixels from image and write them to the Bricklet buffer
                pixels_bw  = bool_list_from_pil_image(image, WIDTH, HEIGHT, (0x00, 0x00, 0x00))
                display.write_black_white(0, 0, WIDTH-1, HEIGHT-1, pixels_bw)

                # Get shade pixels from image and write them to the Bricklet buffer
                pixels_shade = bool_list_from_pil_image(image, WIDTH, HEIGHT, (0x00, 0x99, 0x99))
                display.write_color(0, 0, WIDTH-1, HEIGHT-1, pixels_shade)

                # Draw buffered values to the display
                display.draw()

                # Send value to InfluxDB at instantaneous interval
                #if send_to_influx:
                #    SENSORNAME = SHORT_IDENT+"_"+self.buttons[i].text[0:3]+"_"+deviceIdentifiersDict[sensor.DEVICE_IDENTIFIER]["brick_tag"]
                #    json_body = [
                #        {
                #        "measurement": SENSORNAME,
                #        "tags": {
                #            "sensor": SENSORNAME,
                #        },
                #        "time": datestr,
                #        "fields": {
                #            "value": v,
                #            }
                #        }
                #    ]
                #    if verbose:
                #        print(json_body)
                #    self.influx_client.write_points(json_body)
            i += 1

    def build(self):
        self.title = 'Tinkerforge Sensors'
        self.sensors = []
        self.buttons = []
        self.displays = []
        self.ipcon = None
        self.influx_client = None

        if tfConnect:
            # Create connection and connect to brickd
            self.ipcon = IPConnection()
            self.ipcon.connect(HOST, PORT)

            # Register Enumerate Callback
            self.ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE, cb_enumerate)

            # Trigger Enumerate
            self.ipcon.enumerate()

            sleep(2)

        if debug:
            print(tfIDs)

        # Connect to InfluxDB server
        #if send_to_influx:
        #    print("Connecting to InfluxDB server %s" % INFLUX_AUTH["host"])
        #    # self.influx_client = InfluxDBClient(INFLUXserver, INFLUXport, INFLUXdbuser, INFLUXdbuser_password, INFLUXdbname)
        #    try:
        #        self.influx_client = InfluxDBClient(
        #            host=INFLUX_AUTH["host"],
        #            port=INFLUX_AUTH["port"],
        #            username=INFLUX_AUTH["user"],
        #            password=INFLUX_AUTH["pass"],
        #            database=INFLUX_AUTH["db"],
        #            ssl=INFLUX_AUTH["ssl"],
        #            timeout=1,
        #            retries=5,)
        #    except Exception as e:
        #        print("Error connecting to InfluxDB:")
        #        print(e)

        for tf in tfIDs:
            # try:
            if True:
                # print(len(tf[0]))
                if len(tf[0])<=4:
                    print(tf)
                    if tf[1] in deviceIDs:
                        bricklet = deviceIdentifiersDict[tf[1]]["class"](tf[0],self.ipcon)
                        if deviceIdentifiersDict[tf[1]]["device_type"]== "sensor":
                            self.sensors.append(bricklet)
                        elif deviceIdentifiersDict[tf[1]]["device_type"]== "display":
                            self.displays.append(bricklet)
                        quantity = getattr(bricklet, deviceIdentifiersDict[tf[1]]["value_func"])()+1
                        v = eval(deviceIdentifiersDict[tf[1]]["correction"] % quantity)
                        unit = deviceIdentifiersDict[tf[1]]["unit"]
                        if debug:
                            print(quantity, deviceIdentifiersDict[tf[1]]["correction"] % quantity)
                            print(tf[0],getIdentifier(tf), deviceIdentifiersDict[tf[1]], v, unit)

        print("Sensors:", self.sensors)
        print("Displays:", self.displays)

def main():
    global INTERVAL
    tfApp = tf_App()
    tfApp.build()
    tfApp.cb_sensors()
    schedule.every(INTERVAL).seconds.do(tfApp.cb_sensors)
    return(tfApp)

if __name__ == "__main__":
    tfApp = main()
    try:
        while True:
            time.sleep(0.5)
            schedule.run_pending()
    except (KeyboardInterrupt, SystemExit):
        print("\nGoodbye!")
    if tfConnect:
        tfApp.ipcon.disconnect()
