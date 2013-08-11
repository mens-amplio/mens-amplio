import math
from base import EffectLayer, HeadsetResponsiveEffectLayer

class FireflySwarmLayer(EffectLayer):
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
            
