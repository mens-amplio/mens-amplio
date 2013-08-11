#!/usr/bin/env python
#
# Experimental LED effects code for MensAmplio

from led.model import Model
from led.controller import AnimationController
from led.renderer import Renderer
from led.effects.base import SnowstormLayer, TechnicolorSnowstormLayer
from led.effects.digital_rain import DigitalRainLayer
from led.effects.drifters import *
from led.effects.firefly_swarm import FireflySwarmLayer
from led.effects.impulses import *
from led.effects.lightning_storm import LightningStormLayer
from led.effects.plasma import PlasmaLayer
from led.effects.waves import WavesLayer

            
if __name__ == '__main__':
    model = Model('modeling/graph.data.json', 'modeling/manual.remap.json')
    renderer = Renderer(layers=[
        TreeColorDrifterLayer([(0,1,0), (0,1,1), (1,0,1)], 5), 
        # OutwardColorDrifterLayer([(0,1,0), (0,0,1), (1,0,0)], 5), 
        #HomogenousColorDrifterLayer([(0,1,0), (0,0,1), (1,0,0)], 5), 
        PlasmaLayer(),
        #ImpulsesLayer(),
        #WavesLayer(),
        #DigitalRainLayer(),
        #SnowstormLayer(),
        #TechnicolorSnowstormLayer(),
        #ImpulseLayer2(),
        LightningStormLayer(),
        #FireflySwarm(model),
        ],
        gamma=2.2,
        )
    controller = AnimationController(model, renderer)
    controller.drawingLoop()
