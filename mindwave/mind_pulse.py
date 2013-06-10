#!/usr/bin/python

'''Mind-controlled LEDs. Spooky.'''

import sys
PATH_TO_PULSE_FOLDER = "/home/pi/pulse-test/"
sys.path.append(PATH_TO_PULSE_FOLDER)
from LedStrip_WS2801 import LedStrip_WS2801 as LedStrip
from mindwave import Headset

led_strip = LedStrip("/dev/spidev0.0", 6)
headset = Headset()
while True:
  point = headset.readDatapoint()
  print point
  if point.headsetOnHead():
    led_strip.setAll((
      int(255*point.attention/100.),
      int(255*point.meditation/100.),
      0))
  else:
    led_strip.setAll((0, 0, 255))
  led_strip.update()
