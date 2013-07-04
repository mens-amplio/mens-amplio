#!/usr/bin/env python
#
# Experimental LED effects code for MensAmplio, implemented as an OPC client.
#

from __future__ import division
import sys, time, json, opc_client


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

    def _calculateEdgeCenters(self):
        result = []
        for n1, n2 in self.edges:
            x0, y0, z0 = self.nodes[n1]
            x1, y1, z1 = self.nodes[n2]
            result.append(( (x0+x1)/2, (y0+y1)/2, (z0+z1)/2 ))
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
    targetFrameRate = 60.0     # XXX: Want to go higher, but gl_server can't keep up!


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


class AnimationController(object):
    """Manages the main animation loop. Each EffectLayer from the 'layers' list is run in order to
       produce a final frame of LED data which we send to the OPC server. This class manages frame
       rate control, and handles the advancement of time in EffectParameters.
       """

    def __init__(self, model, layers=None, params=None, server='127.0.0.1:7890'):
        self.socket = opc_client.get_socket(server)
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

        frame = [ [0,0,0] for i in range(self.model.numLEDs) ]
        for layer in self.layers:
            layer.render(self.model, self.params, frame)
        return frame

    def frameToHardwareFormat(self, frame):
        """Convert a frame in our abstract floating-point format to the specific format used
           by the OPC server.
           """
        return [[ min(255, max(0, int(x * 255.0 + 0.5))) for x in pixel ] for pixel in frame ]

    def drawFrame(self):
        """Render a frame and send it to the OPC server"""
        self.advanceTime()
        pixels = self.frameToHardwareFormat(self.renderLayers())
        opc_client.put_pixels(self.socket, 0, pixels)

    def drawingLoop(self):
        """Render frames forever or until keyboard interrupt"""
        try:
            while True:
                self.drawFrame()
        except KeyboardInterrupt:
            pass


class RGBLayer(object):
    """Simplest layer, draws a static RGB color cube."""

    def render(self, model, params, frame):
        for i, rgb in enumerate(frame):
            # Normalized XYZ in the range [0,1]
            xyz = model.edgeCenters[i]
            rgb[0] = xyz[0]
            rgb[1] = xyz[1]
            rgb[2] = xyz[2]


model = Model('graph.data.json')
controller = AnimationController(model)
controller.layers.append(RGBLayer())
controller.drawingLoop()
