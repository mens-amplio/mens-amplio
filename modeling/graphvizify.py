#!/usr/bin/env python
import json

data = json.load(open("graph.data.json"))

print "digraph {"
print "  graph [splines=false];"
for node_id in sorted(data["nodes"], key=int):
  print "  ", node_id, "[shape=point,label=\"\"]", ";"
for edge_id in sorted(data["edges"], key=int):
  edge = data["edges"][edge_id]
  start, stop = edge
  print "  ", start, " -> ", stop, "[arrowhead=none,label=\""+edge_id+"\"]", ";"
print "}"
