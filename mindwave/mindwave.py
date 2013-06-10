'''Classes and tools for interacting with the NeuroSky Mindwave Mobile headset

Example usage:

from headset import Headset

headset = Headset()
point = headset.readDatapoint()
print point.attention
print point.wave_delta
print "Was the headset being worn?", point.headsetOnHead()

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

import bluetooth
import datetime
import logging
import time


LOGGING_LEVEL = logging.INFO
logging.basicConfig(level=LOGGING_LEVEL, format='%(message)s')

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

DATAPOINT_PRINT_FORMAT = '''
Datapoint %(timestr)s
---
Attention: %(attention)s
Meditation: %
'''

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

  def clean(self):
    '''Determine if the data was taken reliably and with the headset worn.'''
    return self.poor_signal < 200 and self.attention > 0

  def complete(self):
    return (self.attention != None and
            self.meditation != None and
            self.poor_signal != None and
            getattr(self, WAVE_NAMES_IN_ORDER[0]) != None)

  def __str__(self):
    dt = datetime.datetime.fromtimestamp(self.timestamp)
    timestr = dt.strftime("%Y-%m-%d %H:%M:%S")
    lines = ["***** Datapoint %s *****" % timestr]
    lines.append("* Poorness of signal (0-200):\t%d" % self.poor_signal)
    lines.append("* Attention (1-100):\t%d" % self.attention)
    lines.append("* Meditation (1-100):\t%d" % self.meditation)
    lines.append("* Blink (0-255):\t%d" % self.blink)
    lines.append("* Raw datapoints recorded:\t%d" % len(self.raw_voltages))
    for wave in WAVE_NAMES_IN_ORDER:
      lines.append("* Wave %s (0-16MM):\t%d" % (wave, getattr(self, wave)))
    lines.append("*" * 40)
    return "\n".join(lines)


class Headset():
  def __init__(self, macaddr='74:E5:43:B1:93:D5'):
    self.macaddr = macaddr
    self.socket = None

  def connect(self):
    logging.info("Attempting to connect to headset at %s" % self.macaddr)
    while True:
      try:
        logging.info("Connecting...")
        self.socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        self.socket.connect((self.macaddr, 1))
        logging.info("...connected!")
        return
      except bluetooth.BluetoothError, e:
        logging.error("...failed to connect to headset(will retry in 5s). "
                      "Error: %s" % str(e))
        time.sleep(5)

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
        if wait_for_clean_data and not datapoint.clean():
          logging.info(
              "Datapoint not clean (either headset is not on properly, or "
              "bluetooth is just warming up). If this keeps up "
              "for more than ~10s, adjust the headset on your head.")
        else:
          break
      logging.debug(datapoint)
      return datapoint
    except bluetooth.BluetoothError, e:
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
