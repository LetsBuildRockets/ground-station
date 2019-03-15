from typing import Any, IO

from PyQt5 import QtGui

from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import smopy
import cv2
import serial
import pynmea2
import numpy as np
import subprocess, time, os, sys
import threading

cmd = ["ssh", "192.168.1.37", "-X", "export DISPLAY=:0; gqrx"]

p = subprocess.Popen(cmd,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.STDOUT)

port = "/dev/ttyUSB0"
ser = serial.Serial(port, baudrate=4800, timeout=0.5)

mapScale = [
    360,
    180,
    90,
    45,
    22.5,
    11.25,
    5.625,
    2.813,
    1.406,
    0.703,
    0.352,
    0.176,
    0.088,
    0.044,
    0.022,
    0.011,
    0.005,
    0.003,
    0.001,
    0.0005
]

app = QApplication([])

mapCenterLat = 41.7390592
mapCenterLon = -72.8686592

groundstationLat = 0
groundstationLon = 0

rocketLat = 0
rocketLon = 0

scaleyboi = 14

we_have_gs_gps_lock = False
we_have_rocket_gps_lock = False

label = QLabel('GPS')
label.show()


def redraw():
    map_thing = np.copy(blank_map_numpy)
    if we_have_gs_gps_lock:
        x, y = blank_map.to_pixels(groundstationLat, groundstationLon)
        cv2.circle(map_thing, (int(x), int(y)), 10, (0, 0, 255), 2)
    else:
        cv2.putText(map_thing, "no ground station gps lock", (10, 60), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 4)

    if we_have_rocket_gps_lock:
        x, y = blank_map.to_pixels(rocketLat, rocketLon)
        cv2.circle(map_thing, (int(x), int(y)), 10, (0, 0, 255), 2)
    else:
        cv2.putText(map_thing, "no rocket gps lock", (10, 120), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 4)

    height, width, channel = map_thing.shape
    q_img = QImage(map_thing.data, width, height, 3 * width, QImage.Format_RGB888)
    label.setPixmap(QPixmap.fromImage(q_img))


def update_background_map():
    global label, blank_map, scaleyboi, blank_map_numpy
    newmap = smopy.Map((mapCenterLat - mapScale[scaleyboi] / 2, mapCenterLon - mapScale[scaleyboi] / 2,
                        mapCenterLat + mapScale[scaleyboi] / 2,
                        mapCenterLon + mapScale[scaleyboi] / 2), z=scaleyboi,
                       tileserver='http://192.168.1.152/osm_tiles/{z}/{x}/{y}.png')
    newmap.save_png('map.png')
    blank_map = newmap
    blank_map_numpy = blank_map.to_numpy()
    height, width, channel = blank_map_numpy.shape
    qImg = QImage(blank_map_numpy.data, width, height, 3 * width, QImage.Format_RGB888)
    label.setPixmap(QPixmap.fromImage(qImg))


def update_my_loc_handler():
    global we_have_gs_gps_lock, groundstationLat, groundstationLon
    try:
        timeoutcount = 10
        data = b''
        while timeoutcount > 0 and data[0:6] != b'$GPGGA':
            data = ser.readline()
        print("data ", data)
        ser.flushInput()
        if data[0:6] == b'$GPGGA':
            if data.__len__() > 60:
                msg = pynmea2.parse(str(data, "utf-8"))
                if msg.gps_qual != "0":
                    newlat = float(msg.lat[0:2]) + float(msg.lat[2:]) / 60.0
                    if msg.lat_dir == "S":
                        newlat = -newlat
                    newlon = float(msg.lon[0:3]) + float(msg.lon[3:]) / 60.0
                    if msg.lon_dir == "W":
                        newlon = -newlon
                    # print("lat: ", newlat, " long: ", newlon)
                    groundstationLat = newlat
                    groundstationLon = newlon
                    we_have_gs_gps_lock = True
            else:
                # print("No ground station gps lock")
                we_have_gs_gps_lock = False
            redraw()
        if we_have_gs_gps_lock is False:
            print("No ground station gps lock")
    except:
        print("Something went wrong")


def update_rocket_loc_handler():
    global we_have_rocket_gps_lock, rocketLat, rocketLon
    while True:
        line = p.stdout.readline()
        print("first part: ", line[0:22])
        if line[0:22] == b'AFSK1200: fm KC1KKR-11':
            AFSKline = (p.stdout.readline()).decode('ascii')
            print("AFSKLINE: ", AFSKline)
            if AFSKline.__len__() > 40:
                time = AFSKline[1:7]
                print("time: ", time)

                lat = AFSKline[8:15]
                lat_dir = AFSKline[15]
                print("lat: ", lat, lat_dir)

                lon = AFSKline[17:25]
                lon_dir = AFSKline[25]
                print("lat: ", lon, lon_dir)

                msg = AFSKline[44:]
                print("msg: ", msg)

                newlat = float(lat[0:2]) + float(lat[2:]) / 60.0
                if lat_dir == "S":
                    newlat = -newlat
                newlon = float(lon[0:3]) + float(lon[3:]) / 60.0
                if lon_dir == "W":
                    newlon = -newlon

                if newlon != 0 and newlat != 0:
                    we_have_rocket_gps_lock = True
                rocketLat = newlat
                rocketLon = newlon
                redraw()

        print(">> dat ", (line.rstrip()))


if __name__ == "__main__":
    update_background_map()

    timer1 = QTimer()
    timer1.setSingleShot(False)
    timer1.timeout.connect(update_my_loc_handler)
    timer1.start(5000)

    timer2 = threading.Thread(target=update_rocket_loc_handler)
    timer2.start()

    app.exec_()
    sys.exit()
