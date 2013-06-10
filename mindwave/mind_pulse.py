#!/usr/bin/python

'''Mind-controlled LEDs. Spooky.'''

import sys
PATH_TO_PULSE_FOLDER = "/home/pi/pulse-test/"
sys.path.append(PATH_TO_PULSE_FOLDER)
from LedStrip_WS2801 import LedStrip_WS2801 as LedStrip
from mindwave import Headset

led_strip = LedStrip("/dev/spidev0.0", 20)
headset = Headset()
while True:
  point = headset.readDatapoint()
  print point
  if point.headsetOnHead():
    a = int(255*point.attention/100.)
    led_strip.setAll((  # G B R
      a, 0, 255-a))
  else:
    led_strip.setAll((0, 255, 0))  # G B R
  led_strip.update()
