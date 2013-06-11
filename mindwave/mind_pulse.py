#!/usr/bin/python

'''Mind-controlled LEDs. Spooky.

Colors the LedStripWS2801 LEDs according to the Mindwave 'attention' reading:
* Green if your attention is high
* Red if your attention is low
* Blue if you're in the middle
* White if the headset is not ready
'''

#############################################
# Update this so python can find the LedStrip code
#############################################
PATH_TO_PULSE_FOLDER = "/home/pi/pulse-test/"

import sys
sys.path.append(PATH_TO_PULSE_FOLDER)
from LedStrip_WS2801 import LedStrip_WS2801 as LedStrip
from mindwave import Headset


led_strip = LedStrip("/dev/spidev0.0", 20)
# Set lights to a soft white to indicate the program is starting,
# but not reading your mind yet.
led_strip.setAll((64, 64, 64))
led_strip.update()
headset = Headset()
while True:
  point = headset.readDatapoint(wait_for_clean_data=True)
  print "Attention:", point.attention
  if point.attention > 66:
    colors = (255, 0, 0)  # Green for paying attention
  elif point.attention < 33:
    colors = (0, 0, 255)  # Red for slacking off
  else:
    colors = (0, 255, 0)  # Blue for in-the-middle
  print "Coloring LEDS to RGB:", (colors[2], colors[0], colors[1])
  led_strip.setAll(colors)
  led_strip.update()
