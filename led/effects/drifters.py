import colorsys
import matplotlib.colors
import numpy
import random
import scipy.interpolate
import time
from base import EffectLayer, HeadsetResponsiveEffectLayer


class ColorDrifterLayer(EffectLayer):
    """ 
    Interpolates between colors in a color list. Adds those values 
    to the values already in the frame. Interpolation is done in HSV space but
    input and output colors are RGB.
    """
    
    # Number of fade steps to precalculate. Could go
    # higher at additional memory cost, but assuming 8-bit output this is probably OK.
    fadeSteps = 255
    
    def __init__(self, colors, switchTime=None):
        l = len(colors)
        if l == 0:
            raise Exception("Can't initialize ColorDrifterLayer with empty color list")
        if l > 1 and time is None:
            raise Exception("ColorDrifterLayer needs a switch time")
        self.colors = numpy.array([ colorsys.rgb_to_hsv(*c) for c in colors ])
        self.active = 0
        self.switchTime = switchTime
        self.lastSwitch = time.time()
        
        # first axis: transition index (0: colors[0]->colors[1], etc)
        # second axis: step [0:254]
        # third axis: r/g/b
        self.values = self._precalculate()
        
    def _precalculate(self):
        # Cache all the intermediate color values, pre-converted to RGB. 
        colorCnt = len(self.colors)
        rgbIndices = numpy.array(range(3))
        values = numpy.zeros([colorCnt, 3, self.fadeSteps])
        
        indices = rgbIndices.repeat(self.fadeSteps)
        steps = numpy.arange(0, 1, 1.0/self.fadeSteps)
        steps = numpy.tile(steps, 3)
        # interpolate between each pair of adjacent colors
        for i in range(colorCnt):
            endpoints = self.colors[[i, self.nextIndex(i)]]
            # object that knows how to fade between endpoints along all RGB indices
            interpolater = scipy.interpolate.RectBivariateSpline([0, 1], rgbIndices, endpoints, kx=1, ky=1)
            # evaluate to get actual values at each step
            values[i] = interpolater.ev(steps, indices).reshape(3, -1)
            
        # move r/g/b dimension to final axis for easier indexing later
        values = values.swapaxes(1,2) 
        
        # convert to RGB
        return matplotlib.colors.hsv_to_rgb(values)
        
    def _updateColor(self, params):
        # Subclasses should remember to call this at the start of their render methods
        if len(self.colors) > 1:
            p = self.proportionComplete(params)
            if p >= 1:
                self.active = self.nextIndex(self.active)
                self.lastSwitch = params.time
        
    def getFadeColor(self, proportion):
        # proportion must be in [0,2) range. Fade is either between active and next
        # colors (if it's <1) or next and next-next colors (if it's <2)
        if proportion < 1:
            index = self.active
        elif proportion < 2: 
            index = self.nextIndex(self.active)
            proportion -= 1
        else:
            raise Exception("Bad fade proportion in ColorDrifterLayer")
        step = int(proportion*(self.fadeSteps-1) + 0.5)
        return self.values[index][step]
        
    def nextIndex(self, index):
        return (index+1) % len(self.colors)
        
    def proportionComplete(self, params):
        return float(params.time - self.lastSwitch)/self.switchTime
        
    @staticmethod
    def getRGB(c):
        return numpy.array(colorsys.hsv_to_rgb(*c))
            
    def render(self, model, params, frame):
        raise NotImplementedError("Implement render in ColorDrifterLayer subclass")


class HomogenousColorDrifterLayer(ColorDrifterLayer):    
    """ Color drift is homogenous across the whole brain """
    def render(self, model, params, frame):
        self._updateColor(params)
        p = self.proportionComplete(params)
        c = self.getFadeColor(p)
        numpy.add(frame, c, frame)


class TreeColorDrifterLayer(ColorDrifterLayer):
    """ Each tree is a bit out of phase, so they drift through the colors at different times """
    def __init__(self, colors, switchTime=None):
        super(TreeColorDrifterLayer,self).__init__(colors, switchTime)
        self.roots = None
        self.cachedModel = None
        
    def render(self, model, params, frame):
        self._updateColor(params)
        if self.roots is None or model != self.cachedModel:
            self.cachedModel = model
            self.roots = range(len(model.roots))
            random.shuffle(self.roots)
        p = self.proportionComplete(params)
        cnt = len(self.roots)
        for root in self.roots:
            p_root = p + float(root)/cnt
            frame[model.edgeTree==root] += self.getFadeColor(p_root)


class OutwardColorDrifterLayer(ColorDrifterLayer):
    
    # 0 means all levels are synced; 1 means that first level hits
    # color[n+1] at the same time that the last one is hitting color[n]
    offset = 0.5
    
    def __init__(self, colors, switchTime=None):
        super(OutwardColorDrifterLayer,self).__init__(colors, switchTime)
        self.levels = None
        self.cachedModel = None
        
    def render(self, model, params, frame):
        self._updateColor(params)
        if self.levels is None or model != self.cachedModel:
            self.cachedModel = model
            self.levels = max(model.edgeHeight)+1
        p = self.proportionComplete(params)
        for i in range(self.levels):
            p2 = p + self.offset * (1 - float(i)/self.levels)
            frame[model.edgeHeight==i] += self.getFadeColor(p2)   
