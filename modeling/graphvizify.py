#!/usr/bin/env python
import json

data = json.load(open("graph.data.json"))
remap = json.load(open("manual.remap.json"))

address_of_led = {str(v):k for k,v in remap.items()}

print "digraph {"
print "  graph [splines=false];"
for edge_id in sorted(data["edges"], key=address_of_led.get):
  edge = data["edges"][edge_id]
  start, stop = edge
  print "  ", start, " -> ", stop, "[arrowhead=none,label=\""+edge_id+"\"]", ";"
for node_id in sorted(data["nodes"], key=int):
  print "  ", node_id, "[shape=point,label=\"\"]", ";"
print "}"
