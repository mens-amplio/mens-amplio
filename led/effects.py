#!/usr/bin/env python

import math
import random
import noise
import numpy
import colorsys
import time
import itertools


class EffectParameters(object):
    """Inputs to the individual effect layers. Includes basics like the timestamp of the frame we're
       generating, as well as parameters that may be used to control individual layers in real-time.
       """

    time = 0
    targetFrameRate = 59.0     # XXX: Want to go higher, but gl_server can't keep up!
    eeg = None


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
        frame[:] = model.edgeCenters[:]


class ResponsiveGreenHighRedLow(HeadsetResponsiveEffectLayer):
    """Colors everything green if the response metric is high, red if low.

    Interpolates in between.
    """

    def render_responsive(self, model, params, frame, response_level):
        if response_level is None:
            # No signal (blue)
            frame[:,2] += 1
        else:
            frame[:,0] += 1 - response_level
            frame[:,1] += response_level

    
class ColorDrifterLayer(EffectLayer):
    """ 
    Interpolates between colors in a color list. Adds those values 
    to the values already in the frame. Interpolation is done in HSV space but
    input and output colors are RGB.
    """
    def __init__(self, colors, switchTime=None):
        l = len(colors)
        if l == 0:
            raise Exception("Can't initialize ColorDrifterLayer with empty color list")
        if l > 1 and time is None:
            raise Exception("ColorDrifterLayer needs a switch time")
        self.colors = numpy.array([ colorsys.rgb_to_hsv(*c) for c in colors ])
        self.active = 0
        self.switchTime = switchTime
        self.lastSwitch = time.time()
        
    def _nextIndex(self, index):
        return (index+1) % len(self.colors)
        
    def _updateColor(self, params):
        """ Subclasses should remember to call this at the start of their render methods """
        if len(self.colors) > 1:
            p = self.proportionComplete(params)
            if p >= 1:
                self.active = self._nextIndex(self.active)
                self.lastSwitch = params.time
        
    def proportionComplete(self, params):
        return float(params.time - self.lastSwitch)/self.switchTime
        
    def getColor(self):
        return self.colors[self.active]
        
    def getNextColor(self):
        return self.colors[self._nextIndex(self.active)]
        
    def getNextNextColor(self):
        return self.colors[self._nextIndex(self.active+1)]
        
    @staticmethod
    def interpolate(c1, c2, p):
        return c1*(1-p) + c2*p
        
    @staticmethod
    def getRGB(c):
        return numpy.array(colorsys.hsv_to_rgb(*c))
            
    def render(self, model, params, frame):
        raise NotImplementedError("Implement render in ColorDrifterLayer subclass")
        
        
class HomogenousColorDrifterLayer(ColorDrifterLayer):    
    """ Color drift is homogenous across the whole brain """
    def render(self, model, params, frame):
        self._updateColor(params)
        p = self.proportionComplete(params)
        c = ColorDrifterLayer.interpolate(self.getColor(), self.getNextColor(), p)
        numpy.add(frame, ColorDrifterLayer.getRGB(c), frame) 
        

class TreeColorDrifterLayer(ColorDrifterLayer):
    """ Each tree is a bit out of phase, so they drift through the colors at different times """
    def __init__(self, colors, switchTime=None):
        super(TreeColorDrifterLayer,self).__init__(colors, switchTime)
        self.roots = None
        self.cachedModel = None
        
    def render(self, model, params, frame):
        self._updateColor(params)
        if self.roots is None or model != self.cachedModel:
            self.cachedModel = model
            self.roots = range(len(model.roots))
            random.shuffle(self.roots)
        p = self.proportionComplete(params)
        cnt = len(self.roots)
        for root in self.roots:
            p_root = p + float(root)/cnt
            if p_root < 1:
                color = ColorDrifterLayer.interpolate(self.getColor(), self.getNextColor(), p_root)
            elif p_root < 2:
                color = ColorDrifterLayer.interpolate(self.getNextColor(), self.getNextNextColor(), p_root-1)
            else:
                raise Exception("TreeColorDrifterLayer is broken")
            frame[model.edgeTree==root] += ColorDrifterLayer.getRGB(color)
            
        
