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

while True:
  unlinked_edges = [ int(x) for x in data['edges'] if int(x) not in edge_parents]
  for edge in unlinked_edges:
    for possible_parent in edge_parents:
      for vertex in edge_data[edge]:
        if vertex in edge_data[possible_parent]:
          parent = possible_parent
          edge_parents[edge] = parent
          child_count[parent] += 1
          edge_addr[edge] = edge_addr[parent] + "." + str(child_count[parent])
          break
      else:
        continue
      break
  if not unlinked_edges:
    break

print(json.dumps(edge_addr, sort_keys=True, indent=4, separators=(',', ': ')))
