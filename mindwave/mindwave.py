'''Classes and tools for interacting with the NeuroSky Mindwave Mobile headset.

Headset:
  Connects over bluetooth to a mac address given to it, and when asked pulls
  bytes and interpreting them per the NeuroSky/ThinkGear protocol. The
  measurements pulled are stored in a Datapoint.
Datapoint:
  Container for the attention, meditation, and brainwave measurements
  from the headset. Also handles parsing the measurements by code.

Details of the communications protocol can be found here:
  http://wearcam.org/ece516/mindset_communications_protocol.pdf
'''

try:
  import bluetooth
  import dbus.exceptions
except ImportError, e:
  # This package may not exist on mac. Can still use FakeHeadset.
  pass
import datetime
import logging
import time
import random


LOGGING_LEVEL = logging.INFO
logging.basicConfig(level=LOGGING_LEVEL, format='%(message)s')

# We have two headsets, choose the right mac address
HEADSET1 = '74:E5:43:B1:93:D5'
HEADSET2 = '74:E5:43:D5:78:CD'
ALL_HEADSET_MAC_ADDRS = [HEADSET1, HEADSET2]

# Byte codes from Neurosky
SYNC                 = 0xAA
POOR_SIGNAL          = 0x02
ATTENTION            = 0x04
MEDITATION           = 0x05
BLINK                = 0x16
RAW                  = 0x80
EEG_WAVES            = 0x83

# Wave values are sent in a special 'EEG' data row that has all the values
# concatenated together, in the following order.
WAVE_NAMES_IN_ORDER = [
  'delta', 'theta', 'alpha_low', 'alpha_high',
  'beta_low', 'beta_high', 'gamma_low', 'gamma_mid']

class Datapoint():
  def __init__(self):
    # Timestamp of this script when it started reading this datapoint
    self.timestamp = time.time()
    # We get about one datapoint per second from the headset,
    # but about 512 raw voltage measurements.
    # Raw datapoints are 16-bit signed integers, (-32768, 32767)
    self.raw_voltages = []
    # Values, 1-100 computed by the headset's mysterious algorithms
    self.attention = None
    self.meditation = None
    # Strength of blink detected, if any (0-255)
    # We don't always read a blink, so by default this is 0 for "no blink"
    self.blink = 0
    # Indicates how poor the signal is (0-200) where 200 means it believes
    # the headset is not on anyone's head
    self.poor_signal = None
    # 8 kinds of brainwaves (likely correspond to frequency bands)
    # Each is a 3-byte unsigned integer, so theoretically 0-16,777,215
    for name in WAVE_NAMES_IN_ORDER:
      setattr(self, name, None)

  def updateValues(self, code, values):
    if code == POOR_SIGNAL:
      self.poor_signal = values[0]
    elif code == ATTENTION:
      self.attention = values[0]
    elif code == MEDITATION:
      self.meditation = values[0]
    elif code == BLINK:
      self.blink = values[0]
    elif code == EEG_WAVES:
      for i, wave in enumerate(WAVE_NAMES_IN_ORDER):
        setattr(self, wave, self.computeWaveValue(values[:3]))
        values = values[3:]
    elif code == RAW:
      raw = (values[0] << 8) + values[1]
      # This should be interpreted as a signed value, so if
      # the highest bit is 1, evaluate as two's complement
      if raw & 0x8000:
        raw = raw - 0xFFFF
      self.raw_voltages.append(raw)
    else:
      logging.error("Unknown code received from headset: %d" % code)

  def computeWaveValue(self, values):
    '''Given an array of 3 bytes in little endian, convert to an integer'''
    # First byte is least significant, third is most significant
    return (values[2] << 16) | (values[1] << 8) | values[0]

  def headsetOnHead(self):
    '''Returns True if the headset is being worn correctly.'''
    return self.poor_signal < 200

  def headsetDataReady(self):
    '''Returns True if the headset is producing data that we can read.'''
    return self.attention > 0

  def complete(self):
    return (self.attention != None and
            self.meditation != None and
            self.poor_signal != None and
            getattr(self, WAVE_NAMES_IN_ORDER[0]) != None)

  def __str__(self):
    dt = datetime.datetime.fromtimestamp(self.timestamp)
    timestr = dt.strftime("%Y-%m-%d %H:%M:%S")
    lines = ["***** Datapoint %s *****" % timestr]
    lines.append("* Headset %sWORN CORRECTLY" %
                 ('' if self.headsetOnHead() else 'NOT '))
    lines.append("* Headset DATA %sREADY" %
                 ('' if self.headsetDataReady() else 'NOT '))
    lines.append("* Poorness of signal (0-200):\t%d" % self.poor_signal)
    lines.append("* Attention (1-100):\t%d" % self.attention)
    lines.append("* Meditation (1-100):\t%d" % self.meditation)
    lines.append("* Blink (0-255):\t%d" % self.blink)
    lines.append("* Raw datapoints recorded:\t%d" % len(self.raw_voltages))
    for wave in WAVE_NAMES_IN_ORDER:
      lines.append("* Wave %s (0-16MM):\t%d" % (wave, getattr(self, wave)))
    lines.append("*" * 40)
    return "\n".join(lines)

