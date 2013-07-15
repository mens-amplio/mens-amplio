#!/usr/bin/env python

import math
import random
import noise
import numpy

class EffectParameters(object):
    """Inputs to the individual effect layers. Includes basics like the timestamp of the frame we're
       generating, as well as parameters that may be used to control individual layers in real-time.
       """

    time = 0
    targetFrameRate = 45.0     # XXX: Want to go higher, but gl_server can't keep up!


class EffectLayer(object):
    """Abstract base class for one layer of an LED light effect. Layers operate on a shared framebuffer,
       adding their own contribution to the buffer and possibly blending or overlaying with data from
       prior layers.

       The 'frame' passed to each render() function is an array of LEDs in the same order as the
       IDs recognized by the 'model' object. Each LED is a 3-element list with the red, green, and
       blue components each as floating point values with a normalized brightness range of [0, 1].
       If a component is beyond this range, it will be clamped during conversion to the hardware
       color format.
       """

    def render(self, model, params, frame):
        raise NotImplementedError("Implement render() in your EffectLayer subclass")

class RGBLayer(EffectLayer):
    """Simplest layer, draws a static RGB color cube."""

    def render(self, model, params, frame):
        for i, rgb in enumerate(frame):
            # Normalized XYZ in the range [0,1]
            x, y, z = model.edgeCenters[i]
            rgb[0] = x
            rgb[1] = y
            rgb[2] = z


def mixAdd(rgb, r, g, b):
    """Mix a new color with the existing RGB list by adding each component."""
    rgb[0] += r
    rgb[1] += g
    rgb[2] += b    
    

def mixMultiply(rgb, r, g, b):    
    """Mix a new color with the existing RGB list by multiplying each component."""
    rgb[0] *= r
    rgb[1] *= g
    rgb[2] *= b 


class BlinkyLayer(EffectLayer):
    """Test our timing accuracy: Just blink everything on and off every other frame."""

    on = False

    def render(self, model, params, frame):
        self.on = not self.on
        if self.on:
            for i, rgb in enumerate(frame):
                mixAdd(rgb, 1, 1, 1)


class PlasmaLayer(EffectLayer):
    """A plasma cloud layer, implemented with smoothed noise."""

    def render(self, model, params, frame):
        # Noise spatial scale, in number of noise datapoints at the fundamental frequency
        # visible along the length of the sculpture. Larger numbers "zoom out".
        # For perlin noise, we have multiple octaves of detail, so staying zoomed in lets
        # us have a lot of detail from the higher octaves while still having gradual overall
        # changes from the lower-frequency noise.

        s = 0.6

        # Time-varying vertical offset. "Flow" upwards, slowly. To keep the parameters to
        # pnoise3() in a reasonable range where conversion to single-precision float within
        # the module won't be a problem, we need to wrap the coordinates at the point where
        # the noise function seamlessly tiles. By default, this is at 1024 units in the
        # coordinate space used by pnoise3().

        z0 = math.fmod(params.time * -1.5, 1024.0)

        for i, rgb in enumerate(frame):
            # Normalized XYZ in the range [0,1]
            x, y, z = model.edgeCenters[i]

            # Perlin noise with some brightness scaling
            rgb[0] += 1.2 * (0.35 + noise.pnoise3(x*s, y*s, z*s + z0, octaves=3))


class WavesLayer(EffectLayer):
    """Occasional wavefronts of light which propagate outward from the base of the tree"""

    def render(self, model, params, frame):

        # Center of the expanding wavefront
        center = math.fmod(params.time * 2.8, 15.0)

        # Width of the wavefront
        width = 0.4

        for i, rgb in enumerate(frame):
            dist = abs((model.edgeDistances[i] - center) / width)
            if dist < 1:
                # Cosine-shaped pulse
                br = math.cos(dist * math.pi/2)

                # Blue-white color
                mixAdd(rgb, br * 0.5, br * 0.5, br * 1.0)


class ImpulsesLayer(EffectLayer):
    """Oscillating neural impulses which travel outward along the tree"""

    def __init__(self, count=10):
        self.positions = [None] * count
        self.phases = [0] * count
        self.frequencies = [0] * count

    def render(self, model, params, frame):
        for i in range(len(self.positions)):

            if self.positions[i] is None:
                # Impulse is dead. Random chance of reviving it.
                if random.random() < 0.05:

                    # Initialize a new impulse with some random parameters
                    self.positions[i] = random.choice(model.roots)
                    self.phases[i] = random.uniform(0, math.pi * 2)
                    self.frequencies[i] = random.uniform(2.0, 10.0)

            else:
                # Draw the impulse
                br = max(0, math.sin(self.phases[i] + self.frequencies[i] * params.time))
                mixAdd(frame[self.positions[i]], br, br, br)

                # Chance of moving this impulse outward
                if random.random() < 0.2:

                    choices = model.outwardAdjacency[i]
                    if choices:
                        self.positions[i] = random.choice(choices)
                    else:
                        # End of the line
                        self.positions[i] = None


