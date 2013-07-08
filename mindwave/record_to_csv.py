#!/usr/bin/python

from mindwave import BluetoothHeadset, WAVE_NAMES_IN_ORDER, FakeHeadset


measurements_file = open("datapoints.csv", "w")
raw_voltage_file = open("raw_voltages.txt", "w")
fields = ('timestamp,poor_signal,attention,meditation,blink'.split(',') +
          WAVE_NAMES_IN_ORDER)
print >>measurements_file, ",".join(fields)

#h = BluetoothHeadset()
h = FakeHeadset()
while True:
  point = h.readDatapoint()
  print point
  values = [str(getattr(point, f,-1)) for f in fields]
  print >>measurements_file, ",".join(values)
  for raw in point.raw_voltages:
    print >>raw_voltage_file, raw
  measurements_file.flush()
  raw_voltage_file.flush()
