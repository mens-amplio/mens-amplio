import numpy
from base import EffectLayer, HeadsetResponsiveEffectLayer

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
