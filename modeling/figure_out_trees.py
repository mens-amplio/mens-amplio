import math
import pprint

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
    degrees = 360 - ((degrees + 90) % 360)
    return degrees
  return foo

data.sort(key = z_sort)
base_rods = data[0:8]

middle_x = mean([x for ((x,y,z),_) in base_rods])
middle_y = mean([y for ((x,y,z),_) in base_rods])

children = {}

for rod in base_rods:
  children[rod] = []

# find the rod above each rod
# for rod in data[8:32]:
#   (upper_down, upper_up) = rod
#   parent = (sorted(children.keys(), key=lambda(lower_down,lower_up): distance_between(lower_up, upper_down) )[0])
#   children[parent].append(rod)
#   children[rod] = []

for rod in data[8:-1]:
  (upper_down, upper_up) = rod
  parent = sorted(data, key=lambda(lower_down,lower_up): distance_between(lower_up, upper_down) )[0]
  if not children.has_key(parent):
    children[parent] = []
  children[parent].append(rod)

def print_tree(rods, depth = 0, relative_to = (middle_x,middle_y)):
  if depth > 1:
    return
  for rod in sorted(rods,key=angle_sort(relative_to)):
    print (" " * (depth * 4)) + "x"+ " " + str(angle_sort(relative_to)(rod)) +" "+str(rod[0])
    if children.has_key(rod):
      print_tree(children[rod], depth + 1, (rod[1][0], rod[1][1]) )

#print_tree(base_rods)

def shift(rod, coords):
  ((x1,y1,z1),(x2,y2,z2)) = rod
  (x, y) = coords
  return ((x1-x,y1-y,z1),(x2-x,y2-y,z2))

def data_tree(rods, depth = 0, relative_to = (middle_x,middle_y)):
  r = []
  for rod in sorted(rods,key=angle_sort(relative_to)):
    d = []
    if children.has_key(rod):
      d = data_tree(children[rod], depth + 1, (rod[1][0], rod[1][1]) )
    r.append( (shift(rod, (middle_x, middle_y)), d) )
  return r

pprint.pprint(data_tree(base_rods))
