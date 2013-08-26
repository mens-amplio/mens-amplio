from __future__ import print_function
import numpy
import time
import traceback
import colorsys
import random

class EffectParameters(object):
    """Inputs to the individual effect layers. Includes basics like the timestamp of the frame we're
       generating, as well as parameters that may be used to control individual layers in real-time.
       """

    time = 0
    targetFrameRate = 59.0     # XXX: Want to go higher, but gl_server can't keep up!
    eeg = None


class EffectLayer(object):
    """Abstract base class for one layer of an LED light effect. Layers operate on a shared framebuffer,
       adding their own contribution to the buffer and possibly blending or overlaying with data from
       prior layers.

       The 'frame' passed to each render() function is an array of LEDs in the same order as the
       IDs recognized by the 'model' object. Each LED is a 3-element list with the red, green, and
       blue components each as floating point values with a normalized brightness range of [0, 1].
       If a component is beyond this range, it will be clamped during conversion to the hardware
       color format.
       """

    transitionFadeTime = 1.0
    maximum_errors = 5

    def render(self, model, params, frame):
        raise NotImplementedError("Implement render() in your EffectLayer subclass")

    def safely_render(self, model, params, frame):
        if not hasattr(self, 'error_count'):
            self.error_count = 0
        try:
            if self.error_count < EffectLayer.maximum_errors:
                self.render(model, params, frame)
        except Exception as err:
            error_log = open('error.log','a')
            error_log.write(time.asctime(time.gmtime()) + " UTC" + " : ")
            traceback.print_exc(file=error_log)
            print("ERROR:", err, "in", self)
            self.error_count += 1
            if self.error_count >= EffectLayer.maximum_errors:
                print("Disabling", self, "for throwing too many errors")

class HeadsetResponsiveEffectLayer(EffectLayer):
    """A layer effect that responds to the MindWave headset in some way.

    Two major differences from EffectLayer:
    1) Constructor expects four paramters:
       -- respond_to: the name of a field in EEGInfo (threads.HeadsetThread.EEGInfo).
          Currently this means either 'attention' or 'meditation'
       -- smooth_response_over_n_secs: to avoid rapid fluctuations from headset
          noise, averages the response metric over this many seconds
       -- minimum_response_level: if the response level is below this, the layer isn't rendered
       -- inverse: If this is true, the layer will respond to (1-response_level)
          instead of response_level
    2) Subclasses now only implement the render_responsive() function, which
       is the same as EffectLayer's render() function but has one extra
       parameter, response_level, which is the current EEG value of the indicated
       field (assumed to be on a 0-1 scale, or None if no value has been read yet).
    """
    def __init__(self, respond_to, smooth_response_over_n_secs=0, minimum_response_level=None, inverse=False):
        # Name of the eeg field to influence this effect
        if respond_to not in ('attention', 'meditation'):
            raise Exception('respond_to was "%s" -- should be "attention" or "meditation"'
                            % respond_to)
        self.respond_to = respond_to
        self.smooth_response_over_n_secs = smooth_response_over_n_secs
        self.measurements = []
        self.timestamps = []
        self.last_eeg = None
        self.last_response_level = None
        self.minimum_response_level = minimum_response_level
        # We want to smoothly transition between values instead of jumping
        # (as the headset typically gives one reading per second)
        self.fading_to = None
        self.inverse = inverse

    def start_fade(self, new_level):
        if not self.last_response_level:
            self.last_response_level = new_level
        else:
            self.fading_to = new_level

    def end_fade(self):
        self.last_response_level = self.fading_to
        self.fading_to = None

    def render(self, model, params, frame):
        now = time.time()
        response_level = None
        # Update our measurements, if we have a new one
        if params.eeg and params.eeg != self.last_eeg and params.eeg.on:
            if self.fading_to:
                self.end_fade()
            # Prepend newest measurement and timestamp
            self.measurements[:0] = [getattr(params.eeg, self.respond_to)]
            self.timestamps[:0] = [now]
            self.last_eeg = params.eeg
            # Compute the parameter to send to our rendering function
            N = len(self.measurements)
            idx = 0
            while idx < N:
                dt = self.timestamps[0] - self.timestamps[idx]
                if dt >= self.smooth_response_over_n_secs:
                    self.measurements = self.measurements[:(idx + 1)]
                    self.timestamps = self.timestamps[:(idx + 1)]
                    break
                idx += 1
            self.start_fade(sum(self.measurements) * 1.0 / len(self.measurements))
            response_level = self.last_response_level
        elif self.fading_to:
            # We assume one reading per second, so a one-second fade
            fade_progress = now - self.timestamps[0]
            if fade_progress >= 1:
                self.end_fade()
                response_level = self.last_response_level
            else:
                response_level = (
                    fade_progress * self.fading_to +
                    (1 - fade_progress) * self.last_response_level)

        if response_level and self.inverse:
            response_level = 1 - response_level
                    
        if self.minimum_response_level == None or response_level >= self.minimum_response_level:
            self.render_responsive(model, params, frame, response_level)


    def render_responsive(self, model, params, frame, response_level):
        raise NotImplementedError(
            "Implement render_responsive() in your HeadsetResponsiveEffectLayer subclass")


