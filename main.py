from PyQt5 import QtGui

from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import smopy
import sys
import cv2
import serial
import pynmea2
import numpy as np


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
mapCenterLong = -72.8686592

scaleyboi = 15

we_have_gs_gps_lock = False

label = QLabel('GPS')
label.show()

# global label2
# label2 = QLabel('IMU')
# label2.show()


def update_background_map():
    global label, blank_map, scaleyboi, blank_map_numpy
    newmap = smopy.Map((mapCenterLat - mapScale[scaleyboi] / 2, mapCenterLong - mapScale[scaleyboi] / 2,
                        mapCenterLat + mapScale[scaleyboi] / 2,
                        mapCenterLong + mapScale[scaleyboi] / 2), z=scaleyboi,
                       tileserver='http://192.168.1.152/osm_tiles/{z}/{x}/{y}.png')
    newmap.save_png('map.png')
    blank_map = newmap
    blank_map_numpy = blank_map.to_numpy()
    height, width, channel = blank_map_numpy.shape
    qImg = QImage(blank_map_numpy.data, width, height, 3 * width, QImage.Format_RGB888)
    label.setPixmap(QPixmap.fromImage(qImg))
    print("done")


def update_my_loc(lat, long):
    global blank_map
    x, y = blank_map.to_pixels(lat, long)
    map_thing = np.copy(blank_map_numpy)
    cv2.circle(map_thing, (int(x), int(y)), 10, (0, 0, 255), 2)
    height, width, channel = map_thing.shape
    q_img = QImage(map_thing.data, width, height, 3 * width, QImage.Format_RGB888)
    label.setPixmap(QPixmap.fromImage(q_img))


def update_my_loc_handler():
    global we_have_gs_gps_lock
    try:
        data = ser.readline()
        ser.flushInput()
        print("data ", data)
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
                    update_my_loc(newlat, newlon)
                    we_have_gs_gps_lock = True
            else:
                # print("No ground station gps lock")
                we_have_gs_gps_lock = False
        if we_have_gs_gps_lock == False:
            print("No ground station gps lock")
            map_thing = np.copy(blank_map_numpy)
            cv2.putText(map_thing, "no ground station gps lock", (10, 60), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 4)
            height, width, channel = map_thing.shape
            q_img = QImage(map_thing.data, width, height, 3 * width, QImage.Format_RGB888)
            label.setPixmap(QPixmap.fromImage(q_img))
    except:
        print("Something went wrong")


if __name__ == "__main__":
    update_background_map()

    timer1 = QTimer()
    timer1.setSingleShot(False)
    timer1.timeout.connect(update_my_loc_handler)
    timer1.start(1000)

    sys.exit(app.exec_())