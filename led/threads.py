#!/usr/bin/env python

import threading
import random
import time
from mindwave.mindwave import FakeHeadset


class ParamThread(threading.Thread):
    """
    Base class for daemon threads that operate on an EffectParameters object
    """
    def __init__(self, params):
        threading.Thread.__init__(self)
        self.daemon = True
        self.params = params

      
class HeadsetThread(ParamThread):
    """
    Polls the Mindwave headset. Each time a new point is received, creates an 
    EEGInfo object and stores it in params.
    """ 
    
    class EEGInfo:
        """
        Extracts/stores all the headset info that the effects might actually care about.
        Attention and meditation values are scaled to floats in the range [0,1].
        """
        def __init__(self, point):
            def scale(n):
                return float(n)/100
            self.attention = scale(point.attention)
            self.meditation = scale(point.meditation)
            self.on = point.headsetOn()
        
    def run(self):
        h = FakeHeadset(bad_data=True)
        while True:
            point = h.readDatapoint()
            self.params.eeg = HeadsetThread.EEGInfo(point)
            print "update"
            
            
            
class FakePulseThread(ParamThread):
    """
    Pretends to poll a pulse sensor and updates a boolean parameter showing
    whether a beat is currently happening.
    """    
    def run(self):
        start = time.time()
        ipiSecs = 1.0 #inter-pulse interval of 1sec -> 60bpm
        while True:
            elapsed = time.time() - start
            # let's just pretend that the ECG r-wave spike has a duration of 
            # 1/8 of the beat cycle
            self.params.pulseHigh = (elapsed % ipiSecs) < (ipiSecs/8)
            time.sleep(0.05)
            
