# Defines a restricted set of playlists to use when we want to test out new
# routines without running the entire set

from led.effects.base import (
    EffectParameters, SnowstormLayer, TechnicolorSnowstormLayer, WhiteOutLayer, 
    RGBLayer, BlinkyLayer, ColorBlinkyLayer, NoDataLayer)
from led.effects.digital_rain import DigitalRainLayer
from led.effects.drifters import *
from led.effects.firefly_swarm import FireflySwarmLayer
from led.effects.impulses import *
from led.effects.lightning_storm import LightningStormLayer
from led.effects.plasma import PlasmaLayer, ZoomingPlasmaLayer
from led.effects.waves import WavesLayer
from led.renderer import Playlist

headsetOn = Playlist([
    [
        #WavesLayer(),
        #LightningStormLayer(),
        TreeColorDrifterLayer([ (1,0,1), (.5,.5,1), (0,0,1) ], 5),
        ZoomingPlasmaLayer(),
        #NoDataLayer(),
        #RGBLayer(),
    ]
])
        
headsetOff = Playlist([
    [
        TreeColorDrifterLayer([ (1,0,1), (.5,.5,1), (0,0,1) ], 5),
        PlasmaLayer(),
    ]
])
        
transition = Playlist([
    [WhiteOutLayer()],
    [SnowstormLayer()],
    [TechnicolorSnowstormLayer()],
    [DigitalRainLayer()],
    [BlinkyLayer()],
    [ColorBlinkyLayer()],
    ], shuffle=True)
