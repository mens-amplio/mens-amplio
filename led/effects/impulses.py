import colorsys
import numpy
import random
from base import EffectLayer, HeadsetResponsiveEffectLayer


class ImpulsesLayer(EffectLayer):
    """Oscillating neural impulses which travel outward along the tree"""

    def __init__(self, count=10):
        self.positions = [None] * count
        self.phases = [0] * count
        self.frequencies = [0] * count

    def render(self, model, params, frame):
        for i in range(len(self.positions)):

            if self.positions[i] is None:
                # Impulse is dead. Random chance of reviving it.
                if random.random() < 0.05:

                    # Initialize a new impulse with some random parameters
                    self.positions[i] = random.choice(model.roots)
                    self.phases[i] = random.uniform(0, math.pi * 2)
                    self.frequencies[i] = random.uniform(2.0, 10.0)

            else:
                # Draw the impulse
                br = max(0, math.sin(self.phases[i] + self.frequencies[i] * params.time))
                frame[self.positions[i]] += br

                # Chance of moving this impulse outward
                if random.random() < 0.2:

                    choices = model.outwardAdjacency[i]
                    if choices:
                        self.positions[i] = random.choice(choices)
                    else:
                        # End of the line
                        self.positions[i] = None


class ImpulseLayer2(HeadsetResponsiveEffectLayer):
    class Impulse():
        def __init__(self, color, edge, motion = "Out"):
            self.color = color
            self.edge = edge
            self.previous_edge = None
            self.dead = False
            self.motion = "Out"

            self.loopChance = 0.1
            self.bounceChance = 0.2

        def _move_to_any_of(self, edges):
            self.previous_edge = self.edge
            self.edge = random.choice(edges)

        def _node_incoming_and_outgoing(self, model):
            nodes = model.edges[self.edge]
            previous_nodes = model.edges[self.previous_edge]
            from_node = (n for n in nodes if n in previous_nodes).next()
            to_node = (n for n in nodes if n != from_node).next()
            return (from_node, to_node)

        def _maybe_loop(self, height):
            if random.random() < self.loopChance:
                if self.motion == 'Out' and height == 4:
                    self.motion = 'Loop'
                elif self.motion == 'In' and height == 5:
                    self.motion = 'Loop'
                elif self.motion == 'Loop' and height == 5:
                    self.motion = 'Out'
                elif self.motion == 'Loop' and height == 4:
                    self.motion = 'In'

        def _maybe_bounce(self, model, params):
            if random.random() < self.bounceChance:
                if self.motion == 'Out':
                    self.motion = 'In'
                    self.move(model, params)
                elif self.motion == 'In':
                    self.motion = 'Out'
                    self.move(model, params)
                else:
                    print "Broken"
                    self.dead = True
                return True

        def _loop_edges(self, to_edges, model):
            in_node, out_node = self._node_incoming_and_outgoing(model)
            out_edges = (e for e in model.edgeListForNodes[out_node] if e != self.edge)
            return [ e for e in out_edges if model.addressMatchesAnyP(model.addressForEdge[e], ["*.*.*.*.*", "*.*.*.*.1.2", "*.*.*.*.2.1"]) ]

        def _possible_moves(self, model, height):
            to_edges = model.edgeAdjacency[self.edge]
            if self.motion == 'Loop':
                return self._loop_edges(to_edges, model)
            elif self.motion == 'Out':
                return [ e for e in to_edges if model.edgeHeight[e] > height ]
            elif self.motion == 'In':
                return [ e for e in to_edges if model.edgeHeight[e] < height ]

        def move(self, model, params):
            height = model.edgeHeight[self.edge]
            self._maybe_loop(height)

            to_edges = self._possible_moves(model, height)

            if to_edges:
                self._move_to_any_of(to_edges)
            else:
                if not self._maybe_bounce(model, params):
                    self.dead = True

        def render(self, model, params, frame):
            numpy.add( frame[self.edge], self.color, frame[self.edge] )

    def __init__(self, respond_to = 'attention', maximum_pulse_count = 40):
        super(ImpulseLayer2,self).__init__(respond_to)
        self.pulses = []
        self.maximum_pulse_count = maximum_pulse_count
        self.last_time = None

        # these are adjustable
        self.frequency = 0.05 # seconds
        self.spawnChance = 0.25
        self.maxColorSaturation = 0.25
        self.brightness = 0.95

    def _move_pulses(self, model, params):
        if not self.last_time:
            self.last_time = params.time
            return
        if params.time < self.last_time + self.frequency:
            return
        self.last_time = params.time

        for pulse in self.pulses:
            pulse.move(model, params)

        self._reap_pulses(model, params)
        self._spawn_pulses(model, params)

    def _reap_pulses(self, model, params):
        for i in reversed(range(len(self.pulses))):
            if self.pulses[i].dead:
                del(self.pulses[i])

    def _spawn_pulses(self, model, params):
        while True:
            if len(self.pulses) >= self.maximum_pulse_count:
                return
            if random.random() > self.spawnChance:
                return
            if self.maxColorSaturation:
                hue = random.random()
                saturation = random.random() * self.maxColorSaturation
                value = self.brightness
                color = numpy.array(colorsys.hsv_to_rgb(hue, saturation, value))
            else: # optimization for saturation 0
                color = numpy.repeat(self.brightness, 3)

            self.pulses.append(ImpulseLayer2.Impulse(color, random.choice(model.roots)))

    def render_responsive(self, model, params, frame, response_level):
        if response_level != None:
            self.spawnChance = response_level * 0.95 # gets much more intense
            self.maxColorSaturation = response_level * 0.50 # gets a little more colory

        self._move_pulses(model, params)
        for pulse in self.pulses:
            pulse.render(model, params, frame)
