#!/usr/bin/env python

import led.effects as effects
from led.model import Model
from led.controller import AnimationController
from led.threads import HeadsetThread, PulseThread

 
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
    