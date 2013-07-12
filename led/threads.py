#!/usr/bin/env python

import threading
import random
import time
from mindwave.mindwave import FakeHeadset

class ParamGetterThread(threading.Thread):
    """
    Base class for daemon threads that store/modify an EffectParameters object
    """
    def __init__(self, params):
        threading.Thread.__init__(self)
        self.daemon = True
        self.params = params
       

class HeadsetThread(ParamGetterThread):
    """
    Polls the Mindwave headset and stores the most recent datapoint in an 
    EffectParameters object.
    """        
    def run(self):
        h = FakeHeadset()
        while True:
            self.params.eegPoint = h.readDatapoint()
            
            
class PulseThread(ParamGetterThread):
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