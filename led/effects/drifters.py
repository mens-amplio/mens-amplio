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

class MinimalColorDrifterLayer(EffectLayer):
    
    fadeSteps = 255
    def __init__(self, colors, switchTime):
        l = len(colors)
        if l == 0:
            raise Exception("Can't initialize MinimalColorDrifterLayer with empty color list")
        self.switchTime = float(switchTime)
        self.rgb_colors = numpy.array(colors)
        self.hsv_colors = matplotlib.colors.rgb_to_hsv(self.rgb_colors.reshape(-1,1,3)).reshape(-1,3)
        self.color_count = len(self.hsv_colors)
        self.secondsPerCycle = self.switchTime * self.color_count
        self.secondsPerFadeColor = self.switchTime / self.fadeSteps
        self.totalSteps = self.fadeSteps * len(colors)
        self.precalc()

    def precalc(self):
        self.fade_colors_hsv = numpy.zeros([self.totalSteps, 3])

        steps = numpy.tile(numpy.arange(0, 1, 1.0/self.fadeSteps), 3)
        indices = numpy.arange(3).repeat(self.fadeSteps)
        for i in range(self.color_count):
            pair_of_colors = self.hsv_colors[[i, (i+1)%self.color_count ]]

            # Hue is a loop, this is how to force the shortest path
            if(pair_of_colors[0,0] - pair_of_colors[1,0] > 0.5):
                pair_of_colors[1,0] += 1
            elif(pair_of_colors[0,0] - pair_of_colors[1,0] < -0.5):
                pair_of_colors[1,0] -= 1
            interpolater = scipy.interpolate.RectBivariateSpline([0,1], [0,1,2], pair_of_colors, kx=1, ky=1)
            between_colors = interpolater.ev(steps, indices).reshape(3, -1)
            between_colors[0] = between_colors[0] % 1 # return hue to 0..1
            between_colors = between_colors.swapaxes(0,1)
            self.fade_colors_hsv[range(i*self.fadeSteps,(i+1)*self.fadeSteps)] = between_colors
        self.fade_colors_rgb = matplotlib.colors.hsv_to_rgb(self.fade_colors_hsv.reshape(-1,1,3)).reshape(-1,3)

    def getFadeColor(self, time):
        index = int( (time % self.secondsPerCycle) / self.secondsPerFadeColor )
        return self.fade_colors_rgb[index]

    def render(self, model, params, frame):
        c = self.getFadeColor(params.time)
        numpy.add(frame, c, frame)

class HomogenousColorDrifterLayer(MinimalColorDrifterLayer):    
    """ Color drift is homogenous across the whole brain """
    # actually, that's the default behavior,


class TreeColorDrifterLayer(MinimalColorDrifterLayer):
    """ Each tree is a bit out of phase, so they drift through the colors at different times """
    def __init__(self, colors, switchTime=None):
        super(TreeColorDrifterLayer,self).__init__(colors, switchTime)
        self.roots = None
        self.cachedModel = None
        
    def render(self, model, params, frame):
        if self.roots is None or model != self.cachedModel:
            self.cachedModel = model
            self.roots = range(len(model.roots))
            random.shuffle(self.roots)
        cnt = len(self.roots)
        for root_index, root in enumerate( self.roots ):
            t_root = params.time + root_index * self.switchTime / cnt
            frame[model.edgeTree==root] += self.getFadeColor(t_root)


class OutwardColorDrifterLayer(MinimalColorDrifterLayer):
    
    # 0 means all levels are synced; 1 means that first level hits
    # color[n+1] at the same time that the last one is hitting color[n]
    offset = 0.5
    
    def __init__(self, colors, switchTime=None):
        super(OutwardColorDrifterLayer,self).__init__(colors, switchTime)
        self.levels = None
        self.cachedModel = None
        
    def render(self, model, params, frame):
        if self.levels is None or model != self.cachedModel:
            self.cachedModel = model
            self.levels = max(model.edgeHeight)+1
        for i in range(self.levels):
            t = params.time + self.offset * self.switchTime * (1 - float(i)/self.levels)
            frame[model.edgeHeight==i] += self.getFadeColor(t)