class Headset:
  """
  Abstract base class for connecting and reading datapoints
  from a Neurosky headset
  """
  def connect(self):
    """
    Connects to the physical headset to begin receiving data
    """
    raise NotImplementedError("Implement in Headset child class")
  
  def disconnect(self):
    """
    Close connection to headset
    """
    raise NotImplementedError("Implement in Headset child class")
  
  def readDatapoint(self, wait_for_clean_data=False):
    """
    Returns a DataPoint object filled with a datapoint received from the headset.
    If headset is not connected, opens connection prior to waiting for data. Blocks until
    a datapoint is received (or, if wait_for_clean_data is true, a clean datapoint is received).
    If connection is lost mid-transmission, returns nothing.
    """
    raise NotImplementedError("Implement in Headset child class")
    
    
    
class FakeHeadset(Headset):
  """
  Emulator class to use during development. Returns datapoints filled with fake
  values at 1sec intervals. Does not actually connect to anything. Does not
  emulate raw data.
  """
  
  # used when generating random values
  am_sd = 20
  am_min = 1
  am_max = 100
  
  # used when generating non-random values
  am_high = 90
  am_low = 10
  
  # used when generating bad data
  on_time = 16
  off_time = 8
  
  def __init__(self, bad_data=False, random_data=False, mean = 50):
    """
      If bad_data is true, poor_signal will flip between 0 and 200 periodically.
      It will otherwise always be 0. 
      
      If random_data is true, attention and meditation values are randomly 
      sampled from a normal distribution (with given mean). If false, they both flip
      between 10 and 90 when poor_signal==0 to allow easy assessment of behavior at extremes.
    """
    self.connected = False
    self.bad_data = bad_data
    self.cnt = 0
    self.am_mean = mean
    self.random_data = random_data
    self.start = time.time()
    self._reset_spoofed_values()
    
  def connect(self):
    self.connected = True
    logging.info("Connected to imaginary headset!")
    
  def disconnect(self):
    self.connected = False
    logging.info("Disconnected from imaginary headset!")
    
  def _new_response_values(self, high_first=False):
      # high_first parameter is only used when self.random_data is false - controls whether
      # high values occur before low ones
      seq = [0] * 5
      def int_constrain(x, minx = self.am_min, maxx = self.am_max):
          return int( min( max(minx,x), maxx ) )
      if self.random_data:
        seq.extend([ int_constrain( random.gauss(self.am_mean, self.am_sd) ) for x in range(self.on_time) ])
      else:
        def add_high(s):
            seq.extend([self.am_high] * (self.on_time/2))
        def add_low(s):
            seq.extend([self.am_low] * (self.on_time - self.on_time/2))
        if high_first:
            add_high(seq)
            add_low(seq)
        else:
            add_low(seq)
            add_high(seq)
      seq.extend([ int_constrain( random.gauss(self.am_mean, self.am_sd) ) for x in range(5) ])
      seq.extend([0] * self.off_time)
      return seq
    
  def _reset_spoofed_values(self):
      self.cnt = 0
      seq = [ 120, 80, 40, 20, 20 ]
      rseq = seq[::-1]
      seq.extend([0] * self.on_time)
      seq.extend(rseq)
      seq.extend([200] * self.off_time)
      self.poor_signal = seq
      high_first = random.random() < 0.5
      self.attention = self._new_response_values(high_first)
      self.meditation = self._new_response_values(high_first)
      assert(len(self.attention)==len(self.poor_signal))
    
  def readDatapoint(self, wait_for_clean_data=False):
    if not self.connected:
      logging.info("Not connected to headset. Connecting now....")
      self.connect()
    while True:
      time.sleep(1)
      datapoint = Datapoint()
      if self.cnt >= len(self.poor_signal):
          self._reset_spoofed_values()
      datapoint.poor_signal = self.poor_signal[self.cnt]
      datapoint.attention = self.attention[self.cnt]
      datapoint.meditation = self.meditation[self.cnt]
      datapoint.blink = 0
      for name in WAVE_NAMES_IN_ORDER:
        setattr(datapoint, name, random.randint(0,1<<23))
      logging.debug(datapoint)
      self.cnt = self.cnt + 1
      if wait_for_clean_data and not datapoint.headsetDataReady():
        logging.info("Headset not on with clear communciation.")
      else:
        return datapoint


