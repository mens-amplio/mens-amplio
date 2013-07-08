#!/usr/bin/python

'''Simple example usage of Mindwave headset

Connects to the headset, and continuously prints the data it reads
in a legible format. Raw data is not shown.
'''

from mindwave import BluetoothHeadset

h = BluetoothHeadset()
while True:
  point = h.readDatapoint()
  print point

# That's it. Easy enough.
