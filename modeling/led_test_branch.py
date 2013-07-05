#!/usr/bin/env python
import opc_client
import json
import sys

# Tests the semantic mapping of LEDs from manual.remap.json
# Usage: ./led_test_branch.py manual.remap.json *.1.1.1 127.0.0.1:7890

remap_data = json.load(open(sys.argv[1]))
target = sys.argv[2]
server = sys.argv[3] if len(sys.argv) > 3 else '127.0.0.1:7890'

def matches(target, addr, partial = False):
  target_parts = target.rsplit('.')
  addr_parts = addr.rsplit('.')
  for target_part, addr_part in zip(target_parts, addr_parts):
    if target_part != '*' and target_part != addr_part:
      return False
  if len(target_parts) == len(addr_parts):
    return True
  if len(target_parts) < len(addr_parts):
    return partial
  return False


exact_matching_addresses = [addr for addr in remap_data if matches(target,addr)]
child_matching_addresses = [addr for addr in remap_data if matches(target,addr, True) and addr not in exact_matching_addresses]
parent_matching_addresses = [addr for addr in remap_data if [True for exact in exact_matching_addresses if matches(addr, exact, True)] and not addr in exact_matching_addresses]

#print(exact_matching_addresses)
#print(child_matching_addresses)
#print(parent_matching_addresses)

exact_matching_leds = [ int(remap_data[addr]) for addr in exact_matching_addresses ]
#print(exact_matching_leds)
child_matching_leds = [ int(remap_data[addr]) for addr in child_matching_addresses ]
parent_matching_leds = [ int(remap_data[addr]) for addr in parent_matching_addresses ]
#print(parent_matching_leds)

pixel_count = max([int(remap_data[k]) for k in remap_data ]) + 1

pixels = [(0,0,0)] * pixel_count

for n in exact_matching_leds:
  pixels[n] = (255,255,255)

for n in child_matching_leds:
  pixels[n] = (0,255,100)

for n in parent_matching_leds:
  pixels[n] = (255,0,0)

socket = opc_client.get_socket(server)
opc_client.put_pixels(socket, 0, pixels)
