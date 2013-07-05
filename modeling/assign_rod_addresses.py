#!/usr/bin/env python
import sys
import json

data = json.load(open(sys.argv[1]))

# it's sort of cheating to know this but the 6 root branches are the lowest numbers
# because figure_out_graph uses Z index to assign the numbers
root_edges = [x for x in range(0,6)]

# recover int keys from jsonified structure :-(
edge_data = {int(key): data['edges'][key] for key in data['edges']}
node_data = {int(key): data['nodes'][key] for key in data['nodes']}

edge_parents = { x: None for x in root_edges }

edge_addr = { x: str(x) for x in root_edges }

child_count = { x: 0 for x in edge_data }

def edge_value(edge, d):
  if d == 1:
    # first branch is low, middle, high
    return node_data[edge_data[edge][1]][2] # Z-index
  return -node_data[edge_data[edge][1]][1] # Y-index

for depth in range(6):
  sorted_edges = sorted(edge_data, key=(lambda e: edge_value(e,depth)))
  unlinked_edges = [ x for x in sorted_edges if x not in edge_parents]
  existing_parents = {k:edge_parents[k] for k in edge_parents}
  for edge in unlinked_edges:
    for possible_parent in existing_parents:
      for vertex in edge_data[edge]:
        if vertex in edge_data[possible_parent]:
          if not edge in edge_parents:
            sys.stderr.write("parent of " + str(edge) + " is " +str( possible_parent ) + "\n")
            parent = possible_parent
            edge_parents[edge] = parent
            child_count[parent] += 1
            edge_addr[edge] = edge_addr[parent] + "." + str(child_count[parent])
  if not unlinked_edges:
    break

print(json.dumps(edge_addr, sort_keys=True, indent=4, separators=(',', ': ')))
