#!/usr/bin/python

'''Mind-controlled LEDs. Spooky.

Colors the LedStripWS2801 LEDs according to the Mindwave 'attention' reading:
* Green if your attention is maxiimal
* Red if your attention is minimal
* Blue if you're in the middle
* White if the headset is not ready
'''

import sys
PATH_TO_PULSE_FOLDER = "/home/pi/pulse-test/"
sys.path.append(PATH_TO_PULSE_FOLDER)
from LedStrip_WS2801 import LedStrip_WS2801 as LedStrip
from mindwave import Headset


led_strip = LedStrip("/dev/spidev0.0", 20)
headset = Headset()
while True:
  point = headset.readDatapoint()
  print "Attention:", point.attention
  colors = (255, 255, 255)  # G B R
  if point.headsetOnHead():
    if point.attention > 66:
      colors = (255, 0, 0)  # Green for paying attention
    elif point.attention < 33:
      colors = (0, 0, 255)  # Red for slacking off
    else:
      colors = (0, 255, 0)  # Blue for in-the-middle
  print "Coloring LEDS to RGB:", (colors[2], colors[0], colors[1])
  led_strip.setAll(colors)
  led_strip.update()
