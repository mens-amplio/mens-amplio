#!/usr/bin/env python

try:
  import smbus
except ImportError, e:
  # This package may not exist. Can still use FakeFlameBoard.
  pass

class FlameBoard(object):
    """
    Represents a flame effect driver board. Assumes board is
    configured to interpret each incoming byte as the index of a relay to be
    toggled (with the exception of 0xF which is treated as a signal to 
    turn all solenoids off).
    
    This class's public methods take index arguments in the range 
    range[0, len(solenoids)]. This class handles the translation between those
    indices and the indices of the actual relays that are being used.
    
    Note that the relays are labeled with 1-based indexing on the physical board,
    but 0-based indexing is used everywhere in the code (both here and on the
    Atmega chip) for simplicity/consistency.
    """
    
    # there are 16 relays on the board, but one index is being repurposed as an all-off signal
    maxSolenoids = 15 
    
    def __init__(self, solenoids):
        # solenoids argument is a list of the relays on the board that are connected
        # to actual solenoids
        self.solenoids = list(set(solenoids)) # remove duplicates
        if min(self.solenoids) < 0:
            raise Exception("Negative solenoid index in FlameBoard constructor")
        if max(self.solenoids) >= self.maxSolenoids:
            raise Exception("Above-max solenoid index in FlameBoard constructor")
    
    def getSolenoids(self, indices):
        # Takes a set of indices in the range [0,len(solenoids)] and converts them to
        # connected solenoid indices. Out-of-range indices are dropped.
        cnt = len(self.solenoids)
        return [ self.solenoids[i] for i in indices if i >= 0 and i < cnt ]
        
    def toggle(self, indices):
        # Sends command to toggle a set of solenoids. Returns the number that
        # were actually toggled (invalid indices excluded)
        raise NotImplementedError("Implement toggle in flameboard subclass")
    
    def all_off(self, throw_io_error=False):
        # Closes all solenoids
        raise NotImplementedError("Implement all_off in flameboard subclass")
    
    
class FakeFlameBoard(FlameBoard):
    """ For testing when hardware isn't connected """
    def __init__(self, solenoids):
        super(FakeFlameBoard, self).__init__(solenoids)
    
    def toggle(self, indices):
        solenoids = self.getSolenoids(indices)
        print "Toggling solenoids:", solenoids
        return solenoids
    
    def all_off(self, throw_io_error=False):
        print "all off"

        
class I2CFlameBoard(FlameBoard):
    """ Manages data transmission to WiFire board over I2C. """
    
    writeCommand = 0x02; # value of linux's #define I2C_FUNC_SMBUS_WRITE_BLOCK_DATA
    allOffCommand = [0xF]
    
    def __init__(self, solenoids):
        super(I2CFlameBoard, self).__init__(solenoids)
    
    def __init__(self, address=0x04):
        self.bus = smbus.SMBus(1)
        self.address = address # must match address in atmega code
        
    def toggle(self, indices):
        solenoids = self.getSolenoids(indices)
        count = len(solenoids)
        if count:
            self.bus.write_block_data(self.address, self.writeCommand, solenoids)
        return count
        
    def all_off(self, throw_io_error=False):
        try:
            self.bus.write_block_data(self.address, self.writeCommand, self.allOffCommand )
        except IOError:
            if throw_io_error: raise
            else: pass

            
# for debugging
if __name__ == '__main__':
    solenoids = range(8,14)
    fb = FakeFlameBoard(solenoids)
    range_str = "Enter comma-delimited inputs 0 - " + str(len(solenoids)-1) + ": "
    while True:
        try:
            nums = map(int, raw_input(range_str).split(','))
            fb.toggle(nums)
        except KeyboardInterrupt:
            fb.all_off()
            raise

