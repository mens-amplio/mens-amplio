#!/usr/bin/env python
import json

data = json.load(open("graph.data.json"))

print "digraph {"
for edge_id in data["edges"]:
  edge = data["edges"][edge_id]
  start, stop = edge
  print "  ", start, " -> ", stop, "[label=\""+edge_id+"\"]", ";"
print "}"
