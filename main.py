from pyforms.basewidget import BaseWidget
from pyforms.controls import ControlFile
from pyforms.controls import ControlText
from pyforms.controls import ControlSlider
from pyforms.controls import ControlPlayer
from pyforms.controls import ControlButton
from pyforms.controls import ControlImage
import cv2
import smopy
import time
import serial
import threading
import pynmea2


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

gs = 0


class GroundStation(BaseWidget):

    def __init__(self, *args, **kwargs):
        super().__init__('Ground Station Software')

        self.mapCenterLat = 41.0730202
        self.mapCenterLong = -72.0839729

        # Definition of the forms fields
        self._runbutton = ControlButton('Run')
        self._mapImage = ControlImage('map')

        self.scaleyboi = 18
        newmap = smopy.Map((self.mapCenterLat - mapScale[self.scaleyboi] / 2, self.mapCenterLong - mapScale[self.scaleyboi] / 2, self.mapCenterLat + mapScale[self.scaleyboi] / 2, self.mapCenterLong + mapScale[self.scaleyboi] / 2), z=self.scaleyboi, tileserver='http://192.168.1.152/osm_tiles/{z}/{x}/{y}.png')
        self.blank_map = newmap
        self.map = self.blank_map.to_numpy()
        self._mapImage.value = self.map

        self._runbutton.value = self.run_event

        # Define the organization of the Form Controls
        self.formset = [{
            'Tab1': ['_runbutton'],
            'Tab2': ['_mapImage']
        }]

        self.update_my_loc_handler()
        self.update_map_center_handler()

    def run_event(self):
        """
        After setting the best parameters run the full algorithm
        """

        print("The function was executed")

    def update_my_loc(self, lat, long):
        x, y = self.blank_map.to_pixels(lat, long)
        self.map = cv2.circle(self.blank_map.to_numpy(), (int(x), int(y)), 2, (255, 0, 0), -1)
        self._mapImage.value = self.map

    def update_my_loc_handler(self):
        try:
            data = ser.readline()
            # print("data ", data)
            if data[0:6] == b'$GPGGA':
                msg = pynmea2.parse(str(data, "utf-8"))
                if msg.gps_qual != "0":
                    newlat = float(msg.lat[0:2]) + float(msg.lat[2:])/60.0
                    if msg.lat_dir == "S":
                        newlat = -newlat
                    newlon = float(msg.lon[0:3]) + float(msg.lon[3:])/60.0
                    if msg.lon_dir == "W":
                        newlon = -newlon
                    # print("lat: ", newlat, " long: ", newlon)
                    self.mapCenterLat = newlat
                    self.mapCenterLong = newlon
                    self.update_my_loc(newlat, newlon)
                    self._mapImage.show()
        except:
            print("Something went wrong")
        threading.Timer(1, self.update_my_loc_handler).start()

    def update_map_center_handler(self):
        new_map = smopy.Map((self.mapCenterLat - mapScale[self.scaleyboi] / 2, self.mapCenterLong - mapScale[self.scaleyboi] / 2,
                            self.mapCenterLat + mapScale[self.scaleyboi] / 2, self.mapCenterLong + mapScale[self.scaleyboi] / 2), z=self.scaleyboi,
                            tileserver='http://192.168.1.152/osm_tiles/{z}/{x}/{y}.png')
        self.blank_map = new_map
        threading.Timer(10, self.update_map_center_handler).start()


if __name__ == '__main__':
    from pyforms import start_app

    start_app(GroundStation)

