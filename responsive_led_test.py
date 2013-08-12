#!/usr/bin/env python

import sys
import time
from flame.flameboard import FakeFlameBoard, I2CFlameBoard
from led.effects.base import (
    EffectParameters, SnowstormLayer, TechnicolorSnowstormLayer, WhiteOutLayer)
from led.effects.digital_rain import DigitalRainLayer
from led.effects.drifters import *
from led.effects.firefly_swarm import FireflySwarmLayer
from led.effects.impulses import *
from led.effects.lightning_storm import LightningStormLayer
from led.effects.plasma import PlasmaLayer
from led.effects.waves import WavesLayer
from led.model import Model
from led.controller import AnimationController, Renderer
from led.threads import FlamesThread, HeadsetThread, ParamThread, LayerSwapperThread
from led.renderer import Renderer, Playlist
from mindwave.mindwave import FakeHeadset, BluetoothHeadset 
               
               
if __name__ == '__main__':  
    masterParams = EffectParameters()
    model = Model('modeling/graph.data.json', 'modeling/manual.remap.json')
    
    headsetOnLayers = Playlist([
        [
            ImpulseLayer2(),
            WavesLayer(color=(1,0,.2)),
            PlasmaLayer(color=(.1,.1,.1)),
        ],
        [
            WavesLayer(),
            LightningStormLayer(),
        ]
    ])
            
    headsetOffLayers = Playlist([
        [
            TreeColorDrifterLayer([ (1,0,1), (.5,.5,1), (0,0,1) ], 5),
            PlasmaLayer(),
        ],
        [
            OutwardColorDrifterLayer([ (1,0,0), (.7,.3,0), (.7,0,.3) ], 10),
            PlasmaLayer(),
        ]
    ])
            
    transitionLayers = Playlist([
        [WhiteOutLayer()],
        [SnowstormLayer()]
        ])
        
        
    renderer = Renderer({ 'on': headsetOnLayers, 'off': headsetOffLayers, 'transition': transitionLayers }, activePlaylist='off')
    flameBoard = FakeFlameBoard()
    pollingThreads = [
        HeadsetThread(masterParams, FakeHeadset(bad_data=True)),
        # HeadsetThread(masterParams, BluetoothHeadset()),
        LayerSwapperThread(masterParams, renderer, headsetOnLayers, headsetOffLayers, transitionLayers),
        FlamesThread(masterParams, flameBoard),
    ]
    for thread in pollingThreads:
        thread.start()
        
    time.sleep(0.05)
    controller = AnimationController(model, renderer=renderer, params=masterParams)
    controller.drawingLoop()
    