class MultiplierLayer(EffectLayer):
    """ Renders two layers in temporary frames, then adds the product of those frames
    to the frame passed into its render method
    """
    def __init__(self, layer1, layer2):
        self.layer1 = layer1
        self.layer2 = layer2        
        
    def render(self, model, params, frame):
        temp1 = numpy.zeros(frame.shape)
        temp2 = numpy.zeros(frame.shape)
        self.layer1.render(model, params, temp1)
        self.layer2.render(model, params, temp2)
        numpy.multiply(temp1, temp2, temp1)
        numpy.add(frame, temp1, frame)


class BlinkyLayer(EffectLayer):
    """Test our timing accuracy: Just blink everything on and off every other frame."""

    on = False

    def render(self, model, params, frame):
        self.on = not self.on
        frame[:] += self.on


class PlasmaLayer(EffectLayer):
    """A plasma cloud layer, implemented with smoothed noise.

       If 'color' is None, this modulates the brightness of the framebuffer's
       existing contents. Otherwise, it's a color 3-tuple.
       """

    def __init__(self, color=None, zoom=0.6):
        self.zoom = zoom
        self.octaves = 3
        self.color = None if color is None else numpy.array(color)
        self.time_const = -1.5
        self.modelCache = None
        self.ufunc = numpy.frompyfunc(noise.pnoise3, 4, 1)

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

        # Cached values based on the current model
        if model is not self.modelCache:
            self.modelCache = model
            self.scaledX = s * model.edgeCenters[:,0]
            self.scaledY = s * model.edgeCenters[:,1]
            self.scaledZ = s * model.edgeCenters[:,2]

        # Compute noise values at the center of each edge
        noise = self.ufunc(self.scaledX, self.scaledY, self.scaledZ + z0,
            self.octaves).astype(frame.dtype)

        # Brightness scaling
        numpy.add(noise, 0.35, noise)
        numpy.multiply(noise, 1.2, noise)

        if self.color is None:
            # Multiply by framebuffer contents
            numpy.multiply(frame, noise.reshape(-1, 1), frame)
        else:
            # Multiply by color, accumulate into current frame
            numpy.add(frame, self.color * noise.reshape(-1, 1), frame)


class WavesLayer(HeadsetResponsiveEffectLayer):
    """Occasional wavefronts of light which propagate outward from the base of the tree"""

    width = 0.4
    minimum_period = -1 # anything less than pi/2 is just as-fast-as-possible

    def __init__(self, color=(0.5, 0.5, 1), period=15.0, speed=1.5, respond_to='meditation', smooth_response_over_n_secs=5):
        super(WavesLayer,self).__init__(respond_to, smooth_response_over_n_secs)
        self.wave_started_at = 0
        self.drawing_wave = False
        self.color = numpy.array(color)
        self.speed = speed
        self.period = period
        self.maximum_period = period

    def render_responsive(self, model, params, frame, response_level):
        # Center of the expanding wavefront
        center = (params.time - self.wave_started_at) * self.speed

        # Only do the rest of the calculation if the wavefront is at all visible.
        if center < math.pi/2:
            self.drawing_wave = True
            # Calculate each pixel's position within the pulse, in radians
            a = model.edgeDistances - center
            numpy.abs(a, a)
            numpy.multiply(a, math.pi/2 / self.width, a)

            # Clamp against the edge of the pulse
            numpy.minimum(a, math.pi/2, a)

            # Pulse shape
            numpy.cos(a, a)

            # Colorize
            numpy.add(frame, a.reshape(-1,1) * self.color, frame)
        elif self.drawing_wave and response_level:
            self.drawing_wave = False
            self.period = self.minimum_period + (self.maximum_period - self.minimum_period) * (1.0 - response_level)
        elif center > self.period:
            self.wave_started_at = params.time
            
            
