#!/usr/bin/env python

import smbus

class FlameBoard:
    """
    Manages data transmission to WiFire board over I2C. Assumes that board is
    configured to interpret each incoming byte as the index of a relay to be
    toggled (with the exception of 0xF which is treated as a signal to 
    turn all solenoids off)
    """
    def __init__(self):
        self.write_command = 0x02; # value of linux's #define I2C_FUNC_SMBUS_WRITE_BLOCK_DATA
        # max allowed on board is 16 (15 if 0xf is used as all-off
        # signal), but we are only using 6.
        self.numSolenoids = 6 
        self.bus = smbus.SMBus(1)
        self.address = 0x04 # must match address in atmega code
        
    def toggle(self, indices):
        """
        Sends command to toggle a list of solenoids. Returns the number of indices that
        were sent (excludes invalid ones).
        """
        indices = [ i for i in indices if self.validIndex(i) ]
        count = len(indices)
        if count:
            self.bus.write_block_data(self.address, self.write_command, indices)
        return count
        
    def validIndex(self, index):
        return index >= 0 and index < self.numSolenoids

    def all_off(self, throw_io_error=False):
        """
        Closes all solenoids
        """
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

