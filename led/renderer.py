#!/usr/bin/env python

import time
import numpy
import random
from effects.base import GammaLayer


class Playlist:
    """ 
    A list of light routines (aka a list of effect layer lists) all intended for use 
    in a single context (e.g. when the headset is on). One routine in the playlist 
    is selected at any given time.
    """
    def __init__(self, routines, index = 0, shuffle=False):
        
        # let's be lazy and pass single effect lists (or single effects)
        # in without having to remember to wrap 'em in extra brackets
        if not isinstance(routines, list):
            routines = [[routines]]
        elif not any(isinstance(l, list) for l in routines):
            routines = [routines]
            
        self.routines = routines
        self.selected = index
        self.order = range(len(self.routines))
        self.shuffle = shuffle
        if shuffle:
            random.shuffle(self.order)
            
    def selection(self):
        return self.routines[self.order[self.selected]]
            
    def advance(self):
        # Switch the selected routine to the next one in the list, either
        # consecutively or randomly depending on whether shuffle is true
        if len(self.routines) > 1:
            selected = self.selected + 1
            if selected >= len(self.routines):
                if self.shuffle:
                    random.shuffle(self.order)
                selected = 0
            self.selected = selected


class Renderer:
    """
    Renders the selected routine from the current playlist and manages 
    fades between playlists. Also applies a gamma correction layer 
    after everything else is rendered.
    At the moment, this class does one of two things: 
    -Calls render on a fade object if one exists
    -Otherwise, renders the current playlist's selected routine directly
    """
    def __init__(self, playlist=None, gamma=2.2):
        self.playlist = playlist
        self.fade = None
        self.gammaLayer = GammaLayer(gamma)
        
    def render(self, model, params, frame):
        if self.fade:
            self.fade.render(model, params, frame)
            # if the fade is finished, grab its end playlist to render next time
            if self.fade.done:
                self.playlist = self.fade.endPlaylist
                self.fade = None
        elif self.playlist:
            for layer in self.playlist.selection():
                layer.render(model, params, frame)
        self.gammaLayer.render(model, params, frame)
        
    def setFade(self, duration, nextPlaylist1, nextPlaylist2=None):
        # TODO check for wonky behavior when one fade is set while another is still in progress
        if nextPlaylist2:
            self.fade = TwoStepLinearFade(self.playlist, nextPlaylist1, nextPlaylist2, duration)
        else:
            self.fade = LinearFade(self.playlist, nextPlaylist1, duration)

class Fade:
    """
    Renders a smooth transition between multiple playlists
    """
    def __init__(self, startPlaylist, endPlaylist):
        self.done = False # should be set to True when fade is complete
        self.startPlaylist = startPlaylist
        self.endPlaylist = endPlaylist # final layer list to be rendered after fade is done
    
    def render(self, model, params, frame):
        raise NotImplementedException("Implement in fader subclass")
        
        
class LinearFade(Fade):
    """
    Renders a simple linear fade between two playlists
    """
    def __init__(self, startPlaylist, endPlaylist, duration):
        Fade.__init__(self, startPlaylist, endPlaylist)
        self.duration = float(duration)
        # set actual start time on first call to render
        self.start = None
        
    def render(self, model, params, frame):
        if not self.start:
            self.start = time.time()
        # render the end layers
        for layer in self.endPlaylist.selection():
            layer.render(model, params, frame)
        percentDone = (time.time() - self.start) / self.duration
        if percentDone >= 1:
            self.done = True
        else:
            # if the fade is still in progress, render the start layers
            # and blend them in
            frame2 = numpy.zeros(frame.shape)
            for layer in self.startPlaylist.selection():
                layer.render(model, params, frame2) 
            numpy.multiply(frame, percentDone, frame)
            numpy.multiply(frame2, 1-percentDone, frame2)
            numpy.add(frame, frame2, frame)

            
class TwoStepLinearFade(Fade):
    """
    Performs a linear fade to an intermediate playlist, then another linear
    fade to a final playlist. Useful for making something brief and dramatic happen.
    """
    def __init__(self, currPlaylist, nextPlaylist, finalPlaylist, duration):
        Fade.__init__(self, currPlaylist, finalPlaylist)
        self.fade1 = LinearFade(currPlaylist, nextPlaylist, duration/2.)
        self.fade2 = LinearFade(nextPlaylist, finalPlaylist, duration/2.)
        
    def render(self, model, params, frame):
        if not self.fade1.done:
            self.fade1.render(model, params, frame)
        else:
            self.fade2.render(model, params, frame)
            self.done = self.fade2.done