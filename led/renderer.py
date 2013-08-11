#!/usr/bin/env python

import time
import numpy
from led.effects import GammaLayer


class RoutineList:
    """ A list of routines (aka a list of effect layer lists) where one routine is active
    at any given time. Iterating through this object is equivalent to iterating through
    the effect layers in the active routine."""
    def __init__(self, routines, index = 0, randomize=False):
        
        # let's be lazy and pass single effect lists (or single effects)
        # in without having to remember to wrap 'em in extra brackets
        if not isinstance(routines, list):
            routines = [[routines]]
        elif not any(isinstance(l, list) for l in routines):
            routines = [routines]
            
        self.routines = routines
        self.active = index
        self.order = range(len(self.routines))
        self.randomize = randomize
        if randomize:
            random.shuffle(self.order)
            
    def __iter__(self):
        return iter( self.routines[self.order[self.active]] )
            
    def advance(self):
        # Switch the active routine to the next one in the list, either
        # consecutively or randomly depending on whether Randomize is true
        if len(self.routines) > 1:
            active = self.active + 1
            if active >= len(self.routines):
                if self.randomize:
                    random.shuffle(self.order)
                active = 0
            self.active = active


class Renderer:
    """
    Renders the currently active layers and manages transitions between layer lists.
    Also applies a gamma correction layer after everything else is rendered.
    At the moment, this class does one of two things: 
    -Calls render on a fade object if one exists
    -Otherwise, renders a list of active layers directly
    """
    def __init__(self, layers=None, gamma=2.2):
        self.activeLayers = layers
        self.fade = None
        self.gammaLayer = GammaLayer(gamma)
        
    def render(self, model, params, frame):
        if self.fade:
            self.fade.render(model, params, frame)
            # if the fade is finished, grab its end layers and just render those
            if self.fade.done:
                self.activeLayers = self.fade.endLayers
                self.fade = None
        elif self.activeLayers:
            for layer in self.activeLayers:
                layer.render(model, params, frame)
        self.gammaLayer.render(model, params, frame)
        
    def setFade(self, duration, nextLayers1, nextLayers2=None):
        # TODO check for wonky behavior when one fade is set while another is still in progress
        if nextLayers2:
            self.fade = TwoStepLinearFade(self.activeLayers, nextLayers1, nextLayers2, duration)
        else:
            self.fade = LinearFade(self.activeLayers, nextLayers1, duration)

class Fade:
    """
    Handles transition between multiple lists of layers
    """
    def __init__(self, startLayers, endLayers):
        self.done = False # should be set to True when fade is complete
        self.startLayers = startLayers
        self.endLayers = endLayers # final layer list to be rendered after fade is done
    
    def render(self, model, params, frame):
        raise NotImplementedException("Implement in fader subclass")
        
        
class LinearFade(Fade):
    """
    Simple linear fade between two sets of layers
    """
    def __init__(self, startLayers, endLayers, duration):
        Fade.__init__(self, startLayers, endLayers)
        self.duration = float(duration)
        # set actual start time on first call to render
        self.start = None
        
    def render(self, model, params, frame):
        if not self.start:
            self.start = time.time()
        # render the end layers
        for layer in self.endLayers:
            layer.render(model, params, frame)
        percentDone = (time.time() - self.start) / self.duration
        if percentDone >= 1:
            self.done = True
        else:
            # if the fade is still in progress, render the start layers
            # and blend them in
            frame2 = numpy.zeros(frame.shape)
            for layer in self.startLayers:
                layer.render(model, params, frame2) 
            numpy.multiply(frame, percentDone, frame)
            numpy.multiply(frame2, 1-percentDone, frame2)
            numpy.add(frame, frame2, frame)

            
class TwoStepLinearFade(Fade):
    """
    Performs a linear fade to an intermediate layer list, then another linear
    fade to a final list. Useful for making something brief and dramatic happen.
    """
    def __init__(self, currLayers, nextLayers, finalLayers, duration):
        Fade.__init__(self, currLayers, finalLayers)
        self.fade1 = LinearFade(currLayers, nextLayers, duration/2.)
        self.fade2 = LinearFade(nextLayers, finalLayers, duration/2.)
        
    def render(self, model, params, frame):
        if not self.fade1.done:
            self.fade1.render(model, params, frame)
        else:
            self.fade2.render(model, params, frame)
            self.done = self.fade2.done