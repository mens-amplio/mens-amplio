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
from led.renderer import Renderer, Playlist
from flame.flameboard import FakeFlameBoard, I2CFlameBoard
from mindwave.mindwave import FakeHeadset, BluetoothHeadset
from threads import FlamesThread, HeadsetThread, ParamThread, LayerSwapperThread
               
               
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
    # i'm leaving the real board out for now so I can run in full mode on my Pi without it
    flameBoard = FakeFlameBoard() #if test else I2CFlameBoard()
    
    # start daemon threads
    threads = [
        HeadsetThread(masterParams, headset),
        LayerSwapperThread(masterParams, renderer, playlists.headsetOn, playlists.headsetOff, playlists.transition),
        FlamesThread(masterParams, flameBoard),
    ]
    for thread in threads:
        thread.start()
    
    # start the lights
    time.sleep(0.05)
    controller.drawingLoop()
    
