# Defines full set of lighting effect playlists to use when actually running piece 

from led.effects.base import (
    EffectParameters, SnowstormLayer, TechnicolorSnowstormLayer, WhiteOutLayer)
from led.effects.digital_rain import DigitalRainLayer
from led.effects.drifters import *
from led.effects.firefly_swarm import FireflySwarmLayer
from led.effects.impulses import *
from led.effects.lightning_storm import LightningStormLayer
from led.effects.plasma import PlasmaLayer
from led.effects.waves import WavesLayer
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
        
headsetOff = Playlist([
    [
        TreeColorDrifterLayer([ (1,0,1), (.5,.5,1), (0,0,1) ], 5),
        PlasmaLayer(),
    ],
    [
        OutwardColorDrifterLayer([ (1,0,0), (.7,.3,0), (.7,0,.3) ], 10),
        PlasmaLayer(),
    ]
])
        
transition = Playlist([
    [WhiteOutLayer()],
    [SnowstormLayer()]
    ])