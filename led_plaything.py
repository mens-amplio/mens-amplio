#!/usr/bin/env python
#
# Experimental LED effects code for MensAmplio

from led.model import Model
from led.controller import AnimationController
import led.effects as effects

if __name__ == '__main__':
    model = Model('modeling/graph.data.json')
    controller = AnimationController(model, [
        effects.PlasmaLayer(),
        #ImpulsesLayer(),
        effects.WavesLayer(),
        effects.GammaLayer(2.2),
        ])
    controller.drawingLoop()
