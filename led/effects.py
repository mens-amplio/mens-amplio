#!/usr/bin/env python

import math
import random
import noise
import numpy
import colorsys
import time

class EffectParameters(object):
    """Inputs to the individual effect layers. Includes basics like the timestamp of the frame we're
       generating, as well as parameters that may be used to control individual layers in real-time.
       """

    time = 0
    targetFrameRate = 45.0     # XXX: Want to go higher, but gl_server can't keep up!
    eeg = None
    eegPrev = None
    
    def eegUpdate(self, eeg):
        self.eegPrev = self.eeg
        self.eeg = eeg
    
    def eegInterpolate(self, attr):
        """
        Interpolates between values in eeg and eegPrev.
        
        Values are scaled by:
        (time elapsed since eeg.timestamp) / (distance between eeg and eegPrev's timestamps)
        
        This assumes that eegUpdate is being called at regular intervals, so the interpolation should
        reach the value from eeg right as eeg is updated. If that assumption is violated and the scale
        factor grows >1 (or if eegPrev is None), returns the value from eeg.
        """
        val = 0
        if self.eeg:
            val = getattr(self.eeg, attr)
            if self.eegPrev:
                interval = self.eeg.timestamp - self.eegPrev.timestamp
                percentage = (time.time() - self.eeg.timestamp)/interval
                if percentage < 1: 
                    val = getattr(self.eegPrev,attr)*(1-percentage) + val*percentage
        return val


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


class HeadsetResponsiveEffectLayer(EffectLayer):
    """A layer effect that responds to the MindWave headset in some way.

    Two major differences from EffectLayer:
    1) Constructor expects two paramters:
       -- respond_to: the name of a field in EEGInfo (threads.HeadsetThread.EEGInfo).
          Currently this means either 'attention' or 'meditation'
       -- smooth_response_over_n_secs: to avoid rapid fluctuations from headset
          noise, averages the response metric over this many seconds
    2) Subclasses now only implement the render_responsive() function, which
       is the same as EffectLayer's render() function but has one extra
       parameter, response_level, which is the current EEG value of the indicated
       field (assumed to be on a 0-1 scale, or None if no value has been read yet).
    """
    def __init__(self, respond_to, smooth_response_over_n_secs=5):
        # Name of the eeg field to influence this effect
        self.respond_to = respond_to
        self.smooth_response_over_n_secs = smooth_response_over_n_secs
        self.measurements = []
        self.timestamps = []
        self.last_eeg = None
        self.last_response_level = None
        # We want to smoothly transition between values instead of jumping
        # (as the headset typically gives one reading per second)
        self.fading_to = None

    def start_fade(self, new_level):
        if not self.last_response_level:
            self.last_response_level = new_level
        else:
            self.fading_to = new_level

    def end_fade(self):
        self.last_response_level = self.fading_to
        self.fading_to = None

    def render(self, model, params, frame):
        now = time.time()
        response_level = None
        # Update our measurements, if we have a new one
        if params.eeg and params.eeg != self.last_eeg and params.eeg.on:
            if self.fading_to:
                self.end_fade()
            # Prepend newest measurement and timestamp
            self.measurements[:0] = [getattr(params.eeg, self.respond_to)]
            self.timestamps[:0] = [now]
            self.last_eeg = params.eeg
            # Compute the parameter to send to our rendering function
            N = len(self.measurements)
            idx = 0
            while idx < N:
                dt = self.timestamps[0] - self.timestamps[idx]
                if dt > self.smooth_response_over_n_secs:
                    self.measurements = self.measurements[:(idx + 1)]
                    self.timestamps = self.timestamps[:(idx + 1)]
                    break
                idx += 1
            if len(self.measurements) > 1:
                self.start_fade(sum(self.measurements) * 1.0 / len(self.measurements))
            response_level = self.last_response_level
        elif self.fading_to:
            # We assume one reading per second, so a one-second fade
            fade_progress = now - self.timestamps[0]
            if fade_progress >= 1:
                self.end_fade()
                response_level = self.last_response_level
            else:
                response_level = (
                    fade_progress * self.fading_to +
                    (1 - fade_progress) * self.last_response_level)

        self.render_responsive(model, params, frame, response_level)

    def render_responsive(self, model, params, frame, response_level):
        raise NotImplementedError(
            "Implement render_responsive() in your HeadsetResponsiveEffectLayer subclass")


