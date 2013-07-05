#!/usr/bin/env python
from __future__ import division
import time
import math
import sys
import itertools
import colorsys

import opc_client

#-------------------------------------------------------------------------------
# handle command line

if len(sys.argv) == 1:
    IP_PORT = '127.0.0.1:7890'
elif len(sys.argv) == 2 and ':' in sys.argv[1] and not sys.argv[1].startswith('-'):
    IP_PORT = sys.argv[1]
else:
    print
    print '    Usage: led_rainbow_snake_test.py [ip:port]'
    print
    print '    If not set, ip:port defauls to 127.0.0.1:7890'
    print
    sys.exit(0)


#-------------------------------------------------------------------------------
# connect to server

print
print '    connecting to server at %s' % IP_PORT
print

SOCK = opc_client.get_socket(IP_PORT)


#-------------------------------------------------------------------------------
# send pixels

print '    sending pixels forever (control-c to exit)...'
print

n_pixels = 255 # TODO: command line this

snake_length = 20
snake_head = 0
fps = 2

for tick in itertools.count():
    pixels = []
    for index in range(n_pixels):
        snake_pos = snake_head - index

        hue = 0
        saturation = 0
        value = 0

        if snake_pos >= 0 and snake_pos < snake_length:
          hue = (5.0/6.0) * snake_pos / snake_length
          saturation = 1
          value = 1

        r, g, b = map(lambda x:opc_client.remap(x,0.0,1.0,0,255), colorsys.hsv_to_rgb(hue, saturation, value))

        pixels.append((r, g, b))
    opc_client.put_pixels(SOCK, 0, pixels)
    time.sleep(1 / fps)
    snake_head += 1
    if snake_head + snake_length > n_pixels:
      snake_head = 0
