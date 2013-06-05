import datetime
import time
import bluetooth
from MindwaveDataPoints import RawDataPoint, EEGPowersDataPoint
from MindwaveDataPointReader import MindwaveDataPointReader


if __name__ == '__main__':
    mindwaveDataPointReader = MindwaveDataPointReader()
    mindwaveDataPointReader.start()
    
    f = open("datapoints.csv", "w")
    headers = ('attention,meditation,poorsignal'.split(',') +
    	       EEGPowersDataPoint.WAVE_NAMES)
    headers.sort()
    print >>f, 'time,' + ','.join(headers)
    data = {}

    while(True):
        try:
            dataPoint = mindwaveDataPointReader.readNextDataPoint()
            if (not dataPoint.__class__ is RawDataPoint):
                print dataPoint
                if dataPoint.__class__ is EEGPowersDataPoint:
                    for name in EEGPowersDataPoint.WAVE_NAMES:
                        if name not in headers:
                            print "*!*!*!*!*!!*!* WTF is this data point?", name
                            continue
                        data[name] = getattr(dataPoint, name)
                else:
                    name, value = dataPoint.name, dataPoint.value
                    if name not in headers:
                        print "*!*!*!*!*!!*!* WTF is this data point?", name
                        continue
                    if name in data:
                        print "<-> Overwriting %s value from %d to %d" % (
                            name, data[name], value)
                    data[name] = value
                if len(data) >= len(headers):
                    values = [data[h] for h in headers]
                    line = str(time.time()) + ',' + ','.join(str(x) for x in values)
                    print "len values:", len(values)
                    print values
                    print >>f, line
                    f.flush()
                    data = {}
                else:
                    print "len data is %d, len headers is %d" % (len(data), len(headers))
        except bluetooth.btcommon.BluetoothError, e:
            print "Bluetooth Error (Headset off?), retrying in 5s"
            time.sleep(5)
