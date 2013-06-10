#!/usr/bin/python

'''A simple program to test your attention

Prints a different message based on your current attention level.

I have found that if I stare fixed at the output, my attention stays
medium-to-high. If I move my eyes around for a few seconds and look back,
it pretty reliably tells me I'm not paying attention.

Not bad...
'''

from mindwave import Headset

h = Headset()
while True:
  point = h.readDatapoint()
  print "-----------------------------------"
  if not point.headsetOnHead():
    print "Haven't established a sound connection yet..."
    print "If this keeps up, adjust the headset on your head"
  elif point.attention > 70:
    print "You're paying super close attention!"
  elif point.attention < 30:
    print "HEY YOU -- quit daydreaming"
  else:
    print "You're sorta kinda paying attention..."
  print "-----------------------------------"
