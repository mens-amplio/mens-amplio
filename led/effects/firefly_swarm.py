import math
import random
import numpy
from base import EffectLayer, HeadsetResponsiveEffectLayer

class FireflySwarmLayer(HeadsetResponsiveEffectLayer):
    """
    Each tree is a firefly. When one blinks, it pulls its neighbors closer or
    further from blinking themselves, bringing the group into and out of sync.
    
    For a full explanation of how this works, see:
    Synchronization of Pulse-Coupled Biological Oscillators
    Renato E. Mirollo; Steven H. Strogatz
    SIAM Journal on Applied Mathematics, Vol. 50, No. 6. (Dec., 1990), pp. 1645-1662
    
    This has a bug - it can miss blinks if update isn't called frequently enough -
    but it's only apparent at unacceptably low framerates and no time to fix now.
    """
    
    class Firefly:
        """
        A single firefly. Its activation level increases monotonically in range [0,1] as
        a function of time. When its activation reaches 1, it initiates a blink and drops
        back to 0.
        """
        
        CYCLE_TIME = 3 # seconds
        NUDGE = 0.2 # how much to nudge it toward firing after its neighbor fires
        EXP = 2.0 # exponent for phase->activation function, chosen somewhat arbitrarily
        
        def __init__(self, tree, color=(1,1,1)):
            self.offset = random.random() * self.CYCLE_TIME
            self.tree = tree
            self.color = color
            self.blinktime = 0
            
        def nudge(self, params, response_level):
            # Bump this firefly forward or backward in its cycle, closer to or further from
            # its next blink, depending on response level
            p = self.phi(params)
            a = self.activation(p)
            
            response = response_level - 0.5
            nudge_size = response*self.NUDGE
            # if we always "desync" at same rate, it won't actually desync
            if response < 0:
                nudge_size *= (random.random()+0.5)
            a2 = max(min(a + nudge_size, 1), 0)
            # find the phase parameter corresponding to that activation level
            p2 = self.activation_to_phi(a2)
            # adjust time offset to bring us to that phase
            self.offset += (p2 - p) * self.CYCLE_TIME

            # TMI
            debug=False
            if self.tree == 1 and debug:
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
            
        def render(self, model, params, frame):
            """
            Draw pulses with sinusoidal ramp-up/ramp-down
            """
            dt = params.time - self.blinktime
            dur = float(self.CYCLE_TIME)/2
            if dt < dur:
                scale = math.sin(math.pi * dt/dur)
                if self.color is None:
                    frame[model.edgeTree==self.tree] *= scale
                else:
                    frame[model.edgeTree==self.tree] += self.color * scale
            else:
                if self.color is None:
                    frame[model.edgeTree==self.tree] = 0
                    
    def __init__(self, respond_to='meditation', color=None):
        super(FireflySwarmLayer, self).__init__(respond_to)
        self.cyclers = []
        self.cachedModel = None
        if color:
            self.color = numpy.array(color, dtype='f')
        else:
            self.color = None
        
    def render_responsive(self, model, params, frame, response_level):
        if model != self.cachedModel:
            self.trees = len(model.roots)
            self.cyclers = [ FireflySwarmLayer.Firefly(e, color=self.color) for e in range(self.trees) ]
            self.cachedModel = model
        
        blink = self.cyclers[0].update(params)
        self.cyclers[0].render(model, params, frame)
        for c in self.cyclers[1:]:
            if blink and response_level:
                c.nudge(params, response_level)
            else:
                c.update(params)
            c.render(model, params, frame)
            
