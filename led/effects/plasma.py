import math
import numpy
import cplasma
from base import EffectLayer, HeadsetResponsiveEffectLayer


class PlasmaLayer(EffectLayer):
    """A plasma cloud layer, implemented with smoothed noise.

       If 'color' is None, this modulates the brightness of the framebuffer's
       existing contents. Otherwise, it's a color 3-tuple.
       """

    def __init__(self, color=None, zoom=0.6):
        # Noise spatial scale, in number of noise datapoints at the fundamental frequency
        # visible along the length of the sculpture. Larger numbers "zoom out".
        # For perlin noise, we have multiple octaves of detail, so staying zoomed in lets
        # us have a lot of detail from the higher octaves while still having gradual overall
        # changes from the lower-frequency noise. 
        self.zoom = zoom
        
        # Time-varying vertical offset. "Flow" upwards, slowly. To keep the parameters to
        # pnoise3() in a reasonable range where conversion to single-precision float within
        # the module won't be a problem, we need to wrap the coordinates at the point where
        # the noise function seamlessly tiles. By default, this is at 1024 units in the
        # coordinate space used by pnoise3().
        self.octaves = 3
        
        self.color = None if color is None else numpy.array(color)
        self.time_const = -1.5
        self.modelCache = None

    def render(self, model, params, frame):
        if model is not self.modelCache:
            self.modelCache = model
        if self.color is not None:
            cplasma.render(self.zoom,
                    self.modelCache.edgeCenters[:,0],
                    self.modelCache.edgeCenters[:,1],
                    self.modelCache.edgeCenters[:,2],
                    params.time, self.time_const, self.octaves, frame, self.color)
        else:
            cplasma.render(self.zoom,
                    self.modelCache.edgeCenters[:,0],
                    self.modelCache.edgeCenters[:,1],
                    self.modelCache.edgeCenters[:,2],
                    params.time, self.time_const, self.octaves, frame)

class ZoomingPlasmaLayer(HeadsetResponsiveEffectLayer):
    def __init__(self, color = None, respond_to = 'meditation'):
        super(ZoomingPlasmaLayer,self).__init__(respond_to)
        self.plasma = PlasmaLayer(color, 0.6)

    def render_responsive(self, model, params, frame, response_level):
        if response_level:
            self.plasma.zoom = 2.1 - response_level * 2
        self.plasma.render(model, params, frame)
