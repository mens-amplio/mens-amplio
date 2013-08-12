import math
import numpy
import random
from base import EffectLayer, HeadsetResponsiveEffectLayer


class Bolt(object):
    """Represents a single lightning bolt in the LightningStormLayer effect."""

    PULSE_INTENSITY = 0.08
    PULSE_FREQUENCY = 10.
    FADE_TIME = 0.25
    SECONDARY_BRANCH_INTENSITY = 0.4

    def __init__(self, model, init_time):
        self.init_time = init_time
        self.pulse_time = random.uniform(.25, .35)
        self.color = numpy.array([v/255.0 for v in [230, 230, 255]])  # Violet storm
        self.life_time = self.pulse_time + Bolt.FADE_TIME
        self.edges, self.intensities = self.choose_random_path(model)

    def choose_random_path(self, model):
        leader_intensity = (1.0 - Bolt.PULSE_INTENSITY)
        branch_intensity = leader_intensity * Bolt.SECONDARY_BRANCH_INTENSITY
        root = random.choice(model.roots)
        edges = [root]
        leader = root
        intensities = [leader_intensity]
        while model.outwardAdjacency[leader]:
            next_leader = random.choice(model.outwardAdjacency[leader])
            for edge in model.outwardAdjacency[leader]:
                edges.append(edge)
                if edge == next_leader:
                    # Main bolt branch fully bright
                    intensities.append(leader_intensity)
                else:
                    # Partially light clipped branches
                    intensities.append(branch_intensity)
            leader = next_leader
        return numpy.array(edges), numpy.array(intensities)

    def update_frame(self, frame, current_time):
        dt = current_time - self.init_time

        if dt < self.pulse_time:  # Bolt fully lit and pulsing
            phase = math.cos(2 * math.pi * dt * Bolt.PULSE_FREQUENCY) 
            intensities = self.intensities + (phase * Bolt.PULSE_INTENSITY)
            c = self.color.reshape(1, -1) * intensities.reshape(-1, 1)
            frame[self.edges] += c

        else:  # Bolt fades out linearly
            fade = 1 - (dt - self.pulse_time) * 1.0 / Bolt.FADE_TIME
            intensities = self.intensities * fade
            c = self.color.reshape(1, -1) * intensities.reshape(-1, 1)
            frame[self.edges] += c


class LightningStormLayer(HeadsetResponsiveEffectLayer):
    """Simulate lightning storm."""

    def __init__(self,
                 max_bolts_per_second = 8.0,
                 min_bolts_per_second = 0.5,
                 respond_to = 'attention',
                 smooth_response_over_n_secs=0):
        # http://www.youtube.com/watch?v=RLWIBrweSU8
        super(LightningStormLayer,self).__init__(
            respond_to, smooth_response_over_n_secs=smooth_response_over_n_secs)
        self.bolts = []
        self.min_bolts_per_second = min_bolts_per_second
        self.max_bolts_per_second = max_bolts_per_second
        self.span = self.max_bolts_per_second - self.min_bolts_per_second
        self.bolts_per_second = None
        self.compute_bolts_per_second(0.5)
        self.last_time = None

    def compute_bolts_per_second(self, response_level):
        self.bolts_per_second = self.min_bolts_per_second + (
            response_level * response_level * self.span)

    def render_responsive(self, model, params, frame, response_level):
        if response_level != None:
            self.compute_bolts_per_second(response_level)

        if not self.last_time:
            self.last_time = params.time

        self.bolts = [bolt for bolt in self.bolts
                      if bolt.init_time + bolt.life_time > params.time]

        # Bolts will strike as a poisson arrival process. That is, randomly,
        # but on average, 'bolts_per_second' bolts will strike per second.
        # The memoryless nature of it will create periods of relative calm
        # and relative flurry.
        if (params.time - self.last_time) * self.bolts_per_second > random.random():
            # Bolts are allowed to overlap, creates some interesting effects
            self.bolts.append(Bolt(model, params.time))

        self.last_time = params.time

        for bolt in self.bolts:
            bolt.update_frame(frame, params.time)
