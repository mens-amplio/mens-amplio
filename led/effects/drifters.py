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
    
    def __init__(self, colors):
        l = len(colors)
        if l == 0:
            raise Exception("Can't initialize ColorDrifterLayer with empty color list")
        self.rgb_colors = numpy.array(colors, dtype='f')
        self.hsv_colors = matplotlib.colors.rgb_to_hsv(self.rgb_colors.reshape(-1,1,3)).reshape(-1,3)
        self.color_count = len(self.hsv_colors)
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

    def render(self, model, params, frame, response_level):
        raise NotImplementedError("Implement render_responsive in ColorDrifterLayer subclass")
        
class TimedColorDrifterLayer(ColorDrifterLayer):    
    """ Color drift is time-based. Default drift behavior is homogenous across the whole brain """
    def __init__(self, colors, switchTime):
        super(TimedColorDrifterLayer,self).__init__(colors)
        self.switchTime = float(switchTime)
        self.secondsPerCycle = self.switchTime * self.color_count
        self.secondsPerFadeColor = self.switchTime / self.fadeSteps

    def getFadeColor(self, time):
        index = int( (time % self.secondsPerCycle) / self.secondsPerFadeColor )
        return self.fade_colors_rgb[index]

    def render(self, model, params, frame):
        c = self.getFadeColor(params.time)
        numpy.add(frame, c, frame)


class TreeColorDrifterLayer(TimedColorDrifterLayer):
    """ Each tree is a bit out of phase, so they drift through the colors at different times """
    def __init__(self, colors, switchTime):
        super(TreeColorDrifterLayer,self).__init__(colors, switchTime)
        self.roots = None
        self.cachedModel = None
        
    def render(self, model, params, frame):
        if self.roots is None or model != self.cachedModel:
            self.cachedModel = model
            self.roots = range(len(model.roots))
            random.shuffle(self.roots)
        cnt = len(self.roots)
        
        # this is much uglier than iterating through the trees calling getFadeColor,
        # but twice as fast
        indices = ((params.time + numpy.array(model.edgeTree) * self.switchTime / cnt) 
            % self.secondsPerCycle) / self.secondsPerFadeColor
        frame += self.fade_colors_rgb[indices.astype(int)]


class OutwardColorDrifterLayer(TimedColorDrifterLayer):
    
    # 0 means all levels are synced; 1 means that first level hits
    # color[n+1] at the same time that the last one is hitting color[n]
    offset = 0.5
    
    def __init__(self, colors, switchTime):
        super(OutwardColorDrifterLayer,self).__init__(colors, switchTime)
        self.levels = None
        self.cachedModel = None
        
    def render(self, model, params, frame):
        if self.levels is None or model != self.cachedModel:
            self.cachedModel = model
            self.levels = max(model.edgeHeight)+1
        
        # this is much uglier than iterating through the levels calling 
        # getFadeColor, but 3x as fast
        indices = ((params.time + self.offset * self.switchTime * (1 - model.edgeHeight/float(self.levels))) 
            % self.secondsPerCycle) / self.secondsPerFadeColor
        frame += self.fade_colors_rgb[indices.astype(int)]

            
class ResponsiveColorDrifterLayer(HeadsetResponsiveEffectLayer):
    """ Drifts between two colors depending on headset response level
    (0 = 100% color 1, 1 = 100% color 2)"""
    def __init__(self, colors, respond_to = 'meditation', smooth_response_over_n_secs=1):
        super(ResponsiveColorDrifterLayer,self).__init__(respond_to, smooth_response_over_n_secs)
        if len(colors) != 2:
            raise Exception("ResponsiveColorDrifterLayer must fade between two colors")
        self.drifter = ColorDrifterLayer(colors)
         
    def getResponsiveColor(self, response_level):
        index = int(ColorDrifterLayer.fadeSteps * response_level) if response_level else 0
        return self.drifter.fade_colors_rgb[index]
        
    def render_responsive(self, model, params, frame, response_level):
        c = self.getResponsiveColor(response_level)
        numpy.add(frame, c, frame)
        