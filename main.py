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
import threading

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

mapCenterLat = 41.730202
mapCenterLong = -72.839729
gs = 0


class GroundStation(BaseWidget):

    def __init__(self, *args, **kwargs):
        super().__init__('Ground Station Software')

        # Definition of the forms fields
        self._runbutton = ControlButton('Run')
        self._mapImage = ControlImage('map')

        map = smopy.Map((mapCenterLat - mapScale[13] / 2, mapCenterLong - mapScale[13] / 2, mapCenterLat + mapScale[13] / 2, mapCenterLong + mapScale[13] / 2), z=13, tileserver='http://192.168.1.152/osm_tiles/{z}/{x}/{y}.png')
        self.blankmap = map
        self.map = self.blankmap
        self._mapImage.value = self.map.to_numpy()

        self._runbutton.value = self.run_event

        # Define the organization of the Form Controls
        self.formset = [{
            'Tab1': ['_runbutton'],
            'Tab2': ['_mapImage']
        }]

    def run_event(self):
        """
        After setting the best parameters run the full algorithm
        """

        print("The function was executed")

    def update_my_loc(self, lat, long):
        x, y = self.blankmap.to_pixels(lat, long)
        self.map = cv2.circle(self.blankmap.to_numpy(), (int(x), int(y)), 2, (255, 0, 0), -1)
        self._mapImage.value = self.map


def do_the_thing():
    for x in range(100):
        if gs != 0:
            gs.update_my_loc(41.736750 + x / 1000, -72.868944)
        time.sleep(.1)


if __name__ == '__main__':
    from pyforms import start_app

    threading.Timer(10, do_the_thing).start()

    start_app(GroundStation)

