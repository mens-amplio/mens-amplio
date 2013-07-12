#!/usr/bin/env python

import smbus

class FlameBoard:
    """
    Manages data transmission to WiFire board over I2C
    """
    def __init__(self):
        self.write_command = 0x02; # value of linux's #define I2C_FUNC_SMBUS_WRITE_BLOCK_DATA
        self.numSolenoids = 6 # max allowed on board is 16, but we are only using 6
        self.bus = smbus.SMBus(1)
        self.address = 0x04 # must match address in atmega code
        
    def toggle(self, index):
        """
        Sends command to toggle a solenoid. Returns success/failure.
        """
        if self.validIndex(index):
            self.bus.write_byte(self.address, index)
            return True
        return False
            
    def toggleMultiple(self, indices):
        """
        Sends command to toggle multiple solenoids at once. Returns the number of indices that
        were sent (excludes invalid ones).
        """
        indices = [ i for i in indices if self.validIndex(i) ]
        count = len(indices)
        if count:
            self.bus.write_block_data(self.address, self.write_command, indices)
        return count
        
    def validIndex(self, index):
        return index >= 0 and index < self.numSolenoids


# for debugging
if __name__ == '__main__':
    fb = FlameBoard()
    range_str = "Enter comma-delimited inputs 0 - " + str(fb.numSolenoids-1) + ": "
    while True:
        nums = map(int, raw_input(range_str).split(','))
        if len(nums) > 1:
            print fb.toggleMultiple(nums)
        elif len(nums) == 1:
            print fb.toggle(nums[0])
    

        
