import math
import pprint
import json

f = open("../modeling/curve_endpoints.txt")
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
data = [rod for rod in data if how_long(rod) > 17]

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
base_rods = data[0:8]

middle_x = mean([x for ((x,y,z),_) in base_rods])
middle_y = mean([y for ((x,y,z),_) in base_rods])

def translate_rod_coordinates(rod, coords):
  ((x1,y1,z1),(x2,y2,z2)) = rod
  (x, y) = coords
  return ((x1-x,y1-y,z1),(x2-x,y2-y,z2))

# move things to be centered around 0,0
data = [ translate_rod_coordinates(rod, (middle_x, middle_y)) for rod in data ]
base_rods = data[0:8]

neighbor_proximity = 2.5
neighborhoods = []
def find_neighborhood(p):
  found_neighborhood = None
  for neighborhood in neighborhoods:
    if found_neighborhood:
      break
    for neighbor in neighborhood:
      if distance_between(neighbor, p) < neighbor_proximity:
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

nodes = []
node_for_model_point = {}

for neighborhood in neighborhoods:
  center = tuple(map(mean, zip(*neighborhood)))
  nodes.append(center)
  for p in neighborhood:
    node_for_model_point[p] = center

node_id = {}
for index, point in enumerate(nodes):
  node_id[point] = index

node_by_id = {index:node for node, index in node_id.items()}

edges = []

for rod in data:
  p1, p2 = rod
  n1 = node_for_model_point[p1]
  n2 = node_for_model_point[p2]
  edge = (node_id[n1], node_id[n2])
  edges.append(edge)

edge_by_id = {index:edge for index, edge in enumerate(edges)}

output = {
  "nodes": node_by_id,
  "edges": edge_by_id
}

#pprint.pprint(output)
print(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))
