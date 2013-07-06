#!/usr/bin/env python
import opc_client
import json
import sys
import time

# Tests the semantic mapping of LEDs from manual.remap.json
# Usage: ./led_display_binary 127.0.0.1:7890

led_count = 256

server = sys.argv[1] if len(sys.argv) > 1 else '127.0.0.1:7890'

colors = {
  128: (255,0,0),      # red
  64:  (205, 140, 0),  # orange
  32:  (255,255,0),    # yellow
  16:  (0,255,0),      # green
  8:   (0,0,255),      # blue
  4:   (111, 0, 255),  # "indigo"
  2:   (128, 0, 128),  # purple
  1:   (255,255,255),  # white
}

socket = opc_client.get_socket(server)

while True:
  for x in reversed(range(8)):
    pixels = [(0,0,0)] * led_count
    bit = 2 ** x
    print(bit)
    color = colors[bit]
    for i in range(led_count):
      if i & bit:
        pixels[i] = color

    opc_client.put_pixels(socket, 0, pixels)
    time.sleep(3)