class RGBLayer(EffectLayer):
    """Simplest layer, draws a static RGB color cube."""

    def render(self, model, params, frame):
        for i, rgb in enumerate(frame):
            # Normalized XYZ in the range [0,1]
            x, y, z = model.edgeCenters[i]
            rgb[0] = x
            rgb[1] = y
            rgb[2] = z


class ResponsiveGreenHighRedLow(HeadsetResponsiveEffectLayer):
    """Colors everything green if the response metric is high, red if low.

    Interpolates in between.
    """

    def render_responsive(self, model, params, frame, response_level):
        for i, rgb in enumerate(frame):
            if response_level is None:
                mixAdd(rgb, 0, 0, 1)
            else:
                mixAdd(rgb, 1 - response_level, response_level, 0)


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

    def __init__(self, zoom = 0.6, color=(1,0,0)):
        self.zoom = zoom
        self.color = color
        self.time_const = -1.5

    def render(self, model, params, frame):
        # Noise spatial scale, in number of noise datapoints at the fundamental frequency
        # visible along the length of the sculpture. Larger numbers "zoom out".
        # For perlin noise, we have multiple octaves of detail, so staying zoomed in lets
        # us have a lot of detail from the higher octaves while still having gradual overall
        # changes from the lower-frequency noise.

        s = self.zoom # defaults to 0.6

        # Time-varying vertical offset. "Flow" upwards, slowly. To keep the parameters to
        # pnoise3() in a reasonable range where conversion to single-precision float within
        # the module won't be a problem, we need to wrap the coordinates at the point where
        # the noise function seamlessly tiles. By default, this is at 1024 units in the
        # coordinate space used by pnoise3().

        z0 = math.fmod(params.time * self.time_const, 1024.0)

        for i, rgb in enumerate(frame):
            # Normalized XYZ in the range [0,1]
            x, y, z = model.edgeCenters[i]

            # Perlin noise with some brightness scaling
            level = 1.2 * (0.35 + noise.pnoise3(x*s, y*s, z*s + z0, octaves=3))

            for w,v in enumerate(self.color):
                rgb[w] += v * level


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

class ImpulseLayer2(EffectLayer):
    class Impulse():
        def __init__(self, color, edge, motion = "Out"):
            self.color = color
            self.edge = edge
            self.previous_edge = None
            self.dead = False
            self.motion = "Out"

            self.loopChance = 0.1
            self.bounceChance = 0.2

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

            if random.random() < self.loopChance:
                if self.motion == 'Out' and height == 3:
                    self.motion = 'Loop'
                elif self.motion == 'In' and height == 4:
                    self.motion = 'Loop'
                elif self.motion == 'Loop' and height == 4:
                    self.motion = 'Out'
                elif self.motion == 'Loop' and height == 3:
                    self.motion = 'In'

            if self.motion == 'Loop':
                in_node, out_node = self._node_incoming_and_outgoing(model)
                to_edges = [e for e in model.edgeListForNodes[out_node] if e != self.edge]
                to_edges = [e for e in to_edges if model.addressMatchesAnyP(model.addressForEdge[e], ["*.*.*.*", "*.*.*.1.2", "*.*.*.2.1"])]
            elif self.motion == 'Out':
                to_edges = [e for e in to_edges if model.edgeHeight[e] > height]
            elif self.motion == 'In':
                to_edges = [e for e in to_edges if model.edgeHeight[e] < height]

            if to_edges:
                self._move_to_any_of(to_edges)
            else:
                if random.random() < self.bounceChance:
                  if self.motion == 'Out':
                      self.motion = 'In'
                      self.move(model, params)
                  elif self.motion == 'In':
                      self.motion = 'Out'
                      self.move(model, params)
                  else:
                      print "Broken"
                      self.dead = True
                else:
                  self.dead = True

        def render(self, model, params, frame):
            if self.dead:
                return
            for v,c in enumerate(self.color):
                frame[self.edge][v] += c

    def __init__(self, maximum_pulse_count = 40):
        self.pulses = [None] * maximum_pulse_count
        self.last_time = None

        # these are adjustable
        self.frequency = 0.05 # seconds
        self.spawnChance = 0.25
        self.maxColorSaturation = 0.25
        self.brightness = 0.95

    def _move_pulses(self, model, params):
        if not self.last_time:
            self.last_time = params.time
            return
        if params.time < self.last_time + self.frequency:
            return
        self._reap_pulses(model, params)
        self._spawn_pulses(model, params)

        self.last_time = params.time
        for pulse in self.pulses:
            if pulse:
                pulse.move(model, params)

    def _reap_pulses(self, model, params):
        for i, p in enumerate(self.pulses):
            if p and p.dead:
                self.pulses[i] = None

    def _spawn_pulses(self, model, params):
        if random.random() < self.spawnChance:
          for i, p in enumerate(self.pulses):
              if not p:
                  if self.maxColorSaturation:
                      hue = random.random()
                      saturation = random.random() * self.maxColorSaturation
                      value = self.brightness
                      color = colorsys.hsv_to_rgb(hue, saturation, value)
                  else: # optimization for saturation 0
                      color = (self.brightness,self.brightness,self.brightness)

                  self.pulses[i] = ImpulseLayer2.Impulse(color, random.choice(model.roots))
                  return self._spawn_pulses(model, params)

    def render(self, model, params, frame):
        self._move_pulses(model, params)
        for pulse in self.pulses:
            if pulse:
                pulse.render(model, params, frame)

