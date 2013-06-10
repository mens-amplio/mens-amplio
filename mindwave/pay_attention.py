#!/usr/bin/python

'''A simple program to test your attention

Prints a different message based on your current attention level.

I have found that if I stare fixed at the output, my attention stays
medium-to-high. If I move my eyes around for a few seconds and look back,
it pretty reliably tells me I'm not paying attention.

...a second trial of this was far less reliable and I couldn't seem to
control it. Unclear how much we can do with this.
'''

from mindwave import Headset

h = Headset()
while True:
  point = h.readDatapoint(wait_for_clean_data=True)
  print "-----------------------------------"
  elif point.attention > 70:
    print "You're paying super close attention!"
  elif point.attention < 30:
    print "HEY YOU -- quit daydreaming"
  else:
    print "You're sorta kinda paying attention..."
  print "-----------------------------------"
