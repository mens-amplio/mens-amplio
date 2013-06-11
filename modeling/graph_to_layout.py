#!/usr/bin/env python

"""Converts a graph JSON file to an OPC layout file.

A graph JSON file defines an object g with two fields:
  - g.nodes is an object whose values are [x, y, z] triples
  - g.edges is an object whose values are pairs of keys in the g.nodes object

An OPC layout file is a JSON array where each element has one of these forms:
  - {"point": [x, y, z]}
  - {"line": [[x1, y1, z1], [x2, y2, z2]]}
"""

import sys
import json

METRES_PER_UNIT = 0.05  # a length of 1 in the graph file is this many metres

def scale(v):
  return [x*METRES_PER_UNIT for x in v]

args = sys.argv[1:]
if len(args) != 2:
    sys.exit('Usage: %s <input.json> <output.json>' % sys.argv[0])

graph = json.load(open(args[0]))
nodes = dict((int(k), scale(v)) for k, v in graph['nodes'].items())
layout = [{'line': [nodes[i], nodes[j]]} for i, j in graph['edges'].values()]

file = open(args[1], 'w')
json.dump(layout, file)
file.close()
