#!/usr/bin/python

'''Mind-controlled LEDs. Spooky.'''

import sys
PATH_TO_PULSE_FOLDER = "/home/pi/pulse-test/"
sys.path.append(PATH_TO_PULSE_FOLDER)
from LedStrip_WS2801 import LedStrip_WS2801 as LedStrip
from mindwave import Headset

def exaggerate(level, maxvalue, exponent=0.4):
  halfmax = maxvalue/2.0
  level -= halfmax
  negative = level < 0
  level = abs(level) ** exponent
  if negative: level = -level
  adjustment = halfmax ** exponent
  level += adjustment
  level = maxvalue * level / (2 * adjustment)
  return level

led_strip = LedStrip("/dev/spidev0.0", 20)
headset = Headset()
while True:
  point = headset.readDatapoint()
  print "Attention:", point.attention
  colors = (0, 255, 0)  # G B R
  if point.headsetOnHead():
    a = exaggerate(point.attention, 100, 0.4)
    greenlevel = int(255.0 * a / 100)
    colors = (greenlevel, 0, 255 - greenlevel)  # G B R
  print "Coloring LEDS to RGB (%d, %d, %d)", (colors[2], colors[0], colors[1])
  led_strip.setAll(colors)
  led_strip.update()
