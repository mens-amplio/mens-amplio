import random

class Playlist:
    """ 
    A list of routines (aka a list of light effect layer lists, or a list of
    flame sequences) all intended for use in a single context (e.g. when the 
    headset is on). One routine in the playlist is selected at any given time.
    """
    def __init__(self, routines, index = 0, shuffle=False):
            
        self.routines = routines
        self.selected = index
        self.order = range(len(self.routines))
        self.shuffle = shuffle
        if shuffle:
            random.shuffle(self.order)
            
    def selection(self):
        return self.routines[self.order[self.selected]]
            
    def advance(self):
        # Switch the selected routine to the next one in the list, either
        # consecutively or randomly depending on whether shuffle is true
        if len(self.routines) > 1:
            selected = self.selected + 1
            if selected >= len(self.routines):
                if self.shuffle:
                    random.shuffle(self.order)
                selected = 0
            self.selected = selected