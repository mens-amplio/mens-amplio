#!/usr/bin/env python

# Input: a file similar to curve_endpoints.txt or rod_endpoints.txt
# whose structure is a list of point pairs
# where each half of a point pair is its own list (of form [x,y,z]

# Output: a mapping of that file
# where point pairs are replaced by semantic info about the rod's visual level,
# its parent rod's address
# and the addresses of its children.

import sys
import json

# Debugging imports
from q import q
from pprint import pprint

args = sys.argv[1:]
infile = None

try:
    infile = open(args[0], 'r')
except:
    print "No source file was provided."
    exit()

infile_points, output_rods = [], []
infile_points = json.load(infile)

pprint(infile_points)
# parse the input file
#for pair in infile_points:
#    q(pair)