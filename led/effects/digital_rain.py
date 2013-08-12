import math
import numpy
import random
from base import EffectLayer, HeadsetResponsiveEffectLayer

class DigitalRainLayer(EffectLayer):
    """Sort of look like The Matrix"""

    transitionFadeTime = 5

    def __init__(self):
        self.tree_count = 6
        self.period = math.pi * 2
        self.maxoffset = self.period
        self.offsets = [ self.maxoffset * n / self.tree_count for n in range(self.tree_count) ]
        self.speed = 2
        self.height = 1/3.0

        random.shuffle(self.offsets)
        self.offsets = numpy.array(self.offsets)

        self.color = numpy.array([v/255.0 for v in [90, 210, 90]])
        self.bright = numpy.array([v/255.0 for v in [140, 234, 191]])

        # Build a color table across one period
        self.colorX = numpy.arange(0, self.period, self.period / 100)
        self.colorY = numpy.array([self.calculateColor(x) for x in self.colorX])

    def calculateColor(self, v):
        # Bright part
        if v < math.pi / 4:
            return self.bright

        # Nonlinear fall-off
        if v < math.pi:
            return self.color * (math.sin(v) ** 2)

        # Empty
        return [0,0,0]

    def render(self, model, params, frame):

        # Scalar animation parameter, based on height and distance
        d = model.edgeCenters[:,2] + 0.5 * model.edgeDistances
        numpy.multiply(d, 1/self.height, d)

        # Add global offset for Z scrolling over time
        numpy.add(d, params.time * self.speed, d)

        # Add an offset that depends on which tree we're in
        numpy.add(d, numpy.choose(model.edgeTree, self.offsets), d)

        # Periodic animation, stored in our color table. Linearly interpolate.
        numpy.fmod(d, self.period, d)
        color = numpy.empty((model.numLEDs, 3))
        color[:,0] = numpy.interp(d, self.colorX, self.colorY[:,0])
        color[:,1] = numpy.interp(d, self.colorX, self.colorY[:,1])
        color[:,2] = numpy.interp(d, self.colorX, self.colorY[:,2])

        # Random flickering noise
        noise = numpy.random.rand(model.numLEDs).reshape(-1, 1)
        numpy.multiply(noise, 0.25, noise)
        numpy.add(noise, 0.75, noise)

        numpy.multiply(color, noise, color)
        numpy.add(frame, color, frame)