class Bolt(object):
    """Represents a single lightning bolt in the LightningStormLayer effect."""

    PULSE_INTENSITY = 0.08
    PULSE_FREQUENCY = 10.
    FADE_TIME = 0.25
    SECONDARY_BRANCH_INTENSITY = 0.4

    def __init__(self, model, init_time):
        self.init_time = init_time
        self.pulse_time = random.uniform(.25, .35)
        self.color = [v/255.0 for v in [230, 230, 255]]  # Violet storm
        self.life_time = self.pulse_time + Bolt.FADE_TIME
        self.edges, self.intensities = self.choose_random_path(model)

    def choose_random_path(self, model):
        leader_intensity = (1.0 - Bolt.PULSE_INTENSITY)
        branch_intensity = leader_intensity * Bolt.SECONDARY_BRANCH_INTENSITY
        root = random.choice(model.roots)
        edges = [root]
        leader = root
        intensities = [leader_intensity]
        while model.outwardAdjacency[leader]:
            next_leader = random.choice(model.outwardAdjacency[leader])
            for edge in model.outwardAdjacency[leader]:
                edges.append(edge)
                if edge == next_leader:
                    # Main bolt branch fully bright
                    intensities.append(leader_intensity)
                else:
                    # Partially light clipped branches
                    intensities.append(branch_intensity)
            leader = next_leader
        return edges, intensities

    def update_frame(self, frame, current_time):
        dt = current_time - self.init_time

        if dt < self.pulse_time:  # Bolt fully lit and pulsing
            phase = math.cos(2 * math.pi * dt * Bolt.PULSE_FREQUENCY) 
            for i, edge in enumerate(self.edges):
                mixAdd(frame[edge], *numpy.multiply(self.color,
                    self.intensities[i] + phase * Bolt.PULSE_INTENSITY))
            pass
        else:  # Bolt fades out linearly
            fade = 1 - (dt - self.pulse_time) * 1.0 / Bolt.FADE_TIME
            for i, edge in enumerate(self.edges):
                mixAdd(frame[edge], *numpy.multiply(
                    self.color, fade * self.intensities[i]))


class LightningStormLayer(EffectLayer):
    """Simulate lightning storm."""

    def __init__(self, bolt_every=.25):
        # http://www.youtube.com/watch?v=RLWIBrweSU8
        self.bolts = []
        self.bolt_every = bolt_every
        self.last_time = None

    def render(self, model, params, frame):
        if not self.last_time:
            self.last_time = params.time

        self.bolts = [bolt for bolt in self.bolts
                      if bolt.init_time + bolt.life_time > params.time]

        # Bolts will strike as a poisson arrival process. That is, randomly,
        # but on average every bolt_every seconds. The memoryless nature of it
        # will create periods of calm as well as periods of constant lightning.
        if (params.time - self.last_time) / self.bolt_every > random.random():
            # Bolts are allowed to overlap, creates some interesting effects
            self.bolts.append(Bolt(model, params.time))

        self.last_time = params.time

        for bolt in self.bolts:
            bolt.update_frame(frame, params.time)

            
class WhiteOut(EffectLayer):
    """ Sets everything to white """
    def render(self, model, params, frame):
        for i, rgb in enumerate(frame):
            mixAdd( rgb, 1, 1, 1 )    
            

class GammaLayer(EffectLayer):
    """Apply a gamma correction to the brightness, to adjust for the eye's nonlinear sensitivity."""

    def __init__(self, gamma):
        self.gamma = gamma

    def render(self, model, params, frame):
        numpy.clip(frame, 0, 1, frame)
        numpy.power(frame, self.gamma, frame)


