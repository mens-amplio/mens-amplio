#!/usr/bin/env python

from __future__ import print_function
import math
import pprint
import json
import sys

number_of_roots = 6
minimum_rod_length = 17 # inches
point_merge_proximity = 3.0 # inches
recenter_coordinates = False

use_kludge_for_MA_Final = True

f = open(sys.argv[1])
data = eval(f.read())

# convert arrays to tuples
data = [tuple([tuple(point) for point in rod]) for rod in data]

def distance_between(p1, p2):
  return math.sqrt(sum( map( lambda(s):s*s, map( lambda(x,y):x-y, zip(p1, p2) ) ) ))

def how_long(c):
  return distance_between(c[0], c[1])

def mean(lst):
  return float(sum(lst))/len(lst) if len(lst) > 0 else float('nan')

# only keep the 18inch rods
data = [rod for rod in data if how_long(rod) > minimum_rod_length]

# flip each rod to be (lower, upper)
for index, rod in enumerate(data):
  ((x1,y1,z1), (x2,y2,z2)) = rod
  (first, second) = rod
  if(z1 > z2):
    data[index] = (second, first)

def z_sort(rod):
  ((x1,y1,z1), (x2,y2,z2)) = rod
  return z1

def angle_sort(point):
  def foo(rod):
    (x,y) = point
    ((x1,y1,z1), (x2,y2,z2)) = rod
    radians = math.atan2(y1 - y, x1 - x)
    degrees = radians * 180 / math.pi
    degrees = ((degrees + 90) % 360)
    return degrees
  return foo

data.sort(key = z_sort)
root_rods = data[0:number_of_roots]

middle_x = mean([x for ((x,y,z),_) in root_rods])
middle_y = mean([y for ((x,y,z),_) in root_rods])

def translate_rod_coordinates(rod, coords):
  ((x1,y1,z1),(x2,y2,z2)) = rod
  (x, y) = coords
  return ((x1-x,y1-y,z1),(x2-x,y2-y,z2))

if recenter_coordinates:
  # move things to be centered around 0,0
  data = [ translate_rod_coordinates(rod, (middle_x, middle_y)) for rod in data ]
  root_rods = data[0:number_of_roots]

# each neighborhood is a list of points that will get merged into a single node
neighborhoods = []

def find_neighborhood(p):
  found_neighborhood = None
  for neighborhood in neighborhoods:
    if found_neighborhood:
      break
    for neighbor in neighborhood:
      if distance_between(neighbor, p) < point_merge_proximity:
        found_neighborhood = neighborhood
        break
  if not found_neighborhood:
    found_neighborhood = []
    neighborhoods.append(found_neighborhood)
  found_neighborhood.append(p)

# sort each point into a neighborhood
for p1,p2 in data:
  find_neighborhood(p1)
  find_neighborhood(p2)


if use_kludge_for_MA_Final:
  # OKAY THIS IS THE MENS_AMPLIO SPECIAL CASE ZONE
  # Each tree in MA_Final has a place where 3 nodes are collapses into 1
  # in that neighborhood, we've got to restore the 3 incoming connections
  # to correct pairs of 6 outgoing connections.
  def subdivide_neighborhood(neighborhood):
    if len(neighborhood) != 9:
      return([neighborhood])
    # maybe it's just the 3 closest together?
    new_neighborhoods = []
    points = [p for p in neighborhood]
    for n in range(3):
      point = points.pop(0)
      points.sort(key=lambda p: distance_between(point, p))
      new_neighborhoods.append([point, points.pop(0), points.pop(0)])
    return new_neighborhoods

  neighborhoods = [n2 for n1 in neighborhoods for n2 in subdivide_neighborhood(n1)]

nodes = []
node_for_model_point = {}
n_lengths = {}
for neighborhood in neighborhoods:
  l = len(neighborhood)
  if l in n_lengths:
    n_lengths[l] += 1
  else:
    n_lengths[l] = 1
  center = tuple(map(mean, zip(*neighborhood)))
  nodes.append(center)
  for p in neighborhood:
    node_for_model_point[p] = center

#print(n_lengths, file=sys.stderr)

node_id = {}
for index, point in enumerate(nodes):
  node_id[point] = index

node_by_id = {index:node for node, index in node_id.items()}

edges = []

for rod in data:
  p1, p2 = rod
  if True or p1 in node_for_model_point and p2 in node_for_model_point:
    n1 = node_for_model_point[p1]
    n2 = node_for_model_point[p2]
    edge = (node_id[n1], node_id[n2])
    edges.append(edge)

edge_by_id = {index:edge for index, edge in enumerate(edges)}

output = {
  "nodes": node_by_id,
  "edges": edge_by_id
}

if (len(sys.argv) > 1) and sys.argv[1] == "python":
  pprint.pprint(output)
else:
  print(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))
