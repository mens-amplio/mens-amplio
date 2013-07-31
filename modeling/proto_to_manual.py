#!/usr/bin/env python
# ./proto_to_manual.py manual.prototree* > manual.remap.json

from __future__ import print_function
import math
import pprint
import json
import sys


f1 = open(sys.argv[1])
tree1 = json.load(f1)

f2 = open(sys.argv[2])
tree2 = json.load(f2)

offset = -1
output = {}

def replace_tree_part(address, tree):
  parts = address.split(".")
  parts[0] = str(tree)
  return(".".join(parts))

for repeat in range(3):
  for tree_index, tree in enumerate([tree1, tree2]):
    for address in sorted(tree.keys()):
      tree_number = 1 + tree_index + 2*repeat
      new_address = replace_tree_part(address, tree_number)
      output[new_address] = tree[address] + offset

  offset = max([output[x] for x in output]) - 1

print(json.dumps(output, sort_keys=True, indent=4, separators=(',', ': ')))
