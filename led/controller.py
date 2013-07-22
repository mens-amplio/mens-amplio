#!/usr/bin/env python

from model import Model
from effects import EffectParameters
from renderer import Renderer
import os
import socket
import time
import sys
import numpy
import math
import struct
   
class AnimationController(object):
    """Manages the main animation loop. Each EffectLayer from the 'layers' list is run in order to
       produce a final frame of LED data which we send to the OPC server. This class manages frame
       rate control, and handles the advancement of time in EffectParameters.
       """

    def __init__(self, model, renderer, params=None, server=None):
        self.opc = FastOPC(server)
        self.model = model
        self.renderer = renderer
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
        self.renderer.render(self.model, self.params, frame)
        return frame

    def frameToHardwareFormat(self, frame):
        """Convert a frame in our abstract floating-point format to the specific format used
           by the OPC server. Does not clip to the range [0,255], this is handled by FastOPC.

           Modifies 'frame' in-place.
           """
        numpy.multiply(frame, 255, frame)

    def drawFrame(self):
        """Render a frame and send it to the OPC server"""
        self.advanceTime()
        pixels = self.renderLayers()
        self.frameToHardwareFormat(pixels)
        self.opc.putPixels(0, pixels)

    def drawingLoop(self):
        """Render frames forever or until keyboard interrupt"""
        try:
            while True:
                self.drawFrame()
        except KeyboardInterrupt:
            pass
        
        
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
           'pixels' is clipped in-place. If any values are out of range, the array is modified.
           """

        numpy.clip(pixels, 0, 255, pixels)
        packedPixels = pixels.astype('B').tostring()
        header = struct.pack('>BBH',
            channel,
            0x00,  # Command
            len(packedPixels))
        self.socket.send(header + packedPixels)
