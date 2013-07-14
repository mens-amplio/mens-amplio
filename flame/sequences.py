import threading
import time
import sys
from flameboard import FlameBoard
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


class FlameThread(threading.Thread):
    """
    Transmits a flame sequence to the flame effects board
    """
    def __init__(self, sequence):
        threading.Thread.__init__(self)
        self.daemon = True
        self.board = FlameBoard()
        self.sequence = sequence

    def run(self):
        start_time = time.time()
        for i in sorted(self.sequence.toggle_times.items()):
            time_secs = float(i[0])/1000 + start_time;
            while time.time() < time_secs:
                pass
            try:
                self.board.toggleMultiple( i[1] )
            except IOError:
                sys.stderr.write( "Transmission to flame board failed. Terminating sequence.\n" )
                break

if __name__ == '__main__':
    seq = FlameSequence( [
        FlameEvent(0, 0, 50),
        FlameEvent(1, 50, 500),
        FlameEvent(5, 200, 200),
        FlameEvent(2, 25, 75),
        FlameEvent(3, 300, 100),
        FlameEvent(1, 1500, 100),
        ] )
    t = FlameThread(seq)
    t.start()
    t.join()
