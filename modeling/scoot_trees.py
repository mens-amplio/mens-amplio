#!/usr/bin/env python

from __future__ import print_function
import math
import pprint
import json
import sys

f = open(sys.argv[1])
data = eval(f.read())

number_of_roots = 6
scoot_to_new_distance = 3.0

edge_by_id = { int(index): value for index,value in data["edges"].items() }
node_by_id = { int(index): value for index,value in data["nodes"].items() }

root_edges = [edge_by_id[i] for i in range(number_of_roots)]
def find_root_for_node(node, skip = None ):
  if not skip:
    skip = set()
  skip.update(set([node]))
  for index, edge in enumerate(root_edges):
    if node in edge:
      return index
  for edge_index, edge in edge_by_id.items():
    if node in edge:
      other_nodes = [n for n in edge if n not in skip]
      for other_node in other_nodes:
        r = find_root_for_node(other_node, skip)
        if r != None:
          return r

scoot_tree_by = []
for edge in root_edges:
  (x,y,z) = node_by_id[ edge[0] ]
  r = math.sqrt( x*x + y*y )
  theta = math.atan2(y, x)
  x2 = (r - scoot_to_new_distance) * math.cos(theta)
  y2 = (r - scoot_to_new_distance) * math.sin(theta)
  scoot_tree_by.append( (-x2,-y2) )
for index, node in node_by_id.items():
  root_index = find_root_for_node(index)
  (dx, dy) = scoot_tree_by[root_index]
  (x,y,z) = node
  node2 = (x+dx, y+dy, z)
  node_by_id[index] = node2

output = {
  "nodes": node_by_id,
  "edges": edge_by_id
}

if (len(sys.argv) > 1) and sys.argv[1] == "python":
  pprint.pprint(output)
else:
  print(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))
