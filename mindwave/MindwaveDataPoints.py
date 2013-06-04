   
class DataPoint:
    def __init__(self, dataValueBytes, name):
        self._dataValueBytes = dataValueBytes
        self.value = dataValueBytes[0]
        self.name = name.lower()

    def __str__(self):
        return ": ".join([self.name, str(self.value)])
                
class PoorSignalLevelDataPoint(DataPoint):
    def __init__(self, dataValueBytes):
        DataPoint.__init__(self, dataValueBytes, 'poorsignal')
        self.amountOfNoise = self._dataValueBytes[0];

    def headSetHasContactToSkin(self):
        return self.amountOfNoise < 200;

    def __str__(self):
        poorSignalLevelString = "Poor Signal Level: " + str(self.amountOfNoise)
        if (not self.headSetHasContactToSkin()):
            poorSignalLevelString += " - NO CONTACT TO SKIN"
        return poorSignalLevelString

class AttentionDataPoint(DataPoint):
    def __init__(self, _dataValueBytes):
        DataPoint.__init__(self, _dataValueBytes, 'attention')

class MeditationDataPoint(DataPoint):
    def __init__(self, _dataValueBytes):
        DataPoint.__init__(self, _dataValueBytes, 'meditation')

class BlinkDataPoint(DataPoint):
    def __init__(self, _dataValueBytes):
        DataPoint.__init__(self, _dataValueBytes, 'blink')

class RawDataPoint(DataPoint):
    def __init__(self, dataValueBytes):
        DataPoint.__init__(self, dataValueBytes, 'raw')
        self.value = self._readRawValue()

    def _readRawValue(self):
        firstByte = self._dataValueBytes[0]
        secondByte = self._dataValueBytes[1]
        # TODO(check if this is correct iwth soem more tests..
        # and see http://stackoverflow.com/questions/5994307/bitwise-operations-in-python
        rawValue = firstByte * 256 + secondByte;
        if rawValue >= 32768:
            rawValue -= 65536
        return rawValue # hope this is correct ;)

class EEGPowersDataPoint(DataPoint):
    WAVE_NAMES = "delta,theta,alpha_low,alpha_high,beta_low,beta_high,gamma_low,gamma_mid".split(",")
    def __init__(self, dataValueBytes):
        DataPoint.__init__(self, dataValueBytes, 'eegpowers')
        self._rememberEEGValues();
        
    def _rememberEEGValues(self):
        for i, name in enumerate(EEGPowersDataPoint.WAVE_NAMES):
            setattr(self, name, self._convertToBigEndianInteger(self._dataValueBytes[3*i:(3*(i+1))]))
        # self.delta = self._convertToBigEndianInteger(self._dataValueBytes[0:3]);
        # self.theta = self._convertToBigEndianInteger(self._dataValueBytes[3:6]);
        # self.lowAlpha = self._convertToBigEndianInteger(self._dataValueBytes[6:9]);
        # self.highAlpha = self._convertToBigEndianInteger(self._dataValueBytes[9:12]);
        # self.lowBeta = self._convertToBigEndianInteger(self._dataValueBytes[12:15]);
        # self.highBeta = self._convertToBigEndianInteger(self._dataValueBytes[15:18]);
        # self.lowGamma = self._convertToBigEndianInteger(self._dataValueBytes[18:21]);
        # self.midGamma = self._convertToBigEndianInteger(self._dataValueBytes[21:24]);


    def _convertToBigEndianInteger(self, threeBytes):
        # TODO(check if this is correct iwth soem more tests..
        # and see http://stackoverflow.com/questions/5994307/bitwise-operations-in-python
        # only use first 16 bits of second number, not rest inc ase number is negative, otherwise
        # python would take all 1s before this bit...
        # same with first number, only take first 8 bits...
        bigEndianInteger = (threeBytes[0] << 16) |\
         (((1 << 16) - 1) & (threeBytes[1] << 8)) |\
          ((1 << 8) - 1) & threeBytes[2]
        return bigEndianInteger
        
    def __str__(self):
        s = "EEG Powers:\n"
        for name in EEGPowersDataPoint.WAVE_NAMES:
            s += "\t\t%s: %d\n" % (name, getattr(self, name))
        return s
        # return """EEG Powers:
        #         delta: {self.delta}
        #         theta: {self.theta}
        #         lowAlpha: {self.lowAlpha}
        #         highAlpha: {self.highAlpha}
        #         lowBeta: {self.lowBeta}
        #         highBeta: {self.highBeta}
        #         lowGamma: {self.lowGamma}
        #         midGamma: {self.midGamma}
        #         """.format(self = self)