class BluetoothHeadset(Headset):
  """
  Represents Mindwave Mobile headset that sends data over Bluetooth
  """
    
  def __init__(self, macaddrs=ALL_HEADSET_MAC_ADDRS):
    self.macaddrs = ALL_HEADSET_MAC_ADDRS
    self.socket = None

  def connect(self):
    addrs = self.macaddrs
    if type(self.macaddrs) != list:
      addrs = [self.macaddrs]
    index = 0
    while True:
      try:
        a = addrs[index]
        logging.info("Attempting to connect to headset #%d at %s..." % (
          (index + 1), a))
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.socket.connect((a, 1))
        logging.info("...connected!")
        return
      except bluetooth.BluetoothError, e:
        logging.error("...failed to connect to headset. "
                      "Error: %s" % str(e))
        if index == len(addrs) - 1:
          logging.error("Will retry in 5s")
          time.sleep(5)
        index = (index + 1) % len(addrs)

  def disconnect(self):
    logging.info("Disconnecting...")
    self.socket.close()
    logging.info("...disconnected from headset.")

  def readDatapoint(self, wait_for_clean_data=False):
    try:
      if not self.socket:
        logging.info("Not connected to headset. Connecting now....")
        self.connect()
      while True:
        datapoint = Datapoint()
        while not datapoint.complete():
          # The Mindwave transmits a series of "packets", each one only containing
          # some of the measurements. We need to keep reading packets until we
          # have all the measurements of one complete Datapoint.
          payload = self.readOnePacket()
          if payload is None:
            # Error reading packet
            logging.error("Dropping packet")
            continue
          logging.debug("Read payload of size %d" % len(payload))
          # Each packet's payload is a series of "data rows" that must be parsed.
          # A "data row" has one of the many possible measurements. A packet may
          # only contain rows for a subset of the measurements.
          while payload:
            payload, code, values = self.pullOneDataRow(payload)
            datapoint.updateValues(code, values)
        if wait_for_clean_data and not datapoint.headsetDataReady():
          logging.info(
              "Datapoint not clean (either headset is not on properly, or "
              "bluetooth is just warming up). If this keeps up "
              "for more than ~10s, adjust the headset on your head.")
        else:
          break
      logging.debug(datapoint)
      return datapoint
    # Not completely sure and can't replicate, but I think the DBusException is the 
    # "111 Bluetooth connection refused" exception we saw during a long test run
    except (bluetooth.BluetoothError, dbus.exceptions.DBusException) as e:
      logging.error("Bluetooth error interacting with headset: %s" % str(e))
      return None
      
  def readOnePacket(self):
    while not (self.readByte() == SYNC and self.readByte() == SYNC):
      logging.debug("Reading bytes until we get to the start of a packet...")
    logging.debug("Found double-sync byte, starting a new packet read.")
    plen = self.readByte()
    if plen > 169:  # Theoretical maximum size, according to datasheet
      logging.error("Bad packet length. Max is 169, received %d." % plen)
      return None
    payload = self.readBytes(plen)
    checksum = self.readByte()
    computed_checksum = self.computeChecksum(payload)
    if checksum != computed_checksum:
      logging.error("Bad checksum. Expected %d, computed %d." % (
          checksum, computed_checksum))
      return None
    logging.debug("Checksum OK (%d)" % checksum)
    return payload

  def computeChecksum(self, data):
    s = sum(data)  # Sum up bytes
    s &= 0xFF  # Take the last 8 bits (e.g. mod by 256)
    return 0xFF - s  # Invert bits

  def pullOneDataRow(self, payload):
    code = payload[0]
    if code <= 0x7F:  # Single-byte value
      num_value_bytes = 1
      payload = payload[1:]
    else:
      num_value_bytes = payload[1]
      payload = payload[2:]
    values = payload[:num_value_bytes]
    payload = payload[num_value_bytes:]
    return payload, code, values

  # Actual socket-using methods below

  def readByte(self):
    '''Reads a single byte as an integer 0-255'''
    return self.readBytes(1)[0]

  def readBytes(self, numbytes):
    '''Reads the requested number of bytes from the headset.

    Returns an array of integers, each in the 0-255 range
    '''
    # Sometimes the socket will not send all the requested bytes
    # on the first request, therefore a loop is necessary...
    missingBytes = numbytes
    received = ""
    while(numbytes > 0):
        received += self.socket.recv(numbytes)
        numbytes = numbytes - len(received)
    # Python represents all bytes as strings. A raw byte (a number 0-255)
    # is represented as something between '\x00' and '\xFF', not unlike
    # chars in C or C++. socket.recv returns a string that is the
    # concatenation of all bytes. For example, if it received 0x22 then 0x33,
    # it would return '\x22\x33'.
    # The 'ord' builtin converts raw bytes to integers,
    # e.g. '\x12' becomes 18 (or equivalently 0x12)
    return [ord(b) for b in received];

class FileHeadset(Headset):
  connected = False
  def connect(self):
    self.connected = True
    logging.info("Connected to filesystem headset!")
    
  def disconnect(self):
    self.connected = False
    logging.info("Disconnected from filesystem headset!")

  def _read(self, name):
    value = 50
    try:
        for line in open(name, 'r'):
            value = int(line)
    except IOError:
        pass
    return value

  def readDatapoint(self, wait_for_clean_data=False):
    if not self.connected:
      logging.info("Not connected to headset. Connecting now....")
      self.connect()
    time.sleep(1)
    datapoint = Datapoint()
    datapoint.poor_signal = 0
    datapoint.attention = self._read("attend")
    datapoint.meditation = self._read("meditate")
    datapoint.blink = 0
    for name in WAVE_NAMES_IN_ORDER:
      setattr(datapoint, name, random.randint(0,1<<23))
    return datapoint