########################################################
# Simple EffectLayer implementations and examples
########################################################


class RGBLayer(EffectLayer):
    """Simplest layer, draws a static RGB color cube."""

    def render(self, model, params, frame):
        frame[:] = model.edgeCenters[:]


class MultiplierLayer(EffectLayer):
    """ Renders two layers in temporary frames, then adds the product of those frames
    to the frame passed into its render method
    """
    def __init__(self, layer1, layer2):
        self.layer1 = layer1
        self.layer2 = layer2        
        
    def render(self, model, params, frame):
        temp1 = numpy.zeros(frame.shape)
        temp2 = numpy.zeros(frame.shape)
        self.layer1.render(model, params, temp1)
        self.layer2.render(model, params, temp2)
        numpy.multiply(temp1, temp2, temp1)
        numpy.add(frame, temp1, frame)


class BlinkyLayer(EffectLayer):
    """Test our timing accuracy: Just blink everything on and off every other frame."""

    on = False

    def render(self, model, params, frame):
        self.on = not self.on
        frame[:] += self.on

class ColorBlinkyLayer(EffectLayer):
    on = False
    def render(self, model, params, frame):
        self.on = not self.on
        color = numpy.array(colorsys.hsv_to_rgb(random.random(),1,1))
        if self.on:
            frame[:] += color


class SnowstormLayer(EffectLayer):
    transitionFadeTime = 1.0
    def render(self, model, params, frame):
        numpy.add(frame, numpy.random.rand(model.numLEDs, 1), frame)


class TechnicolorSnowstormLayer(EffectLayer):
    transitionFadeTime = 1.5
    def render(self, model, params, frame):
        numpy.add(frame, numpy.random.rand(model.numLEDs, 3), frame)


class WhiteOutLayer(EffectLayer):
    """ Sets everything to white """

    transitionFadeTime = 0.5
    def render(self, model, params, frame):
        frame += numpy.ones(frame.shape)
            

class GammaLayer(EffectLayer):
    """Apply a gamma correction to the brightness, to adjust for the eye's nonlinear sensitivity."""

    def __init__(self, gamma):
        # Build a lookup table
        self.lutX = numpy.arange(0, 1, 0.01)
        self.lutY = numpy.power(self.lutX, gamma)

    def render(self, model, params, frame):
        frame[:] = numpy.interp(frame.reshape(-1), self.lutX, self.lutY).reshape(frame.shape)


######################################################################
# Simple HeadsetResponsiveEffectLayer implementations and examples
######################################################################


class ResponsiveGreenHighRedLow(HeadsetResponsiveEffectLayer):
    """Colors everything green if the response metric is high, red if low.

    Interpolates in between.
    """
    def __init__(self, respond_to='attention', smooth_response_over_n_secs=3):
        super(ResponsiveGreenHighRedLow,self).__init__(
            respond_to, smooth_response_over_n_secs=smooth_response_over_n_secs)

    def render_responsive(self, model, params, frame, response_level):
        if response_level is None:
            # No signal (blue)
            frame[:,2] += 1
        else:
            frame[:,0] += 1 - response_level
            frame[:,1] += response_level

            
class BrainStaticLayer(HeadsetResponsiveEffectLayer):
    def __init__(self, minFactor = 0.3, respond_to='meditation', smooth_response_over_n_secs=0):
        super(BrainStaticLayer,self).__init__(respond_to, smooth_response_over_n_secs)
        self.minFactor = minFactor
        
    def render_responsive(self, model, params, frame, response_level):
        r = 1-response_level if response_level else 1
        numpy.multiply(frame, 1-numpy.random.rand(model.numLEDs, 1)*r*self.minFactor, frame)
