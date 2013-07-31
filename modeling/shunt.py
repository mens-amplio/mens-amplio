#!/usr/bin/env python
import sys
import json
import math

skip_addresses = []
skip_leds = []

skip_addresses = [str(x) for x in skip_addresses]

f = open(sys.argv[1])
mapping = json.load(f)

for address in skip_addresses:
  skip_leds.append(mapping[address])

# try to make this stupid-proof to save our addled playa brains
skip_leds = [led for led in set(skip_leds)]
skip_leds.sort()
skip_leds.reverse()

last_led = max(mapping.values())

replace_skipped = {old:new for old,new in zip(skip_leds,range(last_led,0,-1))}

new_mapping = {}
for address, led in mapping.items():
  if led in replace_skipped:
    new_mapping[address] = replace_skipped[led]
  else:
    for skip in skip_leds:
      if skip < led:
        led -= 1
    new_mapping[address] = led

print(json.dumps(new_mapping, sort_keys=True, indent=4, separators=(',', ': ')))