class ThrobbingBrainStemLayer(WavesLayer):
    """ Child of WavesLayer with different speed parameters whose wave only goes a
    certain number of levels up the tree (and is linearly attenuated as it moves up).
    Currently doesn't add any new headset-responsivity, but later we could potentially
    make it change the number of levels or the attenuation.
    """
    def __init__(self, levels=6, period=1, speed=2.5, color=(0.5, 0, 1), respond_to='attention'):
        super(ThrobbingBrainStemLayer, self).__init__(color=color, period=period, speed=speed, respond_to=respond_to)
        self.levels = levels
        self.modelCache = None
        self.scaleFactors = None
        self.start = None
        
    def render(self, model, params, frame):
        if not self.start:
            self.start = params.time
        if model is not self.modelCache:
            self.modelCache = model
            normedHeights = 1 - (model.edgeHeight / float(self.levels))
            normedHeights[normedHeights < 0] = 0
            self.scaleFactors = normedHeights.repeat(3).reshape(model.numLEDs,3)
        
        temp = numpy.zeros(frame.shape)
        super(ThrobbingBrainStemLayer, self).render(model, params, temp)
        frame += temp * self.scaleFactors
        

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
                frame[self.positions[i]] += br

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


class SnowstormLayer(EffectLayer):
    def render(self, model, params, frame):
        numpy.add(frame, numpy.random.rand(model.numLEDs, 1), frame)


class TechnicolorSnowstormLayer(EffectLayer):
    def render(self, model, params, frame):
        numpy.add(frame, numpy.random.rand(model.numLEDs, 3), frame)


class ImpulseLayer2(HeadsetResponsiveEffectLayer):
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
                if self.motion == 'Out' and height == 4:
                    self.motion = 'Loop'
                elif self.motion == 'In' and height == 5:
                    self.motion = 'Loop'
                elif self.motion == 'Loop' and height == 5:
                    self.motion = 'Out'
                elif self.motion == 'Loop' and height == 4:
                    self.motion = 'In'

            if self.motion == 'Loop':
                in_node, out_node = self._node_incoming_and_outgoing(model)
                to_edges = [e for e in model.edgeListForNodes[out_node] if e != self.edge]
                to_edges = [e for e in to_edges if model.addressMatchesAnyP(model.addressForEdge[e], ["*.*.*.*.*", "*.*.*.*.1.2", "*.*.*.*.2.1"])]
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

    def __init__(self, respond_to = 'attention', maximum_pulse_count = 40):
        super(ImpulseLayer2,self).__init__(respond_to)
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

    def render_responsive(self, model, params, frame, response_level):
        if response_level != None:
            self.spawnChance = response_level * 0.95 # gets much more intense
            self.maxColorSaturation = response_level * 0.50 # gets a little more colory

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
        self.color = numpy.array([v/255.0 for v in [230, 230, 255]])  # Violet storm
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
        return numpy.array(edges), numpy.array(intensities)

    def update_frame(self, frame, current_time):
        dt = current_time - self.init_time

        if dt < self.pulse_time:  # Bolt fully lit and pulsing
            phase = math.cos(2 * math.pi * dt * Bolt.PULSE_FREQUENCY) 
            intensities = self.intensities + (phase * Bolt.PULSE_INTENSITY)
            c = self.color.reshape(1, -1) * intensities.reshape(-1, 1)
            for i, edge in enumerate(self.edges):
                frame[edge] += c[i]

        else:  # Bolt fades out linearly
            fade = 1 - (dt - self.pulse_time) * 1.0 / Bolt.FADE_TIME
            intensities = self.intensities * fade
            c = self.color.reshape(1, -1) * intensities.reshape(-1, 1)
            for i, edge in enumerate(self.edges):
                frame[edge] += c[i]


