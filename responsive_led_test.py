#!/usr/bin/env python

import sys
import time
import led.effects as effects
from led.model import Model
from led.controller import AnimationController, Renderer
from led.threads import HeadsetThread, FakePulseThread, ParamThread
from led.renderer import Renderer
 

class LayerSwapperThread(ParamThread):
    """
    Monitors the headset parameter data and changes the active layers in the renderer
    when the headset is taken on or off, or when headset data values cross a certain 
    threshold [not implemented yet]
    """
    def __init__(self, params, renderer):
        ParamThread.__init__(self, params)
        self.renderer = renderer
        self.headsetOn = False
        
        self.headsetOnLayers = [
            effects.ResponsiveGreenHighRedLow('attention'),
            #effects.PlasmaLayer(),
            #effects.PulseLayer2(model),
            ]
        self.headsetOffLayers = [
            effects.RGBLayer(),
            # effects.PlasmaLayer(color=(0,0,1)),
            # effects.LightningStormLayer(bolt_every=1.5)
            ]
        
        renderer.activeLayers = self.headsetOffLayers
        
    def run(self):
        while True:
            if self.params.eeg and self.params.eeg.on:
                if not self.headsetOn:
                    sys.stderr.write("on!\n")
                    self.headsetOn = True
                    self.renderer.setFade(0.5, [effects.WhiteOut()], self.headsetOnLayers)
            else:
                if self.headsetOn:
                    sys.stderr.write("off!\n")
                    self.headsetOn = False
                    self.renderer.setFade(1, self.headsetOffLayers)
            time.sleep(0.05)
                
                
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
    masterParams = effects.EffectParameters()
    model = Model('modeling/graph.data.json', 'modeling/manual.remap.json')
    renderer = Renderer()
    
    pollingThreads = [
        HeadsetThread(masterParams),
        LayerSwapperThread(masterParams, renderer)
        #FakePulseThread(controller.params),
    ]
    for thread in pollingThreads:
        thread.start()
        
    time.sleep(0.05)
    controller = AnimationController(model, renderer=renderer, params=masterParams)
    controller.drawingLoop()
    
