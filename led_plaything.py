#!/usr/bin/env python
#
# Experimental LED effects code for MensAmplio

from led.model import Model
from led.controller import AnimationController
from led.renderer import Renderer
import led.effects as effects

if __name__ == '__main__':
    model = Model('modeling/graph.data.json', 'modeling/manual.remap.json')
    renderer = Renderer([
        # effects.PlasmaLayer(),
        #ImpulsesLayer(),
        # effects.WavesLayer(),
        #effects.DigitalRainLayer(),
        #effects.SnowstormLayer(),
        #effects.TechnicolorSnowstormLayer(),
        # effects.PulseLayer2(model),
        effects.LightningStormLayer(bolt_every=.15),
        effects.GammaLayer(2.2),
        ])
    controller = AnimationController(model, renderer)
    controller.drawingLoop()
