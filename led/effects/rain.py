import itertools
import math
import numpy
import random
from base import EffectLayer, HeadsetResponsiveEffectLayer

class RainLayer(HeadsetResponsiveEffectLayer):
    """
    Raindrop-ish points of light at random places on the model.
    """
    class Raindrop:
        def __init__(self, model, edge, duration=1, color=(1, 1, 1)):
            self.first = edge 
            self.second = model.edgeAdjacency[edge] 
            self.third = [ model.edgeAdjacency[e] for e in self.second ]
            self.third = list(itertools.chain(*self.third))
            self.third = list(set( [e for e in self.third if e is not self.first and e not in self.second] ))
            
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
                if len(self.second) > 0:
                    frame[self.second] += c2
                if len(self.third) > 0:
                    frame[self.third] += c3
            
            
    def __init__(self, respond_to = 'attention', dropEvery=5, inverse=True):
        """ Drop onset times are stochastic but average to one every dropEvery seconds
        when the headset is off or reading 0
        """
        super(RainLayer,self).__init__(respond_to, smooth_response_over_n_secs=1, inverse=inverse)
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
