#!/usr/bin/env python

import led.effects as effects
from led.model import Model
from led.controller import AnimationController
import threading
import random
import time
from mindwave.mindwave import FakeHeadset


def mixMultiply(rgb, r, g, b):    
    """Mix a new color with the existing RGB list by multiplying each component."""
    rgb[0] *= r
    rgb[1] *= g
    rgb[2] *= b 

    
class AttentionColors(effects.EffectLayer):
    """
    Fills the whole model with a shade of blue indicating the most recent attention
    reading from the headset. Does nothing if reading is unavailable.
    """
    def render(self, model, params, frame):
        if hasattr(params, 'eegPoint'):
            b = float(params.eegPoint.attention) / 100;
            for i, rgb in enumerate(frame):
                effects.mixAdd( rgb, 0, 0, b )
                
                
class Pulser(effects.EffectLayer):
    """
    Adds some green across the current frame if the pulse parameter is high.
    Does nothing if parameter is unavailable.
    """
    PULSE_HIGH = 0.5
    PULSE_LOW = 0
    
    def render(self, model, params, frame):
       if hasattr(params, 'pulseHigh'):
           val = self.PULSE_HIGH if params.pulseHigh else self.PULSE_LOW
           for i, rgb in enumerate(frame):
               #mixMultiply( rgb, val, val, val )
               effects.mixAdd(rgb, 0, val, 0)


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
            
        
if __name__ == '__main__':    
    model = Model('modeling/graph.data.json')
    controller = AnimationController(model, [
        AttentionColors(),
        #effects.RGBLayer(),
        Pulser(),
        effects.GammaLayer(2.2),
        ])
        
    pollingThreads = [
        HeadsetThread(controller.params),
        PulseThread(controller.params),
    ]
    for thread in pollingThreads:
        thread.start()
        
    controller.drawingLoop()
    