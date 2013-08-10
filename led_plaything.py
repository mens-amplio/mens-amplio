#!/usr/bin/env python
#
# Experimental LED effects code for MensAmplio

from led.model import Model
from led.controller import AnimationController
from led.renderer import Renderer
import led.effects as effects

            
if __name__ == '__main__':
    model = Model('modeling/graph.data.json', 'modeling/manual.remap.json')
    renderer = Renderer(layers=[
        effects.TreeColorDrifterLayer([(0,1,0), (0,0,1), (1,0,0)], 5), 
        #effects.HomogenousColorDrifterLayer([(0,1,0), (0,0,1), (1,0,0)], 5), 
        effects.PlasmaLayer(),
        #ImpulsesLayer(),
        # effects.WavesLayer(),
        #effects.DigitalRainLayer(),
        #effects.SnowstormLayer(),
        #effects.TechnicolorSnowstormLayer(),
        #effects.ImpulseLayer2(),
        #effects.LightningStormLayer(),
        #effects.FireflySwarm(model),
        ],
        gamma=2.2,
        )
    controller = AnimationController(model, renderer)
    controller.drawingLoop()
