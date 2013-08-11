#!/usr/bin/env python

import threading
import random
import time
import sys


class ParamThread(threading.Thread):
    """
    Base class for daemon threads that operate on an EffectParameters object
    """
    def __init__(self, params):
        threading.Thread.__init__(self)
        self.daemon = True
        self.params = params

      
class HeadsetThread(ParamThread):
    """
    Polls the Mindwave headset. Each time a new point is received, creates an 
    EEGInfo object and stores it in params.
    """ 
    
    class EEGInfo:
        """
        Extracts/stores all the headset info that the effects might actually care about.
        Attention and meditation values are scaled to floats in the range [0,1].
        """
        def __init__(self, point):
            def scale(n):
                return float(n)/100
            self.attention = scale(point.attention)
            self.meditation = scale(point.meditation)
            self.on = point.headsetDataReady()
            self.poor_signal = point.poor_signal

        def __str__(self):
            return "A: {0} M: {1} Signal: {2}".format(self.attention, self.meditation, self.poor_signal) 

    def __init__(self, params, headset):
        super(HeadsetThread,self).__init__(params)
        self.headset = headset

    def run(self):
        while True:
            point = self.headset.readDatapoint()
            self.params.eeg = HeadsetThread.EEGInfo(point)
            print self.params.eeg    
            

class LayerSwapperThread(ParamThread):
    """
    Monitors the headset parameter data and changes the active layers in the renderer
    when the headset is taken on or off, or when headset data values cross a certain 
    threshold [not implemented yet]
    """
    def __init__(self, params, renderer, headsetOnLayers, headsetOffLayers, transitionLayers):
        ParamThread.__init__(self, params)
        self.renderer = renderer
        self.headsetOn = False
        
        self.headsetOnLayers = headsetOnLayers
        self.headsetOffLayers = headsetOffLayers
        self.transitionLayers = transitionLayers
        
        renderer.playlist = self.headsetOffLayers
        
    def run(self):
        while True:
            if self.params.eeg and self.params.eeg.on:
                if not self.headsetOn:
                    sys.stderr.write("on!\n")
                    self.headsetOn = True
                    self.renderer.setFade(0.5, self.transitionLayers, self.headsetOnLayers)
                    self.transitionLayers.advance()
                    self.headsetOnLayers.advance()
            else:
                if self.headsetOn:
                    sys.stderr.write("off!\n")
                    self.headsetOn = False
                    self.renderer.setFade(1, self.headsetOffLayers)
                    self.headsetOffLayers.advance()
            time.sleep(0.05)

