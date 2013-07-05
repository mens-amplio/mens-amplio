#!/usr/bin/env python
import sys
import json

graph_data = json.load(open(sys.argv[1]))
address_data = json.load(open(sys.argv[2]))
remap_data = json.load(open(sys.argv[3]))

output = {
    "edges": { int(remap_data[address_data[edge]]): graph_data["edges"][edge] for edge in graph_data["edges"] },
    "nodes": { int(node): graph_data["nodes"][node] for node in graph_data["nodes"] }
}

print(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))