class LightningStormLayer(HeadsetResponsiveEffectLayer):
    """Simulate lightning storm."""

    def __init__(self, bolt_every=.25, respond_to = 'attention'):
        # http://www.youtube.com/watch?v=RLWIBrweSU8
        super(LightningStormLayer,self).__init__(respond_to)
        self.bolts = []
        self.max_bolt_every = bolt_every * 2.0
        self.bolt_every = bolt_every
        self.last_time = None

    def render_responsive(self, model, params, frame, response_level):
        if response_level != None:
            self.bolt_every = response_level * self.max_bolt_every

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
            
            
class FireflySwarm(EffectLayer):
    """
    A group of phase-coupled fireflies. When one blinks, it pulls its neighbors closer to
    blinking themselves, which will eventually bring the whole group into sync.
    
    For a full explanation of how this works, see:
    Synchronization of Pulse-Coupled Biological Oscillators
    Renato E. Mirollo; Steven H. Strogatz
    SIAM Journal on Applied Mathematics, Vol. 50, No. 6. (Dec., 1990), pp. 1645-1662
    
    This has a subtle bug somewhere where occasionally some edges skip a blink.
    I'm putting off fixing it until we decide if we actually want to use this.
    """
    
    class Firefly:
        """
        A single firefly. Its activation level increases monotonically in range [0,1] as
        a function of time. When its activation reaches 1, it initiates a blink and drops
        back to 0.
        """
        
        CYCLE_TIME = 1.5 # seconds
        NUDGE = 0.15 # how much to nudge it toward firing after its neighbor fires
        EXP = 2.0 # exponent for phase->activation function, chosen somewhat arbitrarily
        
        def __init__(self, edge):
            self.offset = random.random() * self.CYCLE_TIME
            self.edge = edge
            self.color = (1,1,1)
            self.blinktime = 0
            
        def nudge(self, params):
            """ Bump this firefly forward in its cycle, closer to its next blink """
            p = self.phi(params)
            a = self.activation(p)
            
            # if it isn't already blinking...
            if a < 1.0:
                # new activation level, closer to (but not exceeding) blink threshold
                a2 = min(a + self.NUDGE, 1)
                # find the phase parameter corresponding to that activation level
                p2 = self.activation_to_phi(a2)
                # adjust time offset to bring us to that phase
                self.offset += max(p2 - p, 0) * self.CYCLE_TIME

                # TMI
                debug=False
                if self.edge == 66 and debug:
                    print self.offset,
                    print p,
                    print p2,
                    print self.phi(params),
                    print self.activation(self.phi(params))

                # now that we've changed its state, we need to re-update it
                self.update(params)
        
        def phi(self, params):
            """ 
            Converts current time + time offset into phi (oscillatory phase parameter in range [0,1]) 
            """
            return ((params.time + self.offset) % self.CYCLE_TIME)/self.CYCLE_TIME + 0.01
        
        def activation(self, phi):
            """ 
            Converts phi into activation level. Activation function must be concave in order for
            this algorithm to work.
            """
            return pow(phi, 1/self.EXP)
            
        def activation_to_phi(self, f):
            """ Convert from an activation level back to a phi value. """
            return pow(f, self.EXP)
            
        def update(self, params):
            """ 
            Note the time when activation crosses threshold, so we can use it as the onset time for rendering the
            actual blink. Return whether firefly has just crossed the threshold or not so we know whether to nudge its
            neighbors.
            """
            p = self.phi(params)
            blink = self.activation(p) >= 1
            if blink:
                self.blinktime = params.time
            return blink
            
        def render(self, params, frame):
            """
            Draw pulses with sinusoidal ramp-up/ramp-down
            """
            dt = params.time - self.blinktime
            dur = float(self.CYCLE_TIME)/2
            if dt < dur:
                scale = math.sin(math.pi * dt/dur)
                for v,c in enumerate(self.color):
                    frame[self.edge][v] += c * scale
    
    def __init__(self, model):
        self.cyclers = [ FireflySwarm.Firefly(e) for e in range(model.numLEDs) ]
        
    def render(self, model, params, frame):
        for c in self.cyclers:
            if c.update(params):
                # the first root node nudges all the other ones - otherwise the trees
                # won't sync with each other
                if c.edge == model.roots[0]:
                    for m in model.roots[1:]:
                        self.cyclers[m].nudge(params)
                # each firefly affects its local neighbors only. having nudges propagate
                # outward only is both prettier (synchronization starts at the brainstem
                # and moves up) and faster.
                for adj in model.outwardAdjacency[c.edge]:
                    self.cyclers[adj].nudge(params)
        for c in self.cyclers:
            c.render(params, frame)
            

