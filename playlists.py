# Defines full set of lighting effect playlists to use when actually running piece 

from led.effects.base import (
    EffectParameters, SnowstormLayer, TechnicolorSnowstormLayer, WhiteOutLayer, NoDataLayer)
from led.effects.digital_rain import DigitalRainLayer
from led.effects.drifters import *
from led.effects.firefly_swarm import FireflySwarmLayer
from led.effects.impulses import *
from led.effects.lightning_storm import LightningStormLayer
from led.effects.plasma import PlasmaLayer
from led.effects.waves import WavesLayer
from led.effects.rain import RainLayer
from led.renderer import Playlist

headsetOn = Playlist([
    [
        ImpulseLayer2(),
        WavesLayer(color=(1,0,.2)),
        PlasmaLayer(color=(.1,.1,.1)),
    ],
    [
        WavesLayer(),
        LightningStormLayer(),
    ]
])

def make_plasma_playlist(drifters):
    l = []
    for d in drifters:
        rand = random.random()
        routine = [d, PlasmaLayer(zoom=0.3+rand/2)]
        if random.random() < 1:
            routine.append(RainLayer(dropEvery=2+rand*3))
        l.append(routine)
        
    return Playlist(l, shuffle=True)
        
headsetOff = make_plasma_playlist([
        OutwardColorDrifterLayer([ (1,0.1,0.2), (0.2,0.1,1) ], 15), #red/purple/blue
        TreeColorDrifterLayer([ (0.5,1,0.5), (0.5,0.5,1), (0.6,0.1,0.8)], 15), #green/blue, a bit of purple
        OutwardColorDrifterLayer([ (1,.6,.4), (0, 0.2, 1) ], 15), #purple/pink/blue
        TreeColorDrifterLayer([ (1, .8, 0), (1, .3, 0) ], 15), #red/orange
        OutwardColorDrifterLayer([ (.5, 0, 1), (1, .4, .4) ], 15), #deep pink/blue/purple
        TimedColorDrifterLayer([ (.8, .3, 0), (.6, .6, .8) ], 15), #red/pink/blue
        TreeColorDrifterLayer([ (0.1,1,0.2), (0.1,0.2,1) ], 15), #green/blue
    ])
        
transition = Playlist([
    [WhiteOutLayer()],
    [SnowstormLayer()]
    ])