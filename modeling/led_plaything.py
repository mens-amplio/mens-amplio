#!/usr/bin/env python
#
# Experimental LED effects code for MensAmplio, implemented as an OPC client.
#
# Dependencies:
#     sudo pip install noise numpy
#

from __future__ import division
import sys
import time
import json
import random
import math
import os
import socket
import struct
import noise
import numpy


class Model(object):
    """A model of the physical sculpture. Holds information about the position and
       connectedness of the LEDs.

       In the animation code, LEDs are represented as zero-based indices which match the
       indices used by the OPC server.
       
       The model is initialized using a JSON object which contains 3D positions for each vertex,
       and a list of graph edges which represent the lit segments between these vertices.
       """

    def __init__(self, filename):
        # Raw graph data
        self.graphData = json.load(open(filename))

        # Edges: Array of node ID 2-tuples. Indices of this array match LED indices.
        self.edges = map(tuple, self._strDictToArray(self.graphData['edges']))

        # Number of LEDs = number of edges
        self.numLEDs = len(self.edges)

        # Raw Nodes: Array of 3-tuples with physical locations of each node.
        #   Indices are arbitrary, and only need to match the values in self.edges.
        self.rawNodes = map(tuple, self._strDictToArray(self.graphData['nodes']))

        # Axis-aligned bounding box, for understanding the extent of the coordinate space.
        #   The minimum and maximum are 3-vectors in the same coordinate space as self.nodes.
        self.minAABB = [ min(v[i] for v in self.rawNodes) for i in range(3) ]
        self.maxAABB = [ max(v[i] for v in self.rawNodes) for i in range(3) ]

        # Scaled Nodes: It's easier to work with coordinates in the range [0, 1], so scale them according
        #   to the AABB we discovered above.
        self.nodes = [[ (v[i] - self.minAABB[i]) / (self.maxAABB[i] - self.minAABB[i]) for i in range(3) ] for v in self.rawNodes]

        # Edge centers: Array of 3-tuples with the physical center of each edge.
        self.edgeCenters = self._calculateEdgeCenters()

        # Which edges are "roots" of the tree? We'll look for edges centered in the bottom tenth of the sculpture.
        self.roots = [ i for i, (x, y, z) in enumerate(self.edgeCenters) if z < 0.1 ] 

        # Edge distances: To handle propagating things "outward" vs. "inward", we look at the distance between an edge's
        #   center and the bottom-center of the whole sculpture. Going 'out of' the tree vs 'into' can be measured
        #   using this value.
        self.edgeDistances = self._calculateEdgeDistances()

        # Reverse mapping from nodes to list of edges which are connected to those nodes
        self.edgeListForNodes = self._calculateEdgeListForNodes()

        # Edge adjacency: Which edges are directly connected to each edge?
        self.edgeAdjacency = self._calculateEdgeAdjacency()

        # Outward adjacency: Which edges are adjacent and at a greater edgeDistance?
        self.outwardAdjacency = self._calculateOutwardAdjacency()

    def _calculateEdgeCenters(self):
        result = []
        for n1, n2 in self.edges:
            x0, y0, z0 = self.nodes[n1]
            x1, y1, z1 = self.nodes[n2]
            result.append(( (x0+x1)/2, (y0+y1)/2, (z0+z1)/2 ))
        return result

    def _calculateEdgeDistances(self):
        result = []
        for x, y, z in self.edgeCenters:

            # Distance relative to bottom-center, in normalized coordinates.
            dx = x - 0.5
            dy = y - 0.5
            dz = z

            result.append(math.sqrt(dx*dx + dy*dy + dz*dz))
        return result

    def _calculateEdgeListForNodes(self):
        result = [ [] for node in self.nodes ]
        for edge, (n1, n2) in enumerate(self.edges):
            result[n1].append(edge)
            result[n2].append(edge)
        return result

    def _calculateEdgeAdjacency(self):
        result = []
        for edge, (n1, n2) in enumerate(self.edges):

            # All edges connected to either endpoint
            adj = self.edgeListForNodes[n1] + self.edgeListForNodes[n2]

            # Remove self
            while edge in adj:
                adj.remove(edge)

            result.append(adj)
        return result

    def _calculateOutwardAdjacency(self):
        result = []
        for edge, adj in enumerate(self.edgeAdjacency):
            dist = self.edgeDistances[edge]
            result.append([ e for e in adj if self.edgeDistances[e] > dist ])
        return result

    def _strDictToArray(self, d):
        # The graph data JSON file uses string-keyed dictionaries where we'd really rathe
        # have arrays. Check the format of such a dict and return it converted to an array.
        
        result = []
        for i in range(len(d)):
            key = str(i)
            if key not in d:
                raise ValueError("Sequential JSON dictionary is missing key %r" % key)
            result.append(d[key])
        return result


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