class RainLayer(HeadsetResponsiveEffectLayer):
    """
    Raindrop-ish points of light at random places on the model.
    """
    class Raindrop:
        def __init__(self, model, edge, duration=1, color=(.75, .75, 1)):
            self.first = edge 
            self.second = model.edgeAdjacency[edge] 
            self.third = [ model.edgeAdjacency[e] for e in self.second ]
            self.third = list(itertools.chain(*self.third))
            self.third = set( [e for e in self.third if e is not self.first and e not in self.second] )
            
            self.done = False
            self.start = None
            self.color = numpy.array(color)
            self.duration = duration
            # lag between when an edge lights up and its adjacent edges do
            self.delay = float(duration)/12
            
        def get_color(self, params, delay=0, attenuate=0):
            dt = params.time - self.start - delay
            if dt > 0 and dt < self.duration:
                return self.color * math.sin(math.pi * 2 * dt / self.duration) * (1.0-attenuate)
            else:
                return numpy.array([0,0,0])
            
        def render(self, model, params, frame):
            if not self.start:
                self.start = params.time
            if params.time - self.start > self.duration + self.delay:
                self.done = True
                
            if not self.done:
                # drop propagates out from starting edge, fading as it goes
                c1 = self.get_color(params)
                c2 = self.get_color(params, self.delay, 0.6)
                c3 = self.get_color(params, self.delay*2, 0.8)
                frame[self.first] = c1
                for i in self.second:
                    frame[i] += c2
                for i in self.third:
                    frame[i] += c3
            
            
    def __init__(self, model, respond_to = 'attention', dropEvery=5):
        """ Drop onset times are stochastic but average to one every dropEvery seconds
        when the headset is off or reading 0
        """
        super(RainLayer,self).__init__(respond_to, 1)
        self.dropEvery = dropEvery
        self.minDropEvery = dropEvery / 10.0 # how fast it'll go if headset is reading 1
        self.drops = []
        self.lastTime = None
        
    def getResponsiveInterval(self, response_level):
        if response_level is None:
            return self.dropEvery
        else:
            return self.minDropEvery + (1.0-response_level)*(self.dropEvery-self.minDropEvery)
        
    def render_responsive(self, model, params, frame, response_level):
        if not self.lastTime:
            self.lastTime = params.time
        self.drops = [ d for d in self.drops if not d.done ]
        if (params.time - self.lastTime) / self.getResponsiveInterval(response_level) > random.random():
            self.drops.append( RainLayer.Raindrop(model, random.randint(0, model.numLEDs-1)) )
            self.lastTime = params.time
        for d in self.drops:
            d.render(model, params, frame)

            
class WhiteOutLayer(EffectLayer):
    """ Sets everything to white """
    def render(self, model, params, frame):
        frame += numpy.ones(frame.shape)
            

class GammaLayer(EffectLayer):
    """Apply a gamma correction to the brightness, to adjust for the eye's nonlinear sensitivity."""

    def __init__(self, gamma):
        # Build a lookup table
        self.lutX = numpy.arange(0, 1, 0.01)
        self.lutY = numpy.power(self.lutX, gamma)

    def render(self, model, params, frame):
        frame[:] = numpy.interp(frame.reshape(-1), self.lutX, self.lutY).reshape(frame.shape)
