#!/usr/bin/env python

import sys
import time
import led.effects as effects
from led.model import Model
from led.controller import AnimationController, Renderer
from led.threads import HeadsetThread, ParamThread, LayerSwapperThread
from led.renderer import Renderer, RoutineList
from mindwave.mindwave import FakeHeadset, BluetoothHeadset 
               
               
if __name__ == '__main__':  
    masterParams = effects.EffectParameters()
    model = Model('modeling/graph.data.json', 'modeling/manual.remap.json')
    renderer = Renderer()
    
    headsetOnLayers = RoutineList([
        [
            effects.ImpulseLayer2(),
            effects.WavesLayer(color=(1,0,.2)),
            effects.PlasmaLayer(color=(.1,.1,.1)),
        ],
        [
            effects.WavesLayer(),
            effects.LightningStormLayer(),
        ]
    ])
            
    headsetOffLayers = RoutineList([
        [
            effects.TreeColorDrifterLayer([ (1,0,1), (.5,.5,1), (0,0,1) ], 5),
            effects.PlasmaLayer(),
        ],
        [
            effects.OutwardColorDrifterLayer([ (1,0,0), (.7,.3,0), (.7,0,.3) ], 10),
            effects.PlasmaLayer(),
        ]
    ])
            
    transitionLayers = RoutineList([
        [effects.WhiteOutLayer()],
        [effects.SnowstormLayer()]
        ])
    
    pollingThreads = [
        HeadsetThread(masterParams, FakeHeadset(bad_data=True)),#BluetoothHeadset()),
        LayerSwapperThread(masterParams, renderer, headsetOnLayers, headsetOffLayers, transitionLayers)
    ]
    for thread in pollingThreads:
        thread.start()
        
    time.sleep(0.05)
    controller = AnimationController(model, renderer=renderer, params=masterParams)
    controller.drawingLoop()
    