class FastOPC(object):
    """High-performance Open Pixel Control client, using Numeric Python.
       By default, assumes the OPC server is running on localhost. This may be overridden
       with the OPC_SERVER environment variable, or the 'server' keyword argument.
       """

    def __init__(self, server=None):
        self.server = server or os.getenv('OPC_SERVER') or '127.0.0.1:7890'
        self.host, port = self.server.split(':')
        self.port = int(port)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))

    def putPixels(self, channel, pixels):
        """Send a list of 8-bit colors to the indicated channel. (OPC command 0x00).
           'Pixels' is an array of any shape, in RGB order. Pixels range from 0 to 255.
           They need not already be clipped to this range; that's taken care of here.
           """

        packedPixels = pixels.clip(0, 255).astype('B').tostring()
        header = struct.pack('>BBH',
            channel,
            0x00,  # Command
            len(packedPixels))
        self.socket.send(header + packedPixels)


class AnimationController(object):
    """Manages the main animation loop. Each EffectLayer from the 'layers' list is run in order to
       produce a final frame of LED data which we send to the OPC server. This class manages frame
       rate control, and handles the advancement of time in EffectParameters.
       """

    def __init__(self, model, layers=None, params=None, server=None):
        self.opc = FastOPC(server)
        self.model = model
        self.layers = layers or []
        self.params = params or EffectParameters()

        self._fpsFrames = 0
        self._fpsTime = 0
        self._fpsLogPeriod = 0.5    # How often to log frame rate

    def advanceTime(self):
        """Update the timestep in EffectParameters.

           This is where we enforce our target frame rate, by sleeping until the minimum amount
           of time has elapsed since the previous frame. We try to synchronize our actual frame
           rate with the target frame rate in a slightly loose way which allows some jitter in
           our clock, but which keeps the frame rate centered around our ideal rate if we can keep up.

           This is also where we log the actual frame rate to the console periodically, so we can
           tell how well we're doing.
           """

        now = time.time()
        dt = now - self.params.time
        dtIdeal = 1.0 / self.params.targetFrameRate

        if dt > dtIdeal * 2:
            # Big jump forward. This may mean we're just starting out, or maybe our animation is
            # skipping badly. Jump immediately to the current time and don't look back.

            self.params.time = now

        else:
            # We're approximately keeping up with our ideal frame rate. Advance our animation
            # clock by the ideal amount, and insert delays where necessary so we line up the
            # animation clock with the real-time clock.

            self.params.time += dtIdeal
            if dt < dtIdeal:
                time.sleep(dtIdeal - dt)

        # Log frame rate

        self._fpsFrames += 1
        if now > self._fpsTime + self._fpsLogPeriod:
            fps = self._fpsFrames / (now - self._fpsTime)
            self._fpsTime = now
            self._fpsFrames = 0
            sys.stderr.write("%7.2f FPS\n" % fps)

    def renderLayers(self):
        """Generate a complete frame of LED data by rendering each layer."""

        frame = numpy.zeros((self.model.numLEDs, 3))
        for layer in self.layers:
            layer.render(self.model, self.params, frame)
        return frame

    def frameToHardwareFormat(self, frame):
        """Convert a frame in our abstract floating-point format to the specific format used
           by the OPC server. Does not clip to the range [0,255], this is handled by FastOPC.
           """
        return frame * 255.0

    def drawFrame(self):
        """Render a frame and send it to the OPC server"""
        self.advanceTime()
        pixels = self.frameToHardwareFormat(self.renderLayers())
        self.opc.putPixels(0, pixels)

    def drawingLoop(self):
        """Render frames forever or until keyboard interrupt"""
        try:
            while True:
                self.drawFrame()
        except KeyboardInterrupt:
            pass


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


class GammaLayer(EffectLayer):
    """Apply a gamma correction to the brightness, to adjust for the eye's nonlinear sensitivity."""

    def __init__(self, gamma):
        self.gamma = gamma

    def render(self, model, params, frame):
        for rgb in frame:
            for i in range(3):
                rgb[i] = math.pow(max(0, rgb[i]), self.gamma)


if __name__ == '__main__':
    model = Model('graph.data.json')
    controller = AnimationController(model, [
        PlasmaLayer(),
        #ImpulsesLayer(),
        WavesLayer(),
        GammaLayer(2.2),
        ])
    controller.drawingLoop()
