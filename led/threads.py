#!/usr/bin/env python

import threading
import random
import time
import math
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
    Polls the Mindwave headset and maintains a buffer of the last few datapoints.
    Each time a new point is received, creates a EEGInfo object and passes it to
    self.params.eegUpdate
    """ 
    
    class EEGInfo:
        """
        Extracts/stores all the recent headset info that the effects might actually care about.
        Attention and meditation values are scaled to floats in the range [0,1].
        """
        def __init__(self, points):
            """
            points: buffer of the last few mindwave.Datapoints received
            """
            def scale(n):
                return float(n)/100
            last = points[-1]
            self.attention = scale(last.attention)
            self.meditation = scale(last.meditation)
            self.on = last.poor_signal == 0
            def average(points, attr):
                return scale( sum(getattr(p, attr) for p in points) / len(points) ) #TODO disregard zeros?
            self.attentionSmooth = average(points, 'attention')
            self.meditationSmooth = average(points, 'meditation')
            self.timestamp = time.time()
           
    def __init__(self, params):
        ParamThread.__init__(self, params)
        self.priorPoints = []
        self.lastParams = None
        self.bufferSize = 3
        
    def run(self):
        h = FakeHeadset(bad_data=True)
        while True:
            point = h.readDatapoint()
            if len(self.priorPoints) == self.bufferSize:
                self.priorPoints = self.priorPoints[1:]
            self.priorPoints.append(point)
            self.params.eegUpdate(HeadsetThread.EEGInfo(self.priorPoints))
            
            
            
class PulseThread(ParamThread):
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
            