class DigitalRainLayer(EffectLayer):
    """Sort of look like The Matrix"""
    def __init__(self):
        #self.grid = 9
        self.tree_count = 6
        self.period = math.pi * 2
        self.maxoffset = self.period
        self.offsets = [ self.maxoffset * n / self.tree_count for n in range(self.tree_count) ]
        self.speed = 2
        self.height = 1/3.0
        random.shuffle(self.offsets)
        #self.offsets = [ [random.random() * self.maxoffset for x in range(self.grid)] for y in range(self.grid) ]
        #self.offsets = [random.random() * self.maxoffset for t in range(self.tree_count)]
        self.color = [v/255.0 for v in [90, 210, 90]]
        self.bright = [v/255.0 for v in [140, 234, 191]]

    def function(self,n):
        v = math.fmod(n, self.period)
        if v < math.pi / 4:
          return 1
        if v < math.pi:
          return math.sin(v) ** 2
        return 0

    def render(self, model, params, frame):
        for i, rgb in enumerate(frame):
            x,y,z = model.edgeCenters[i]
            out = model.edgeDistances[i]
            #offset = self.offsets[int(y*self.grid)][int(x*self.grid)]
            offset = self.offsets[model.edgeTree[i]]
            d = z + out/2.0
            alpha = self.function(params.time*self.speed + d/self.height + offset)
            shake = random.random() * 0.25 + 0.75

            for w, v in enumerate(self.color):
                if alpha == 1:
                    rgb[w] += shake * alpha * self.bright[w]
                else:
                    rgb[w] += shake * alpha * v

class SnowstormLayer(EffectLayer):
    def render(self, model, params, frame):
        for i, rgb in enumerate(frame):
            level = random.random()
            for w, v in enumerate(rgb):
                rgb[w] += level

class TechnicolorSnowstormLayer(EffectLayer):
    def render(self, model, params, frame):
        for i, rgb in enumerate(frame):
            for w, v in enumerate(rgb):
                level = random.random()
                rgb[w] += level

class PulseLayer2(EffectLayer):
    class Pulse():
        def __init__(self, color, edge, motion = "Out"):
            self.color = color
            self.edge = edge
            self.previous_edge = None
            self.dead = False
            self.motion = "Out"

        def _move_to_any_of(self, edges):
            self.previous_edge = self.edge
            self.edge = random.choice(edges)

        def _node_incoming_and_outgoing(self, model):
            nodes = model.edges[self.edge]
            previous_nodes = model.edges[self.previous_edge]
            from_node = [n for n in nodes if n in previous_nodes][0]
            to_node = [n for n in nodes if n != from_node][0]
            return (from_node, to_node)

        def move(self, model, params):
            height = model.edgeHeight[self.edge]
            nodes = model.edges[self.edge]
            to_edges = [e for n in nodes for e in model.edgeListForNodes[n] if e != self.edge ]

            if self.motion == 'Out':
                to_edges = [e for e in to_edges if model.edgeHeight[e] > height]
            elif self.motion == 'In':
                to_edges = [e for e in to_edges if model.edgeHeight[e] < height]

            if to_edges:
                self._move_to_any_of(to_edges)
            else:
                if self.motion == 'Out':
                    self.motion = 'In'
                    self.move(model, params)
                elif self.motion == 'In':
                    self.motion = 'Out'
                    self.move(model, params)

        def render(self, model, params, frame):
            if self.dead:
                return
            for v,c in enumerate(self.color):
                frame[self.edge][v] += c

    def __init__(self, model, pulse_colors = [(1.0,1.0,1.0)]):
        # later the pulses will get generated automatically
        # and we won't have to pass the model into the constructor
        self.pulses = [PulseLayer2.Pulse(color, random.choice(model.roots)) for color in pulse_colors]
        self.last_time = None
        self.frequency = 0.1 # seconds

    def _move_pulses(self, model, params):
        if not self.last_time:
            self.last_time = params.time
            return
        if params.time < self.last_time + self.frequency:
            return
        self.last_time = params.time
        for pulse in self.pulses:
            pulse.move(model, params)


    def render(self, model, params, frame):
        self._move_pulses(model, params)
        for pulse in self.pulses:
            pulse.render(model, params, frame)

class GammaLayer(EffectLayer):
    """Apply a gamma correction to the brightness, to adjust for the eye's nonlinear sensitivity."""

    def __init__(self, gamma):
        self.gamma = gamma

    def render(self, model, params, frame):
        numpy.clip(frame, 0, 1, frame)
        numpy.power(frame, self.gamma, frame)


