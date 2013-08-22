import math
import numpy
from base import EffectLayer, HeadsetResponsiveEffectLayer


class WavesLayer(HeadsetResponsiveEffectLayer):
    """Occasional wavefronts of light which propagate outward from the base of the tree"""

    width = 0.4
    minimum_period = -1 # anything less than pi/2 is just as-fast-as-possible

    def __init__(self, color=(0.5, 0.5, 1), period=5.0, speed=1.5, respond_to='meditation', smooth_response_over_n_secs=0, inverse=False):
        super(WavesLayer,self).__init__(respond_to, smooth_response_over_n_secs, inverse=inverse)
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
