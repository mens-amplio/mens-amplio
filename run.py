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
from led.controller import AnimationController
from led.renderer import Renderer
from playlist import Playlist
from flame.flameboard import FakeFlameBoard, I2CFlameBoard
from flame.sequences import SyncedBursts, SequentialBursts
from mindwave.mindwave import FakeHeadset, BluetoothHeadset, FileHeadset
from threads import FlamesThread, HeadsetThread, LayerSwapperThread
               
               
if __name__ == '__main__':
    # load playlist definitions
    test = len(sys.argv) > 1 and sys.argv[1] == 'test'
    if test:
        print "Loading test layer definitions"
        import testplaylists as playlists
    else:
        print "Importing real layer definitions"
        import playlists
        
    # defining this here rather than in separate files since it will be
    # much less likely to change and needn't differ between test and full modes
    flameSequences = Playlist([
        SyncedBursts(5, 1000, 250, 4),
        SyncedBursts(5, 500, 500, 7),
        SequentialBursts(6, 250, 3),
        SequentialBursts(6, 750, 1),
        ], shuffle=True)
    solenoids = range(8, 14)
    
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
    flameBoard = FakeFlameBoard(solenoids) if test else I2CFlameBoard(solenoids)
    
    # start daemon threads
    threads = [
        HeadsetThread(masterParams, headset),
        LayerSwapperThread(masterParams, renderer),
        FlamesThread(masterParams, flameBoard, flameSequences),
    ]
    for thread in threads:
        thread.start()
    
    # start the lights
    time.sleep(0.05)
    controller.drawingLoop()
    
