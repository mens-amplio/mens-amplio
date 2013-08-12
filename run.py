#!/usr/bin/env python
#
# Runs Mens Amplio lights on real hardware with full or test functionality
#
# Usage: ./run.py or ./run.py test
#
# Edit light playlists in playlists.py or testplaylists.py

import sys
import time
from led.model import Model
from led.effects.base import EffectParameters
from led.controller import AnimationController, Renderer
from led.threads import HeadsetThread, ParamThread, LayerSwapperThread
from led.renderer import Renderer, Playlist
from mindwave.mindwave import FakeHeadset, BluetoothHeadset
               
               
if __name__ == '__main__':
    # load playlist definitions
    test = len(sys.argv) > 1 and sys.argv[1] == 'test'
    if test:
        print "Loading test layer definitions"
        import testplaylists as playlists
    else:
        print "Importing real layer definitions"
        import playlists
    
    # create lighting and headset control objects
    masterParams = EffectParameters()
    model = Model('modeling/graph.data.json', 'modeling/manual.remap.json')
    renderer = Renderer({ 
        'on': playlists.headsetOn, 
        'off': playlists.headsetOff, 
        'transition': playlists.transition 
        }, 
        activePlaylist='off')
    controller = AnimationController(model, renderer=renderer, params=masterParams)
    headset = FakeHeadset(bad_data=True) if test else BluetoothHeadset()
    
    # start daemon threads
    threads = [
        HeadsetThread(masterParams, headset),
        LayerSwapperThread(masterParams, renderer, playlists.headsetOn, playlists.headsetOff, playlists.transition)
    ]
    for thread in threads:
        thread.start()
    
    # start the lights
    time.sleep(0.05)
    controller.drawingLoop()
    
