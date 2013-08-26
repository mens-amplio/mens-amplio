import threading
import time
import sys
import random
from flameboard import I2CFlameBoard, FakeFlameBoard
from collections import defaultdict
from itertools import combinations


class FlameEvent:
    """
    Represents the opening and closing of a solenoid at a given index. Start
    (relative to beginning of containing sequence) and duration are both 
    in millseconds.
    """
    def __init__(self, index, start, duration):
        self.index = index
        self.start = start
        self.duration = duration
        self.end = start + duration

    def __str__(self):
        return "#" + str(self.index) + " (" + str(self.start) + "-" + str(self.end) + ")"

    def collides(self, other):
        """
        Whether two events are trying to fire the same solenoid at the same time
        """
        return other.index == self.index and ( 
            min(self.end, other.end) - max(self.start, other.start) >= 0
            )


class FlameSequence:
    """
    A sequence of flame events to be displayed together. Checks for event 
    collisions and extracts the timepoints where solenoids need to be toggled.
    """
    def __init__(self, events):
        self.events = events
        self.toggle_times = defaultdict(list)
        
        # check for collisions
        for c in combinations(events, 2):
            if FlameEvent.collides(*c):
                raise Exception("Collision between " + str(c[0]) + " and " + str(c[1]) )

        for e in events:
            # create dictionary of event times -> indices to be toggled
            self.toggle_times[e.start].append(e.index)
            self.toggle_times[e.end].append(e.index)


class SyncedBursts(FlameSequence):
    """
    Fire all poofers in unison in a series of bursts
    """
    def __init__(self, num_solenoids, burst_duration, ibi, reps):
        """
        num_solenoids: toggle all indices in range(num_solenoids)
        burst_duration: in milliseconds
        ibi: inter-burst interval (beween end of one and start of next), in ms
        reps: how many bursts
        """
        events = [ FlameEvent(i, (ibi+burst_duration)*r, burst_duration) for i in range(num_solenoids) for r in range(reps) ]
        FlameSequence.__init__(self, events)


class SequentialBursts(FlameSequence):
    """
    Fires the solenoids one at a time in a random sequence.
    """
    def __init__(self, num_solenoids, burst_duration, reps):
        indices = range(num_solenoids)
        random.shuffle(indices)
        events = [ FlameEvent(indices[i], burst_duration*(r*num_solenoids+i), burst_duration) for i in range(num_solenoids) for r in range(reps) ]
        FlameSequence.__init__(self,events)


def RunSequence(seq, board):
    start_time = time.time()
    for i in sorted(seq.toggle_times.items()):
        time_secs = float(i[0])/1000 + start_time;
        while time.time() < time_secs:
            time.sleep(0.1)
        failures = 0
        while failures < 3:
            try:
                board.toggle( i[1] )
                break;
            except IOError:
                sys.stderr.write( "Flame board transmission failed, retrying...\n" )
                failures += 1
        if failures >= 3:
            sys.stderr.write( "Transmission to flame board failed. Terminating sequence.\n" )
            break
    time.sleep(0.25)
    board.all_off() #just in case
    time.sleep(0.05) #to ensure the flame board is done processing this before we start another sequence


if __name__ == '__main__':
    solenoids = range(8, 14)
    board = I2CFlameBoard(solenoids)
    RunSequence(SequentialBursts(6, 250, 3), board)
    time.sleep(0.5)
    RunSequence(SyncedBursts(6, 250, 500, 5), board)
