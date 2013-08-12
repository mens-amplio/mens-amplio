#!/usr/bin/env python

# import smbus

class FlameBoard:
    """
    Represents a flame effect driver board. Assumes board is
    configured to interpret each incoming byte as the index of a relay to be
    toggled (with the exception of 0xF which is treated as a signal to 
    turn all solenoids off)
    """
    
    # max allowed on our real board is 16 (15 if 0xf is used as all-off
    # signal), but we are only using 6.
    numSolenoids = 6
    
    def getValidIndices(self, indices):
        return [ i for i in indices if i >= 0 and i < self.numSolenoids ]
        
    def toggle(self, indices):
        # Sends command to toggle a list of solenoids. Returns the number of indices that
        # were sent (excludes invalid ones).
        raise NotImplementedError("Implement toggle in flameboard subclass")
    
    def all_off(self, throw_io_error=False):
        # Closes all solenoids
        raise NotImplementedError("Implement all_off in flameboard subclass")
    
    
class FakeFlameBoard(FlameBoard):
    """ For testing when hardware isn't connected """
    def toggle(self, indices):
        indices = self.getValidIndices(indices)
        print "Flame solenoids on:", indices
        return indices
    
    def all_off(self, throw_io_error=False):
        print "all off"

        
class I2CFlameBoard(FlameBoard):
    """ Manages data transmission to WiFire board over I2C. """
    
    write_command = 0x02; # value of linux's #define I2C_FUNC_SMBUS_WRITE_BLOCK_DATA
    
    def __init__(self, address=0x04):
        self.bus = smbus.SMBus(1)
        self.address = address # must match address in atmega code
        
    def toggle(self, indices):
        indices = self.getValidIndices(indices)
        count = len(indices)
        if count:
            self.bus.write_block_data(self.address, self.write_command, indices)
        return count
        
    def all_off(self, throw_io_error=False):
        try:
            self.bus.write_block_data(self.address, self.write_command, [0xF] )
        except IOError:
            if throw_io_error: raise
            else: pass

            
# for debugging
if __name__ == '__main__':
    fb = FlameBoard()
    range_str = "Enter comma-delimited inputs 0 - " + str(fb.numSolenoids-1) + ": "
    while True:
        try:
            nums = map(int, raw_input(range_str).split(','))
            print fb.toggle(nums)
        except KeyboardInterrupt:
            fb.all_off()
            raise

