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
        self.zoom = zoom
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
