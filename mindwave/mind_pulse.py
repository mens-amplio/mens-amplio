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
from mindwave import BluetoothHeadset

def GetColorsForAttentionLevel(attention):
  redlevel = int((point.attention - 33) * 255 / 33.0)
  redlevel = max(min(redlevel, 255), 0)
  bluelevel = 255 - redlevel
  return redlevel, 0, bluelevel

led_strip = LedStrip("/dev/spidev0.0", 20)
# Set lights to a soft white to indicate the program is starting,
# but not reading your mind yet.
led_strip.setAll((64, 64, 64))
led_strip.update()
headset = BluetoothHeadset()
while True:
  point = headset.readDatapoint()
  if not point or not point.clean():
    print ("Not getting clean data yet. If you see this at startup, wait ~20s. "
           "If it persists, adjust the headset for a better fit.")
    led_strip.setAll((64, 64, 64))
    led_strip.update()
    continue
  print "Attention:", point.attention
  r, g, b = GetColorsForAttentionLevel(point.attention)
  print "Coloring LEDS to RGB:", (r, g, b)
  led_strip.setAll((g, b, r))  # LED strip uses funky ordering
  led_strip.update()
